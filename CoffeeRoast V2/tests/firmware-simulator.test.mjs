import { readFile } from 'node:fs/promises';
import { SimulationTransport } from '../src/serial.js';

const firmware = await readFile(new URL('../../ESP32S3 Zero/RoastingControl/RoastingControl.ino', import.meta.url), 'utf8');
const constant = (name, fallback) => Number(firmware.match(new RegExp(`${name}\\s*=\\s*([0-9.]+)`))?.[1] ?? fallback);
const fanAcceleration = constant('fanMaxAcceleration', 2);
const loopMilliseconds = constant('delayValue', 50);
const minimumFan = constant('MIN_SAFE_FAN', 50);

function assert(condition, message) {
  if (!condition) throw new Error(`Fehlgeschlagen: ${message}`);
}
function approximately(actual, expected, tolerance = 0.01) {
  return Math.abs(actual - expected) <= tolerance;
}

let now = 0;
const simulator = new SimulationTransport(() => {}, { speed: 1, now: () => now });
await simulator.connect();
assert(fanAcceleration === 2 && loopMilliseconds === 50 && minimumFan === 50, 'Simulator-Konstanten entsprechen der Firmware');

await simulator.setFan(255);
await simulator.setHeater(180);
simulator.advance(1.0);
let status = await simulator.getSnapshot();
assert(status.fan < minimumFan, 'Lüfter befindet sich während des Softstarts unter der Freigabeschwelle');
assert(status.heater === 0, 'SSR bleibt während des Lüfter-Softstarts gesperrt');

simulator.advance(0.4);
status = await simulator.getSnapshot();
assert(status.fan >= minimumFan, 'Lüfter erreicht die Sicherheitsgrenze gerampt');
assert(status.heater === 180, 'SSR wird erst nach bestätigtem Luftstrom freigegeben');

const startTemperature = status.rawTemperature;
simulator.advance(8);
status = await simulator.getSnapshot();
assert(status.rawTemperature > startTemperature, 'Thermisches Modell reagiert auf Heizleistung');

await simulator.setHeater(0);
await simulator.setFan(0);
simulator.temp = 80;
simulator.advance(4);
status = await simulator.getSnapshot();
assert(status.fanTarget >= minimumFan, 'Firmware hält über 60 °C mindestens den Sicherheitslüfter');
assert(status.heater === 0, 'Kühlung hält das SSR aus');

// Failsafe: Ziel springt auf 255, der Ist-Lüfter darf aber nur mit 2 PWM je 50 ms steigen.
simulator.fan = 20;
simulator.fanTarget = 20;
simulator.injectSensorFault(true);
simulator.advance(10.6);
status = await simulator.getSnapshot();
assert(status.state === 'failsafe', '21 fehlerhafte 500-ms-Messungen lösen Failsafe aus');
assert(status.heater === 0, 'Failsafe schaltet das SSR ab');
assert(status.fanTarget === 255, 'Failsafe setzt volle Lüfter-Zieldrehzahl');
assert(status.fan < 255, 'Failsafe setzt den Ist-Lüfter nicht sprunghaft auf 255');
const fanAfterFailsafe = status.fan;
simulator.advance(loopMilliseconds / 1000);
status = await simulator.getSnapshot();
assert(approximately(status.fan - fanAfterFailsafe, fanAcceleration), 'Failsafe-Lüfter steigt exakt mit der Firmware-Rampe');

console.log('CoffeeRoast ESP32-Firmware- und Thermosimulation: OK');
