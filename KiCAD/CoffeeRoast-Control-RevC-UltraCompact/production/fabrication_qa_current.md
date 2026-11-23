# CoffeeRoast RevC UltraCompact fabrication QA

Run date: 2026-07-29  
Toolchain: KiCad CLI / pcbnew 9.0.8, reviewed Freerouting session 2.2.4  
Board: `CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb`

## Verdict

**CAD and manufacturing outputs are ready for a prototype upload and assembler preview.** No order or payment has been made. Supplier mapping, polarity/rotation, enclosure mechanics and USB-C access still require human preview approval before payment.

## Mechanical identity

- Outline: 96 × 60 mm (5,760 mm²)
- 26.9% less area than RevB 105 × 75 mm
- 64.0% less area than original 160 × 100 mm
- Primary field connectors: bottom edge
- USB-C: opposite/top edge, slightly inset
- ESP32 antenna keepout: top-right region, copper/component free
- Front and back functional labeling present

## Electrical and CAD checks

- schematic ERC: 0 violations
- full PCB DRC: 0 violations
- unconnected items: 0
- schematic parity: 0 problems
- U2/MAX6675 topology and position verification: PASS
- zones refilled on F.Cu and B.Cu
- 24 V path: 1.20 mm
- FAN_NEG path: 1.00 mm
- BUCK_SW path: 0.80 mm
- routing angle audit: 466 segments ≥0.5 mm checked, 0 non-45/90-degree segments
- placement and routing visual QA completed on top, bottom and combined copper renders

## Assembly export

- PCBA designators: 43
- grouped JLC BOM rows: 30
- CPL designators: 43
- DNP/hand-solder rows: 21
- mapping-review rows: 43
- Gerber/drill origin and CPL frame: bottom-left, 0 × 60 mm auxiliary origin
- ZIP integrity: PASS

## SHA-256

```text
c8881e4da830908de482804b0cc6a0cf660f0117a01e4e9f0a1b4027b998f2a7  CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb
00544203c23db5c745e398db3b75c7d9599aa1a369559ba6cb0b5ae3f229b25b  CoffeeRoast-Control-RevC-UltraCompact_partial_smd_pcba_package.zip
ce661c9f6d8ae13d8baf975852ac686fe2e33be35b5794fd8b21eb4da06a7196  CoffeeRoast-Control-RevC-UltraCompact_JLC_Gerber_Drill.zip
a1631c8342d2f7ba24f94addacc6787d0b86ffb8a6571e19b39cbfd43866734d  routing/freerouting-wide.ses
```

## Mandatory pre-payment preview

1. Confirm finished size 96 × 60 mm.
2. Confirm USB-C mouth and enclosure/cable access.
3. Confirm ESP32 antenna area remains free in the manufacturer preview and enclosure.
4. Confirm U2, U4, U5, U6, J5, D2–D5, Q1, Q2 and SW1/SW2 orientation.
5. Confirm Q1 center/rotation and all three TO-220 leads.
6. Confirm L1 pad overlap and selected supplier model.
7. Reconfirm exact supplier codes, stock and substitutions.
8. Do not place or route any 230 V wiring on this controller PCB.
