# CoffeeRoast Control RevD Balanced — placement candidate

RevD is a **separate placement candidate** derived from the exact RevC UltraCompact circuit and footprints. It keeps the **96 × 60 mm, two-layer** board outline but distributes the functional blocks more evenly over the usable area.

The proven RevC project remains untouched.

## What changed

- Thermocouple/MAX6675 block moved upward and opened out.
- SSR and fan-driver support parts use more of the centre-left area instead of crowding the bottom edge.
- RESET/BOOT controls and probes have clearer service access.
- USB-C remains on the top edge. J5 is rotated 180° so the XKB `Product Edge`/mating face is exactly at board `y = 0`; the fine SMT tail row is inboard at `y = 7.345 mm`. Field wiring remains grouped along the bottom edge.
- ESP32-S3-WROOM-1 moved to the top edge; the physical antenna front is exactly flush with `y = 0`.
- The on-board antenna keepout is now **48 × 6.2 mm**: Espressif's 18 × 6.2 mm antenna area plus conservative 15 mm side clearances; forward clearance lies outside the PCB.
- Buck converter moved upward into the recovered right-hand area.
- SSR, ESC/PWM, fan and 24 V field pads are distributed farther apart along the bottom edge.
- Front and back silkscreen identify the functional blocks, including USB/ESD, MAX6675 thermocouple front-end, SSR driver, 10 V gate supply, fan driver/MOSFET, ESP32-S3, antenna keepout and 24 V-to-3.3 V buck stage.
- Three compact, unpopulated 1.27 mm headers reserve the future local user interface without changing firmware:
  - `J7` digital microphone: 3V3, GND, BCLK, WS, DATA, SEL;
  - `J8` I2C LCD: 3V3, GND, SDA, SCL, INT, RST;
  - `J9` four-button panel: GND, BTN1, BTN2, BTN3, BTN4, optional 3V3.
- All three future UI connectors are explicitly 3.3 V interfaces. They are hardware reservations only; pin initialization, I2S/I2C drivers, pull-ups and button handling are not implemented in software yet.
- J7–J9 now use horizontal pad rows. Every pin function is printed immediately beside its pad with 90-degree text on both board sides, and each complete MIC/LCD/BUTTONS group is enclosed by its own silkscreen frame.
- Board remains SELV/low voltage only; 230 VAC stays outside the PCB.

## Current verification state

This revision is intentionally stopped at the **visual-placement acceptance gate** before routing:

- board outline: **96 × 60 mm**
- copper layers: **F.Cu + B.Cu only**
- placement DRC: **0 violations**
- expected unrouted connections: **159**
- schematic ERC: **0 violations**
- schematic/PCB parity: **0 issues**
- orientation/polarity audit: **PASS, 32 functional references asserted**
- top and bottom placement renders: `render/placement/top-ui.png`, `render/placement/bottom-ui.png`
- detailed audit: `docs/orientation_and_mechanical_audit.md`

It is **not fabrication-ready**. Routing, GND pours, full DRC/parity, angle audit, Gerbers, BOM/CPL and manufacturer preview are deliberately deferred until the placement is visually accepted.

## Reproduce the placement

From this directory with KiCad/pcbnew 9.0.8:

```bash
python3 -m pip install -r tools/requirements.txt
python3 tools/add_ui_connectors_to_schematic.py
/usr/bin/python3 tools/build_balanced_revd.py
/usr/bin/python3 tools/audit_orientation_sensitive_parts.py
kicad-cli pcb drc --severity-all --format json \
  --all-track-errors --schematic-parity \
  -o qa/placement-ui-parity-drc.json CoffeeRoast-Control-RevD-Balanced.kicad_pcb
kicad-cli sch erc --format json \
  -o qa/erc-ui.json CoffeeRoast-Control-RevD-Balanced.kicad_sch
```

Both UI/schematic and placement scripts are idempotent: a second normal run is a hash-identical no-op. Pass `--force` to the placement script only when deliberately regenerating after editing its coordinates. It clears placement-dependent copper, applies the RevD coordinates, restores the two-layer outline and labels, and refills the retained baseline GND zone.

The detailed UI pin map, including physical pad coordinates, is in `docs/ui_expansion_connectors.csv`. The 1.27 mm headers remain `HAND/DNP` placeholders until the display, microphone module and enclosure cable scheme are selected.

## Electrical simulation

A reproducible block-level electrical simulation is in `sim/`. It covers the 24 V-to-3.3 V buck power stage, feedback corners, fan MOSFET loss, 10 V gate-supply budget, 24 V PSU loading, input bulk capacitance, USB CC current and an external SSR-input sweep. See `sim/README.md` for results and explicit model limits.
