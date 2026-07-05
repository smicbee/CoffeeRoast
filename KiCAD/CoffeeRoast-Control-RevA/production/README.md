# CoffeeRoast-Control RevA.1 partial-SMD PCBA handoff

Generated first-order package for the chosen approach: PCB fabrication plus **top-side SMD assembly only**, with THT/power/mechanical parts hand-soldered after delivery.

## Files

- `partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip` — upload bundle containing Gerbers, drill, BOM, CPL, DNP list, and ordering notes.
- `partial-smd-pcba/gerbers/` — board fabrication Gerbers.
- `partial-smd-pcba/drill/` — Excellon drill file, map, and report.
- `partial-smd-pcba/assembly/bom_smd_partial.csv` — SMD assembly BOM for the first prototype run.
- `partial-smd-pcba/assembly/cpl_smd_partial.csv` — top-side centroid/place file for the SMD assembly BOM.
- `partial-smd-pcba/assembly/dnp_hand_solder.csv` — debug pads, THT, power, and placeholder parts that should not be assembled by the PCB house.
- `partial-smd-pcba/assembly/part_mapping_review.csv` — preferred exact MPN/spec checklist to use while mapping parts in the assembler UI.
- `selected_parts.csv` / `selected_parts.md` — selected purchase/assembly candidates, including hand-solder and RevA.2-only parts.

## Current partial-assembly scope

Assemble by PCB house: ESP32 module, MAX6675, USB-C connector, Q2, and the known-good 0805 passives. Supplier/JLC part numbers are pre-filled for this conservative assembly set.

Hand-solder / DNP for the first prototype: J1-J4 screw terminals, F1, D1, Q1 fan MOSFET, U3 exact 3V3 regulator, U4 24V->5V buck, C4 input bulk capacitor, SW1/SW2, U5 USB ESD, D2/D3 TVS, C5 thermocouple filter, and all debug/test pads. U5/D2/D3/C5 have selected candidate parts, but the current RevA.1 footprints are draft/custom and should not be automated-assembled until RevA.2.

## Remaining manual step before actual checkout

The generated BOM now has JLC supplier/C-codes for the conservative first assembly set. In the JLCPCB/PCBWay UI, still re-confirm availability and visually inspect orientations before paying. If a part cannot be confidently mapped, mark it DNP and hand-solder it later.

## Verification

Package ZIP integrity was tested with `unzip -t`.
KiCad error-level DRC remains clean: 0 violations, 0 unconnected pads, 0 footprint errors.
