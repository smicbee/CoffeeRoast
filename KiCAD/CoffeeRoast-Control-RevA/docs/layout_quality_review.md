# CoffeeRoast RevA.2 layout-quality review

Review date: 2026-07-12  
Toolchain: KiCad CLI / pcbnew 9.0.8

## Scope

This pass applies the project `pcb-layout-quality-guidelines` to the existing two-layer board without changing the electrical architecture, connector positions, ESP32 placement, USB topology or assembly split. The goal was to fix actual layout risks first and only then clean visibly arbitrary routing.

## Measured baseline

- 551 track segments, 58 vias, one B.Cu GND zone.
- Full KiCad DRC: 2 warning-level `copper_sliver` findings; error-level DRC clean.
- `+24V_RAW`: 0.60 mm.
- `+24V_FUSED`: mostly 0.60 mm, one 0.30 mm test-pad branch.
- `FAN_NEG`: mostly 0.20 mm, two 0.45 mm segments, one 0.55/0.30 mm transition via.
- Q1 source-return stub: 0.45 mm with a 0.55/0.30 mm via.
- Several recently extended Reset/Boot/test-pad branches used arbitrary 14.9°, 18.4° and 23.2° angles.
- Stale silkscreen still referred to the removed +5V/U3 stage.

The 0.20 mm `FAN_NEG` route was the main electrical issue. A legacy conservative external-layer trace estimate puts 2.5 A at roughly 1.06 mm for a 10 °C rise or 0.70 mm for a 20 °C rise on 1 oz copper. This estimate is a design aid, not a substitute for IPC-2152 validation or thermal testing.

## Applied changes

- Added `CoffeeRoast-Control-RevA.kicad_dru`:
  - minimum 1.0 mm track width for `+24V_RAW`, `+24V_FUSED`, and `FAN_NEG`;
  - critical-current via minimum 0.60 mm drill and 0.30 mm annular ring.
- Widened both 24 V rails to 1.20 mm.
- Widened all `FAN_NEG` segments to 1.00 mm.
- Replaced the FAN_NEG autorouter dogleg around D1 with an exact 45° / horizontal / 45° route that remains DRC-clean.
- Enlarged the FAN_NEG layer transition to 1.20/0.60 mm.
- Widened the explicit Q1 source-return stub to 1.00 mm and its transition via to 1.20/0.60 mm.
- Replaced arbitrary-angle TP24V, TP3V3, Reset and Boot extension segments with deliberate 45°/orthogonal geometry.
- Removed two obsolete/dangling +3V3 vias from the former regulator area.
- Removed stale `TP5V`/`U3` silkscreen and corrected U4/SSR labels from 5 V to 3.3 V.
- Increased the B.Cu GND-zone minimum thickness from 0.20 to 0.25 mm and refilled the zone.
- Added the idempotent generator/ECO script `tools/improve_layout_quality.py`.

## Verified result

- 552 track segments, 56 vias, one refilled B.Cu GND zone.
- Full DRC including errors, warnings and exclusions: **0 violations**.
- Unconnected items: **0**.
- Error-level DRC: **0 violations**.
- Post-pass widths:
  - `+24V_RAW`: 1.20 mm throughout;
  - `+24V_FUSED`: 1.20 mm throughout;
  - `FAN_NEG`: 1.00 mm throughout;
  - FAN_NEG transition: 1.20 mm diameter / 0.60 mm drill.
- The ECO script was run twice; the board hash remained identical after the second run.
- Top and bottom SVG/PNG views were regenerated and visually checked.

## Deliberately retained geometry

- Four direct bottom-side debug-breakout tracks are about 47.2° and two are about 64.8°. They are low-current GPIO access lines, electrically noncritical and shorter than orthogonal detours. They were retained rather than lengthened for cosmetics.
- The USB-C breakout keeps footprint-driven short non-45° GND entry segments. USB D+/D- were not moved in this pass because the existing routing is DRC-clean and a casual cosmetic reroute would create more risk than value.
- The large ESP32 antenna keepout remains copper-free. The B.Cu GND zone stays continuous around the keepout rather than being arbitrarily split.

## Remaining fabrication gates

A clean DRC does **not** make this board order-ready by itself:

1. Exact sourced footprints/land patterns are still mandatory for U4, U5, Q1, D2, D3 and the mechanical/THT parts called out in the README.
2. Confirm 1 oz/2 oz copper, allowed temperature rise and real 2.5 A fan duty with the chosen board house; thermal-test the assembled current path.
3. Review J5 enclosure fit and antenna keepout mechanically.
4. Use only the regenerated RevA.2 package. All earlier RevA.1/Y4 uploads and carts are stale.
5. Inspect JLC/assembler Gerber and placement previews before payment; no checkout was performed here.
