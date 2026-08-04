# RevD final routing

This branch contains the completed, reproducible two-layer routing for the accepted RevD placement.

## Generated state

- Router: pinned Freerouting 2.2.4
- Maximum passes: 100; Freerouting stops early on convergence
- Final tracks/vias: 700 total, including 38 vias
- PCB layers: F.Cu and B.Cu
- Combined render: `render/final-routing/routing_combined.png`
- Top/bottom renders are in the same directory.

## Verification result

- Schematic ERC violations: 0
- PCB DRC violations: 0
- Schematic/PCB parity issues: 0
- Unconnected items: 0
- Non-45°/90° segments: 0
- `+24V_RAW`: 34 segments, all 1.0 mm, no vias
- `FAN_NEG`: 12 segments, all 1.0 mm, no vias
- USB D+/D- total-length skew: 1.745 mm
- Orientation audit: PASS, all 67 footprints classified and 32 functional references asserted

## Use

The route is a local manufacturing candidate. Gerber, drill, BOM, CPL and DNP/HAND
outputs are generated under `production/partial-smd-pcba/`. A live manufacturer
placement preview, current-stock check and physical enclosure/USB/tall-part review
remain mandatory before payment; local zero-DRC is not permission to skip those gates.
