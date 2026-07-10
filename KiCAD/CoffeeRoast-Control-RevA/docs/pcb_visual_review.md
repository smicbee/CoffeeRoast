# CoffeeRoast Control RevA.1 PCB Visual Review

Generated visual handoff artifacts for the CoffeeRoast RevA.1 low-voltage controller PCB.

## Rendered files

- `../render/coffeeroast_component_map_annotated.png`  
  Full component placement map. Every real component footprint is called out with a reference bubble and a side table containing the exact KiCad x/y coordinate in mm.
- `../render/coffeeroast_jlc_pcba_placement_annotated.png`  
  JLC-PCBA-only callout map. Green callouts are the current first-pass Standard PCBA set from `production/partial-smd-pcba/assembly/bom_smd_partial.csv`; gray outlines are intentionally not assembled by JLC in this prototype pass.
- `../render/coffeeroast_actual_traces_overlay.png`  
  Trace/net overlay generated from the actual KiCad tracks and vias. Colors group nets by function so the JLC preview and layout can be checked against the intended power/control paths.
- `../render/coffeeroast_functional_block_diagram.png`  
  Functional block diagram explaining the build/order decision: low-voltage PCB only, external PSU/SSR/enclosure for hazardous energy, and which functional blocks are JLC PCBA vs hand/DNP.

## Color legend

### Component maps

- Green: JLC PCBA / automatically assembled in the current BOM+CPL set.
- Orange: Hand-solder, DNP, or later footprint/mechanical verification.
- Gray: Debug/test pads or non-PCBA visual context.
- Purple pad marks: footprint/pad locations for visual comparison with JLC preview.

### Trace/net overlay

- Orange: `+24V_RAW`, `+24V_FUSED`, and fan high-current path.
- Yellow: `+5V` / USB VBUS related power.
- Green: `+3V3` rail.
- Cyan: USB D+/D-/CC routing.
- Purple: MAX6675 SPI and thermocouple related nets.
- Pink: fan/SSR PWM and MOSFET/driver gate control nets.
- Gray/white: GND, board outline, vias, and reference points.

## Current assembly interpretation

Current JLC PCBA set:

- U1 ESP32-S3-WROOM module
- U2 MAX6675 SOIC-8
- J5 USB-C receptacle
- Q2 2N7002 SSR driver
- C1, C2, C3
- R1, R2, R3, R4, R5, R6, R7, R8, R10, R11

Keep out of the first automated PCBA placement unless re-reviewed:

- J1-J4 large hand-solder pads, F1 fuse holder, D1 flyback diode, Q1 fan MOSFET, C4 bulk capacitor, SW1/SW2 buttons: hand-solder/mechanical confirmation items. Do not request connector assembly on J1-J4.
- D2/D3 TVS, U5 USB ESD, C5 thermocouple filter: useful protection/filter positions, but current footprints are treated as DNP/draft until exact land patterns and orientation are rechecked.
- U3/U4 regulator/buck footprints: prototype/wire-in or RevA.2 footprint decision, not current JLC placement.

## Safety and ordering notes

- RevA.1 remains a low-voltage controller PCB: 24V/3A input only, no 230VAC on the PCB.
- The external 230VAC path, PSU, SSR/heatsink, PE/chassis bonding, fuse/switch, strain relief, and thermal cut-off remain enclosure-level work.
- Do not checkout/pay from the JLC cart without explicit user approval.
- Before ordering, compare the JLC preview against the PCBA-only callout map and manually confirm orientation for U1, U2, J5, and Q2.

## Re-generation

The PNGs above are generated from KiCad board data and the partial-SMD assembly CSVs by:

```bash
/usr/bin/python3 KiCAD/CoffeeRoast-Control-RevA/tools/render_pcb_visuals.py
```

This script is a visual-review helper only. It does not replace KiCad ERC/DRC, exact-footprint review, or manufacturer placement/orientation preview checks.
