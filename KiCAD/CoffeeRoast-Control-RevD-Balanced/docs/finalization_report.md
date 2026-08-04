# CoffeeRoast RevD Balanced finalization report

Date: 2026-08-04

## Result

RevD Balanced is finalized locally as a reproducible 96 × 60 mm, two-layer manufacturing candidate. This report does not replace the mandatory live PCBA placement preview, current-stock check or physical enclosure fit check before payment.

## Final design identity

- Board revision: `D-FINAL`
- Layers: `F.Cu`, `B.Cu`
- Footprints: 67
- ESP32: ESP32-S3-WROOM-1-N8R8
- Future UI connectors `J7`–`J9`: `HAND/DNP`; software remains deferred
- Controller PCB remains low-voltage only; 230 VAC stays outside the PCB
- Accepted gate-drive supply: `+24V_RAW` feeds `VDRV10` through R16 (2.7 kΩ), with D5 (BZT52C10) clamping the local U6 supply to approximately 10 V. This architecture remains intentionally unchanged.

## Corrections made during finalization

- Removed the inherited board-wide rule area that Specctra exported as a complete B.Cu routing keepout.
- Replaced it with real F.Cu/B.Cu GND planes.
- Moved USB series resistors R7/R8 beside the ESP32 USB pins.
- Added a constrained fine-pitch USB-VBUS escape before general routing.
- Routed `+24V_RAW` and `FAN_NEG` at 1.0 mm from the start rather than widening a dense 0.2 mm autoroute afterward.
- Kept copper, tracks and vias out of all optical fiducials and removed their inherited electrical GND assignment.
- Added exact-duplicate removal for pre-seeded SES routes.
- Added fail-closed final geometry and angle audit.
- Created a RevD-specific partial-PCBA exporter with corrected C4/C5 supplier mappings and explicit J7–J9 HAND/DNP handling.

## Verification evidence

- KiCad schematic ERC: `0 violations`
- KiCad routed PCB DRC: `0 violations`
- Unconnected PCB items: `0`
- Schematic/PCB parity: `0 issues`
- Orientation/mechanical audit: `PASS`, 32 functional references asserted; all 67 footprints classified
- Routing angle audit: `0` segments outside 0°/45°/90°/135°
- Final routing: 678 tracks/vias, 31 vias
- `+24V_RAW`: 35 segments, all 1.0 mm, no vias
- `FAN_NEG`: 12 segments, all 1.0 mm, no vias
- USB D− total length: 56.095 mm
- USB D+ total length: 61.790 mm
- USB absolute length skew: 5.694 mm; negligible timing skew for this short USB Full-Speed path
- Repeated normal `finalize_routing.py` execution: hash-identical no-op once `D-FINAL` exists
- RevD BOM/CPL generation: PASS
- `J7`, `J8`, `J9`: absent from assembly BOM/CPL and present in DNP/HAND list
- Gerber/drill ZIP contains fabrication files only and no unsafe archive paths

## Final artifacts and SHA-256

```text
36a915c7685176810cd3c1c5419741995e61dbf59157b9d63e821bb6ad18f0c1  CoffeeRoast-Control-RevD-Balanced.kicad_pcb
8849b886c2a915ef51b01b9c861c40271aab4d201a60a00611c3d72c58d94d5a  production/partial-smd-pcba/CoffeeRoast-Control-RevD-Balanced_JLC_Gerber_Drill.zip
de8106418032c81a647e4574ac79c87545ec95a0f40152b1c77c2af68c4d3d03  production/partial-smd-pcba/CoffeeRoast-Control-RevD-Balanced_partial_smd_pcba_package.zip
```

## Remaining external release gates

1. Upload only the generated RevD Gerber/drill ZIP in a fresh manufacturer workspace.
2. Upload the generated RevD BOM and CPL; do not reuse RevC or RevA placement state.
3. Confirm the live Gerber and component-placement previews are aligned without Auto-Align.
4. Confirm Pin 1/polarity and exact package for J5, U1, U2, U4–U6, Q1–Q2, D1–D5, C4, L1 and SW1/SW2.
5. Reconfirm supplier availability and reject substitutions with different pinout or land pattern.
6. Check USB cable access, C4/Q1 height and the selected enclosure physically.
7. Payment/order remains a separate explicit approval step.
