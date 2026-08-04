# OpenSCAD snap-fit enclosure

Canonical rounded, tool-free enclosure variant for the CoffeeRoast RevD PCB.

## Design

- Source: `CoffeeRoast_RevD_enclosure.scad`
- PCB: 96 × 60 × 1.6 mm
- Rounded rectangular tray: 100.4 × 64.4 × 30 mm, 3 mm corner radius
- No PCB mounting holes, separate guide rails, lid screws or cylindrical corner towers
- PCB drops into a 0.60 mm-per-side pocket
- Four floor contacts support the PCB; four lid pads retain it vertically
- Snap cap wraps around the tray with 0.30 mm nominal clearance
- Two opposed 10 mm side cantilevers engage shallow tray recesses
- 8 mm skirt and 0.55 mm snap depth keep estimated PETG bending strain conservative
- Bottom-edge pry notch allows removal without tools
- USB, five field-wire exits, RESET/BOOT holes and RF-safe lid vents remain included

The snap fit is still material/printer dependent. Print in PETG or the intended final
material and tune `snap_clearance`, `snap_tab_depth`, `skirt_t` and `skirt_h` after a
fit test. PLA is acceptable only as a cold dimensional prototype.

## Build

OpenSCAD 2021.01 was used for the verified export.

```bash
cd KiCAD/CoffeeRoast-Control-RevD-Balanced/mechanical/enclosure
openscad/build.sh
```

`build.sh` exports and verifies:

```text
openscad/generated/tray.stl
openscad/generated/tray.3mf
openscad/generated/lid_print.stl
openscad/generated/lid_print.3mf
openscad/generated/lid_design.stl
openscad/generated/board_proxy.stl
openscad/generated/preview_closed.png
openscad/generated/preview_exploded.png
openscad/generated/verification.json
openscad/generated/manifest.json
```

Use `tray.stl`/`tray.3mf` and `lid_print.stl`/`lid_print.3mf` for slicing. Both are
already oriented with their broad exterior face on the print bed and require no
intentional support in the encoded geometry. Always inspect the slicer preview.

## Open interactively

```bash
openscad openscad/CoffeeRoast_RevD_enclosure.scad
```

The top-level `part` selector accepts:

- `"closed"` — closed assembly preview
- `"exploded"` — exploded assembly preview
- `"tray"`
- `"lid"` — design/assembly orientation
- `"lid_print"` — FDM orientation
- `"board_proxy"`

## Verification result

The automated verifier currently reports `PASS`:

- tray and lid are single connected components;
- zero open or non-manifold STL edges;
- expected external envelopes match;
- 3MF archives are structurally valid;
- closed and exploded preview renders were generated.

This is still a prototype rather than a final mechanical release. Remaining gates are
physical snap cycling, exact Q1/C4 installed height, real USB plug fit, wire bend and
strain relief, and worst-case enclosure temperature.
