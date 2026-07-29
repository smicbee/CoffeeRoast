# CoffeeRoast Control RevD Balanced — placement candidate

RevD is a **separate placement candidate** derived from the exact RevC UltraCompact circuit and footprints. It keeps the **96 × 60 mm, two-layer** board outline but distributes the functional blocks more evenly over the usable area.

The proven RevC project remains untouched.

## What changed

- Thermocouple/MAX6675 block moved upward and opened out.
- SSR and fan-driver support parts use more of the centre-left area instead of crowding the bottom edge.
- RESET/BOOT controls and probes have clearer service access.
- USB-C remains on the top edge; field wiring remains grouped along the bottom edge.
- ESP32-S3-WROOM-1 moved to the top edge; the physical antenna front is exactly flush with `y = 0`.
- The on-board antenna keepout is now **48 × 6.2 mm**: Espressif's 18 × 6.2 mm antenna area plus conservative 15 mm side clearances; forward clearance lies outside the PCB.
- Buck converter moved upward into the recovered right-hand area.
- SSR, ESC/PWM, fan and 24 V field pads are distributed farther apart along the bottom edge.
- Front and back silkscreen identify the functional blocks, including USB/ESD, MAX6675 thermocouple front-end, SSR driver, 10 V gate supply, fan driver/MOSFET, ESP32-S3, antenna keepout and 24 V-to-3.3 V buck stage.
- Board remains SELV/low voltage only; 230 VAC stays outside the PCB.

## Current verification state

This revision is intentionally stopped at the **visual-placement acceptance gate** before routing:

- board outline: **96 × 60 mm**
- copper layers: **F.Cu + B.Cu only**
- placement DRC: **0 violations**
- expected unrouted connections: **141**
- schematic ERC: **0 violations**
- top and bottom placement renders: `render/placement/top.png`, `render/placement/bottom.png`

It is **not fabrication-ready**. Routing, GND pours, full DRC/parity, angle audit, Gerbers, BOM/CPL and manufacturer preview are deliberately deferred until the placement is visually accepted.

## Reproduce the placement

From this directory with KiCad/pcbnew 9.0.8:

```bash
/usr/bin/python3 tools/build_balanced_revd.py
kicad-cli pcb drc --severity-all --format json \
  -o qa/placement-drc.json CoffeeRoast-Control-RevD-Balanced.kicad_pcb
kicad-cli sch erc --format json \
  -o qa/erc.json CoffeeRoast-Control-RevD-Balanced.kicad_sch
```

The build script is version-marked and idempotent: a second normal run is a hash-identical no-op. Pass `--force` only when deliberately regenerating the placement after editing its coordinates. It clears placement-dependent copper, applies the RevD coordinates, restores the two-layer outline and labels, and refills the retained baseline GND zone.
