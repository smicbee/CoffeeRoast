# CoffeeRoast expanded JLC PCBA candidates (no J1-J4)

This folder is for testing whether JLC can assemble more than the conservative 19-part set.

Hard rule preserved: `J1`, `J2`, `J3`, `J4` / `C3697` are NOT included. They are hand-solder pads only.

## BOM options

1. `assembly/bom_jlc_pcba_28_mappable_no_j1_j4.csv`
   - 19 proven parts + 9 extra parts with known candidate JLC/LCSC codes.
   - Extra parts: C5, D1, D2, D3, Q1, SW1, SW2, U4, U5.

2. `assembly/bom_jlc_pcba_31_all_real_no_j1_j4_manual_select.csv`
   - The 28 above + C4, F1, U3 with blank supplier code for manual JLC selection.

## CPL / placement variants

Because the current JLC placement preview was reported off-board, I generated three coordinate conventions for each BOM size:

- `*_jlc_bottom_origin_y_flipped_no_j1_j4.csv` — previous Y=100-KiCadY convention.
- `*_raw_top_left_positive_y_no_j1_j4.csv` — raw KiCad board coordinates, positive Y downward.
- `*_kicad_official_negative_y_no_j1_j4.csv` — KiCad position export convention, negative Y for top side.

Try only one CPL at a time in JLC. If placement is off-board, delete/replace the CPL in JLC and try the next variant.

## Must-check before payment

- No J1/J2/J3/J4/C3697 in selected parts or placement.
- U1, U2, J5, Q2 match the Gerber landmarks.
- For added THT/mechanical/draft-footprint candidates, verify footprint/orientation visually; manual placement cannot fix a wrong land pattern.
