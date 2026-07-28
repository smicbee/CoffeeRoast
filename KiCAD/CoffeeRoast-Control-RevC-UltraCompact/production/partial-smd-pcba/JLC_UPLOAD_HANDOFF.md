# JLCPCB upload handoff — CoffeeRoast-Control RevC UltraCompact

This package is a **new compact PCB revision** derived from the ordered and proven
RevA.2 circuit. Do not reuse Gerber, CPL or placement state from any RevA order.

## Upload files

- PCB Gerber/Drill: `CoffeeRoast-Control-RevC-UltraCompact_JLC_Gerber_Drill.zip`
- Assembly BOM: `assembly/bom_smd_partial_jlc.csv`
- Placement CPL: `assembly/cpl_smd_partial.csv`

## Mechanical identity

- Finished outline: nominal 96.0 x 60.0 mm.
- Primary field wiring is on the bottom edge: thermocouple, SSR, ESC, fan and 24V input.
- USB-C is on the opposite/top edge; verify enclosure access to the slightly inset receptacle mouth.
- The ESP32 antenna region touches the top edge and must remain free of copper, parts and enclosure metal.
- Gerber, drill and CPL use the same bottom-left origin; do not use Auto-Align to hide a source mismatch.

## Required verification gates

- U2: `MAX6675ISA+T / C16030`, SOIC-8, CPL `10.0000 / 17.0000 / Top / 180.00`.
- U2 physical Pin 1 is the rectangular pad at board coordinate `12.475 / 44.905 mm`, net `GND`; confirm the assembler marker on this pad.
- U2 pin mapping: 1 GND, 2 THERMO_MINUS, 3 THERMO_PLUS, 4 +3V3, 5 MAX_SCK, 6 MAX_CS, 7 MAX_DO, 8 GND.
- J5: `C319148`, CPL `15.0000 / 54.0000 / 0.00`; confirm shell tabs and product edge.
- Q1: `STP55NF06L / C77582`, TO-220 THT assembly, CPL centre `56.5400 / 12.0000` on the middle lead.
- SW1/SW2: `TL3301AF160QG / C273519`, CPL rotations `90.00` and `90.00`.
- L1: `FNR6045S220MT / C168080`; exact land pattern is 2.20 x 5.72 mm pads on 5.00 mm centers.
- J1-J4 and J6 remain DNP/hand-solder and must not appear in automated placement.

## Local QA

- KiCad DRC: 0 violations.
- Unconnected items: 0.
- Schematic parity: 0 findings.
- KiCad ERC: 0 violations.

Uploading or saving a cart revision is not production approval. Verify live stock,
BOM mapping, Gerber identity and every critical component placement before payment.
