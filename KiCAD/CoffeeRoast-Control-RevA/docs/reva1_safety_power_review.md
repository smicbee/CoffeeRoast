# CoffeeRoast RevA.1 Safety-/Power-Review

Stand: 2026-07-05
Board: `CoffeeRoast-Control-RevA.kicad_pcb`
Scope: Low-voltage controller PCB, JLC/PCBA ordering decision, enclosure/mains boundary before first prototype.

## Kurzfazit

RevA.1 ist als Low-Voltage-Controller bestellbar, wenn die Bestellung konservativ bleibt: PCB + die bereits sichere Top-SMD-Bestueckung, optional nur klar gepruefte Zusatzteile. Nicht auf "alles bestuecken" umstellen.

Der wichtigste Vorbehalt ist nicht 230VAC auf der PCB - die ist korrekt ausserhalb gehalten -, sondern der 24V/3A-Fan-/Power-Pfad: Die KiCad-Daten enthalten keine Kupferzonen und die aktuell gerouteten +24V/FAN/GND-Tracks liegen laut Board-Auszug bei ca. 0.20 bis 0.45 mm. Das ist fuer einen echten 3A-Dauerpfad nicht als finale Auslegung zu behandeln. Fuer RevA.1: mit Strombegrenzung/realem Fan messen oder Fanleistung extern/mit Drahtbruecke fuehren; fuer eine robuste Endversion RevA.2 breitere Leiterbahnen/Kupferflaechen bzw. definierte Hochstromfuehrung vorsehen.

230VAC bleibt Gehaeusearbeit: IEC/fused inlet, Hauptschalter, zertifiziertes 230VAC->24VDC/3A-Netzteil, externer SSR mit Kuehlkoerper, Schutzleiter/Chassis-Bonding, Zugentlastung und thermische Abschaltung. F1 auf der PCB schuetzt nur die 24V-Seite und ersetzt keine Netzsicherung.

## Gepruefte Quellen

- `docs/netlist.csv`: Power tree und USB/SSR/Thermocouple-Netze.
- `docs/mains_enclosure_wiring.md`: One-plug/off-board-230VAC-Grenze.
- `docs/reva1_optimizations.md`: RevA.1-Zusatzschutz und bewusst offene RevA.2-Punkte.
- `production/partial-smd-pcba/assembly/bom_smd_partial.csv`: aktuell sichere JLC-SMD-Bestueckung.
- `production/partial-smd-pcba/assembly/dnp_hand_solder.csv`: DNP/Handloet-/Footprint-Risiken.
- `production/partial-smd-pcba/assembly/footprint_max_pcba_review.md`: Max-PCBA-Footprintpruefung.
- `render/coffeeroast_component_map_annotated.png` und `render/coffeeroast_actual_traces_overlay.png`: visuelle Lage-/Netzpruefung.
- `render/drc_report_errors_only_current.txt`: 0 KiCad error-level DRC violations, 0 unconnected pads, 0 footprint errors.
- Eigener `pcbnew`-Auszug: keine Zonen; +24V/FAN/GND-Trackbreiten meist 0.20 mm, max. 0.45 mm in den relevanten Hochstromnetzen.

## Power tree / Grenzen

```text
230VAC im Gehaeuse
  -> IEC/fused inlet + Hauptschalter + PE/Chassis
  -> zertifiziertes isoliertes 24V/3A-Netzteil
       -> J1 auf PCB: +24V_RAW/GND
       -> C4/D2 Eingangsschutz (DNP/Footprint pruefen)
       -> F1 24V-seitige Sicherung
       -> +24V_FUSED
            -> J2 Fan ueber Q1 Low-Side-MOSFET, D1/D3 Clamp
            -> U4 24V->5V Buck
                 -> J3 externer SSR-DC-Eingang ueber Q2 Low-Side
                 -> U3 5V->3V3 fuer ESP32-S3/MAX6675

230VAC-Heizer: nur ueber externes SSR-Modul im Gehaeuse, nicht auf der PCB.
```

Positive Punkte:

- Keine 230VAC-Netze auf der PCB gefunden; das ist fuer RevA.1 die richtige Grenze.
- USB-C ist als Device/data-only mit CC1/CC2 5.1k Pulldowns dokumentiert; USB_VBUS ist nicht als Boardversorgung vorgesehen.
- MAX6675 laeuft auf 3V3, also keine 5V-GPIO-Gefahr am ESP32.
- SSR-Ausgang ist nur ein Low-Voltage-DC-Steuereingang an J3; die gefaehrliche AC-Schaltstrecke bleibt beim externen SSR.
- Testpads fuer 24V/5V/3V3/GND erleichtern sicheres Bring-up mit Strombegrenzung.

Offene Punkte vor Einbau:

- Exaktes 24V-Netzteil mechanisch/elektrisch auswaehlen: zertifiziert, isoliert, 3A ausreichend, Gehaeuse-/Temperaturfreigabe, PE falls erforderlich.
- Mains-Sicherung nach Heizer+PSU-Last und lokalen Regeln auslegen; PCB-F1 ist nur die DC-Branch-Sicherung.
- SSR-Modul passend zum Heizerstrom auswaehlen, Kuehlkoerper/Belueftung im Gehaeuse festlegen und nicht dicht neben Thermocouple-/USB-/ESP-Leitungen fuehren.
- Thermische Abschaltung/thermal fuse am Heizerpfad beibehalten oder nachruesten; Firmware-/SSR-Steuerung ist keine alleinige Sicherheitsebene.
- Alle externen Leitungen mit Zugentlastung: Netz, Heizer, Fan, 24V, Thermocouple, USB.

## Ampel-Liste

### Gruen: OK fuer Bestellung

Diese Punkte sind fuer die erste Bestellung plausibel, solange die JLC-Preview/Rotationen bestaetigt werden:

- PCB-Fertigung als Low-Voltage-Controller, kein 230VAC auf der Platine.
- Aktuelle konservative Top-SMD-PCBA aus `bom_smd_partial.csv`:
  - `U1` ESP32-S3-WROOM-1, `U2` MAX6675, `J5` USB-C, `Q2` 2N7002.
  - `R1/R2/R3/R4/R5/R6/R7/R8/R10/R11`, `C1/C2/C3`.
- USB-C CC/R-Setup: `R10/R11 = 5.1k` nach GND, `R7/R8 = 27R` in den Datenleitungen.
- SSR-Steuerung als Low-Voltage-Ausgang zu externem SSR: `J3 +5V/SSR_NEG`, kein AC auf der PCB.
- Bring-up nur mit Labornetzteil/Strombegrenzung, zuerst ohne Fan/SSR/Heizerlast.

### Gelb: OK fuer Prototyp mit Messung / Review

Diese Punkte sind fuer RevA.1 nutzbar, aber nicht blind als Serien-/Endauslegung behandeln:

- `J1-J4` nicht mehr als bestueckte 5.08-mm-Terminals behandeln: aktueller Stand sind grosse Handloet-Pads ohne Connector-PCBA. Kabel direkt einloeten und im Gehaeuse mechanisch zugentlasten.
- `Q1` IRLB8721/FQP30N06L-Klasse: Pinout/Footprint plausibel, aber Fanstrom, Gehaeusetemperatur und Gate-Ansteuerung mit realem Fan messen. Bei 3A Dauerlast MOSFET und Leiterbahn thermisch beobachten.
- 24V/Fan-Strompfad: aktuell keine Kupferzonen und nur ca. 0.20-0.45-mm-Tracks. Grobe IPC-2221-Naehung fuer 1 oz externe Leiterbahn: 0.20 mm liegt nur um ~0.7A bei 10C bzw. ~1.2A bei 30C Temperaturanstieg; 0.45 mm um ~1.3A/10C bzw. ~2.2A/30C. Fuer 3A daher nur mit realer Messung, Stromlimit, kurzer Laufzeit oder zusaetzlicher Draht-/Externfuehrung.
- `F1` 24V-Sicherung: T3.15A ist als Branch-Schutz plausibel, aber exakten Halter/Fuse, Ausloesecharakteristik und Fan-Anlaufstrom vor Montage pruefen. Alternativ externen Inline-DC-Fuseholder verwenden.
- `C4` 220uF/35V Bulk: elektrisch sinnvoll, aber erst exakte Elko-Teilenummer, Pitch, Lead-Durchmesser, Polung und Bauhoehe gegen Gehaeuse pruefen.
- `U4` 24V->5V Buck und `U3` 5V->3V3: fuer Prototyp moeglich als Wire-in/Handloet-Loesung, aber der aktuelle Footprint ist nicht die finale automatische Bestueckung. Ausgangsrauschen/Temperatur unter WLAN+SSR+MAX6675 messen.
- Thermocouple an `J4`: elektrisch ok fuer K-Type/MAX6675, aber mechanische Zugentlastung und Abstand zu Netz-/Heizer-/Fanleitungen im Gehaeuse entscheiden. Nur isolierte/geeignete Sonde verwenden.
- USB bei laufendem Roaster: Datenverbindung erst testen, wenn 24V/3V3 stabil sind. PC/Laptop nicht als Sicherheitsbarriere betrachten; USB-Kabel mechanisch sichern und vom Netz-/Heizerbereich fernhalten.

### Orange: Nicht auf RevA.1 bestuecken lassen

Diese Teile sollten nicht wegen hoher PCBA-Grundkosten einfach in die automatische Bestueckung aufgenommen werden:

- `D1` SB560/Flyback: aktueller DO-201AD-Kandidat wirkt fuer den vorhandenen 10.16-mm/1.0-mm-Drill-Footprint nicht sicher passend. Handloeten/alternativen Footprint waehlen.
- `D2/D3` SMBJ33A TVS: aktuelle Pads sind nicht als Standard-SMB/DO-214AA verifiziert. DNP lassen oder Footprints in RevA.2 ersetzen.
- `C5` Thermocouple-Filter: aktueller Footprint ist nicht 0805 und der Filter kann Messwerte beeinflussen. DNP bis Noise-Test.
- `U5` USB-ESD: aktueller Custom/Draft-Footprint passt nicht sicher zu USBLC6-2SC6. DNP; fuer RevA.2 mit exaktem SOT-23-6/USB-ESD-Footprint neu routen.
- `SW1/SW2`: bisher notierter Kandidat ist laut bestehender Footprintpruefung falsch; nicht automatisch bestuecken lassen.
- `U3/U4` automatische PCBA: nicht ohne exakte Regler-/Buck-Footprints und thermische/EMI-Pruefung.

### Rot: RevA.2 noetig / nicht durch Bestellung loesen

Diese Punkte sollten nicht in RevA.1 hineingedrueckt werden:

- Finaler 3A-Fan-Dauerbetrieb ueber die jetzigen schmalen Leiterbahnen. RevA.2 braucht breite Hochstromtraces/Kupferflaechen, ggf. 2 oz Kupfer oder definierte Off-board-Powerfuehrung, plus erneute DRC/thermische Messung.
- Serien-/Einbauversion mit automatisierter Bestueckung aller Schutzteile: D1/D2/D3/U5/C5/U3/U4 brauchen exakte Footprints/Parts und erneute Layoutpruefung.
- Mains-integrierte PCB oder AC-Heizerpfad auf der Controllerplatine. Nicht fuer RevA.1; wenn spaeter gewollt, eigene Safety-/Creepage-/Clearance-/Normen-Review und Layoutrevision.
- Mechanische Endloesung fuer Thermocouple-Mini-Jack, USB-Panelzugang, Netzteil-/SSR-Montage und Kabelzugentlastung. Das muss mit dem Gehaeuse zusammen entschieden werden, bevor ein "fertiges" Board entsteht.

## Entscheidungen vor Bestellung

1. Bestellung nicht auf "alles bestuecken" aendern. Empfehlung: aktuelle konservative SMD-Liste beibehalten; `J1-J4` bleiben Handloet-Pads ohne Connector-Bestueckung. Optional nur `Q1` in der JLC-Quote testen, wenn die Preview/THT-Review ihn akzeptiert.
2. Wenn Mehrkosten fuer Standard-PCBA ohnehin anfallen: Geld eher in sichere, verifizierte SMD-Teile stecken, nicht in unsichere Schutz-/Power-Footprints.
3. Vor Checkout festlegen, dass `J1-J4/F1/C4/U3/U4` handgeloetet bzw. gewired werden; `Q1` nur bei bestandener JLC-THT-Preview automatisch bestuecken. Fuer den ersten Prototyp ist Handloeten/Wiren hier sicherer als erzwungene automatische Bestueckung.
4. Vor Einbau festlegen: Netzteilposition, SSR-Kuehlkoerper, PE/Chassis, Hauptschalter, Netzsicherung, thermische Sicherung, Kabelverschraubungen/Zugentlastungen, Abstand zwischen mains/heater und Low-voltage/thermocouple/USB.
5. Bring-up-Sequenz dokumentieren: ohne Heizer, ohne Fanlast, Labornetzteil current limit, Rails messen, ESP/USB testen, SSR-LED/SSR-Input testen, Fan bei steigender Strombegrenzung testen, danach erst Integration in das mains-Gehaeuse.

## Prototyp-Bring-up-Messplan

- Sichtpruefung: JLC-Orientierung U1/U2/J5/Q2, keine Bruecken, USB-C mechanisch sauber.
- Widerstandstest stromlos: +24V_RAW->GND, +24V_FUSED->GND, +5V->GND, +3V3->GND auf Kurzschluss pruefen.
- 24V-Einspeisung mit Labornetzteil und niedrigem Current Limit starten; TP24V/TP5V/TP3V3 messen.
- ESP32 ueber USB erkennen lassen, ohne Fan/SSR/Heizerlast.
- SSR-Ausgang an Dummy-Last/LED oder SSR-Input testen, nicht sofort am Heizer.
- Fan mit realem 24V-Fan stufenweise testen: Strom, Q1-Temperatur, J2/F1/J1-Temperatur, Leiterbahn-/Pad-Erwaermung nach 1/5/15 Minuten pruefen.
- Thermocouple lesen, dabei Abstand zu Fan-/Heizerleitungen testen; `C5` nur nach nachgewiesenem Noise-Problem nachruesten.

## Bestell-Empfehlung

Fuer jetzt: RevA.1 als Low-voltage-Prototyp bestellen, aber konservativ teilbestuecken. Keine Panik wegen mains auf der PCB - die Grenze ist richtig gesetzt. Nicht versuchen, die hohe PCBA-Grundgebuehr durch riskante Max-Bestueckung zu "retten". Der reale Sicherheitsgewinn entsteht durch saubere Gehaeuse-/Mains-Arbeit und durch Messung des 24V/Fan-Pfads, nicht durch automatisches Platzieren ungepruefter Schutz-/Power-Teile.
