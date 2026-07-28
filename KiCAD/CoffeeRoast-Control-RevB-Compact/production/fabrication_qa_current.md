# CoffeeRoast RevB Compact fabrication QA

Run date: 2026-07-28  
Toolchain: KiCad CLI / pcbnew 9.0.8, Freerouting 2.2.4  
Board: `CoffeeRoast-Control-RevB-Compact.kicad_pcb`

## Verdict

**CAD and manufacturing files are released for prototype-order review.**
No order, upload or payment has been performed. Manufacturer Gerber/BOM/CPL previews
and live component mappings remain mandatory before payment.

## Mechanical result

- Nominal outline: 105.0 x 75.0 mm
- Previous proven RevA.2 outline: 160.0 x 100.0 mm
- Area reduction: 50.78%
- Primary field connectors: left edge
- USB-C: opposite/right edge
- ESP32 antenna: top edge with active copper/component keepout
- Front and back connector/pin labels: present

## Electrical CAD gates

- Schematic ERC: 0 violations
- Full PCB DRC: 0 violations
- Unconnected items: 0
- Schematic parity: 0 findings
- Nominal board outline closed
- B.Cu GND zone refilled
- `+24V_RAW`: 1.20 mm deliberate routes
- `FAN_NEG`: 1.00 mm deliberate routes
- `BUCK_SW`: 0.80 mm
- Copper-angle audit: 355 segments >=0.5 mm checked; 0 arbitrary-angle findings

## Manufacturing package

- PCBA BOM designators: 43
- Grouped JLC BOM rows: 30
- CPL designators: 43
- DNP/hand-solder rows: 21
- Part-mapping review rows: 43
- Full package ZIP integrity: PASS (`unzip -t`)

SHA-256:

```text
cbb1de418ff6f78c9e88c40c0d56de45c42c3e9b06d9d303f6a5d81864f53a00  CoffeeRoast-Control-RevB-Compact.kicad_pcb
0d18461dccb1fd8658492c6b135dedae6cd970d325e786d7f28c2dfbd4ba9aa4  CoffeeRoast-Control-RevB-Compact_partial_smd_pcba_package.zip
5d554ef7f46caea0ccd2701ce2a77ad8033a5113ed708c2fc886e27bc91da8ba  CoffeeRoast-Control-RevB-Compact_JLC_Gerber_Drill.zip
```

## Manual gates before payment

1. Use a fresh RevB upload; do not reuse RevA Gerber/CPL placement state.
2. Confirm finished dimensions are 105 x 75 mm.
3. Confirm J5 is flush with the right product edge.
4. Confirm the ESP32 antenna keepout is empty in copper and assembly previews.
5. Confirm U2 Pin 1, U4 exposed-pad orientation, USB/ESD orientation, diode polarity,
   switch rotation, Q1 three-lead placement and L1 terminal overlap.
6. Re-confirm supplier availability and package mapping for all 43 designators.
7. Keep J1-J4, J6, D1 and C4 in the documented manual-assembly scope; C5 remains DNP.
8. Use current-limited/external-fused 24 V bring-up and thermally validate the 2.5 A fan path.
9. Keep all 230 VAC wiring off-board.
