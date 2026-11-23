# CoffeeRoast RevA.2 fabrication QA current

Run date: 2026-07-14
Toolchain: KiCad CLI / pcbnew 9.0.8
Board: `CoffeeRoast-Control-RevA.kicad_pcb`

## Verdict

**Freigegeben für Prototyp-PCB-Fertigung und den dokumentierten partiellen Top-SMD-Bestückungsumfang.**

Die früheren Draft-/Placeholder-Footprints für Buck, Gate-Treiber, USB-ESD, TVS, Taster, Leistungshalbleiter und Support-Bauteile wurden durch konkrete, datenblatt- und padnummernbezogen geprüfte Teile ersetzt. Die On-board-Sicherung F1 wurde auf Nutzerwunsch entfernt; `+24V_FUSED` ist in `+24V_RAW` aufgegangen. J6 ergänzt einen ESC-Handlötanschluss mit `+24V / GND / PWM(GPIO10) / GND`. Schaltplan und PCB sind synchron. Die Freigabe umfasst nicht Zahlung, Serienfreigabe oder den Netzspannungs-/Gehäuseaufbau.

## Elektrische und CAD-Verifikation

- Schematic ERC: **0 violations**.
- Full PCB DRC including warnings and all-track errors: **0 violations**.
- Unconnected PCB items: **0**.
- Schematic parity: **0 problems**.
- Local footprint/library mismatches: **0 findings**.
- `+24V_RAW`: 1.20 mm routed current paths, including the new ESC feed.
- `FAN_NEG`: 1.00 mm routed current path.
- Critical fan via: 1.20 mm diameter / 0.60 mm drill.
- B.Cu GND zone refilled with 0.25 mm minimum thickness.
- Exact-hardware script: stable; second application is a hash-identical no-op.

Machine-readable reports are included in:

- `production/partial-smd-pcba/qa/erc.json`
- `production/partial-smd-pcba/qa/drc_full_parity.json`

## Exact hardware scope

Key selections include:

- U4: TI `LMR16010PDDAR`, 60 V / 1 A HSOIC-8 PowerPAD.
- U6: TI `UCC27511DBVR`, split-output SOT-23-6 gate driver.
- Q1: ST `STP55NF06L`, TO-220, hand-soldered.
- U5: ST `USBLC6-2SC6`, SOT-23-6 USB ESD.
- D1: Vishay `SS56-E3/57T`, SMB flyback diode, hand-soldered.
- D2/D3: `SMBJ33A-13-F`, SMB TVS.
- J6: four 5.08 mm hand-solder pads, pin order `+24V / GND / PWM(GPIO10) / GND`.
- SW1/SW2: E-Switch `TL3301AF160QG`.
- C4: Panasonic `EEU-FR1V221B`, 220 uF / 35 V radial.

Full MPN, supplier mapping, footprint and assembly disposition are in `docs/bom.csv` and the package assembly CSV files.

## Visual QA

- Final top and bottom 3D renders were generated and reviewed.
- No components or pads lie outside the board outline.
- No obvious component-body/courtyard overlap was visible.
- ESP32 antenna keepout is visible at the board edge and free of copper in the checked layout.
- Final schematic render was reviewed after spreading the functional blocks and hiding long MPN value fields; net labels and references are readable without material overlap.
- Final renders are under `render/final/`.

## Current fabrication/PCBA package

`production/partial-smd-pcba/CoffeeRoast-Control-RevA2_partial_smd_pcba_package.zip`

- Size: **150881 bytes**.
- SHA-256: `68debc6edbfff353f872d5104943ac7d755ffb2721f405b2fcd5bb7511df3529`.
- ZIP integrity: `unzip -t` passed with no compressed-data errors.
- Top-side PCBA BOM: **42 designators**.
- CPL: **42 matching designators**.
- Gerber, drill, BOM, CPL, DNP/manual list, part-mapping review and machine-readable QA reports are included.
- Prior RevA.1/Y4 artifacts remain under `production/obsolete-reva1/` and are **do not order**.

## Mandatory order and bring-up checks

1. Use a fresh manufacturer upload; previous carts/uploads are stale.
2. Inspect Gerber, drill and placement previews before payment.
3. Re-confirm live supplier mapping for R15/R16 and stop if a package or MPN differs.
4. Confirm Pin 1/polarity/rotation for U1, U2, U4, U5, U6, J5, Q2, D2-D5 and SW1/SW2 in the assembler UI.
5. Hand-solder J1-J4, J6, D1, Q1 and C4; leave C5 DNP until thermocouple testing.
6. Before using J6, verify the ESC accepts 24 V supply and 3.3 V logic-level PWM; do not feed a BEC output into the PCB.
7. First power-up uses a current-limited 24 V bench supply or an external 24 V fuse.
8. Thermally validate the real 24 V / 2.5 A fan stage and the ESC supply path in the enclosure before any series use.
9. 230 VAC wiring, certified PSU, external SSR/heatsink, PE/chassis bonding and independent thermal cutoff remain outside this PCB.
10. No checkout, upload, payment or order was performed.
