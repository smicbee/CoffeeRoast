# CoffeeRoast RevD enclosure prototypes

## Current preferred implementation: OpenSCAD snap lid

The current design is `openscad/CoffeeRoast_RevD_enclosure.scad`: a rounded,
tool-free enclosure with two side snap tabs, no lid screws and no cylindrical corner
towers. Build it with `openscad/build.sh`; printable STL/3MF files and verification
artifacts are under `openscad/generated/`. See `openscad/README.md`.

## Previous CadQuery screw-lid prototype

The earlier CadQuery implementation below is retained for traceability, but its
screw-tower geometry is superseded by the OpenSCAD snap-fit variant.

Parametric CadQuery enclosure for `CoffeeRoast-Control-RevD-Balanced`.

**Status: prototype, not mechanically released.** The exact PCB outline and footprint
anchors come from the RevD KiCad board. Connector envelopes, cable exits and tall-part
heights still require coupons and the manufactured PCBA.

## Mechanical concept

- 96 × 60 × 1.6 mm PCB drops vertically into a fitted tray pocket.
- No PCB mounting holes, PCB changes or separate guide rails are used.
- Four isolated underside pads support the PCB while avoiding known THT solder joints.
- Four broad pads descending from the lid retain the PCB vertically. A 0.20 mm nominal
  gap is reserved for fit tolerance or thin TPU/foam pads after measurement.
- Four M3 enclosure screw towers sit outside the PCB envelope. Their holes belong to
  the enclosure, not the PCB.
- J5 USB-C exits through the KiCad `y=0` wall.
- Separate opposite-wall openings are provided for THERMO, SSR, ESC/AUX, FAN and 24 V.
- RESET and BOOT have 4 mm lid access holes.
- Lid vents are over the Q1/buck/L1 region and outside the ESP32 antenna keepout.
- The enclosure is SELV-only. Mains, PSU mains side and SSR load side stay outside or
  behind a separately engineered safety barrier.

## Key prototype dimensions

| Parameter | Value |
|---|---:|
| PCB | 96 × 60 × 1.6 mm |
| Lateral PCB clearance | 0.60 mm per side |
| Wall / floor / lid | 1.60 mm |
| PCB underside support | 2.80 mm above floor |
| Clear height above PCB | 24.0 mm, provisional |
| Tray height | 30.0 mm |
| Body without external screw towers | 100.4 × 64.4 mm |
| Overall tower envelope | about 112.4 × 76.4 mm |
| M3 insert bore | 4.20 mm, coupon required |

The USB opening, wire openings, Q1/C4 proxies, button actuation and insert bore are
explicitly provisional. Edit the `Parameters` dataclass in `enclosure.py`; do not
manually edit generated STEP/STL files.

## Reproduce

Python 3.11 and CadQuery 2.8.0 are the verified environment.

```bash
cd KiCAD/CoffeeRoast-Control-RevD-Balanced/mechanical/enclosure
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python enclosure.py
.venv/bin/python verify_enclosure.py
/usr/bin/python3 verify_kicad_clearances.py
unset DISPLAY
xvfb-run -a -s '-screen 0 1800x1200x24' .venv/bin/python render_previews.py
```

Generated artifacts:

- `generated/tray.step`, `generated/tray.stl`, `generated/tray.3mf`
- `generated/lid.step`, `generated/lid.stl` — design/assembly orientation
- `generated/lid_print.step`, `generated/lid_print.stl`, `generated/lid_print.3mf` — recommended FDM orientation,
  outer face on the bed and hold-down pads upward
- `generated/assembly_closed.step`
- `generated/board_proxy.step`, `generated/board_proxy.stl`
- `generated/manifest.json`, including parameters, dimensions and SHA-256 hashes
- `generated/verification.json`
- `generated/kicad_clearance_verification.json`
- `generated/preview_exploded.png`, `generated/preview_closed.png`,
  `generated/preview_usb_side.png`

## Printing baseline

For a calibrated 0.4 mm nozzle:

- Start with PETG while actual enclosure temperature is unknown; do not release PLA
  merely because a room-temperature prototype fits.
- Use 0.20 mm layers and at least 3–4 perimeters.
- Print the tray with its floor on the bed and opening upward.
- Print `lid_print.stl` with the outer face on the bed; the hold-down pads grow upward.
- No support should be needed for the current parts, but inspect the slicer preview.
- First print connector/insert coupons or a low-height tray before committing to the
  full-height enclosure.

Material gate based on measured worst-case enclosure temperature plus a 15 °C margin:

- up to 45 °C: PLA only for lightly loaded prototypes;
- 46–60 °C: PETG;
- 61–75 °C: ASA or ABS;
- 76–95 °C: PC after material-specific coupons and heat testing;
- above 95 °C: relocate/shield the electronics or qualify another enclosure concept.

## Physical release gates

1. Measure the produced PCBA, especially Q1 and C4 installed height and Q1 standoff.
2. Fit-test the exact J5 receptacle with the intended USB-C plug and cable bend.
3. Measure J1–J4/J6 wire diameters and bend radii; choose actual strain-relief hardware.
4. Verify the four underside support locations against solder protrusions on the PCBA.
5. Print M3 insert and lid-fit coupons in the final material.
6. Perform three assembly cycles, ten connector insertion cycles and cable strain tests.
7. Measure ambient, enclosure air, PCB, Q1/buck zone and boss temperatures under the
   real worst-case roast cycle before selecting the final material.
8. Re-run `verify_enclosure.py`; then record the measured parameters before release.

Digital verification passing means only that the generated solids are valid/manifold,
have no modeled collisions and respect the encoded antenna/clearance rules. It is not
a substitute for the physical gates above.
