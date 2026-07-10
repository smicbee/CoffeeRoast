# CoffeeRoast RevA.1 PCBA-Entscheidungsbrief

Stand: 2026-07-05

Scope: Synthese der Kanban-Kindkarten fuer die JLC-Entscheidung "Partial-PCBA beibehalten oder wegen Standard-PCBA-Aufpreis mehr bestuecken lassen?" Keine Bestellung, kein Checkout, keine Zahlung ohne explizite User-Freigabe.

## Kurzentscheidung

Nicht alles bestuecken lassen.

Empfehlung fuer RevA.1:

1. **Sicherster Bestellweg: konservative Partial-PCBA beibehalten.**
   JLC bestueckt nur die bereits gepruefte Baseline: `C1 C2 C3 J5 Q2 R1 R2 R3 R4 R5 R6 R7 R8 R10 R11 U1 U2`.
2. **Wenn der Standard-PCBA-Aufpreis besser genutzt werden soll: separates Max-PCBA-Quote/Preview-Experiment anlegen.**
   Dafuer nicht die Partial-Dateien ueberschreiben, sondern `production/partial-smd-pcba/assembly/max_pcba_candidate_bom.csv` und `max_pcba_candidate_cpl.csv` verwenden. Diese enthalten Baseline + `J1 J2 J3 J4`.
3. **`Q1` bleibt optionaler Sonderfall, nicht Default.**
   Footprint/Pinout wirken plausibel, aber THT-Power, Fan-Strom, Waerme, mechanische Belastung und JLC-Orientierung sind riskanter. Nur separat pruefen, wenn der User diesen Versuch bewusst will.
4. **Alle anderen DNP-/Handteile bleiben fuer RevA.1 Handloeten, DNP oder RevA.2-Redesign.**
   Insbesondere `C4 C5 D1 D2 D3 F1 SW1 SW2 U3 U4 U5` nicht nur wegen der hohen Bestueckungsgrundkosten automatisch bestuecken lassen.

## Warum diese Entscheidung

- Der Standard-PCBA-Modus ist plausibel/noetig, weil `U1` ESP32-S3-WROOM bei JLC als Standard-only auftauchen kann. Das macht die Grundgebuehr aber nicht zu einem Grund, unsichere Footprints mitzunehmen.
- Die aktuelle Fertigungsbasis ist als Low-Voltage-Controller plausibel: KiCad error-only DRC meldet 0 Verstoesse, 0 unverbundene Pads und 0 Footprint-Fehler; das Produktions-ZIP wurde nach dem aktuellen Board-/Silkscreen-Stand regeneriert und `unzip -t` war OK.
- Die Max-PCBA-Footprintpruefung findet fuer `J1-J4` mit `C3697` eine sinnvolle Quote-/Preview-Chance. Fuer viele andere DNP-Teile fehlen dagegen exakte Landpatterns, bestaetigte JLC-Teile oder mechanische/thermische Sicherheit.
- Die Visuals zeigen klar: RevA.1 ist eine 24V/3A-Low-Voltage-Controllerplatine; 230VAC bleibt im Gehaeuse bei PSU/SSR/Heizer, nicht auf der PCB.

## Optionen im Vergleich

| Option | Inhalt | Nutzen | Hauptrisiko | Empfehlung |
|---|---|---|---|---|
| Partial-PCBA / so bestellen | Baseline 17 Positionen: U1, U2, J5, Q2, 0805 R/C | Niedrigstes Assembly-Risiko; naechst am bereits geprueften Paket | Handloeten/extern fuer Power- und Klemmenteile bleibt noetig | **Default fuer ersten Prototyp** |
| Max-PCBA Quote/Preview | Baseline + `J1-J4` als `C3697` | Koennte die ohnehin vorhandene Standard-PCBA-Gebuehr besser nutzen | JLC muss THT/right-angle Terminals akzeptieren; Orientierung, Schraubzugang, Preis/Leadtime pruefen | **Nur als separates Vergleichsprojekt, nicht direkt bestellen** |
| Max-PCBA + `Q1` | Zusaetzlich TO-220 Fan-MOSFET | Weniger Handloeten am Fanpfad | THT-Power/Mechanik/Thermik, realer Fan-Strom, JLC-Preview | **Optionaler Sondertest nach User-Opt-in** |
| Alles bestuecken | Alle DNP-/Handteile in PCBA ziehen | Weniger Handarbeit auf dem Papier | Mehrere falsche/unsichere Footprints, falscher SW-Kandidat, USB-ESD/TVS/Regler/Buck nicht bestaetigt | **Nicht machen** |
| RevA.2 | Footprints/Powerpfad/mechanische Anschluesse gezielt ueberarbeiten | Sauberer Serien-/Einbaupfad | Neue Layout-/DRC-/Preview-Runde | **Fuer robuste Endversion einplanen** |

## Kostenwirkung

- Die reine Standard-PCBA-Grundgebuehr ist durch `U1` wahrscheinlich sowieso im Cart. Zusatzteile sind trotzdem nicht automatisch kostenlos: JLC kann fuer THT, manuelle Kontrolle, Standard/Extended-Teile, Leadtime oder PCBA-Menge zusaetzlich aufschlagen.
- `J1-J4` sind die einzigen Zusatzteile, bei denen ein Mehrbestueckungsversuch fachlich Sinn ergibt. Wenn JLC sie akzeptiert und der Preis-/Leadtime-Sprung klein bleibt, ist Max-PCBA als Vergleich interessant.
- Wenn `J1-J4` nicht eindeutig akzeptiert werden, falsch herum im Preview stehen oder teuer/manuell werden, ist Partial-PCBA wirtschaftlich und technisch besser.
- Kein Preisvorteil rechtfertigt `D1/D2/D3/C5/U5/SW1/SW2/U3/U4` auf unsicheren Footprints.

## Wichtigste Risiken/Gates

### Vor jeder Bestellung

- Keine Zahlung/kein Checkout ohne explizites OK.
- Alten JLC-Cart als stale behandeln, falls er vor dem regenerierten ZIP/aktuellen BOM-CPL-Stand erstellt wurde.
- Top-side PCBA, Menge, Teile-Mapping, Nullmengen und Substitutionen in der JLC-BOM-Tabelle manuell pruefen.
- Placement Preview visuell gegen `render/coffeeroast_component_map_annotated.png`, `render/coffeeroast_jlc_pcba_placement_annotated.png` und `render/coffeeroast_actual_traces_overlay.png` abgleichen.

### Fuer Partial-PCBA

- Die 17 Baseline-Designatoren muessen selektiert sein, Menge > 0 haben und die erwarteten C-Codes zeigen.
- Orientierung/Pin-1 besonders pruefen fuer `U1` ESP32-S3-WROOM, `U2` MAX6675, `J5` USB-C und `Q2` 2N7002.

### Fuer Max-PCBA mit `J1-J4`

- Separaten Upload/neue Revision verwenden, nicht den bisherigen Partial-Cart still veraendern.
- `J1-J4` muessen als `C3697` gemappt, selektiert, Top-side, Menge 1 und von JLC als assemblebar akzeptiert sein.
- Right-angle-Oeffnung/Schraubzugang muss im 2D/3D/Mechanical Preview zur Gehaeuse-/Kabelseite passen.
- Preis/Leadtime-Aufschlag gegen Partial dem User nennen und erst danach Freigabe einholen.

### Sicherheits-/Power-Grenze

- RevA.1 bleibt Low-Voltage: 230VAC, Netzsicherung, Hauptschalter, PSU, SSR-Heizerpfad, PE/Chassis, Zugentlastung und thermische Sicherung sind Gehaeuse-/Verdrahtungsarbeit.
- Der 24V/Fan-Pfad ist fuer den ersten Prototyp messpflichtig: Board hat keine Kupferzonen und relevante +24V/FAN/GND-Tracks sind laut Review schmal. Bring-up mit Strombegrenzung; realen Fan-Strom, Q1/J2/J1/Leiterbahn-Erwaermung messen. Fuer eine robuste RevA.2 Hochstrompfade breiter/anders fuehren.

## Naechste konkrete JLC-Schritte

1. **Partial-Pfad pruefen:** aktuellen/regenerierten ZIP-Stand hochladen oder Cart als frisch bestaetigen; `bom_smd_partial.csv` + `cpl_smd_partial.csv` verwenden; 17 Baseline-Positionen und Preview pruefen; Preis/Leadtime notieren.
2. **Optionalen Max-Vergleich anlegen:** neues JLC-Projekt/neue Revision mit gleichem ZIP, aber `max_pcba_candidate_bom.csv` + `max_pcba_candidate_cpl.csv`; 21 Positionen erwarten; besonders `J1-J4` als `C3697` pruefen; Preis/Leadtime notieren.
3. **Nicht im Checkout handeln:** Beide Varianten nur vergleichen. Danach User entscheiden lassen: "Partial so bestellen" oder "Max-PCBA mit J1-J4 weiterverwenden". Ohne explizites OK stoppen.
4. **Wenn JLC `J1-J4` ablehnt oder unsicher previewt:** Max-PCBA abbrechen und Partial-PCBA bevorzugen; J1-J4 handloeten.
5. **Wenn User `Q1` trotzdem testen will:** als separates bewusstes UI-Experiment pruefen, nicht in den Default-Max-CSV hineinmischen.

## Kindkarten / Quellen

- `t_7960ea98` Footprint Audit: `production/partial-smd-pcba/assembly/max_pcba_footprint_audit.md`. Ergebnis: `J1-J4` SAFE_FOR_JLC unter JLC-Preview/THT-Gate; `Q1` CONDITIONAL; viele andere DNP-Teile REDESIGN/HAND_SOLDER/CONDITIONAL.
- `t_ea9d4e7c` Max-PCBA BOM Engineer: `production/partial-smd-pcba/assembly/max_pcba_proposal.md`, `max_pcba_candidate_bom.csv`, `max_pcba_candidate_cpl.csv`. Ergebnis: Kandidaten-CSV = Baseline + `J1-J4`, `Q1` absichtlich ausgelassen.
- `t_a3c78583` JLC Handoff: `production/jlc_partial_vs_max_handoff.md`. Ergebnis: konkrete JLC-Schrittfolge und Entscheidungsgates fuer Partial vs Max.
- `t_956de182` Safety/Power Review: `docs/reva1_safety_power_review.md`. Ergebnis: Low-voltage-Grenze korrekt; 24V/Fan-Pfad im Prototyp messen; kein automatisches Alles-Bestuecken.
- `t_cde7e0de` Fabrication QA: `production/fabrication_qa_current.md` und `render/drc_report_errors_only_current.txt`. Ergebnis: error-only DRC sauber, ZIP OK; alte Cart-Items ggf. stale.
- `t_de3f898f` Visual QA: `docs/pcb_visual_review.md` und Render-PNGs. Ergebnis: Komponentenkarten, PCBA-only Ansicht, reale Leiterbahn-/Netz-Overlay und Funktionsdiagramm fuer Preview-Abgleich.

## Antwort an den User

Kurz gesagt: Ich wuerde RevA.1 nicht auf "alles bestuecken" umstellen. Fuer den ersten Prototyp bleibt die konservative Partial-PCBA der sicherste Weg. Wenn wir die Standard-PCBA-Gebuehr besser ausnutzen wollen, dann nur als neues Max-PCBA-Quote/Preview mit zusaetzlich `J1-J4`; `Q1` nur optional nach bewusster Entscheidung. Alles andere bleibt Handloeten/DNP/RevA.2. Bestellt wird erst nach JLC-Preview und deiner expliziten Freigabe.
