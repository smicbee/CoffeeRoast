const encoder = new TextEncoder();

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

  async connect(requestUserPort = true) {
    if (!WebSerialTransport.isSupported()) throw new Error('Web Serial wird von diesem Browser nicht unterstützt. Bitte Chrome oder Edge verwenden.');
    const port = requestUserPort ? await navigator.serial.requestPort() : (await navigator.serial.getPorts())[0];
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
  constructor(onLog = () => {}) { this.onLog=onLog;this.connected=false;this.temp=25;this.heater=0;this.fan=0;this.last=performance.now();this.portName='Digitaler Röster'; }
  async connect(){this.connected=true;this.last=performance.now();this.onLog('Simulation gestartet');return'popcorn roaster'}
  async disconnect(){this.connected=false;this.heater=0;this.fan=0;this.onLog('Simulation beendet')}
  update(){const now=performance.now(),dt=Math.min(2,(now-this.last)/1000);this.last=now;const ambient=25,heating=this.heater/255*10.5,cooling=(this.temp-ambient)*(.008+this.fan/255*.012);this.temp=clamp(this.temp+(heating-cooling)*dt,ambient,280)}
  async getStatus(){this.update();return`state=simulation,temp=${this.temp.toFixed(1)},heater=${Math.round(this.heater)},fan=${Math.round(this.fan)},fanTarget=${Math.round(this.fan)},errors=0`}
  async getSnapshot(){return parseControllerStatus(await this.getStatus())}
  async getTemperature(){this.update();return this.temp}
  async getFan(){return this.fan}
  async setHeater(value){this.update();this.heater=clamp(value,0,255)}
  async setFan(value){this.update();this.fan=clamp(value,0,255)}
  async safeOutputs(){this.heater=0;this.fan=255}
}

export function parseControllerStatus(line) {
  const values = {};
  String(line).trim().split(',').forEach(part => { const i=part.indexOf('='); if(i>0) values[part.slice(0,i).trim()]=part.slice(i+1).trim(); });
  const rawTemperature=Number.parseFloat(values.temp);
  if(!values.state||!Number.isFinite(rawTemperature))throw new Error(`Ungültiger Controllerstatus: ${line}`);
  return {raw:String(line).trim(),state:values.state,temperature:rawTemperature*1.1,rawTemperature,heater:clamp(Number.parseFloat(values.heater),0,255),fan:clamp(Number.parseFloat(values.fan),0,255),fanTarget:clamp(Number.parseFloat(values.fanTarget),0,255),errors:Math.max(0,Number.parseInt(values.errors,10)||0)};
}
function isNumericLine(line){return String(line).trim()!==''&&Number.isFinite(Number(String(line).trim()))}
function clamp(value,min,max){return Math.max(min,Math.min(max,Number(value)||0))}
function hex(value){return Number(value).toString(16).padStart(4,'0').toUpperCase()}
function delay(milliseconds){return new Promise(resolve=>setTimeout(resolve,milliseconds))}
