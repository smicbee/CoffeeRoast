# CoffeeRoast RevA.2 fabrication QA current

Run date: 2026-07-12
Toolchain: KiCad CLI / pcbnew 9.0.8
Board: `CoffeeRoast-Control-RevA.kicad_pcb`

## Verdict

The RevA.2 fabrication/partial-PCBA package was regenerated after the critical-current and routing-quality changes. KiCad DRC/ERC and ZIP integrity are clean. This is still a prototype handoff, not an unconditional order release: exact U4/U5/Q1/D2/D3/mechanical footprints and manufacturer previews remain required.

## Electrical/layout verification

- Full PCB DRC: **0 violations**.
- Error-only PCB DRC: **0 violations**.
- Unconnected PCB items: **0**.
- Schematic ERC: **0 violations**.
- `+24V_RAW`: 1.20 mm throughout.
- `+24V_FUSED`: 1.20 mm throughout.
- `FAN_NEG`: 1.00 mm throughout.
- FAN_NEG via: 1.20 mm diameter / 0.60 mm drill.
- Explicit Q1 source return: 1.00 mm plus 1.20/0.60 mm via.
- B.Cu GND zone refilled with 0.25 mm minimum thickness; previous copper-sliver warnings are gone.
- Current DRC/ERC JSON reports: `render/layout-quality-post/`.

## Current package

`production/partial-smd-pcba/CoffeeRoast-Control-RevA2_partial_smd_pcba_package.zip`

- Size: **146649 bytes**.
- SHA-256: `40c3c6dbb87218e5cc1c6bd8bb4346e5986782b1b10d740080e59b432a5eccc9`.
- ZIP integrity: `unzip -t` passed with no compressed-data errors.
- BOM: 19 top-side SMD designators.
- Gerber/drill/BOM/CPL/DNP/reference files are included.
- Stale RevA.1/Y4 artifacts were moved under `production/obsolete-reva1/` and are explicitly marked **do not order**.

## Remaining no-go gates

1. Confirm exact sourced U4 24V→3.3V module and footprint/pinout.
2. Confirm exact U5, D2, D3, Q1 and all THT/mechanical footprints before placement or fabrication approval.
3. Validate the real 2.5 A fan path thermally for the selected copper weight and ambient conditions.
4. Inspect manufacturer Gerber render, board dimensions and drill preview.
5. For PCBA, inspect selected/unselected BOM parts and placement/orientation for U1, U2, J5, Q2 and passives.
6. Do not reuse earlier JLC uploads or cart items; RevA.2 requires a fresh upload.
7. No checkout or payment was performed.
