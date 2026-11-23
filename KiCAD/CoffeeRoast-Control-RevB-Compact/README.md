# CoffeeRoast Control RevB Compact

Compact mechanical redesign of the ordered and proven CoffeeRoast RevA.2 circuit.
The working RevA.2 project remains untouched in `../CoffeeRoast-Control-RevA/`.

## Result

- Nominal board outline: **105 x 75 mm**.
- Previous outline: 160 x 100 mm.
- Board area reduction: **50.78%**.
- Circuit, exact components and connector pin assignments are preserved.
- All primary field wiring is grouped on the **left edge**:
  1. J4 thermocouple (`TC+`, `TC-`)
  2. J3 external SSR (`3V3`, `SSR-`)
  3. J6 ESC (`24V`, `GND`, `PWM`, `GND`)
  4. J2 fan (`24V`, `FAN-`)
  5. J1 supply (`24V`, `GND`)
- J5 USB-C is on the **opposite/right edge**.
- JGPIO1 remains on the lower edge as a secondary expansion/service row.
- RESET and BOOT remain accessible from the top side.
- Front and back silkscreen repeat connector names, pin functions, board identity and the low-voltage safety note.

## Deliberate compacting decisions

The duplicated 40 ESP32 probe pads plus 40 wire-attach pads from RevA.2 were removed.
They were board-only debug geometry and duplicated access already available through the
module pads, purposeful test points and JGPIO1. The following service points remain:

- TP24V
- TP3V3
- TPGND
- TPRESET1
- TPBOOT1
- TPSSR1
- JGPIO1

The ESP32 antenna is on the top edge. Its footprint keepout remains active on both copper
layers; no copper, component or enclosure metal should enter that region.

## Routing policy

- `+24V_RAW`: 1.20 mm deliberate routes.
- `FAN_NEG`: 1.00 mm deliberate routes.
- `BUCK_SW`: 0.80 mm.
- Critical power via: 1.20 mm diameter / 0.60 mm drill.
- B.Cu GND plane is refilled after every routing operation.
- Every routed segment at least 0.5 mm long is horizontal, vertical or 45 degrees;
  arbitrary-angle/high-current traces are not accepted.
- KiCad full DRC includes `--all-track-errors --schematic-parity`.

The remaining signal routing was generated with pinned Freerouting 2.2.4, then the
24 V, fan-current and buck switching routes were replaced with deterministic reviewed
geometry by `tools/rebuild_critical_routes.py`.

## Reproduction

Run scripts with the system Python containing KiCad's `pcbnew` module:

```bash
/usr/bin/python3 tools/build_compact_revb.py
/usr/bin/python3 tools/route_compact_revb.py
/usr/bin/python3 tools/rebuild_critical_routes.py
/usr/bin/python3 tools/render_route_qa.py
/usr/bin/python3 tools/prepare_partial_pcba_package.py
```

`route_compact_revb.py` pins Freerouting 2.2.4 by SHA-256 and refuses to reroute an
already completed board. Start from a fresh RevA.2-derived project copy for a full rebuild.

## Verification

The current checked-in design passes:

- Schematic ERC: 0 violations
- Full PCB DRC: 0 violations
- Unconnected items: 0
- Schematic parity: 0 findings
- Copper angle audit: 0 non-45-degree segments longer than 0.5 mm

Human-facing outputs are under `render/final/`:

- top and bottom 3D board renders
- top, bottom and combined copper-route views
- schematic PDF and SVG
- ERC and DRC JSON reports

## Manufacturing output

Generated files are under:

```text
production/partial-smd-pcba/
```

The package contains Gerber, drill, grouped BOM, CPL, DNP/hand-solder list, part-mapping
review and QA reports. Use a **fresh** manufacturer upload; never reuse RevA Gerber/CPL
state or Auto-Align as a substitute for matching source origins.

This remains a low-voltage controller PCB. No 230 VAC belongs on the board. Before payment,
verify manufacturer previews, live stock, package/polarity, the USB product edge, ESP32
antenna clearance, Q1 lead placement, switch rotation and L1 terminal overlap.
