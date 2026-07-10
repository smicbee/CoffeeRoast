# CoffeeRoast V2 Web

Moderne, browserbasierte Neuimplementierung der bisherigen `iRoastControl`-Anwendung.

## Funktionen

- direkte USB/COM-Verbindung zum ESP32 über die Web Serial API
- kompatibel mit dem bestehenden Textprotokoll (`hello`, `get temp`, `get status`, `get fan`, `set setpoint`, `set fan`)
- Zustände: Leerlauf, Vorheizen, bereit, Rösten, Abkühlen und Failsafe
- Safety-Preflight vor jedem realen Heizvorgang
- Import und Auswahl der bestehenden `.kpro`-Rezepte
- PID-Regelung, automatischer Röstgrad-Stopp, Lüfterkurve
- eingebaute Simulation ohne Hardware
- responsiver Canvas-Live-Plot und CSV-Export
- keine serverseitige Gerätefreigabe: der Browser spricht lokal mit dem vom Benutzer ausgewählten USB-Gerät

## Browser

Web Serial benötigt einen Chromium-Browser wie Chrome oder Edge und einen sicheren Kontext (`https://` oder `localhost`). Firefox und Safari unterstützen Web Serial derzeit nicht. Simulation und Rezeptanzeige funktionieren trotzdem.

## Lokal starten

```bash
python3 -m http.server 4173 --directory "CoffeeRoast V2"
```

Dann `http://localhost:4173/` in Chrome/Edge öffnen.

## Sicherheit

Die Website ersetzt keine hardwareseitige Temperaturabschaltung, Netztrennung oder Beaufsichtigung. Bei Failsafe und Abkühlen wird Heizung `0` gesendet und der Lüfter hochgefahren. Browser-/USB-Abbruch kann eine Hardware-Sicherheitsebene nicht ersetzen.
