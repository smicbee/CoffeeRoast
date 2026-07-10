# Desktop-, Firmware- und Web-Parität

Desktop-Basis: `codex/fix-bugs-and-crashes` bei `2c96788`. Aktuelle integrierte Basis: `main` bei `2a05fb0`. Die beim Merge beibehaltene Main-Firmware enthält – anders als der isolierte Desktop-Branch – bereits `get status`.

## Serielles Protokoll

- 115200 Baud, 8N1, kein Flow Control, `\n` als Befehlsabschluss.
- `hello` → `popcorn roaster`.
- `get status` → `state=...,temp=...,heater=...,fan=...,fanTarget=...,errors=...,healthyReadings=...,failsafeLatched=...,version=...,protocol=...,hardware=...`.
- `reset failsafe` → `failsafe reset` nur bei Heizung 0, Lüfter mindestens 50 und mindestens drei gesunden Messungen; sonst `failsafe reset denied`.
- `get info` → `product=CoffeeRoast,firmware=1.3.0,protocol=3,hardware=CoffeeRoast-RevA-ESP32S3-WROOM-1-N8R8`.
- `get temp`, `get fan` und `get setpoint` liefern eine numerische Zeile.
- `set fan N` und `set setpoint N` antworten nicht.
- `Failsafe!` kann spontan zwischen Antworten eintreffen.

Die Website serialisiert alle Operationen in einer FIFO-Warteschlange und akzeptiert je Request nur das erwartete Antwortformat. Spontane Failsafe-/Bootzeilen können damit nicht mehr als Temperatur oder Lüfterwert fehlinterpretiert werden. Der Regelzyklus verwendet den atomaren Status, sodass Temperatur und reale Ausgänge aus demselben Zeitpunkt stammen.

## Versions- und Hardwarekompatibilität

Die empfohlene Firmware meldet drei unabhängige Kennungen:

- Firmware `1.3.0`;
- Protokoll `3`;
- Hardware `CoffeeRoast-RevA-ESP32S3-WROOM-1-N8R8`.

Nur Protokoll 3 mit der exakten Hardwarekennung gilt als voll kompatibel. Eine Firmware mit `get status`, aber ohne Versionsfelder wird als Legacy erkannt und bleibt zur bewussten Rückwärtskompatibilität steuerbar. Eine vorhandene, aber falsche Protokoll- oder Hardwarekennung blockiert den Heizstart. Der Web-Flasher stellt getrennte, jeweils für ESP32-S3 erkannte 8-MB-Images bereit: die empfohlene Firmware und den unveränderten Main-Stand `2a05fb0` vor unseren Firmwareänderungen.

## Sicherer Ablauf

### Verbinden

1. Port öffnen und DTR setzen.
2. ESP32-Auto-Reset abwarten; `hello` bis 10 Sekunden wiederholen.
3. Bootmeldungen ignorieren und `get status` vollständig parsen.
4. Erst danach verbunden melden und die reale Temperatur anzeigen.

### Vorheizen

Der Desktop-Branch hat hier einen kritischen Widerspruch: `prepareRoast()` setzt Heizung 0 und `pre-heating` wechselt bereits bei einer positiven Temperatur zu `ready`; real wird nicht vorgeheizt. Dieser Fehler wird bewusst nicht kopiert.

1. frischen Status und Preflight prüfen;
2. **zuerst** `set fan <Startwert>`;
3. `set setpoint 0`, bis der gerampte Ist-Lüfter mindestens PWM 40 erreicht;
4. ohne Lüfterbestätigung nach 10 Sekunden Failsafe;
5. erst danach Heizleistung freigeben und die leere Kammer auf das einstellbare Vorheizziel (Standard 180 °C) bringen;
6. am Ziel sofort Heizung 0 und Zustand `ready`.

### Rösten

Je Zyklus: Lüfterziel senden, realen Lüfter prüfen, erst danach Heizwert senden, dann atomaren Status lesen. Rezept-Kp/Ki/Kd und Zukunftsziel werden tatsächlich verwendet. PID-Aktualisierung maximal alle drei Sekunden, dynamische Gains, frühes Heizlimit 170 und Lüfterkurve entsprechen dem Branch. Auto-Drop nach Zeit oder Temperatur bleibt beim Start erhalten. RoR nutzt 30 Sekunden inklusive negativer Werte; First Crack wird nur bei `expect_fc > 0` erkannt; DTR und Live-Phase werden angezeigt.

### Abkühlen/Failsafe

Abkühlen sendet zuerst Heizung 0 und danach das Lüfterziel 255. Anders als der fehlerhafte Desktop-Code bleibt die Kühlung bis unter 60 °C aktiv. Im Failsafe wird die Heizung sofort auf 0 gesetzt und ausschließlich das Lüfterziel auf 255 angehoben; der reale PWM-Ausgang läuft weiterhin über die Firmware-Rampe mit höchstens 2 PWM-Schritten je 50 ms und springt nicht auf volle Leistung.

## Firmware-Härtung

- Temperatur bleibt `float`; NaN und unplausible Werte werden vor Übernahme geprüft.
- Nach einem schlechten ersten Wert kann der Sensor nach drei konsistenten plausiblen Messungen neu synchronisieren, statt dauerhaft bei 0 zu hängen.
- `get status` meldet den tatsächlich am SSR angewendeten Heizwert.
- Zusätzlich zur Web-Sperre verhindert ein Firmware-Interlock jeden SSR-Ausgang, solange der reale gerampte Lüfter PWM 50 nicht erreicht hat.

## Bewusst korrigierte Desktop-Bugs

- instabiler Handshake ohne Newline/Bootwartezeit;
- unkoordinierte serielle Requests und blinde Antwortzuordnung;
- defektes Vorheizen;
- gelöschter Zeit-Auto-Drop in `runCurve()`;
- Profilende durch Clamp unerreichbar;
- Rezept-PID ignoriert;
- First Crack bei `expect_fc = 0` sofort ausgelöst;
- Kühlung nur mit Röstlüfterkurve statt Vollleistung;
- Failsafe-Lüfter 200 statt 255.
