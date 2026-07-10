# CoffeeRoast V2 Web

Moderne, browserbasierte Neuimplementierung der bisherigen `iRoastControl`-Anwendung.

## Funktionen

- direkte USB/COM-Verbindung zum ESP32 über die Web Serial API
- Ablaufbasis: `codex/fix-bugs-and-crashes` bei Referenzcommit `2c96788`
- Vorbereitung mit gültiger Temperatur, bestätigtem Lüfterlauf und gesperrter Heizung
- serialisierte Kommunikation mit atomarem `get status`-Polling
- Auto-Drop nach Zeit/Temperatur, 30-Sekunden-RoR, First Crack, DTR und Live-Phasen
- kompatibel mit dem bestehenden Textprotokoll (`hello`, `get temp`, `get status`, `get fan`, `set setpoint`, `set fan`)
- Zustände: Leerlauf, Vorbereitung, bereit, Rösten, Abkühlen und Failsafe
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

## Protokoll- und Ablaufprüfung

Details: [`docs/firmware-web-protocol-parity.md`](docs/firmware-web-protocol-parity.md)

```bash
node "CoffeeRoast V2/tests/protocol-parity.test.mjs"
node "CoffeeRoast V2/tests/engine-flow.test.mjs"
```

## Sicherheit

Die Website ersetzt keine hardwareseitige Temperaturabschaltung, Netztrennung oder Beaufsichtigung. Bei Failsafe und Abkühlen wird Heizung `0` gesendet und der Lüfter hochgefahren. Browser-/USB-Abbruch kann eine Hardware-Sicherheitsebene nicht ersetzen.
