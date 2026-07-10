# CoffeeRoast RevA.1: JLC Partial-PCBA vs Max-PCBA Handoff

Stand: 2026-07-05

Status: Vorbereitung fuer Warenkorb-/Quote-Vergleich. Keine Bestellung, kein Checkout, keine Zahlung ohne neue explizite Freigabe durch den User.

Board/Projekt:

- KiCad PCB: `KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb`
- Aktueller Partial-PCBA-Handoff: `KiCAD/CoffeeRoast-Control-RevA/production/jlc_order_handoff.md`
- Partial-SMD BOM/CPL: `KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/assembly/bom_smd_partial.csv` und `cpl_smd_partial.csv`
- Max-PCBA Kandidaten-BOM/CPL: `KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/assembly/max_pcba_candidate_bom.csv` und `max_pcba_candidate_cpl.csv`
- Audit/Begruendung: `KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/assembly/max_pcba_footprint_audit.md` und `max_pcba_proposal.md`
- Visuelle Referenz: `KiCAD/CoffeeRoast-Control-RevA/render/coffeeroast_component_map_annotated.png` und `coffeeroast_actual_traces_overlay.png`

Wichtige Sicherheitsgrenze: RevA.1 ist eine Low-Voltage-Controller-PCB. 230 VAC bleibt ausserhalb der PCB in der Gehaeuse-/Netzteil-/SSR-Verdrahtung.

## Kurzentscheidung

Nicht "alles" bestuecken lassen.

Sinnvolle Optionen:

1. **So bestellen / Partial-PCBA beibehalten**
   - JLC bestueckt nur die bisher sichere Baseline: `C1 C2 C3 J5 Q2 R1 R2 R3 R4 R5 R6 R7 R8 R10 R11 U1 U2`.
   - Power-/Mechanik-/DNP-Teile bleiben Handloeten, extern oder RevA.2-Redesign.
   - Vorteil: geringster Assembly-Risikograd; der aktuelle Warenkorb/Projektstand bleibt am naechsten am bereits geprueften Partial-SMD-Paket.

2. **Max-PCBA neu hochladen / neu quoten**
   - JLC quote/preview testet Baseline plus `J1 J2 J3 J4` mit `C3697`.
   - Dazu **nicht** die Partial-BOM ueberschreiben, sondern die separaten `max_pcba_candidate_*` Dateien verwenden.
   - Vorteil: Falls JLC THT-Terminals sauber akzeptiert, werden die vier Klemmen trotz ohnehin vorhandener Standard-PCBA-Gebuehr mitbestueckt.
   - Risiko/Gate: THT-Akzeptanz, Right-Angle-Orientierung, mechanischer Zugriff, Kosten-/Leadtime-Sprung.

Optional nur nach bewusster Zusatzentscheidung:

- `Q1` kann als separates JLC-UI-Experiment geprueft werden (`IRLB8721PBF`/`C153222` oder `FQP30N06L`/`C243087`), ist aber wegen THT-Power, Fan-Strom, Waerme und mechanischer Belastung nicht im Default-Max-CSV enthalten.

## Dateien fuer die zwei Wege

### Weg A: "So bestellen" / Partial-PCBA

Benutzen:

- Gerber/Drill/ZIP aus `KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/`
- BOM: `assembly/bom_smd_partial.csv`
- CPL: `assembly/cpl_smd_partial.csv`
- DNP/Handloeten als Referenz: `assembly/dnp_hand_solder.csv`

Erwartete PCBA-Designatoren: 17 Positionen

`C1 C2 C3 J5 Q2 R1 R2 R3 R4 R5 R6 R7 R8 R10 R11 U1 U2`

Nicht in PCBA aufnehmen:

`C4 C5 D1 D2 D3 F1 J1 J2 J3 J4 Q1 SW1 SW2 U3 U4 U5` plus alle Test-/Debug-Pads.

### Weg B: "Max-PCBA neu hochladen"

Benutzen:

- Gleicher Gerber/Drill/ZIP-Stand, aber BOM/CPL im JLC-Assembly-Schritt durch die Max-Kandidaten ersetzen.
- BOM: `assembly/max_pcba_candidate_bom.csv`
- CPL: `assembly/max_pcba_candidate_cpl.csv`

Erwartete PCBA-Designatoren: 21 Positionen

`C1 C2 C3 J1 J2 J3 J4 J5 Q2 R1 R2 R3 R4 R5 R6 R7 R8 R10 R11 U1 U2`

Neue Zusatzteile gegenueber Partial:

- `J1` 24V input terminal, `C3697`, Position 10.0000 / 18.0000 mm, Top, Rotation 0.00
- `J2` 24V fan terminal, `C3697`, Position 10.0000 / 48.0000 mm, Top, Rotation 0.00
- `J3` external SSR terminal, `C3697`, Position 140.0000 / 70.0000 mm, Top, Rotation 0.00
- `J4` K-type thermocouple terminal/prototype clamp, `C3697`, Position 140.0000 / 52.0000 mm, Top, Rotation 0.00

Wichtig: Wenn BOM/CPL geaendert werden, den bisherigen JLC-Warenkorb als potentiell stale behandeln. Besser ein neues JLC-Quote-Projekt/Revision anlegen und die Preise/Preview nebeneinander vergleichen, statt im bestehenden Cart stillschweigend Teile zu ersetzen.

## JLC-Schrittfolge fuer den Vergleich

### Gemeinsame Vorpruefung

1. Bestehenden Cart nur lesen/pruefen. Nichts loeschen, nichts bestellen, nichts zahlen.
2. Pruefen, ob der aktuelle Warenkorb wirklich ein Projekt mit zwei Zeilen ist: PCB-Fertigung plus passende Standard-PCBA. Das ist normal und kein Duplikat.
3. Standard-PCBA ist erwartbar/noetig, weil `U1` ESP32-S3-WROOM bei JLC als Standard-only auftauchen kann.
4. PCB-Basisdaten kontrollieren: 2 Layer, 160 x 100 mm, FR-4, 1.6 mm, 1 oz, Top-side assembly, elektrische Pruefung aktiv.
5. Nach Economic/Standard-PCBA-Umschaltung die Assembly-Menge erneut kontrollieren; JLC kann die PCBA-Menge wieder auf die PCB-Menge setzen.

### Weg A: vorhandenen Partial-Warenkorb final pruefen

1. Im aktuellen Projekt die BOM/CPL-Zuordnung fuer `bom_smd_partial.csv` und `cpl_smd_partial.csv` oeffnen.
2. In der BOM-Tabelle nicht nur der Summary vertrauen. Fuer jede der 17 Positionen pruefen:
   - Checkbox selektiert
   - effektive Menge ungleich 0
   - erwarteter Supplier Code/C-Code
   - keine unerwartete Substitution
   - Basic/Extended/Standard-Kompatibilitaet plausibel
3. Placement Preview fuer alle Baseline-Teile nach der Checkliste unten abgleichen.
4. Kosten notieren: PCB, PCBA/Setup, Teile, Versand, Assembly-Menge, Leadtime.
5. Entscheidungsgate: Wenn alle Teile/Orientierungen korrekt sind und der User explizit zustimmt, ist das der sichere "so bestellen" Weg. Ohne User-OK nicht checkouten.

### Weg B: neuen Max-PCBA-Quote/Preview-Test erzeugen

1. Neues JLC-Quote-Projekt/Revision mit demselben Gerber/ZIP anlegen oder einen klar als neu erkennbaren Upload verwenden.
2. Assembly-BOM/CPL durch `max_pcba_candidate_bom.csv` und `max_pcba_candidate_cpl.csv` laden.
3. Erwartete 21 Designatoren gegen JLC-BOM-Tabelle zaehlen. Besonders `J1-J4` muessen vorhanden, selektiert, Menge 1 je Designator und als `C3697` gemappt sein.
4. Pruefen, ob JLC diese THT/right-angle terminals im gewaehlten Standard-PCBA-Prozess wirklich akzeptiert. Wenn JLC sie als nicht assemblebar, manuell zu pruefen, stark verteuert oder rotationsunsicher markiert: Max abbrechen und Partial bevorzugen.
5. Placement/3D/Mechanical Preview fuer Baseline plus `J1-J4` nach der Checkliste unten pruefen.
6. Kosten notieren: PCB, Standard-PCBA/Setup, zusaetzliche THT-/Manual-/Labor-Kosten, Teilekosten, Versand, Assembly-Menge, Leadtime.
7. Nur wenn Preis/Preview besser oder akzeptabel sind, User entscheiden lassen: "Max-PCBA neu hochladen/so verwenden". Ohne explizites OK nicht bestellen.

## Placement-Preview-Checkliste

Die KiCad-Positionen stammen aus der aktuellen CPL. JLC kann Rotationen anders darstellen; entscheidend ist der sichtbare Pad-/Pin-/Gehaeuseabgleich, nicht nur die Gradzahl.

### Baseline-Teile in beiden Wegen

- `U1` ESP32-S3-WROOM, Position 85.0000 / 25.0000 mm, Top, Rotation 0.00
  - Modulvariante/MPN (`ESP32-S3-WROOM-1-N8R8` / `C2913201`) stimmt.
  - Antennenseite und Keepout liegen wie im Board/Render vorgesehen am Modulende, keine 180-Grad-Drehung.
  - Pinreihen liegen auf den roten/USB/MAX6675-Leiterbahnen wie im Trace-Overlay, nicht gespiegelt.
  - Keine Kupfer-/Silk-/Bauteilkollision im Antennenbereich.

- `U2` MAX6675 SOIC-8, Position 98.0000 / 55.0000 mm, Top, Rotation 0.00
  - Pin-1-Markierung/Notch/Dot passt zum Footprint.
  - Thermocouple-Seite zeigt zur `J4`-Leitungsgruppe; SPI/Versorgung zeigt zur ESP32-Seite.
  - `C3` Decoupling sitzt nahe und wird nicht durch ein falsches U2-Mapping verdeckt.

- `J5` USB-C receptacle, Position 145.0000 / 31.0000 mm, Top, Rotation 90.00
  - Oeffnung/Mating-Seite zeigt zur rechten Boardkante.
  - Shell-/Mount-Pads und USB-D+/D-/CC-Pins liegen sichtbar auf den Pads.
  - Keine 180-Grad-Drehung, kein Bottom/Top-Flip.

- `Q2` 2N7002 SSR driver, Position 118.0000 / 70.0000 mm, Top, Rotation 0.00
  - SOT-23-Gehaeuse liegt auf allen drei Pads.
  - Pinout passt zur SSR-Treiberfunktion (`+5V`/SSR-Ausgang/Gate-Netz laut Board), keine gespiegelte SOT-23-Orientierung.
  - Verbindung Richtung `J3`/SSR-Pfad im Trace-Overlay plausibel.

- 0805-Widerstaende/Kondensatoren `C1 C2 C3 R1 R2 R3 R4 R5 R6 R7 R8 R10 R11`
  - Werte und C-Codes stimmen, besonders gruppierte gleiche C-Codes mit korrekter Gesamtmenge:
    - `C1 C2`: 10uF 0805 `C15850`
    - `C3`: 100nF 0805 `C49678`
    - `R1 R3`: 100R `C17408`
    - `R2 R4`: 100k `C149504`
    - `R5 R6`: 10k `C17414`
    - `R7 R8`: 27R `C17594`
    - `R10 R11`: 5.1k `C27834`
  - Alle liegen auf Top, Pads voll abgedeckt, keine Footprint-Verschiebung.
  - Rotation ist bei unpolarisierten 0805 elektrisch unkritisch, aber die Pads muessen deckungsgleich sitzen.

### Zusaetzliche Max-PCBA-Kandidaten

- `J1` 24V input terminal, `C3697`, Position 10.0000 / 18.0000 mm, Top, Rotation 0.00
  - Right-angle-Oeffnung/Schraubzugang zeigt zur erwarteten linken/gehaeusezugaenglichen Seite.
  - Polung `+24V_RAW` / `GND` gegen Beschriftung und Anschlussplan pruefen.
  - Abstand zu `F1`, `C4`, Boardkante und Gehaeusezugentlastung plausibel.

- `J2` 24V fan terminal, `C3697`, Position 10.0000 / 48.0000 mm, Top, Rotation 0.00
  - Oeffnung/Schraubzugang wie bei `J1`; Kabelweg zum Fan realistisch.
  - Fan-Strompfad und Leiterbahn-/Padmechanik plausibel; keine Kollision mit `D3`/DNP-Bereich.

- `J3` external SSR terminal, `C3697`, Position 140.0000 / 70.0000 mm, Top, Rotation 0.00
  - Oeffnung zeigt fuer SSR-Kabel nach aussen/zugentlastbar.
  - Nets `+5V` / `SSR_NEG` nicht vertauscht gegen das externe SSR-Eingangskabel.

- `J4` K-type thermocouple terminal, `C3697`, Position 140.0000 / 52.0000 mm, Top, Rotation 0.00
  - Oeffnung/Schraubzugang fuer Thermoelementleitung passend.
  - `THERMO_PLUS` / `THERMO_MINUS` Polung explizit gegen Anschlussplan markieren.
  - Nur als Prototyp-Klemmenloesung behandeln; echte K-Type-Minibuchse bleibt RevA.2/mechanische Entscheidung.

### Optionaler Sonderfall `Q1` (nicht im Default-Max-CSV)

Nur pruefen, wenn der User bewusst einen weiteren Quote-Versuch mit Fan-MOSFET wuenscht:

- `Q1` fan MOSFET, Position 45.0000 / 48.0000 mm, Top, Rotation 0.00
- Kandidaten: `IRLB8721PBF` / `C153222` oder `FQP30N06L` / `C243087`
- Gate/Drain/Source gegen Boardnets `FAN_GATE`, `FAN_NEG`, `GND` pruefen.
- TO-220-Koerperrichtung, Hoehe, Kuehlung, Drahtzug/Kabelkraefte und realen Fan-Strom pruefen.
- Wenn JLC THT-Power/TO-220 nicht eindeutig sauber previewt oder stark verteuert: `Q1` handloeten.

## Teile, die nicht in RevA.1-Max-PCBA gehoeren

Nicht automatisch bei JLC bestuecken lassen:

- `C4`: erst nach exakter radialer 220uF/35V-MPN, Lead-Durchmesser, Polung, Hoehe und Footprintcheck.
- `F1`: erst nach exakt passendem 5x20-mm-Fuseholder/JLC-Teil und Gehaeusezugang.
- `D1`: aktuelles Footprint nicht sicher fuer DO-201AD/SB560-Automontage.
- `D2 D3`: aktuelle Draft-Pads nicht als Standard-SMB/DO-214AA bestaetigt.
- `C5`: aktueller Padabstand ist nicht 0805; RevA.2-Redesign.
- `SW1 SW2`: bisheriger `C92655`-Kandidat ist laut LCSC ein Slide Switch, kein passender 6x6-Taster.
- `U3`: aktuelles Regler-Footprint passt nicht zu den genannten Reglerklassen.
- `U4`: Buck-Modul/JLC-Code nicht bestaetigt; handloeten/wire-in.
- `U5`: aktuelles USB-ESD-Footprint ist kein sicheres SOT-23-6L/USBLC6-Layout.

## Vergleichstabelle fuer den User

Vor einer Entscheidung diese Werte aus JLC notieren:

| Punkt | Partial-PCBA / so bestellen | Max-PCBA / neu hochladen |
|---|---|---|
| Projekt/Revision/Suffix | aktuelles Cart-Projekt, z.B. Y3 | neuer Upload/neue Revision |
| BOM/CPL | `bom_smd_partial.csv` / `cpl_smd_partial.csv` | `max_pcba_candidate_bom.csv` / `max_pcba_candidate_cpl.csv` |
| Erwartete PCBA-Designatoren | 17 | 21 |
| Neue Risiko-Teile | keine | `J1-J4` THT right-angle terminals |
| JLC akzeptiert alle Teile? | ja/nein eintragen | ja/nein eintragen |
| Placement Preview OK? | ja/nein eintragen | ja/nein eintragen |
| 3D/mechanical Preview OK? | ja/nein eintragen | ja/nein eintragen |
| PCB-Menge | eintragen | eintragen |
| PCBA-Menge | eintragen | eintragen |
| Gesamtpreis ohne Versand | eintragen | eintragen |
| Versand/Leadtime | eintragen | eintragen |
| Entscheidung | "so bestellen" nur mit User-OK | "Max-PCBA neu hochladen" nur mit User-OK |

## Entscheidungs-Gate

### Freigabe fuer "so bestellen"

Nur wenn alle Punkte wahr sind:

- Die 17 Partial-PCBA-Designatoren sind selektiert, haben Menge > 0 und die erwarteten C-Codes.
- `U1`, `U2`, `J5`, `Q2` und alle 0805-Teile sehen im Placement Preview richtig aus.
- Standard-PCBA-Menge/Kosten sind akzeptiert.
- Keine unerwartete BOM-Substitution oder Nullmengen-Zeile bleibt offen.
- User sagt explizit, dass genau dieser Cart bestellt werden soll.

### Freigabe fuer "Max-PCBA neu hochladen"

Nur wenn alle Punkte wahr sind:

- Neuer Quote/Upload nutzt die Max-Kandidaten-BOM/CPL, nicht eine still geaenderte Partial-Datei.
- `J1-J4` sind als `C3697` gemappt, selektiert, Menge 1 und Top-side.
- JLC akzeptiert die THT-Terminals im Standard-PCBA-Prozess ohne ungepruefte Sonderannahme.
- Right-angle-Oeffnung/Schraubzugang von `J1-J4` ist im Preview korrekt.
- Preis-/Leadtime-Aufschlag gegenueber Partial wurde dem User genannt.
- User gibt explizit frei, die Max-PCBA-Variante weiterzuverwenden oder zu bestellen.

### Sofort abbrechen / Partial bevorzugen, wenn

- JLC `J1-J4` nicht eindeutig als assemblebar akzeptiert.
- JLC die `C3697`-Orientierung nicht klar previewt oder die Klemmen sichtbar falsch herum stehen.
- PCBA-Menge/Kosten nach Standard-PCBA-Umschaltung unerwartet steigen und nicht durch den User bestaetigt sind.
- Irgendein Baseline-Teil (`U1`, `U2`, `J5`, `Q2`, 0805) unselektiert, mit Menge 0 oder falsch orientiert erscheint.
- JLC einen Ersatz/C-Code vorschlaegt, der nicht gegen Footprint/Datenblatt geprueft wurde.

## Empfohlene Antwort an den User

"Nicht alles bestuecken lassen. Der sichere aktuelle Weg ist Partial-PCBA mit U1/U2/J5/Q2/0805. Wenn wir den Standard-PCBA-Aufpreis besser ausnutzen wollen, lohnt nur ein neuer Max-PCBA-Quote-Test mit zusaetzlich J1-J4. Q1 ist optional, aber nicht Default. Alle anderen DNP-/Handteile bleiben fuer RevA.1 Handloeten oder RevA.2-Redesign. Bestellen erst nach Placement-Preview und deiner expliziten Freigabe."
