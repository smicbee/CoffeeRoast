# CoffeeRoast V2 Web

Moderne, browserbasierte Neuimplementierung der bisherigen `iRoastControl`-Anwendung.

## Funktionen

- direkte USB/COM-Verbindung zum ESP32 über die Web Serial API
- Ablaufbasis: `codex/fix-bugs-and-crashes` bei Referenzcommit `2c96788`
- sicherer Vorheizablauf mit bestätigtem Lüfterlauf, danach Aufheizen auf 180 °C Standardziel
- integrierte Firmware v1.2.0 mit robustem Temperatursensor-Resync, hardwareseitigem SSR-Lüfterinterlock sowie Firmware-/Protokoll-/Hardwarekennung
- Browser-Flasher für den auf dem RevA-PCB vorgesehenen ESP32-S3-WROOM-1-N8R8 mit 8 MB Flash und 8 MB OPI-PSRAM
- getrennte Flashoption für die empfohlene Firmware und den exakten Legacy-Main-Stand `2a05fb0`
- Lüfter-Softstart auch im Failsafe: Ziel 255, Istwert maximal 2 PWM-Schritte je 50 ms
- serialisierte Kommunikation mit atomarem `get status`-Polling
- Auto-Drop nach Zeit/Temperatur, 30-Sekunden-RoR, First Crack, DTR und Live-Phasen
- kompatibel mit dem bestehenden Textprotokoll (`hello`, `get temp`, `get status`, `get fan`, `set setpoint`, `set fan`)
- Zustände: Leerlauf, Vorheizen, bereit, Rösten, Abkühlen und Failsafe
- Safety-Preflight vor jedem realen Heizvorgang
- Import und Auswahl der bestehenden `.kpro`-Rezepte
- PID-Regelung, Auto-Drop und temperaturabhängige Lüfterkurve
- eingebaute Simulation ohne Hardware
- responsiver Canvas-Live-Plot und CSV-Export
- keine serverseitige Gerätefreigabe: der Browser spricht lokal mit dem vom Benutzer ausgewählten USB-Gerät

## Browser

Web Serial benötigt einen Chromium-Browser wie Chrome oder Edge und einen sicheren Kontext (`https://` oder `localhost`). Firefox und Safari unterstützen Web Serial derzeit nicht. Simulation und Rezeptanzeige funktionieren trotzdem.

Beim ersten Verbinden kann das Öffnen des COM-Ports den ESP32 automatisch neu starten. CoffeeRoast V2 wartet deshalb auf den Bootvorgang und wiederholt den `hello`-Handshake bis zu 10 Sekunden. Falls weiterhin keine Antwort kommt, andere Serial-Monitore schließen, den richtigen USB-/COM-Port wählen und erneut verbinden.

## Lokal starten

```bash
python3 -m http.server 4173 --directory "CoffeeRoast V2"
```

Dann `http://localhost:4173/` in Chrome/Edge öffnen.

## Firmware direkt installieren

Die Website bindet ESP Web Tools ein. In Chrome oder Edge über HTTPS:

1. Eine laufende Röstung beenden und den Röster abkühlen lassen.
2. Den normalen Controller in der Website trennen.
3. Im Bereich **Firmware** entweder die empfohlene Version 1.2.0 oder bewusst den aufgeklappten Legacy-Stand auswählen.
4. Ausschließlich das angeschlossene **CoffeeRoast RevA mit ESP32-S3-WROOM-1-N8R8** auswählen.
5. Nach dem Flashen den Controller neu verbinden. Die empfohlene Firmware muss `version=1.2.0`, `protocol=2` und `hardware=CoffeeRoast-RevA-ESP32S3-WROOM-1-N8R8` melden. Der Legacy-Stand besitzt absichtlich keine Versionsmetadaten und erscheint als „Legacy-Firmware“.

Die Manifeste liegen unter `firmware/manifest-current.json` und `firmware/manifest-legacy.json`. Beide 8-MB-Merged-Images wurden mit folgenden Zielparametern gebaut:

- FQBN `esp32:esp32:esp32s3`
- ESP32-S3-WROOM-1-N8R8: 8 MB Flash, 8 MB OPI-PSRAM
- DIO, 80 MHz
- Partitionierung `default_8MB`
- native Hardware-USB-CDC, CDC beim Boot aktiviert
- ESP32-Arduino-Core 3.3.10
- Adafruit MAX6675 1.1.2

Reproduzierbarer Build:

```bash
ARDUINO_CLI=/pfad/zu/arduino-cli bash "CoffeeRoast V2/firmware/build.sh"
```

Der Flasher überschreibt Programm und Einstellungen. Er ist nicht für ESP32-, ESP32-C3- oder ESP32-S2-Boards bestimmt.

## Protokoll- und Ablaufprüfung

Details: [`docs/firmware-web-protocol-parity.md`](docs/firmware-web-protocol-parity.md)

```bash
node "CoffeeRoast V2/tests/protocol-parity.test.mjs"
node "CoffeeRoast V2/tests/engine-flow.test.mjs"
node "CoffeeRoast V2/tests/firmware-simulator.test.mjs"
```

## Sicherheit

Die Website ersetzt keine hardwareseitige Temperaturabschaltung, Netztrennung oder Beaufsichtigung. Bei Failsafe und Abkühlen wird Heizung `0` gesendet und das Lüfterziel auf `255` gesetzt. Der reale Lüfterausgang steigt auch im Failsafe ausschließlich über die Firmware-Rampe von höchstens 2 PWM-Schritten je 50 ms. Browser-/USB-Abbruch kann eine Hardware-Sicherheitsebene nicht ersetzen.
