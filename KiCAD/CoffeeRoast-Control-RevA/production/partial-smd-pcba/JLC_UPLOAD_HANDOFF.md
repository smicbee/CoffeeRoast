# JLCPCB replacement handoff — CoffeeRoast-Control RevA2

This package is the corrected replacement for current order `SMT026071960340_Y12`
(PCB `13013207A`) after JLC identified insufficient L1 solder overlap. It also supersedes
the stopped order/project `SMT026071660949_Y11` and replacement workspace
`relevanceFileAccessId=752fd014ee974e0cb8aea562422c8f6a`.
Do **not** resume Quote & Order from any previous Gerber or placement state.

## Upload files

- PCB Gerber/Drill: `CoffeeRoast-Control-RevA2_JLC_Gerber_Drill.zip`
- Assembly BOM: `assembly/bom_smd_partial_jlc.csv`
- Placement CPL: `assembly/cpl_smd_partial.csv`

## Required verification gates

- Quantity: 5 PCB / 5 PCBA, top-side standard PCBA.
- U2: `MAX6675ISA+T / C16030`, SOIC-8, CPL `128.0000 / -40.0000 / Top / 180.00`.
- U2 physical Pin 1 is the rectangular pad at board coordinate `130.475 / 61.905 mm`, net `GND`; confirm the assembler marker on this pad.
- U2 pin mapping: 1 GND, 2 THERMO_MINUS, 3 THERMO_PLUS, 4 +3V3, 5 MAX_SCK, 6 MAX_CS, 7 MAX_DO, 8 GND.
- J5: `C319148`, Product Edge remains at board edge X=160 mm.
- Q1: `STP55NF06L / C77582`, TO-220 THT assembly.
- L1: `FNR6045S220MT / C168080`; exact land pattern is 2.20 × 5.72 mm pads on 5.00 mm centers. Confirm full terminal/pad overlap in JLC's review image.
- Gerber, drill and CPL use the same bottom-left origin; a fresh placement import must not require JLC Auto-Align.
- C6 and C7: `90.00°`.
- J1-J4 remain DNP/hand-solder and must not appear in JLC placement.

## Local QA

- KiCad DRC: 0 violations.
- Unconnected items: 0.
- Schematic parity: 0 findings.
- KiCad ERC: 0 violations.
- Dedicated U2 topology/numeric sanity: PASS (`sim/results/u2_max6675_verification.json`).

Uploading or saving a replacement cart revision is not production approval. Verify JLC BOM
selection, the fresh Gerber identity, and component placement before payment.
