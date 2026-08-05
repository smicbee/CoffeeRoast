# OpenSCAD snap-fit enclosure

Canonical rounded, tool-free enclosure variant for the CoffeeRoast RevD PCB.

## Design

- Source: `CoffeeRoast_RevD_enclosure.scad`
- Functional PCB: 96 × 60 × 1.6 mm
- Final JLCPCB Y15 production file: 96 × 70 × 1.6 mm as delivered, consisting
  of the same 96 × 60 mm PCB plus one 5 mm V-scored process rail on each of
  the two connector edges
- Rounded rectangular tray: 100.4 × 64.4 × 30 mm, 3 mm corner radius
- No PCB mounting holes, separate guide rails, lid screws or cylindrical corner towers
- PCB drops into a 0.60 mm-per-side pocket
- Four floor contacts support the PCB; four lid pads retain it vertically
- Snap cap wraps around the tray with 0.30 mm nominal clearance
- Two opposed 10 mm side cantilevers engage shallow tray recesses
- 8 mm skirt and 0.55 mm snap depth keep estimated PETG bending strain conservative
- Bottom-edge pry notch allows removal without tools
- USB, five field-wire exits, RESET/BOOT holes and RF-safe lid vents remain included

## Final ordered JLCPCB geometry

The downloaded production file for `CoffeeRoast-Control-RevD-Balanced_JLC_Gerber_Drill_Y15`
was checked rather than relying on the local KiCad outline. JLC CAM reports an
outer size of 96 × 70 mm. Its processed outline and V-cut layer place score
lines at 5 mm and 65 mm, leaving the original 96 × 60 mm functional PCB between
two removable 5 mm assembly rails.

The returned archive is preserved under
`production/partial-smd-pcba/jlcpcb-returned/`; the extracted dimensions and
archive checksum are recorded in `jlcpcb_y15_geometry.json` and checked by the
automated verifier.

**Recommended operating build:** snap off both process rails and print the
normal `tray`/`lid_print` pair. The rails sit directly in front of the USB-C and
field-wire connector edges, so keeping them attached in the working enclosure
would obstruct the intended cable paths.

For an as-delivered fit check or transport holder, set:

```bash
openscad -D 'board_variant="production_rails_attached"' \
  -D 'part="tray"' CoffeeRoast_RevD_enclosure.scad
```

`build.sh` exports both variants. The rail-attached variant shifts every
functional KiCad coordinate by exactly 5 mm inside the longer pocket; USB,
button, support, hold-down and vent locations therefore remain registered to
the 96 × 60 mm circuit core rather than drifting with the enlarged outline.

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
openscad/generated/tray_rails_attached.stl
openscad/generated/tray_rails_attached.3mf
openscad/generated/lid_rails_attached_print.stl
openscad/generated/lid_rails_attached_print.3mf
openscad/generated/board_proxy_rails_attached.stl
openscad/generated/preview_closed.png
openscad/generated/preview_exploded.png
openscad/generated/preview_closed_rails_attached.png
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
