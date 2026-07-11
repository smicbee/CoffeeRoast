const encoder = new TextEncoder();
export const EXPECTED_FIRMWARE = Object.freeze({
  product: 'CoffeeRoast',
  protocol: 3,
  hardware: 'CoffeeRoast-Waveshare-ESP32-S3-Zero',
  minimumVersion: '1.3.2'
});

export class WebSerialTransport {
  constructor(onLog = () => {}) {
    this.port = null;
    this.reader = null;
    this.readBuffer = '';
    this.lines = [];
    this.waiters = [];
    this.onLog = onLog;
    this.connected = false;
    this.portName = 'USB-Controller';
    this.operationQueue = Promise.resolve();
    this.failsafeSeen = false;
  }

  static isSupported() { return 'serial' in navigator; }

  async connect(portOrRequest = true) {
    if (!WebSerialTransport.isSupported()) throw new Error('Web Serial wird von diesem Browser nicht unterstützt. Bitte Chrome oder Edge verwenden.');
    const port = typeof portOrRequest === 'object' && portOrRequest
      ? portOrRequest
      : portOrRequest
        ? await navigator.serial.requestPort()
        : (await navigator.serial.getPorts())[0];
    if (!port) throw new Error('Noch kein Controller für diese Website freigegeben.');
    await port.open({ baudRate: 115200, dataBits: 8, stopBits: 1, parity: 'none', flowControl: 'none', bufferSize: 4096 });
    this.port = port;
    this.connected = true;
    const info = port.getInfo?.() || {};
    this.portName = info.usbVendorId ? `USB ${hex(info.usbVendorId)}:${hex(info.usbProductId || 0)}` : 'Serieller Controller';
    this.readLoop();
    try {
      try { await port.setSignals?.({ dataTerminalReady: true, requestToSend: false }); } catch {}
      const answer = await this.handshake();
      this.log('✓ Controller erkannt: popcorn roaster');
      return answer;
    } catch (error) {
      await this.disconnect(false);
      throw error;
    }
  }

  async handshake(timeout = 10000) {
    const deadline = performance.now() + timeout;
    await delay(900);
    while (performance.now() < deadline) {
      await this.writeRaw('hello');
      try {
        return await this.readMatchingLine(line => line.trim().toLowerCase() === 'popcorn roaster', Math.min(1500, Math.max(100, deadline - performance.now())));
      } catch {}
      await delay(250);
    }
    throw new Error(`Keine Antwort auf "hello" innerhalb von ${Math.round(timeout / 1000)} Sekunden. Prüfe den COM-Port und schließe andere Serial-Monitore.`);
  }

  async readLoop() {
    try {
      this.reader = this.port.readable.getReader();
      const decoder = new TextDecoder();
      while (this.connected) {
        const { value, done } = await this.reader.read();
        if (done) break;
        this.readBuffer += decoder.decode(value, { stream: true });
        const chunks = this.readBuffer.split(/\r?\n/);
        this.readBuffer = chunks.pop() || '';
        chunks.forEach(line => this.pushLine(line.trim()));
      }
    } catch (error) {
      if (this.connected) this.log(`! Lesefehler: ${error.message}`);
    } finally {
      try { this.reader?.releaseLock(); } catch {}
      this.reader = null;
    }
  }

  pushLine(line) {
    if (!line) return;
    this.log(`← ${line}`);
    const waiter = this.waiters.shift();
    if (waiter) waiter.resolve(line); else this.lines.push(line);
  }

  readLine(timeout = 1500) {
    if (this.lines.length) return Promise.resolve(this.lines.shift());
    return new Promise((resolve, reject) => {
      const waiter = { resolve: value => { clearTimeout(waiter.timer); resolve(value); }, reject };
      waiter.timer = setTimeout(() => {
        const index = this.waiters.indexOf(waiter);
        if (index >= 0) this.waiters.splice(index, 1);
        reject(new Error('Zeitüberschreitung bei Controller-Antwort'));
      }, timeout);
      this.waiters.push(waiter);
    });
  }

  async writeRaw(command) {
    if (!this.connected || !this.port?.writable) throw new Error('Controller nicht verbunden');
    const writer = this.port.writable.getWriter();
    try { await writer.write(encoder.encode(`${command}\n`)); this.log(`→ ${command}`); }
    finally { writer.releaseLock(); }
  }

  runExclusive(operation) {
    const result = this.operationQueue.then(operation, operation);
    this.operationQueue = result.catch(() => {});
    return result;
  }

  async send(command) { return this.runExclusive(() => this.writeRaw(command)); }

  async readMatchingLine(validator, timeout = 1500) {
    const deadline = performance.now() + timeout;
    while (performance.now() < deadline) {
      const line = await this.readLine(Math.max(100, deadline - performance.now()));
      if (/^failsafe!?$/i.test(line.trim())) {
        this.failsafeSeen = true;
        this.log('! Spontane Firmware-Failsafe-Meldung');
        continue;
      }
      if (validator(line)) return line;
      this.log(`· Ignorierte asynchrone Zeile: ${line}`);
    }
    throw new Error('Zeitüberschreitung bei passender Controller-Antwort');
  }

  async request(command, validator = () => true, timeout = 1500) {
    return this.runExclusive(async () => {
      await this.writeRaw(command);
      return this.readMatchingLine(validator, timeout);
    });
  }

  async getStatus() {
    const response = (await this.request('get status', line => /^state=/i.test(line.trim()), 1800)).trim();
    this.failsafeSeen = /state=failsafe/i.test(response);
    return response;
  }
  async getSnapshot() { return parseControllerStatus(await this.getStatus()); }
  async getTemperature() {
    const raw = (await this.request('get temp', isNumericLine, 1800)).trim();
    return Number.parseFloat(raw) * 1.1;
  }
  async getFan() {
    const raw = await this.request('get fan', isNumericLine, 1200);
    return clamp(Number.parseFloat(raw), 0, 255);
  }
  async setHeater(value) { await this.send(`set setpoint ${Math.round(clamp(value, 0, 255))}`); }
  async setFan(value) { await this.send(`set fan ${Math.round(clamp(value, 0, 255))}`); }
  async safeOutputs() { if (this.connected) try { await this.setHeater(0); await this.setFan(255); } catch {} }

  async disconnect(makeSafe = true) {
    if (!this.port) return;
    if (makeSafe) await this.safeOutputs();
    this.connected = false;
    try { await this.reader?.cancel(); } catch {}
    try { await this.port.close(); } catch {}
    this.port = null;
    this.lines.length = 0;
    this.waiters.splice(0).forEach(waiter => waiter.reject(new Error('Verbindung getrennt')));
    this.log('— Controller getrennt');
  }
  log(line) { this.onLog(`${new Date().toLocaleTimeString('de-DE')} ${line}`); }
}

export class SimulationTransport {
  constructor(onLog = () => {}, { speed = 6, now = () => performance.now() } = {}) {
    this.onLog = onLog;
    this.connected = false;
    this.temp = 25;
    this.relayTarget = 0;
    this.appliedHeater = 0;
    this.fanTarget = 0;
    this.fan = 0;
    this.errors = 0;
    this.healthyReadings = 0;
    this.abortSignal = false;
    this.sensorFault = false;
    this.speed = speed;
    this.now = now;
    this.last = this.now();
    this.loopCarry = 0;
    this.sensorCarry = 0;
    this.portName = `ESP32-Röstersimulator (${speed}×)`;
  }

  async connect() {
    this.connected = true;
    this.last = this.now();
    this.onLog('ESP32-Firmwaresimulation gestartet');
    return 'popcorn roaster';
  }

  async disconnect() {
    this.update();
    this.connected = false;
    this.relayTarget = 0;
    this.appliedHeater = 0;
    this.fanTarget = 0;
    this.fan = 0;
    this.onLog('ESP32-Firmwaresimulation beendet');
  }

  update() {
    const current = this.now();
    const seconds = Math.min(5, Math.max(0, (current - this.last) / 1000) * this.speed);
    this.last = current;
    this.advance(seconds);
  }

  advance(seconds) {
    this.loopCarry += Math.max(0, seconds);
    while (this.loopCarry >= 0.05) {
      this.loopCarry -= 0.05;
      this.firmwareLoop(0.05);
    }
  }

  firmwareLoop(dt) {
    const PWM_MIN = 0, PWM_MAX = 255, MIN_SAFE_FAN = 128;

    this.sensorCarry += dt;
    while (this.sensorCarry >= 0.5) {
      this.sensorCarry -= 0.5;
      if (this.sensorFault) { this.errors += 1; this.healthyReadings = 0; }
      else { this.errors = 0; this.healthyReadings = Math.min(255, this.healthyReadings + 1); }
      if (this.errors > 20) this.abortSignal = true;
    }

    if (this.temp > 60) this.fanTarget = Math.max(this.fanTarget, MIN_SAFE_FAN);
    if (this.relayTarget > 0) this.fanTarget = Math.max(this.fanTarget, MIN_SAFE_FAN);
    this.relayTarget = clamp(this.relayTarget, PWM_MIN, PWM_MAX);
    this.fanTarget = clamp(this.fanTarget, PWM_MIN, PWM_MAX);

    if (this.abortSignal) {
      this.relayTarget = PWM_MIN;
      this.fanTarget = PWM_MAX;
    }

    if (Math.abs(this.fan - this.fanTarget) <= 2) this.fan = this.fanTarget;
    if (this.fan < this.fanTarget) this.fan += 2;
    else if (this.fan > this.fanTarget) this.fan -= 2;
    this.fan = clamp(this.fan, PWM_MIN, PWM_MAX);

    // Exact firmware interlock; only the thermal response is a physical model.
    this.appliedHeater = !this.abortSignal && this.fan >= MIN_SAFE_FAN ? this.relayTarget : PWM_MIN;
    const ambient = 25;
    const heating = this.appliedHeater / PWM_MAX * 8.2;
    const cooling = (this.temp - ambient) * (0.006 + this.fan / PWM_MAX * 0.010);
    this.temp = clamp(this.temp + (heating - cooling) * dt, ambient, 300);
  }

  async getStatus() {
    this.update();
    const state = this.abortSignal ? 'failsafe' : 'ok';
    return `state=${state},temp=${this.temp.toFixed(2)},heater=${this.appliedHeater.toFixed(2)},fan=${this.fan.toFixed(2)},fanTarget=${this.fanTarget.toFixed(2)},errors=${this.errors},healthyReadings=${this.healthyReadings},failsafeLatched=${this.abortSignal?1:0},version=1.3.2,protocol=3,hardware=CoffeeRoast-Waveshare-ESP32-S3-Zero`;
  }
  async getSnapshot() { return parseControllerStatus(await this.getStatus()); }
  async getTemperature() { this.update(); return this.temp * 1.1; }
  async getFan() { this.update(); return this.fan; }
  async setHeater(value) { this.update(); this.relayTarget = clamp(value, 0, 255); }
  async setFan(value) { this.update(); this.fanTarget = clamp(value, 0, 255); }
  async safeOutputs() { this.update(); this.relayTarget = 0; this.appliedHeater = 0; this.fanTarget = 255; }
  injectSensorFault(active = true) { this.sensorFault = active; }
}

export function parseControllerStatus(line) {
  const raw=String(line).trim(),values={};
  raw.split(',').forEach(part=>{const i=part.indexOf('=');if(i>0)values[part.slice(0,i).trim()]=part.slice(i+1).trim()});
  const requiredBase=['state','temp','heater','fan','fanTarget','errors'];
  const missingBase=requiredBase.filter(key=>values[key]===undefined||values[key]==='');
  if(missingBase.length)throw new Error(`Controllerstatus unvollständig (${missingBase.join(', ')}): ${line}`);
  if(!/^(ok|failsafe)$/i.test(values.state))throw new Error(`Unbekannter Controllerzustand: ${values.state}`);

  const temperatureUnavailable=/^nan$/i.test(values.temp),rawTemperature=temperatureUnavailable?NaN:Number(values.temp),heater=Number(values.heater),fan=Number(values.fan),fanTarget=Number(values.fanTarget),errors=Number(values.errors);
  const numericValues=[heater,fan,fanTarget,errors];
  if((!Number.isFinite(rawTemperature)&&!temperatureUnavailable)||numericValues.some(value=>!Number.isFinite(value))||!Number.isInteger(errors)||errors<0||heater<0||heater>255||fan<0||fan>255||fanTarget<0||fanTarget>255){
    throw new Error(`Ungültige numerische Statuswerte: ${line}`);
  }

  const hasMetadata=['version','protocol','hardware'].some(key=>values[key]!==undefined);
  if(hasMetadata){
    const missingMetadata=['version','protocol','hardware'].filter(key=>values[key]===undefined||values[key]==='');
    if(missingMetadata.length)throw new Error(`Versionsmetadaten unvollständig (${missingMetadata.join(', ')}): ${line}`);
    if(!/^\d+\.\d+\.\d+$/.test(values.version))throw new Error(`Ungültige Firmwareversion: ${values.version}`);
    if(!/^\d+$/.test(values.protocol))throw new Error(`Ungültige Protokollversion: ${values.protocol}`);
    if(Number(values.protocol)>=3){
      const missingSafety=['healthyReadings','failsafeLatched'].filter(key=>values[key]===undefined||values[key]==='');
      if(missingSafety.length)throw new Error(`Protokoll-3-Sicherheitsfelder fehlen (${missingSafety.join(', ')}): ${line}`);
      if(!/^\d+$/.test(values.healthyReadings)||!/^([01])$/.test(values.failsafeLatched))throw new Error(`Ungültige Protokoll-3-Sicherheitsfelder: ${line}`);
      if((values.state.toLowerCase()==='failsafe')!==(values.failsafeLatched==='1'))throw new Error(`Inkonsistenter Failsafe-Status: ${line}`);
    }
  }

  const snapshot={raw,state:values.state.toLowerCase(),temperature:rawTemperature*1.1,rawTemperature,heater,fan,fanTarget,errors,version:values.version||'',protocol:hasMetadata?Number(values.protocol):0,hardware:values.hardware||'',healthyReadings:Math.max(0,Number.parseInt(values.healthyReadings,10)||0),failsafeLatched:values.failsafeLatched==='1'};
  snapshot.compatibility=assessFirmwareCompatibility(snapshot);
  return snapshot;
}
export function assessFirmwareCompatibility(snapshot){
  if(!snapshot.version&&!snapshot.protocol&&!snapshot.hardware)return{level:'legacy',label:'Legacy-Firmware',compatible:true,reason:'Keine Versionsmetadaten; Basiskompatibilität über get status erkannt.'};
  if(snapshot.protocol!==EXPECTED_FIRMWARE.protocol)return{level:'incompatible',label:'Nicht kompatibel',compatible:false,reason:`Protokoll ${snapshot.protocol||'unbekannt'}, benötigt ${EXPECTED_FIRMWARE.protocol}.`};
  if(snapshot.hardware!==EXPECTED_FIRMWARE.hardware)return{level:'incompatible',label:'Falsche Hardware',compatible:false,reason:`Hardware ${snapshot.hardware||'unbekannt'}, erwartet ${EXPECTED_FIRMWARE.hardware}.`};
  if(compareVersions(snapshot.version,EXPECTED_FIRMWARE.minimumVersion)<0)return{level:'outdated',label:'Update empfohlen',compatible:true,reason:`Firmware ${snapshot.version}, empfohlen ab ${EXPECTED_FIRMWARE.minimumVersion}.`};
  return{level:'compatible',label:'Voll kompatibel',compatible:true,reason:`Firmware ${snapshot.version} · Protokoll ${snapshot.protocol} · ${snapshot.hardware}`};
}
function compareVersions(a,b){const pa=String(a).split('.').map(Number),pb=String(b).split('.').map(Number);for(let i=0;i<Math.max(pa.length,pb.length);i++){const d=(pa[i]||0)-(pb[i]||0);if(d)return d}return 0}
function isNumericLine(line){return String(line).trim()!==''&&Number.isFinite(Number(String(line).trim()))}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||0))}
function hex(value){return Number(value).toString(16).padStart(4,'0').toUpperCase()}
function delay(milliseconds){return new Promise(resolve=>setTimeout(resolve,milliseconds))}
