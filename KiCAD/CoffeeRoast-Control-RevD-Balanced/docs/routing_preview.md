# RevD routing preview

This branch contains an intentionally non-production routing visualization for the
accepted RevD placement.

## Generated state

- Router: pinned Freerouting 2.2.4
- Passes: 20
- Imported tracks/vias: 426
- PCB layers: F.Cu and B.Cu
- Combined render: `render/routing-preview/routing_combined.png`
- Top/bottom renders are in the same directory.

## Verification result

- Schematic/PCB parity issues: 0
- Remaining unconnected items reported by KiCad: 43
- DRC violations: 50, all `track_width`
- The width findings are on the critical `+24V_RAW` and `FAN_NEG` routes because
  the general-purpose router emitted them below the project's required 1.0 mm.

A trial blanket widening to 1.0 mm caused clearance/shorting errors and was
reverted. These critical nets therefore require deliberate manual routing rather
than post-hoc widening of the autorouter geometry.

## Use

This artifact exists to let the user judge the visual consequence of the current
placement. It is not fabrication-ready and must not be used for Gerber/BOM/CPL
release. Before routing acceptance: manually rebuild the power/fan paths, finish
all remaining connections, review USB and thermocouple paths, restore continuous
return planes, then require zero DRC violations and zero unintended unconnected
items.
