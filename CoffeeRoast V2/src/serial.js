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
  }

  static isSupported() { return 'serial' in navigator; }

  async connect(requestUserPort = true) {
    if (!WebSerialTransport.isSupported()) throw new Error('Web Serial wird von diesem Browser nicht unterstützt. Bitte Chrome oder Edge verwenden.');
    let port;
    if (requestUserPort) {
      port = await navigator.serial.requestPort();
    } else {
      const ports = await navigator.serial.getPorts();
      port = ports[0];
      if (!port) throw new Error('Noch kein Controller für diese Website freigegeben.');
    }
    await port.open({ baudRate: 115200, dataBits: 8, stopBits: 1, parity: 'none', flowControl: 'none', bufferSize: 4096 });
    this.port = port;
    this.connected = true;
    const info = port.getInfo?.() || {};
    this.portName = info.usbVendorId ? `USB ${hex(info.usbVendorId)}:${hex(info.usbProductId || 0)}` : 'Serieller Controller';
    this.readLoop();

    try {
      // Einige ESP32-/CP210x-Varianten benötigen DTR. Das Setzen kann zugleich
      // einen Auto-Reset auslösen, deshalb bekommt die Firmware anschließend
      // bewusst Zeit zum Booten.
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
    let lastLine = '';

    // Port.open()/DTR startet viele ESP32-Boards neu. Ein sofortiges "hello"
    // geht dann während des Bootloaders verloren.
    await delay(900);

    while (performance.now() < deadline) {
      await this.send('hello');
      const attemptDeadline = Math.min(deadline, performance.now() + 1500);

      // Bootmeldungen oder leere/stale Zeilen überspringen und nur auf die
      // tatsächliche Protokollkennung reagieren.
      while (performance.now() < attemptDeadline) {
        try {
          const line = await this.readLine(Math.max(100, attemptDeadline - performance.now()));
          lastLine = line;
          if (line.trim().toLowerCase() === 'popcorn roaster') return line;
        } catch {
          break;
        }
      }
      await delay(250);
    }

    const detail = lastLine ? ` Letzte Antwort: ${lastLine}` : '';
    throw new Error(`Keine Antwort auf \"hello\" innerhalb von ${Math.round(timeout / 1000)} Sekunden.${detail} Prüfe den COM-Port und schließe andere Serial-Monitore.`);
  }

  async readLoop() {
    try {
      this.reader = this.port.readable.getReader();
      while (this.connected) {
        const { value, done } = await this.reader.read();
        if (done) break;
        this.readBuffer += new TextDecoder().decode(value, { stream: true });
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

  readLine(timeout = 1200) {
    if (this.lines.length) return Promise.resolve(this.lines.shift());
    return new Promise((resolve, reject) => {
      const waiter = { resolve: value => { clearTimeout(waiter.timer); resolve(value); }, reject };
      waiter.timer = setTimeout(() => {
        const i = this.waiters.indexOf(waiter);
        if (i >= 0) this.waiters.splice(i, 1);
        reject(new Error('Zeitüberschreitung bei Controller-Antwort'));
      }, timeout);
      this.waiters.push(waiter);
    });
  }

  async send(command) {
    if (!this.connected || !this.port?.writable) throw new Error('Controller nicht verbunden');
    const writer = this.port.writable.getWriter();
    try { await writer.write(encoder.encode(`${command}\n`)); this.log(`→ ${command}`); }
    finally { writer.releaseLock(); }
  }

  async request(command, timeout = 1200) {
    await this.send(command);
    return await this.readLine(timeout);
  }

  async getStatus() { return (await this.request('get status')).trim(); }

  async getTemperature() {
    const raw = (await this.request('get temp')).trim();
    const value = Number.parseFloat(raw);
    if (!Number.isFinite(value)) throw new Error(`Ungültige Temperatur: ${raw}`);
    return value * 1.1; // Kompatibilität mit der bisherigen App-Kalibrierung
  }

  async getFan() {
    try { const value = Number.parseFloat(await this.request('get fan', 700)); return Number.isFinite(value) ? clamp(value, 0, 255) : 0; }
    catch { return 0; }
  }

  async setHeater(value) { await this.send(`set setpoint ${Math.round(clamp(value, 0, 255))}`); }
  async setFan(value) { await this.send(`set fan ${Math.round(clamp(value, 0, 255))}`); }

  async safeOutputs() {
    if (!this.connected) return;
    try { await this.setHeater(0); await this.setFan(255); } catch {}
  }

  async disconnect(makeSafe = true) {
    if (!this.port) return;
    if (makeSafe) await this.safeOutputs();
    this.connected = false;
    try { await this.reader?.cancel(); } catch {}
    try { await this.port.close(); } catch {}
    this.port = null;
    this.lines.length = 0;
    this.waiters.splice(0).forEach(w => w.reject(new Error('Verbindung getrennt')));
    this.log('— Controller getrennt');
  }

  log(line) { this.onLog(`${new Date().toLocaleTimeString('de-DE')} ${line}`); }
}

export class SimulationTransport {
  constructor(onLog = () => {}) { this.onLog = onLog; this.connected = false; this.temp = 25; this.heater = 0; this.fan = 0; this.last = performance.now(); this.portName = 'Digitaler Röster'; }
  async connect() { this.connected = true; this.last = performance.now(); this.onLog('Simulation gestartet'); return 'popcorn roaster'; }
  async disconnect() { this.connected = false; this.heater = 0; this.fan = 0; this.onLog('Simulation beendet'); }
  update() { const now = performance.now(), dt = Math.min(2, (now - this.last) / 1000); this.last = now; const ambient = 25; const heating = (this.heater / 255) * 10.5; const cooling = (this.temp - ambient) * (0.008 + (this.fan / 255) * 0.012); this.temp = clamp(this.temp + (heating - cooling) * dt, ambient, 280); }
  async getStatus() { this.update(); return `state=simulation temp=${this.temp.toFixed(1)} heater=${Math.round(this.heater)} fan=${Math.round(this.fan)} errors=0`; }
  async getTemperature() { this.update(); return this.temp; }
  async getFan() { return this.fan; }
  async setHeater(value) { this.update(); this.heater = clamp(value, 0, 255); }
  async setFan(value) { this.update(); this.fan = clamp(value, 0, 255); }
  async safeOutputs() { this.heater = 0; this.fan = 255; }
}

function clamp(value, min, max) { return Math.max(min, Math.min(max, Number(value) || 0)); }
function hex(value) { return Number(value).toString(16).padStart(4, '0').toUpperCase(); }
function delay(milliseconds) { return new Promise(resolve => setTimeout(resolve, milliseconds)); }
