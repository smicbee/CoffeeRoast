# CoffeeRoast-Control RevA.2 partial-SMD PCBA package

This package is the order-ready RevA.2 handoff for **PCB fabrication + top-side PCBA**, including the selected THT Q1; the remaining manual parts are soldered afterward.

## Upload set

- `gerbers/` + `drill/` — PCB fabrication data.
- `assembly/bom_smd_partial.csv` — exact selected components intended for assembly.
- `assembly/bom_smd_partial_jlc.csv` — grouped BOM for direct JLC upload.
- `assembly/cpl_smd_partial.csv` — centroid/place file for those selected components.
- `assembly/dnp_hand_solder.csv` — parts intentionally not assembled by the PCB house.
- `assembly/part_mapping_review.csv` — MPN/package/orientation checklist.

## Important ordering notes

- The PCB, schematic and named nets passed full DRC, ERC and schematic-parity checks before this package was generated.
- Re-confirm live supplier stock before each order; the preferred supplier codes reflect the latest validated JLC mappings.
- CPL rotations for non-polar two-pad R/C/L parts are derived from the actual pad axis, preventing 90° errors from pre-rotated custom footprints such as C6/C7.
- L1 uses the supplier-matched FNR6045S220MT / C168080 land pattern: 2.20 × 5.72 mm pads on 5.00 mm centers.
- Gerber, drill and CPL data share the bottom-left drill/place origin; do not accept a JLC Auto-Align prompt as a substitute for this source-file alignment.
- D1, C4, J1-J4 and J6 are intentionally manual; C5 is intentionally DNP pending thermocouple noise/bias testing. Q1 is included for JLC THT hand-solder assembly.
- J6 pin order is +24V / GND / PWM(GPIO10) / GND; the PCB has no on-board fuse, so use a current-limited or externally fused 24V source.
- U4/U5/U6, D2/D3, the buck support parts and SW1/SW2 now use exact package-qualified footprints and are included in the top-side assembly set.
- The controller PCB remains low-voltage only. 230VAC wiring, PSU, SSR, heatsink, PE/chassis bonding and thermal cut-off are enclosure-level work.
- In the assembler preview, visually confirm Pin 1/polarity/rotation for U1, U2, U4, U5, U6, J5, Q1, Q2, D2-D5 and the two switches.
- A previous JLC upload/cart is stale after this RevA.2 hardware migration; use a fresh upload.

## Verification run

- Full KiCad DRC: 0 violations
- Schematic parity: 0 problems
- Schematic ERC: 0 violations
- Unconnected PCB items: 0
- Footprint/library findings: 0

## Recommended order flow

1. Upload the Gerber/drill data or this ZIP for PCB fabrication.
2. Enable top-side SMT assembly.
3. Upload `assembly/bom_smd_partial.csv` and `assembly/cpl_smd_partial.csv`.
4. Map exact MPNs/supplier codes and stop if any package or polarity differs.
5. Assemble only the 43 BOM designators in this generated package.
6. Inspect the manufacturer's Gerber, drill and placement previews before payment.
7. Hand-solder the manual/DNP list after the boards arrive and perform current-limited bring-up.
