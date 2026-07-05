# CoffeeRoast-Control RevA.1 partial-SMD PCBA package

This package is for the recommended first prototype order: **PCB fabrication + top-side SMD assembly only**, with power/THT/mechanical parts hand-soldered afterward.

## Upload set

- `gerbers/` + `drill/` — PCB fabrication data.
- `assembly/bom_smd_partial.csv` — SMD parts intended for assembly.
- `assembly/cpl_smd_partial.csv` — centroid/place file for those SMD parts.
- `assembly/dnp_hand_solder.csv` — parts intentionally not assembled by the PCB house.
- `assembly/part_mapping_review.csv` — preferred MPN/spec checklist for the assembler UI.

## Important ordering notes

- This is a **partial assembly handoff**, not a one-click final manufacturing release.
- Supplier/LCSC/JLC part numbers are pre-filled for the conservative first PCBA set. Re-confirm availability in the assembler UI before ordering.
- Do not ask the PCB house to place the DNP/hand-solder list for the first prototype.
- `U3` and `U4` are intentionally **not** in the first PCBA placement set because the exact switching-regulator/buck implementation is still the main RevA.2 decision.
- `U5`, `D2`, `D3`, and `C5` are also DNP for the first PCBA package: they are useful RevA.1 robustness footprints, but their current draft/custom land patterns should be replaced with exact sourced footprints before automated assembly.
- The controller PCB remains low-voltage only. 230VAC wiring, PSU, SSR, heatsink, PE/chassis bonding, and thermal cut-off are enclosure-level work.
- In the assembler UI, visually confirm rotation/orientation for U1 ESP32-S3-WROOM, U2 MAX6675, J5 USB-C, Q2, and polarized/marked passives.

## Verification run

- KiCad error-level DRC: 0 violations
- Unconnected pads: 0
- Footprint errors: 0

## Recommended order flow

1. Upload the ZIP or the Gerber/drill files for PCB fabrication.
2. Enable SMT assembly for the top side only.
3. Upload `assembly/bom_smd_partial.csv` and `assembly/cpl_smd_partial.csv`.
4. In the assembler UI, map supplier part numbers and mark anything uncertain as DNP.
5. Order 5 boards, but only 2 assembled if the UI allows it.
6. Hand-solder J1-J4, F1, D1, Q1, U3, U4, C4, SW1, SW2 after the boards arrive.
