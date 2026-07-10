# JLC current no-J1-J4 upload set

Use this set for the current CoffeeRoast RevA.1 quote.

## Upload to PCB quote

- `CoffeeRoast-Control-RevA1_JLC_GERBER_ONLY_no_assembly_csv.zip`

This ZIP intentionally contains only Gerber/drill files, no BOM/CPL/DNP CSVs.

## Upload in SMT/PCBA step

Use ONLY these two files:

- `assembly/bom_jlc_pcba_19_no_j1_j4.csv`
- `assembly/cpl_jlc_pcba_19_no_j1_j4.csv`

Expected assembled designators: 19 (`U1`, `U2`, `J5`, `Q2`, `R1-R8`, `R10`, `R11`, `C1-C3`, `C6`, `C7`).

Do NOT upload any DNP/hand-solder/reference CSV. `J1-J4` are hand-solder pads only and must not appear in JLC selected parts or part placement.

## Placement check

If JLC still shows `J1-J4` / `C3697`, clear the old BOM/CPL state or start a fresh quote using the gerber-only ZIP above, then upload only the two no-J1-J4 assembly CSVs.
