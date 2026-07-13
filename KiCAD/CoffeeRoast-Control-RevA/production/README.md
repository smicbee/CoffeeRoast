# CoffeeRoast-Control RevA.2 partial-SMD PCBA handoff

Current first-prototype package: PCB fabrication plus **top-side SMD assembly**, with the documented THT/power/connectors hand-soldered after delivery.

## Current files

- `partial-smd-pcba/CoffeeRoast-Control-RevA2_partial_smd_pcba_package.zip` — current upload bundle containing Gerbers, drill, BOM, CPL, DNP/manual list, QA reports and ordering notes.
- `partial-smd-pcba/gerbers/` — current board fabrication Gerbers.
- `partial-smd-pcba/drill/` — Excellon drill file, map and report.
- `partial-smd-pcba/assembly/bom_smd_partial.csv` — 42-designator SMD assembly BOM.
- `partial-smd-pcba/assembly/cpl_smd_partial.csv` — matching top-side centroid/place file.
- `partial-smd-pcba/assembly/dnp_hand_solder.csv` — debug pads and manual/DNP positions.
- `partial-smd-pcba/qa/` — machine-readable ERC and full DRC/parity reports.

`obsolete-reva1/` contains superseded RevA.1/Y4 packages. **Do not upload or order anything from that directory.** Any earlier manufacturer upload/cart is stale.

## Current design changes

- F1 and the separate `+24V_FUSED` rail are removed.
- The board now uses one direct `+24V_RAW` rail; provide overcurrent protection via a current-limited or externally fused 24V supply.
- J6 is a four-pad ESC hand-solder connector with fixed order: `+24V / GND / PWM(GPIO10) / GND`.
- GPIO10 is output-capable and avoids the ESP32-S3's input-only/strapping-sensitive alternatives on the spare GPIO row.

## Assembly scope

- Assemble by PCB house: exactly the parts in `bom_smd_partial.csv` and `cpl_smd_partial.csv`.
- Hand-solder: J1-J4, J6, D1, Q1 and C4.
- C5 remains DNP pending thermocouple noise/bias testing; debug/test pads receive no component.

## Checkout and bring-up gates

1. Re-confirm live component availability and inspect polarity/orientation/placement in the assembler UI.
2. Verify the ESC accepts a 24V input and 3.3V PWM before wiring J6; do not connect a BEC output to J6 pin 1.
3. Use a current-limited bench supply or an external 24V fuse for first power-up.
4. Do not pay until Gerber, drill, BOM selection and placement preview match the current board.

## Verification

- Schematic ERC: 0 violations.
- Full KiCad DRC: 0 violations.
- Unconnected items: 0.
- Schematic parity: 0 problems.
- ZIP integrity: passed.
- No checkout, upload, payment or order has been performed.
