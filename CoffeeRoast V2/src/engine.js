export const RoastState = Object.freeze({ IDLE:'idle', PREHEATING:'preheating', READY:'ready', RUNNING:'running', COOLING:'cooling', FAILSAFE:'failsafe' });

export class RoastEngine extends EventTarget {
  constructor() {
    super();
    this.transport = null;
    this.recipe = null;
    this.state = RoastState.IDLE;
    this.connected = false;
    this.preheatTarget = 180;
    this.initialFanPercent = 100;
    this.stopAt = -1;
    this.elapsed = 0;
    this.temperature = NaN;
    this.target = 0;
    this.heater = 0;
    this.fan = 0;
    this.status = '';
    this.sensorErrors = 0;
    this.samples = [];
    this.pid = new PidController();
    this.startedAt = 0;
    this.timer = 0;
    this.busy = false;
  }

  setTransport(transport) { this.transport = transport; }
  setRecipe(recipe) {
    this.recipe = recipe;
    this.pid.configure(recipe?.pid || {});
    this.stopAt = -1;
    this.emit();
  }
  setRoastLevel(level) { this.stopAt = !level || !this.recipe ? -1 : this.recipe.roastLevels[level - 1] ?? -1; this.emit(); }

  async connect() {
    if (!this.transport) throw new Error('Kein Transport gewählt');
    await this.transport.connect();
    this.connected = true;
    this.status = await this.transport.getStatus();
    if (/failsafe/i.test(this.status)) await this.enterFailsafe('Controller meldet Failsafe');
    this.startPolling(); this.emit();
  }

  async disconnect() {
    this.stopPolling();
    if (this.transport) await this.transport.disconnect(true);
    this.connected = false; this.state = RoastState.IDLE; this.status = ''; this.target = 0; this.heater = 0; this.fan = 0; this.emit();
  }

  startPolling() { this.stopPolling(); this.timer = window.setInterval(() => this.tick(), 500); this.tick(); }
  stopPolling() { if (this.timer) clearInterval(this.timer); this.timer = 0; }

  async refreshStatus() {
    if (!this.connected) return '';
    this.status = await this.transport.getStatus();
    if (/failsafe/i.test(this.status)) await this.enterFailsafe('Controller meldet Failsafe');
    this.emit(); return this.status;
  }

  async beginPreheat() {
    if (!this.connected || !this.recipe) throw new Error('Controller und Rezept werden benötigt.');
    this.samples = []; this.elapsed = 0; this.startedAt = performance.now(); this.pid.reset();
    this.state = RoastState.PREHEATING; this.target = this.preheatTarget; this.emit();
  }

  beginRoast() {
    if (this.state !== RoastState.READY && this.state !== RoastState.COOLING) return;
    this.samples = []; this.elapsed = 0; this.startedAt = performance.now(); this.pid.reset(); this.state = RoastState.RUNNING; this.emit();
  }

  async coolDown(reason = 'Manuell beendet') {
    if (!this.connected) return;
    this.state = RoastState.COOLING; this.target = 0; this.heater = 0; this.status = reason;
    await this.transport.setHeater(0); await this.transport.setFan(255); this.fan = 255; this.emit();
  }

  async enterFailsafe(reason) {
    this.state = RoastState.FAILSAFE; this.target = 0; this.heater = 0; this.fan = 255; this.status = reason;
    try { await this.transport?.safeOutputs(); } catch {} this.emit();
  }

  async tick() {
    if (this.busy || !this.connected || !this.transport) return;
    this.busy = true;
    try {
      if ([RoastState.PREHEATING,RoastState.RUNNING].includes(this.state)) this.elapsed = Math.max(0, (performance.now() - this.startedAt) / 1000);
      await this.calculateOutputs();
      await this.transport.setHeater(this.heater);
      await this.transport.setFan(this.fan);
      const temp = await this.transport.getTemperature();
      this.validateTemperature(temp);
      if (this.state === RoastState.FAILSAFE) return;
      this.temperature = temp;
      if (this.state !== RoastState.IDLE || Number.isFinite(temp)) this.recordSample();
      this.handleTransitions();
    } catch (error) {
      this.sensorErrors += 5;
      this.status = error.message;
      if (this.sensorErrors > 20) await this.enterFailsafe(`Kommunikation/Sensor ausgefallen: ${error.message}`);
    } finally { this.busy = false; this.emit(); }
  }

  async calculateOutputs() {
    const baseFan = this.initialFanPercent / 100 * 255;
    if (this.state === RoastState.PREHEATING) {
      this.target = this.preheatTarget;
      this.fan = baseFan;
      const error = this.target - (Number.isFinite(this.temperature) ? this.temperature : 25);
      this.heater = clamp(80 + error * 1.35, 0, 210);
    } else if (this.state === RoastState.RUNNING) {
      const second = clamp(Math.floor(this.elapsed), 0, this.recipe.profile.length - 1);
      this.target = this.recipe.profile[second];
      this.fan = calculateFan(this.temperature, baseFan);
      this.heater = this.pid.update(this.elapsed, this.temperature, this.recipe.profile);
    } else if (this.state === RoastState.READY) {
      this.target = this.preheatTarget; this.heater = 0; this.fan = baseFan;
    } else if (this.state === RoastState.COOLING || this.state === RoastState.FAILSAFE) {
      this.target = 0; this.heater = 0; this.fan = 255;
    } else {
      this.target = 0; this.heater = 0; this.fan = Number.isFinite(this.temperature) && this.temperature >= 60 ? calculateFan(this.temperature, baseFan) : 0;
    }
  }

  validateTemperature(temp) {
    if (!Number.isFinite(temp) || temp < -50 || temp > 450) this.sensorErrors += 5;
    else this.sensorErrors = Math.max(0, this.sensorErrors - 1);
    if (this.sensorErrors > 20) this.enterFailsafe('Unplausible Thermoelement-Messwerte');
  }

  handleTransitions() {
    if (this.state === RoastState.PREHEATING && this.temperature >= this.preheatTarget) { this.state = RoastState.READY; this.heater = 0; this.status = 'Vorheizen abgeschlossen – Bohnen einfüllen'; }
    if (this.state === RoastState.RUNNING) {
      if (this.elapsed >= this.recipe.duration || (this.stopAt >= 0 && this.elapsed >= this.stopAt)) this.coolDown('Röstprofil abgeschlossen');
    }
    if (this.state === RoastState.COOLING && this.temperature < 60) { this.state = RoastState.IDLE; this.heater = 0; this.fan = 0; this.status = 'Abkühlen abgeschlossen'; }
  }

  recordSample() {
    const previous = this.samples[this.samples.length - 1];
    const sample = { time: this.elapsed, temperature: this.temperature, target: this.target, heater: this.heater, fan: this.fan, state: this.state, recordedAt: new Date().toISOString() };
    if (!previous || sample.time - previous.time >= .45 || sample.state !== previous.state) this.samples.push(sample);
  }

  snapshot() { return { state:this.state, connected:this.connected, elapsed:this.elapsed, temperature:this.temperature, target:this.target, heater:this.heater, fan:this.fan, status:this.status, sensorErrors:this.sensorErrors, samples:this.samples, recipe:this.recipe, stopAt:this.stopAt, portName:this.transport?.portName || '' }; }
  emit() { this.dispatchEvent(new CustomEvent('update', { detail: this.snapshot() })); }
}

class PidController {
  constructor() { this.configure({}); this.reset(); }
  configure({ kp=3, ki=.02, kd=.2, future=40 }) { this.kp=finite(kp,3); this.ki=finite(ki,.02); this.kd=finite(kd,.2); this.future=finite(future,40); }
  reset(){ this.integral=0; this.previousError=0; this.previousTime=-1; this.lastOutput=0; }
  update(time,temp,profile){
    if(!Number.isFinite(temp)) return 0;
    const targetTime=clamp(Math.round(time+this.future),0,profile.length-1), target=profile[targetTime], error=target-temp;
    const dt=this.previousTime>=0?time-this.previousTime:0;
    if(dt>0&&dt<2.5)return this.lastOutput;
    if(dt>0)this.integral=clamp(this.integral+error*dt,-5000,5000);
    const derivative=dt>0?(error-this.previousError)/dt:0;
    let kp=temp<100?this.kp*.6:this.kp,ki=this.ki,kd=this.kd;
    kp*=1+.2*(temp/220);if(temp>190){kp*=.8;ki*=.5;kd*=1.2}
    let output=kp*error+ki*this.integral+kd*derivative;if(time<120)output=Math.min(output,170);
    this.previousError=error;this.previousTime=time;this.lastOutput=clamp(output,0,255);return this.lastOutput;
  }
}
function calculateFan(temp, initial){const min=Math.max(128,initial*.7);if(!Number.isFinite(temp)||temp<=100)return initial;if(temp>=230)return min;const progress=(temp-100)**2/130**2;return clamp(initial-(initial-min)*progress,0,255)}
function finite(v,f){v=Number(v);return Number.isFinite(v)?v:f}function clamp(v,a,b){return Math.max(a,Math.min(b,Number(v)||0))}
