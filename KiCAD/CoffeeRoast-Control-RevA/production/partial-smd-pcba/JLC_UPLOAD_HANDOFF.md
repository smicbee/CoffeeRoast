# JLCPCB replacement handoff — CoffeeRoast-Control RevA2

This package replaces the stopped order/project `SMT026071660949_Y11`.
Do not reuse the previous Gerber, BOM or CPL files.

## Upload files

- PCB Gerber/Drill: `CoffeeRoast-Control-RevA2_JLC_Gerber_Drill.zip`
- Assembly BOM: `assembly/bom_smd_partial_jlc.csv`
- Placement CPL: `assembly/cpl_smd_partial.csv`

## Required verification gates

- Quantity: 5 PCB / 5 PCBA, top-side standard PCBA.
- U2: `MAX6675ISA+T / C16030`, SOIC-8, CPL `125.0000 / 40.0000 / Top / 180.00`.
- U2 physical Pin 1 is the rectangular pad at board coordinate `127.475 / 61.905 mm`, net `GND`; the silkscreen dot is at the same package corner.
- U2 pin mapping: 1 GND, 2 THERMO_MINUS, 3 THERMO_PLUS, 4 +3V3, 5 MAX_SCK, 6 MAX_CS, 7 MAX_DO, 8 GND.
- J5: `C319148`, KiCad origin `156.325 / 31.000 mm`; JLC CPL `156.3250 / 69.0000 / Top / 90.00`; Product Edge remains at board edge X=160 mm.
- Q1: `STP55NF06L / C77582`, TO-220 THT assembly.
- C6 and C7: `90.00°`.
- J1–J4 remain DNP/hand-solder and must not appear in JLC placement.

## Local QA

- KiCad DRC: 0 violations.
- Unconnected items: 0.
- Schematic parity: 0 findings.
- KiCad ERC: 0 violations.
- Grouped JLC BOM: 30 rows / 43 unique designators.

Uploading or saving a replacement cart revision is not production approval. Verify JLC BOM selection and component placement first.
