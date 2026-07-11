# Ergebnis: CoffeeRoast V2 Web

## Umsetzung

Die bisherige WinForms-Anwendung wurde als eigenständige, moderne Webanwendung unter `CoffeeRoast V2/` neu umgesetzt.

### Funktionsumfang

- modernes responsives Dark-UI für Desktop, Tablet und Mobilgeräte
- direkter Zugriff auf den lokalen ESP32 über die Web Serial API
- kompatibles Textprotokoll:
  - `hello`
  - `get temp`
  - `get fan`
  - `get status`
  - `set setpoint <0-255>`
  - `set fan <0-255>`
- explizite Zustandsmaschine für Idle, Vorheizen, Ready, Rösten, Abkühlen und Failsafe
- Safety-Preflight vor realem Vorheizen
- sichere Ausgänge bei Abkühlung, Failsafe und bewusstem Trennen
- Erkennung wiederholter Sensor-/Kommunikationsfehler
- Übernahme aller 17 bestehenden `.kpro`-Rezepte
- robuster, dependency-freier PCHIP-Rezeptinterpolator
- PID-Regelung und temperaturabhängige Lüftersteuerung
- Röstgradwahl mit automatischem Profil-Stopp
- eingebauter digitaler Röster zur Simulation ohne Hardware
- eigener Canvas-Live-Plot für Zieltemperatur, Ist-Temperatur, Heizung und Lüfter
- Diagramm-Tooltip, Zoom/Reset und CSV-Messdatenexport
- Diagnoseansicht mit Controllerstatus, Sensorfehlern, PID-Werten und Kommunikationslog

## Deployment

- Produktionspfad: `/var/www/coffeeroast.michaelbeetz.de`
- Caddy-Site: `coffeeroast.michaelbeetz.de`
- öffentliche URL: https://coffeeroast.michaelbeetz.de/
- HTTPS-Zertifikat automatisch durch Caddy/Let's Encrypt ausgestellt
- Security-Header für Content-Type, Referrer und Web-Serial-Berechtigung gesetzt

## Verifikation

- JavaScript-Syntax aller Module mit `node --check` geprüft
- alle 17 Rezepte automatisiert eingelesen und auf endliche Profilwerte geprüft
- lokaler Browser-Test ohne JavaScript-Fehler
- 17 Rezeptoptionen im UI bestätigt
- Simulationspfad praktisch geprüft:
  - Simulation verbinden
  - Preflight-Dialog öffnen
  - vier Sicherheitsbestätigungen erzwingen
  - Vorheizen starten
  - steigende Temperatur, Heiz- und Lüfterausgabe im UI beobachten
- Caddy-Konfiguration erfolgreich validiert
- Caddy nach Reload aktiv
- öffentliche HTTPS-Seite liefert HTTP 200
- Let's-Encrypt-Zertifikat für `coffeeroast.michaelbeetz.de` bestätigt

## Bedienhinweis

Die Hardwareverbindung benötigt Chrome oder Edge. Die Website greift ausschließlich im Browser auf das vom Benutzer freigegebene USB-Gerät zu. Firefox und Safari unterstützen Web Serial nicht; Simulation, Rezepte und UI bleiben dort nutzbar.

Die Anwendung ersetzt keine hardwareseitige Temperaturabschaltung, Netztrennung oder Beaufsichtigung des Rösters.

## Ergänzung: System-Untermenü in der Kopfleiste

- Diagnose, Controllerstatus, PID/Protokoll und Firmwareverwaltung wurden aus der permanenten rechten Seitenleiste in das neue **System**-Untermenü der sticky Kopfleiste verschoben.
- Das Menü aktualisiert beim Öffnen den Controllerstatus, sofern eine Verbindung besteht.
- Es lässt sich per erneutem Klick, Klick außerhalb oder Escape schließen.
- Das Popover besitzt eine begrenzte Höhe, einen eigenen Scrollbereich und ein responsives Mobil-Layout.
- Röststeuerung und Luftstrom bleiben als einzige permanente Karten in der Seitenleiste.
- Bestehende Diagnose-IDs, PID-Einstellungen, Firmware-Flasher und Post-Flash-Verifikation bleiben funktional erhalten.
- DOM-Struktur, eindeutige IDs, JavaScript-Syntax und sämtliche Tests wurden geprüft.
- Das geschlossene und geöffnete Menü wurde in Chromium bei 1440 × 1000 visuell kontrolliert.
