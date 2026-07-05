# CoffeeRoast RevA.1 JLCPCB order handoff

Status: upload/preflight prepared on 2026-07-05. No payment/order was placed.

## What was completed

- Local ZIP integrity verified with `unzip -t`.
- KiCad error-level DRC re-run: 0 DRC violations, 0 unconnected pads, 0 footprint errors.
- Gerber/Drill/Assembly package uploaded to JLCPCB's upload API.
- JLC gerber analysis returned `head=ok`.
- JLC detected:
  - Layers: 2
  - Board size: 160.0 mm x 100.0 mm
  - Gerber result: 0

## Files

Main upload package:

`production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip`

Assembly files inside the package:

- `assembly/bom_smd_partial.csv`
- `assembly/cpl_smd_partial.csv`
- `assembly/dnp_hand_solder.csv`
- `assembly/part_mapping_review.csv`

Local selected-parts references:

- `production/selected_parts.md`
- `production/selected_parts.csv`

## JLC upload identifiers

These are not passwords, but treat them as project/order identifiers.

- Upload file ID: `f0faa4c0862947d1b4b273692f1dd94c`
- JLC fileSystemAccessId from upload API: `8761998275287769088`
- JLC technologyDiscernRecordNum from analysis: `a07f8e0658854f43a7e7254a902bf6c3`

Resume URL after login:

`https://cart.jlcpcb.com/quote?uploadNum=f0faa4c0862947d1b4b273692f1dd94c`

If that URL does not restore the upload after login, manually upload the ZIP above.

## Recommended JLC settings

PCB:

- Product: Standard PCB/PCBA
- Base material: FR-4
- Layers: 2
- Dimensions: should auto-detect 160 x 100 mm
- Quantity: 5 boards
- Thickness: 1.6 mm
- Color: Green or default
- Surface finish: LeadFree HASL or ENIG if price is acceptable
- Outer copper: 1 oz
- Electrical test: Flying Probe Fully Test
- Mark on PCB: Remove Mark if possible

PCBA:

- Enable SMT Assembly
- Side: Top side only
- Use `assembly/bom_smd_partial.csv`
- Use `assembly/cpl_smd_partial.csv`
- Assemble only the 17 BOM positions in `bom_smd_partial.csv`
- If possible, order 5 PCBs but only 2 assembled

Do not assemble / leave DNP:

- U5 USB ESD
- D2/D3 TVS
- C5 thermocouple filter
- J1-J4 terminals
- F1 fuse holder
- D1 fan diode
- Q1 fan MOSFET
- U3/U4 regulators/modules
- C4 input electrolytic
- SW1/SW2 buttons
- all TP/PAD debug pads

## Manual UI checks before paying

- Confirm U1 ESP32-S3 orientation and antenna keepout preview.
- Confirm U2 MAX6675 pin-1 orientation.
- Confirm J5 USB-C orientation.
- Confirm Q2 SOT-23 orientation.
- Confirm all JLC supplier/C-codes still resolve:
  - C2913201, C16030, C319148, C8545, C17408, C149504, C17414, C17594, C27834, C15850, C49678.
- If any part is unavailable or preview looks wrong, mark that part DNP and hand-solder later.

## Current blocker

The site redirected to JLCPCB login before I could continue into cart/checkout. The assistant stopped before credentials/payment.
