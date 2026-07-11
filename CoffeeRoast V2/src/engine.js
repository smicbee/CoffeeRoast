export const RoastState=Object.freeze({IDLE:'idle',PREHEATING:'preheating',READY:'ready',RUNNING:'running',MANUAL:'manual',COOLING:'cooling',FAILSAFE:'failsafe'});

export class RoastEngine extends EventTarget{
  constructor(){
    super();this.transport=null;this.recipe=null;this.state=RoastState.IDLE;this.connected=false;this.preheatTarget=180;this.initialFanPercent=100;
    this.autoDropEnabled=false;this.autoDropMode='time';this.autoDropTarget=600;this.expectedFirstCrack=208;this.firstCrackSecond=-1;this.phase='idle';this.preparationStartedAt=0;
    this.elapsed=0;this.temperature=NaN;this.target=0;this.heater=0;this.fan=0;this.actualHeater=NaN;this.actualFan=NaN;this.status='';this.sensorErrors=0;this.samples=[];this.firmwareCompatibility={level:'unknown',label:'Unbekannt',compatible:false,reason:'Noch kein Firmwarestatus gelesen.'};this.firmwareVersion='';this.protocolVersion=0;this.hardwareId='';this.manualTarget=0;this.manualFanPercent=50;
    this.pid=new PidController();this.startedAt=0;this.timer=0;this.busy=false;
  }
  setTransport(transport){this.transport=transport}
  setRecipe(recipe){this.recipe=recipe;this.pid.configure(recipe?.pid||{});this.expectedFirstCrack=Number.isFinite(recipe?.expectedFirstCrack)?recipe.expectedFirstCrack:208;this.emit()}
  setAutoDrop(enabled,mode='time',target=600){this.autoDropEnabled=Boolean(enabled);this.autoDropMode=mode==='temperature'?'temperature':'time';this.autoDropTarget=Math.max(0,Number(target)||0);this.emit()}

  async connect(portOrRequest=true){
    if(!this.transport)throw new Error('Kein Transport gewählt');
    await this.transport.connect(portOrRequest);this.connected=true;
    try{const controller=await this.transport.getSnapshot();this.applyControllerSnapshot(controller);if(!this.firmwareCompatibility.compatible){await this.enterFailsafe(`Firmware nicht kompatibel: ${this.firmwareCompatibility.reason||'unbekannter Grund'}`)}else if(/failsafe/i.test(controller.state))await this.enterFailsafe('Controller meldet Failsafe');this.startPolling();this.emit()}
    catch(error){this.connected=false;await this.transport.disconnect(false);throw new Error(`Controller erkannt, aber Statusprotokoll ungültig: ${error.message}`)}
  }
  async disconnect(){this.stopPolling();if(this.transport)await this.transport.disconnect(true);this.connected=false;this.state=RoastState.IDLE;this.status='';this.target=0;this.heater=0;this.fan=0;this.actualHeater=NaN;this.actualFan=NaN;this.emit()}
  startPolling(){this.stopPolling();this.timer=window.setInterval(()=>this.tick(),500);this.tick()}
  stopPolling(){if(this.timer)clearInterval(this.timer);this.timer=0}
  async refreshStatus(){if(!this.connected)return'';const controller=await this.transport.getSnapshot();this.applyControllerSnapshot(controller);if(!this.firmwareCompatibility.compatible)await this.enterFailsafe(`Firmware nicht kompatibel: ${this.firmwareCompatibility.reason||'unbekannter Grund'}`);else if(/failsafe/i.test(controller.state))await this.enterFailsafe('Controller meldet Failsafe');this.emit();return this.status}

  async beginPreheat(){
    if(!this.connected||!this.recipe)throw new Error('Controller und Rezept werden benötigt.');
    if(this.state!==RoastState.IDLE)throw new Error('Lüftervorbereitung ist nur aus dem sicheren Leerlauf möglich.');
    if(this.firmwareCompatibility.level!=='unknown'&&!this.firmwareCompatibility.compatible)throw new Error(`Firmware nicht kompatibel: ${this.firmwareCompatibility.reason}`);
    this.samples=[];this.elapsed=0;this.startedAt=0;this.pid.reset();this.firstCrackSecond=-1;this.phase='preparation';this.preparationStartedAt=performance.now();
    this.state=RoastState.PREHEATING;this.target=0;this.fan=this.initialFanPercent/100*255;this.heater=0;
    await this.transport.setHeater(0);await this.transport.setFan(this.fan);this.emit();
  }
  beginRoast(){if(this.state!==RoastState.READY)return false;this.samples=[];this.elapsed=0;this.startedAt=performance.now();this.pid.reset();this.firstCrackSecond=-1;this.phase='charging';this.state=RoastState.RUNNING;this.emit();return true}
  async setManualControl(targetTemperature,fanPercent){if(!this.connected)throw new Error('Controller nicht verbunden.');if(![RoastState.IDLE,RoastState.READY,RoastState.MANUAL].includes(this.state))throw new Error('Manueller Modus ist nur aus Leerlauf oder Bereit möglich.');this.manualTarget=clamp(targetTemperature,0,250);this.manualFanPercent=clamp(fanPercent,0,100);if(this.manualTarget>0)this.manualFanPercent=Math.max(50,this.manualFanPercent);if(this.state!==RoastState.MANUAL){this.samples=[];this.elapsed=0;this.startedAt=performance.now();this.pid.reset();this.state=RoastState.MANUAL;this.phase='manual'}this.target=this.manualTarget;this.fan=Math.max(this.manualTarget>0?128:0,this.manualFanPercent/100*255);this.heater=0;await this.transport.setHeater(0);await this.transport.setFan(this.fan);this.status=`Manuell: ${this.manualTarget} °C · Lüfter ${this.manualFanPercent} %`;this.emit()}
  async coolDown(reason='Manuell beendet'){if(!this.connected)return;this.state=RoastState.COOLING;this.phase='cooling';this.target=0;this.heater=0;this.status=reason;await this.transport.setHeater(0);await this.transport.setFan(255);this.fan=255;this.emit()}
  async enterFailsafe(reason){this.state=RoastState.FAILSAFE;this.target=0;this.heater=0;this.fan=255;this.status=reason;try{await this.transport?.safeOutputs()}catch{}this.emit()}

  async tick(){
    if(this.busy||!this.connected||!this.transport)return;this.busy=true;
    try{
      const controller=await this.transport.getSnapshot();
      this.applyControllerSnapshot(controller);
      if(!this.firmwareCompatibility.compatible){await this.enterFailsafe(`Firmware nicht kompatibel: ${this.firmwareCompatibility.reason||'unbekannter Grund'}`);return}
      this.validateTemperature(controller.temperature);
      if(/failsafe/i.test(controller.state))await this.enterFailsafe('Firmware meldet Failsafe');
      if(this.state===RoastState.FAILSAFE)return;

      if(this.state===RoastState.RUNNING||this.state===RoastState.MANUAL)this.elapsed=Math.max(0,(performance.now()-this.startedAt)/1000);
      this.calculateOutputs();
      await this.transport.setFan(this.fan);
      const heating=this.state===RoastState.RUNNING||this.state===RoastState.MANUAL;
      const requiredFan=requestedFanMinimum(this.heater),fanConfirmed=Number.isFinite(this.actualFan)&&this.actualFan>=requiredFan;
      const requestedHeater=this.heater,safeHeater=heating&&!fanConfirmed?0:requestedHeater;
      await this.transport.setHeater(safeHeater);
      this.heater=requestedHeater;
      if(this.state!==RoastState.IDLE||Number.isFinite(this.temperature))this.recordSample();
      await this.handleTransitions();
    }catch(error){this.sensorErrors+=5;this.status=error.message;if(this.sensorErrors>20)await this.enterFailsafe(`Kommunikation/Sensor ausgefallen: ${error.message}`)}
    finally{this.busy=false;this.emit()}
  }

  calculateOutputs(){
    const baseFan=this.initialFanPercent/100*255;
    if(this.state===RoastState.PREHEATING){this.target=0;this.fan=baseFan;this.heater=0}
    else if(this.state===RoastState.RUNNING){const second=clamp(Math.floor(this.elapsed),0,this.recipe.profile.length-1);this.target=this.recipe.profile[second];this.fan=calculateFan(this.temperature,baseFan);this.heater=this.pid.update(this.elapsed,this.temperature,this.recipe.profile)}
    else if(this.state===RoastState.MANUAL){this.target=this.manualTarget;this.fan=Math.max(this.manualTarget>0?128:0,this.manualFanPercent/100*255);this.heater=this.manualTarget>0?this.pid.update(this.elapsed,this.temperature,[this.manualTarget]):0}
    else if(this.state===RoastState.READY){this.target=0;this.heater=0;this.fan=baseFan}
    else if(this.state===RoastState.COOLING){this.target=0;this.heater=0;this.fan=255}
    else if(this.state===RoastState.FAILSAFE){this.target=0;this.heater=0;this.fan=255}
    else{this.target=0;this.heater=0;this.fan=Number.isFinite(this.temperature)&&this.temperature>=60?calculateFan(this.temperature,baseFan):0}
  }
  applyControllerSnapshot(c){this.status=c.raw;this.temperature=c.temperature;this.actualHeater=c.heater;this.actualFan=c.fan;this.sensorErrors=Math.max(this.sensorErrors,c.errors||0);this.firmwareCompatibility=c.compatibility||{level:'legacy',label:'Legacy-Firmware',compatible:true,reason:'Statusprotokoll ohne Versionsmetadaten.'};this.firmwareVersion=c.version||'';this.protocolVersion=c.protocol||0;this.hardwareId=c.hardware||''}
  validateTemperature(temp){if(!Number.isFinite(temp)||temp<-50||temp>450)this.sensorErrors+=5;else this.sensorErrors=Math.max(0,this.sensorErrors-1);if(this.sensorErrors>20)this.enterFailsafe('Unplausible Thermoelement-Messwerte')}

  async handleTransitions(){
    if(this.state===RoastState.PREHEATING&&performance.now()-this.preparationStartedAt>10000&&!(Number.isFinite(this.actualFan)&&this.actualFan>=40)){await this.enterFailsafe('Vorbereitung fehlgeschlagen: Lüfterstart nicht bestätigt');return}
    if(this.state===RoastState.PREHEATING&&Number.isFinite(this.actualFan)&&this.actualFan>=40){this.state=RoastState.READY;this.phase='ready';this.target=0;this.heater=0;this.status='Lüftergeschwindigkeit bestätigt – bereit zum Rösten';await this.transport.setHeater(0)}
    if(this.state===RoastState.RUNNING){
      const ror=this.currentRoR();if(this.expectedFirstCrack>0&&this.firstCrackSecond<0&&this.temperature>=this.expectedFirstCrack)this.firstCrackSecond=Math.round(this.elapsed);this.phase=detectPhase(this.temperature,ror,this.elapsed,this.firstCrackSecond,this.expectedFirstCrack);
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
  snapshot(){return{state:this.state,connected:this.connected,elapsed:this.elapsed,temperature:this.temperature,target:this.target,heater:Number.isFinite(this.actualHeater)?this.actualHeater:this.heater,fan:Number.isFinite(this.actualFan)?this.actualFan:this.fan,heaterTarget:this.heater,fanTarget:this.fan,status:this.status,sensorErrors:this.sensorErrors,samples:this.samples,recipe:this.recipe,autoDropEnabled:this.autoDropEnabled,autoDropMode:this.autoDropMode,autoDropTarget:this.autoDropTarget,expectedFirstCrack:this.expectedFirstCrack,firstCrackSecond:this.firstCrackSecond,ror:this.currentRoR(),phase:this.phase,portName:this.transport?.portName||'',firmwareCompatibility:this.firmwareCompatibility,firmwareVersion:this.firmwareVersion,protocolVersion:this.protocolVersion,hardwareId:this.hardwareId,manualTarget:this.manualTarget,manualFanPercent:this.manualFanPercent}}
  emit(){this.dispatchEvent(new CustomEvent('update',{detail:this.snapshot()}))}
}

export function calibratePidFromSamples(samples,current={}){const valid=(samples||[]).filter(s=>s?.state===RoastState.RUNNING&&Number.isFinite(s.temperature)&&Number.isFinite(s.target)&&s.target>0&&Number.isFinite(s.heater));if(valid.length<30)throw new Error('Mindestens 30 Messpunkte einer laufenden Röstung werden benötigt.');const errors=valid.map(s=>s.target-s.temperature),meanError=errors.reduce((a,b)=>a+b,0)/errors.length,rmse=Math.sqrt(errors.reduce((a,b)=>a+b*b,0)/errors.length),ceilingRate=valid.filter(s=>(Number.isFinite(s.heaterTarget)?s.heaterTarget:s.heater)>=165).length/valid.length,overshootRate=errors.filter(e=>e<-3).length/errors.length;let factor=Math.exp(meanError/60)*(1+ceilingRate*.35);if(overshootRate>.2)factor*=.8;factor=clamp(factor,.55,3);const kp=clamp(finite(current.kp,3)*factor,.1,20),kiBase=Math.max(finite(current.ki,.02),meanError>4?.01:0),ki=clamp(kiBase*factor*(meanError>4?1.2:.9),0,1),kd=clamp(finite(current.kd,.2)*clamp(1/Math.sqrt(factor),.7,1.2),0,20);return{kp,ki,kd,metrics:{sampleCount:valid.length,meanError,rmse,ceilingRate,overshootRate,factor}}}

class PidController{
  constructor(){this.configure({});this.reset()}
  configure({kp=3,ki=.02,kd=.2,future=40}){this.kp=finite(kp,3);this.ki=finite(ki,.02);this.kd=finite(kd,.2);this.future=finite(future,40)}
  reset(){this.integral=0;this.previousError=0;this.previousTime=-1;this.lastOutput=0}
  update(time,temp,profile){if(!Number.isFinite(temp))return 0;const targetTime=clamp(Math.round(time+this.future),0,profile.length-1),target=profile[targetTime],error=target-temp,dt=this.previousTime>=0?time-this.previousTime:0;if(dt>0&&dt<3)return this.lastOutput;if(dt>0)this.integral=clamp(this.integral+error*dt,-5000,5000);const derivative=dt>0?(error-this.previousError)/dt:0;let kp=temp<100?this.kp*.6:this.kp,ki=this.ki,kd=this.kd;kp*=1+.2*temp/220;if(temp>190){kp*=.8;ki*=.5;kd*=1.2}let output=kp*error+ki*this.integral+kd*derivative;this.previousError=error;this.previousTime=time;this.lastOutput=clamp(output,0,255);return this.lastOutput}
}
function requestedFanMinimum(heater){return Number(heater)>0?128:0}
function calculateFan(temp,initial){const min=Math.max(128,initial*.7);if(!Number.isFinite(temp)||temp<=100)return initial;if(temp>=230)return min;return clamp(initial-(initial-min)*(temp-100)**2/130**2,0,255)}
function detectPhase(temp,ror,elapsed,firstCrack,expected){if(elapsed<60&&Number.isFinite(ror)&&ror<0)return'charging';if(firstCrack>=0&&elapsed>firstCrack)return temp>235?'second-crack':'development';if(expected>0&&temp>=expected-5&&temp<=expected+10)return'first-crack';if(temp>=150)return'maillard';if(temp>0)return'drying';return'idle'}
function finite(value,fallback){value=Number(value);return Number.isFinite(value)?value:fallback}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||0))}
