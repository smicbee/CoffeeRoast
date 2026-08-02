# RevD orientation and mechanical audit

Date: 2026-08-02  
Scope: `CoffeeRoast-Control-RevD-Balanced.kicad_pcb`, placement candidate before routing

## Verdict

The USB-C orientation defect was confirmed and corrected. No second pin-number,
polarity, package-orientation or hard placement defect was found in the remaining
board inventory. The board remains a placement candidate with 159 intentionally
unrouted connections; this audit does not make it fabrication-ready.

## Corrected defects

### J5 USB-C orientation

Part: XKB `U262-161N-4BVC11`, LCSC `C319148`.

The manufacturer drawing and product photographs show that the fine SMT contact
tails are on the rear of the receptacle, opposite the mating opening and the
recommended `Product Edge`. The previous layout placed those fine tails toward
the upper board edge, so the receptacle mouth faced the board interior.

Corrected placement:

- J5 anchor: `(15.000, 3.675) mm`
- rotation: `180°`
- manufacturer Product Edge / mating face: board `y = 0.000 mm`
- fine SMT tail row after correction: board `y = 7.345 mm`

The Product Edge calculation is asserted by
`tools/audit_orientation_sensitive_parts.py`; a future generator run cannot
silently restore the old orientation.

Official source:
`https://datasheet.lcsc.com/datasheet/pdf/6ab4574fae21ebac789092d44ed82bb5.pdf?productCode=C319148`

### C4/C5 supplier mappings

A live LCSC product-detail comparison exposed two stale/wrong codes in
`docs/bom.csv`:

- C4 `EEU-FR1V221B`: changed from unrelated connector `C3697` to `C1583130`.
- C5 `CC0805JRNPO9BN102`: changed from unrelated diode `C139684` to `C62774`.

C4 is hand-soldered and its copied footprint did not carry a production
silkscreen polarity mark. A `+` mark is now placed beside the positive pad on
both board sides. C5 remains DNP pending thermocouple noise/bias testing.

## Complete inventory coverage

The PCB contains 67 footprints:

- 32 functional/orientation-sensitive references are asserted explicitly by the
  automated audit: `J1-J9`, `JGPIO1`, `U1`, `U2`, `U4-U6`, `Q1-Q2`, `D1-D5`,
  `C4`, `L1`, `SW1-SW2`, and all six test-point footprints.
- 29 non-polar R/C passives have no electrical polarity requirement; their
  package sizes and placement clearances are covered by the footprint/library
  parity and placement DRC.
- 6 fiducials are mechanically non-polar and were checked for board-edge access.

## Pin-1 and polarity findings

| Group | Result | Evidence |
|---|---|---|
| J1-J4 field pads | PASS | Pad 1 nets match the adjacent 24 V, fan, SSR and thermocouple labels. |
| J5 USB-C | PASS after correction | Exact XKB footprint, 180°, Product Edge at `y=0`; GND/VBUS/CC/D+/D- pad nets asserted. |
| J6 ESC | PASS | Left-to-right pad order is `24V, GND, GPIO10/PWM, GND`; front/back labels agree. |
| J7-J9 UI reservations | PASS | Pin nets, square pad 1, 90° per-pad text and group frames agree on both sides. |
| JGPIO1 | PASS | Pad order is GPIO `3, 46, 9, 10, 48, 45`; labels agree. |
| U1 ESP32-S3-WROOM-1-N8R8 | PASS | All module pad numbers/nets asserted; antenna front is flush with `y=0`. |
| U2 MAX6675 | PASS | Pin 1 GND; pins 2/3 thermo-/thermo+; pins 4-8 supply/SPI/GND match datasheet mapping. |
| U4 LMR16010 | PASS | Pins 1-9 BOOT/VIN/EN/RT/FB/PGOOD/GND/SW/EP-GND asserted. |
| U5 USBLC6-2SC6 | PASS | D-/GND/D+ and mirrored protected-side pads plus VBUS match the device pinout. |
| U6 UCC27511 | PASS | VDD/OUTH/OUTL/GND/IN-/IN+ mapping matches the selected device use. |
| Q1 STP55NF06L | PASS | TO-220 pins 1/2/3 are Gate/Drain/Source = gate/FAN_NEG/GND. |
| Q2 2N7002 | PASS | SOT-23 pins 1/2/3 are Gate/Source/Drain = SSR_GATE/GND/SSR_NEG. |
| D1-D5 | PASS | Pad 1 is cathode in the selected exact footprints; cathode/anode nets implement flyback, TVS, buck catch and 10 V clamp polarities correctly. |
| C4 | PASS after marking | Positive pad 1 is `+24V_RAW`, pad 2 is GND; explicit two-sided `+` added. |
| L1 | PASS | Non-polar; exact FNR6045S 5.00 mm terminal spacing retained. |
| SW1/SW2 | PASS | Opposite pad rows are EN/GND and BOOT/GND; exact TL3301 footprint retained. Assembler model rotation still requires preview confirmation. |
| Test points | PASS | +24 V, +3V3, GND, RESET, BOOT and SSR pad nets agree with both-side labels. |

## Mechanical findings

- Board outline remains exactly `96 × 60 mm` on two copper layers.
- J5's mating face is on the top Product Edge; its rear signal tails are now
  inboard and adjacent to U5/USB routing space.
- ESP32 antenna keepout is asserted as board rectangle
  `(x=48.0, y=0.0, w=48.0, h=6.2) mm`; placement DRC reports no forbidden item.
- J1-J4 and J6 mating/solder access remains unobstructed at the bottom edge.
- J7-J9 remain accessible, outside the ESP32 antenna keepout and clear of the
  USB opening.
- Courtyard, silkscreen, mask, hole and edge checks report zero placement DRC
  violations.
- C4 and Q1 are the tall hand/THT parts. Their 2D courtyards are clear, but
  final enclosure Z-height and tool access must still be checked against the
  selected enclosure.
- The local KiCad installation used for render generation does not display all
  3D bodies, so exact enclosure-volume acceptance must not be inferred from the
  PNG render alone.

## Automated verification

Run:

```bash
/usr/bin/python3 tools/audit_orientation_sensitive_parts.py
kicad-cli pcb drc --severity-all --all-track-errors --schematic-parity \
  --format json -o qa/placement-ui-parity-drc.json \
  CoffeeRoast-Control-RevD-Balanced.kicad_pcb
```

Expected audit status: `PASS`, 32 checked functional references.  
Expected placement DRC: 0 violations, 159 unrouted, 0 parity issues.

## Remaining fabrication gates

1. Route the board, add/refill final return planes, and rerun full routed DRC.
2. Generate a fresh BOM/CPL; do not reuse RevC placement files.
3. Confirm every polarized and pin-1 marker in the assembler preview, especially
   J5, U1, U2, U4-U6, Q1-Q2, D1-D5, C4 and SW1/SW2.
4. Reconfirm live supplier stock and reject substitutions with different
   package or pinout. At audit time the preferred R7/R8 code was not in stock;
   use an equivalent 27-ohm 0805 only after BOM review.
5. Check USB cable, connector opening and all tall parts against the actual
   enclosure before ordering.
