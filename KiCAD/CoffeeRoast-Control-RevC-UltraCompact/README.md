# CoffeeRoast Control RevC UltraCompact

Compact mechanical revision of the ordered and proven CoffeeRoast RevA.2 circuit. RevB remains the conservative 105 × 75 mm reference; RevC reduces the board to **96 × 60 mm** without changing the intended electrical functions.

## Mechanical layout

- Board outline: **96 × 60 mm** (5,760 mm²)
- Primary field wiring shares the bottom edge:
  - thermocouple
  - SSR
  - ESC
  - fan
  - 24 V input
- USB-C is on the opposite/top edge.
- The optional GPIO service row is internal to the left/middle service area.
- ESP32 antenna keepout reaches the top edge and remains free of copper and components.
- Functional labels are present on front and back.
- The PCB carries SELV/low voltage only; 230 VAC remains outside the board.

## Area reduction

| Revision | Size | Area |
|---|---:|---:|
| Original RevA.2 | 160 × 100 mm | 16,000 mm² |
| RevB Compact | 105 × 75 mm | 7,875 mm² |
| RevC UltraCompact | 96 × 60 mm | 5,760 mm² |

RevC is 26.9% smaller than RevB and 64.0% smaller than the original outline.

## Routing rules

- `+24V_RAW`: 1.20 mm
- `FAN_NEG`: 1.00 mm
- `BUCK_SW`: 0.80 mm
- signal routing uses horizontal, vertical or 45-degree geometry except sub-0.5-mm pad escapes
- B.Cu and F.Cu GND pours are refilled before verification
- ESP32 antenna keepout is enforced on both copper layers

The reviewed routing result is pinned in `routing/freerouting-wide.ses`. `tools/apply_reviewed_routing.py` imports that exact session and adds the reviewed finish routes; it does not invoke an unpinned autorouter run.

## Reproduction

From the project directory, using KiCad/pcbnew 9.0.8:

```bash
/usr/bin/python3 tools/build_ultracompact_revc.py
/usr/bin/python3 tools/apply_reviewed_routing.py
kicad-cli sch erc --format json -o render/final/qa/erc.json CoffeeRoast-Control-RevC-UltraCompact.kicad_sch
kicad-cli pcb drc --format json --all-track-errors --schematic-parity -o render/final/qa/drc.json CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb
/usr/bin/python3 tools/prepare_partial_pcba_package.py
```

On the committed finished board, the build and route scripts are intentional no-ops.

## Release gate

CAD and manufacturing outputs are suitable for a prototype upload only after:

1. ERC and full DRC report zero violations and zero unconnected items.
2. Top, bottom and routing renders are visually reviewed.
3. Gerber/drill archive integrity is checked.
4. BOM/CPL anchors and polarity/rotation are inspected in the assembler preview.
5. Exact supplier mappings and stock are reconfirmed.
6. USB-C enclosure access and cable clearance are checked mechanically.

No order or payment is performed by these scripts.
