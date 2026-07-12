# CoffeeRoast-Control RevA.2 partial-SMD PCBA handoff

Current first-prototype package: PCB fabrication plus **top-side SMD assembly only**, with THT/power/mechanical parts hand-soldered after delivery.

## Current files

- `partial-smd-pcba/CoffeeRoast-Control-RevA2_partial_smd_pcba_package.zip` — current RevA.2 upload bundle containing Gerbers, drill, BOM, CPL, DNP list and ordering notes.
- `partial-smd-pcba/gerbers/` — current board fabrication Gerbers.
- `partial-smd-pcba/drill/` — Excellon drill file, map and report.
- `partial-smd-pcba/assembly/bom_smd_partial.csv` — conservative SMD assembly BOM.
- `partial-smd-pcba/assembly/cpl_smd_partial.csv` — top-side centroid/place file.
- `partial-smd-pcba/assembly/dnp_hand_solder.csv` — debug pads, THT, power and placeholder parts excluded from automated assembly.
- `partial-smd-pcba/assembly/part_mapping_review.csv` — preferred exact MPN/spec checklist for assembler mapping.

`obsolete-reva1/` contains superseded RevA.1 and Y4 packages. **Do not upload or order anything from that directory.** Any earlier manufacturer upload/cart item is stale after the RevA.2 copper changes.

## Current partial-assembly scope

Assemble by PCB house: U1 ESP32 module, U2 MAX6675, J5 USB-C connector, Q2 and the known-good SMD passives listed in the generated BOM.

Hand-solder / DNP for the first prototype: J1-J4, F1, D1, Q1, U4, C4, SW1/SW2, U5, D2/D3, C5 and all debug/test pads. U4 still requires an exact 24V→3.3V module/footprint decision. U5/D2/D3/C5 remain DNP until exact land patterns are verified.

## Remaining manual step before checkout

Re-confirm component availability and inspect orientation/placement in the assembler UI. If a part cannot be confidently mapped, mark it DNP and hand-solder it later. Do not pay until the current RevA.2 Gerber preview, BOM selection and placement preview all match the board.

## Verification

- Full KiCad DRC: 0 violations.
- Unconnected items: 0.
- ZIP integrity: verify with `unzip -t` after each regeneration.
- No checkout or payment has been performed.
