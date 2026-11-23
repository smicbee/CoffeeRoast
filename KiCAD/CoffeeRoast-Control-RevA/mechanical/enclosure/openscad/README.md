# OpenSCAD snap-fit enclosure — ordered CoffeeRoast RevA.2

Canonical rounded, tool-free enclosure for the larger RevA.2 board that was
ordered and delivered under JLCPCB production item Y13.

## Board contract

- JLCPCB as-delivered piece: **160 × 110 × 1.6 mm**
- Functional PCB after depaneling: **160 × 100 × 1.6 mm**
- Two removable 5 mm process rails, V-scored at y=5 mm and y=105 mm
- Returned production archive and SHA-256 are recorded in
  `jlcpcb_y13_geometry.json`

The enclosure is intentionally designed for the 160 × 100 mm board **after both
process rails are removed**. The returned production archive is preserved under
`production/partial-smd-pcba/jlcpcb-returned/` and checked by the verifier.

## Mechanical design

- Source: `CoffeeRoast_RevA2_enclosure.scad`
- Tray body: 164.4 × 104.4 × 33.0 mm
- PCB pocket clearance: 0.60 mm per side
- Four isolated floor supports; no added PCB holes or continuous guide rails
- Six lid hold-down pads retain the PCB vertically
- Rounded snap cap with two opposed snap pairs and a pry notch
- Left-wall exits: J1 24V input and J2 fan
- Right-wall exits: J3 SSR, J4 thermocouple and J5 USB-C
- Front-wall exit: J6 ESC harness
- Lid access holes: RESET and BOOT
- Power-stage ventilation above Q1/U4/L1 and away from the ESP32 antenna region

`clear_above_pcb=27 mm` is deliberately conservative but provisional. The real
installed Q1 and C4 heights must be measured before mechanical release.

## Build

```bash
cd KiCAD/CoffeeRoast-Control-RevA/mechanical/enclosure/openscad
./build.sh
```

Generated artifacts:

```text
generated/tray.stl
generated/tray.3mf
generated/lid_print.stl
generated/lid_print.3mf
generated/lid_design.stl
generated/board_proxy.stl
generated/preview_closed.png
generated/preview_exploded.png
generated/preview_front.png
generated/preview_right.png
generated/verification.json
generated/manifest.json
```

Use `tray.stl`/`tray.3mf` and `lid_print.stl`/`lid_print.3mf` for slicing. The
parts are already oriented with a broad exterior face on the print bed. Inspect
the slicer preview before printing.

## Verification and remaining physical gates

The automated build requires:

- closed manifold STL meshes;
- one connected component for each print part;
- expected 160 × 100 mm board-derived envelopes;
- valid 3MF archives;
- rendered closed and exploded previews;
- exact checksum and dimensions of the returned JLCPCB Y13 production archive.

This remains a prototype until the manufactured assembly has passed Q1/C4
height measurement, exact USB and cable fit, snap cycling in the final material,
strain-relief review and worst-case enclosure-temperature testing.
