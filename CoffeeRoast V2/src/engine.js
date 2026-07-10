export const RoastState=Object.freeze({IDLE:'idle',PREHEATING:'preheating',READY:'ready',RUNNING:'running',COOLING:'cooling',FAILSAFE:'failsafe'});

export class RoastEngine extends EventTarget{
  constructor(){
    super();this.transport=null;this.recipe=null;this.state=RoastState.IDLE;this.connected=false;this.initialFanPercent=100;
    this.autoDropEnabled=false;this.autoDropMode='time';this.autoDropTarget=600;this.expectedFirstCrack=208;this.firstCrackSecond=-1;this.phase='idle';this.preparationStartedAt=0;
    this.elapsed=0;this.temperature=NaN;this.target=0;this.heater=0;this.fan=0;this.actualHeater=NaN;this.actualFan=NaN;this.status='';this.sensorErrors=0;this.samples=[];
    this.pid=new PidController();this.startedAt=0;this.timer=0;this.busy=false;
  }
  setTransport(transport){this.transport=transport}
  setRecipe(recipe){this.recipe=recipe;this.pid.configure(recipe?.pid||{});this.expectedFirstCrack=recipe?.expectedFirstCrack||208;this.emit()}
  setAutoDrop(enabled,mode='time',target=600){this.autoDropEnabled=Boolean(enabled);this.autoDropMode=mode==='temperature'?'temperature':'time';this.autoDropTarget=Math.max(0,Number(target)||0);this.emit()}

  async connect(){
    if(!this.transport)throw new Error('Kein Transport gewählt');
    await this.transport.connect();this.connected=true;
    try{const controller=await this.transport.getSnapshot();this.applyControllerSnapshot(controller);if(/failsafe/i.test(controller.state))await this.enterFailsafe('Controller meldet Failsafe');this.startPolling();this.emit()}
    catch(error){this.connected=false;await this.transport.disconnect(false);throw new Error(`Controller erkannt, aber Statusprotokoll ungültig: ${error.message}`)}
  }
  async disconnect(){this.stopPolling();if(this.transport)await this.transport.disconnect(true);this.connected=false;this.state=RoastState.IDLE;this.status='';this.target=0;this.heater=0;this.fan=0;this.actualHeater=NaN;this.actualFan=NaN;this.emit()}
  startPolling(){this.stopPolling();this.timer=window.setInterval(()=>this.tick(),500);this.tick()}
  stopPolling(){if(this.timer)clearInterval(this.timer);this.timer=0}
  async refreshStatus(){if(!this.connected)return'';const controller=await this.transport.getSnapshot();this.applyControllerSnapshot(controller);if(/failsafe/i.test(controller.state))await this.enterFailsafe('Controller meldet Failsafe');this.emit();return this.status}

  async beginPreheat(){
    if(!this.connected||!this.recipe)throw new Error('Controller und Rezept werden benötigt.');
    this.samples=[];this.elapsed=0;this.startedAt=0;this.pid.reset();this.firstCrackSecond=-1;this.phase='preparation';this.preparationStartedAt=performance.now();
    this.state=RoastState.PREHEATING;this.target=0;this.fan=this.initialFanPercent/100*255;this.heater=0;
    await this.transport.setFan(this.fan);await this.transport.setHeater(0);this.emit();
  }
  beginRoast(){if(this.state!==RoastState.READY&&this.state!==RoastState.COOLING)return;this.samples=[];this.elapsed=0;this.startedAt=performance.now();this.pid.reset();this.firstCrackSecond=-1;this.phase='charging';this.state=RoastState.RUNNING;this.emit()}
  async coolDown(reason='Manuell beendet'){if(!this.connected)return;this.state=RoastState.COOLING;this.phase='cooling';this.target=0;this.heater=0;this.status=reason;await this.transport.setHeater(0);await this.transport.setFan(255);this.fan=255;this.emit()}
  async enterFailsafe(reason){this.state=RoastState.FAILSAFE;this.target=0;this.heater=0;this.fan=255;this.status=reason;try{await this.transport?.safeOutputs()}catch{}this.emit()}

  async tick(){
    if(this.busy||!this.connected||!this.transport)return;this.busy=true;
    try{
      if(this.state===RoastState.RUNNING)this.elapsed=Math.max(0,(performance.now()-this.startedAt)/1000);
      this.calculateOutputs();
      await this.transport.setFan(this.fan);
      const heating=this.state===RoastState.PREHEATING||this.state===RoastState.RUNNING;
      const fanConfirmed=Number.isFinite(this.actualFan)&&this.actualFan>=40;
      const requestedHeater=this.heater,safeHeater=heating&&!fanConfirmed?0:requestedHeater;
      await this.transport.setHeater(safeHeater);
      const controller=await this.transport.getSnapshot();this.applyControllerSnapshot(controller);this.heater=requestedHeater;this.validateTemperature(controller.temperature);
      if(/failsafe/i.test(controller.state))await this.enterFailsafe('Firmware meldet Failsafe');
      if(this.state===RoastState.FAILSAFE)return;
      if(this.state!==RoastState.IDLE||Number.isFinite(this.temperature))this.recordSample();
      await this.handleTransitions();
    }catch(error){this.sensorErrors+=5;this.status=error.message;if(this.sensorErrors>20)await this.enterFailsafe(`Kommunikation/Sensor ausgefallen: ${error.message}`)}
    finally{this.busy=false;this.emit()}
  }

  calculateOutputs(){
    const baseFan=this.initialFanPercent/100*255;
    if(this.state===RoastState.PREHEATING){this.target=0;this.fan=baseFan;this.heater=0}
    else if(this.state===RoastState.RUNNING){const second=clamp(Math.floor(this.elapsed),0,this.recipe.profile.length-1);this.target=this.recipe.profile[second];this.fan=calculateFan(this.temperature,baseFan);this.heater=this.pid.update(this.elapsed,this.temperature,this.recipe.profile)}
    else if(this.state===RoastState.READY){this.target=0;this.heater=0;this.fan=baseFan}
    else if(this.state===RoastState.COOLING){this.target=0;this.heater=0;this.fan=Number.isFinite(this.temperature)&&this.temperature<60?0:calculateFan(this.temperature,baseFan)}
    else if(this.state===RoastState.FAILSAFE){this.target=0;this.heater=0;this.fan=255}
    else{this.target=0;this.heater=0;this.fan=Number.isFinite(this.temperature)&&this.temperature>=60?calculateFan(this.temperature,baseFan):0}
  }
  applyControllerSnapshot(c){this.status=c.raw;this.temperature=c.temperature;this.actualHeater=c.heater;this.actualFan=c.fan;this.sensorErrors=Math.max(this.sensorErrors,c.errors||0)}
  validateTemperature(temp){if(!Number.isFinite(temp)||temp<-50||temp>450)this.sensorErrors+=5;else this.sensorErrors=Math.max(0,this.sensorErrors-1);if(this.sensorErrors>20)this.enterFailsafe('Unplausible Thermoelement-Messwerte')}

  async handleTransitions(){
    if(this.state===RoastState.PREHEATING&&performance.now()-this.preparationStartedAt>10000&&(!(this.temperature>0)||!(Number.isFinite(this.actualFan)&&this.actualFan>=40))){await this.enterFailsafe('Vorbereitung fehlgeschlagen: Temperatur oder Lüfterstart nicht bestätigt');return}
    if(this.state===RoastState.PREHEATING&&this.temperature>0&&Number.isFinite(this.actualFan)&&this.actualFan>=40){this.state=RoastState.READY;this.phase='ready';this.heater=0;this.status='Vorbereitung abgeschlossen – Temperatur gültig, Lüfter bestätigt';await this.transport.setHeater(0)}
    if(this.state===RoastState.RUNNING){
      const ror=this.currentRoR();if(this.firstCrackSecond<0&&this.temperature>=this.expectedFirstCrack)this.firstCrackSecond=Math.round(this.elapsed);this.phase=detectPhase(this.temperature,ror,this.elapsed,this.firstCrackSecond,this.expectedFirstCrack);
      const autoDrop=this.autoDropEnabled&&((this.autoDropMode==='time'&&this.elapsed>=this.autoDropTarget)||(this.autoDropMode==='temperature'&&this.temperature>=this.autoDropTarget));
      if(this.elapsed>=this.recipe.duration||autoDrop)await this.coolDown(autoDrop?'Auto-Drop erreicht':'Röstprofil abgeschlossen');
    }
    if(this.state===RoastState.COOLING&&this.temperature<60){this.state=RoastState.IDLE;this.phase='cooling';this.heater=0;this.fan=0;this.status='Abkühlen abgeschlossen';await this.transport.setHeater(0);await this.transport.setFan(0)}
  }
  currentRoR(){return this.samples.length?this.samples[this.samples.length-1].ror:NaN}
  recordSample(){
    const previous=this.samples[this.samples.length-1];let reference=null;for(const item of this.samples){if(item.time<=this.elapsed-30)reference=item;else break}
    const ror=reference&&this.elapsed>reference.time?(this.temperature-reference.temperature)/(this.elapsed-reference.time)*60:NaN;
    const sample={time:this.elapsed,temperature:this.temperature,target:this.target,heater:Number.isFinite(this.actualHeater)?this.actualHeater:this.heater,fan:Number.isFinite(this.actualFan)?this.actualFan:this.fan,heaterTarget:this.heater,fanTarget:this.fan,ror,phase:this.phase,state:this.state,recordedAt:new Date().toISOString()};
    if(!previous||sample.time-previous.time>=.45||sample.state!==previous.state)this.samples.push(sample)
  }
  snapshot(){return{state:this.state,connected:this.connected,elapsed:this.elapsed,temperature:this.temperature,target:this.target,heater:Number.isFinite(this.actualHeater)?this.actualHeater:this.heater,fan:Number.isFinite(this.actualFan)?this.actualFan:this.fan,heaterTarget:this.heater,fanTarget:this.fan,status:this.status,sensorErrors:this.sensorErrors,samples:this.samples,recipe:this.recipe,autoDropEnabled:this.autoDropEnabled,autoDropMode:this.autoDropMode,autoDropTarget:this.autoDropTarget,expectedFirstCrack:this.expectedFirstCrack,firstCrackSecond:this.firstCrackSecond,ror:this.currentRoR(),phase:this.phase,portName:this.transport?.portName||''}}
  emit(){this.dispatchEvent(new CustomEvent('update',{detail:this.snapshot()}))}
}

class PidController{
  constructor(){this.configure({});this.reset()}
  configure({kp=3,ki=.02,kd=.2,future=40}){this.kp=finite(kp,3);this.ki=finite(ki,.02);this.kd=finite(kd,.2);this.future=finite(future,40)}
  reset(){this.integral=0;this.previousError=0;this.previousTime=-1;this.lastOutput=0}
  update(time,temp,profile){if(!Number.isFinite(temp))return 0;const targetTime=clamp(Math.round(time+this.future),0,profile.length-1),target=profile[targetTime],error=target-temp,dt=this.previousTime>=0?time-this.previousTime:0;if(dt>0&&dt<3)return this.lastOutput;if(dt>0)this.integral=clamp(this.integral+error*dt,-5000,5000);const derivative=dt>0?(error-this.previousError)/dt:0;let kp=temp<100?this.kp*.6:this.kp,ki=this.ki,kd=this.kd;kp*=1+.2*temp/220;if(temp>190){kp*=.8;ki*=.5;kd*=1.2}let output=kp*error+ki*this.integral+kd*derivative;if(time<120)output=Math.min(output,170);this.previousError=error;this.previousTime=time;this.lastOutput=clamp(output,0,255);return this.lastOutput}
}
function calculateFan(temp,initial){const min=Math.max(128,initial*.7);if(!Number.isFinite(temp)||temp<=100)return initial;if(temp>=230)return min;return clamp(initial-(initial-min)*(temp-100)**2/130**2,0,255)}
function detectPhase(temp,ror,elapsed,firstCrack,expected){if(elapsed<60&&Number.isFinite(ror)&&ror<0)return'charging';if(firstCrack>=0&&elapsed>firstCrack)return temp>235?'second-crack':'development';if(temp>=expected-5&&temp<=expected+10)return'first-crack';if(temp>=150)return'maillard';if(temp>0)return'drying';return'idle'}
function finite(value,fallback){value=Number(value);return Number.isFinite(value)?value:fallback}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||0))}
