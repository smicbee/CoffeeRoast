# Branch-, Firmware- und Web-Parität

Referenz: `origin/codex/fix-bugs-and-crashes` bei `2c96788`; Firmware: `ESP32S3 Zero/RoastingControl/RoastingControl.ino`.

## Protokoll

- 115200 Baud, 8N1, kein Flow Control, `\n` als Befehlsabschluss.
- `hello` → `popcorn roaster`.
- `get status` → `state=...,temp=...,heater=...,fan=...,fanTarget=...,errors=...`.
- `get temp` und `get fan` liefern jeweils eine numerische Zeile.
- `set fan N` und `set setpoint N` antworten nicht.
- `Failsafe!` kann spontan zwischen Antworten eintreffen.

Die Website serialisiert deshalb alle Operationen in einer FIFO-Warteschlange und akzeptiert je Request nur das erwartete Antwortformat. Spontane `Failsafe!`-Zeilen können nicht mehr als Temperatur fehlinterpretiert werden. Der Regelzyklus nutzt den atomaren Firmwarestatus, sodass Temperatur und reale Ausgänge aus demselben Zeitpunkt stammen.

## Ablauf aus dem Branch

### Verbinden

1. Port öffnen und DTR setzen.
2. ESP32-Auto-Reset abwarten; `hello` bis 10 Sekunden wiederholen.
3. `get status` vollständig parsen.
4. Erst danach verbunden melden und Bohnen-/Isttemperatur anzeigen.

### Vorbereitung (`pre-heating` im Desktop-Code)

`ControlClass.prepareRoast()` setzt im Branch `setPoint = 0`. Im Zustand `pre-heating` wird der Startlüfter gesetzt; erst eine gültige Temperatur führt zu `ready`.

Die Website bildet das so ab und ergänzt den fehlenden Safety-Nachweis:

1. frischen Status und Preflight prüfen;
2. **zuerst** `set fan <Startwert>`;
3. `set setpoint 0` – Heizung bleibt aus;
4. auf Temperatur > 0 und realen Firmware-Lüfter-PWM ≥ 40 warten;
5. erst dann `ready`;
6. nach 10 Sekunden ohne Bestätigung Failsafe statt blind weiterzulaufen.

### Rösten

Je Zyklus: Lüfterziel senden, realen Lüfter prüfen, erst danach Heizwert senden, dann `get status`. PID, Zukunftsziel 40 Sekunden, dynamisches Kp/Ki/Kd, frühes Heizlimit 170 und temperaturabhängige Lüfterkurve entsprechen dem Branch. Auto-Drop unterstützt Zeit und Temperatur. RoR wird wie im Branch über 30 Sekunden berechnet; First Crack, DTR und Live-Phase werden angezeigt.

### Abkühlen/Failsafe

Abkühlen sendet zuerst Heizung 0 und danach Lüfter 255. Im weiteren Verlauf folgt der Lüfter der Branch-Kurve und stoppt unter 60 °C. Failsafe hält Heizung 0 und Lüfter 255. Die Firmware erzwingt zusätzlich Mindestlüfter bei Hitze/Heizung.

## Erkannte Branch-Widersprüche, bewusst nicht übernommen

- Desktop-Gerätesuche schreibt `hello` ohne Newline und schließt den gefundenen Port im `finally`; die Website verwendet den stabilen offenen Port und korrektes Zeilenende.
- Desktop-Serialzugriffe sind nicht synchronisiert; die Website verhindert Antwortvertauschung.
- `runCurve()` setzt `stopAt = -1` und kann damit den zuvor gewählten Zeit-Auto-Drop löschen; die Website behält den konfigurierten Auto-Drop.
- `pre-heating` prüft im Desktop nur `measuredTemp > 0`; die Website verlangt zusätzlich realen Lüfterlauf.
