# CoffeeRoast-Control RevA routing notes

## Status after automated routing

Routing was performed with KiCad 9 + Freerouting from a Specctra DSN export.

Generated artifacts:

- `render/coffeeroast_reva2.dsn` — DSN exported from KiCad.
- `render/coffeeroast_reva2.ses` — Freerouting session result.
- `render/drc_report_errors_only.txt` — KiCad DRC, errors only.
- `render/drc_report_autorouted4.txt` — full DRC including warnings.
- `render/kicad_top.png` / `render/kicad_bottom.png` — KiCad-rendered board views.

DRC summary:

```text
Error-level DRC: 0 violations
Unconnected pads: 0
Footprint errors: 0
Full DRC still has silkscreen warnings only.
```

## Important caveats

- The current USB-C footprint on the routed board is a **routable draft 6-pin USB-C placeholder** representing GND, VBUS, D-, D+, CC1, and CC2. Before ordering PCBs, replace it with the exact USB-C connector footprint you will buy and rerun routing/DRC.
- Default low-voltage netclass clearance is set to 0.10 mm for this autorouted draft. This is acceptable for many PCB fabs but must be confirmed with the chosen manufacturer. The board intentionally has no 230VAC copper.
- Freerouting is useful for a first route, but the final board should still be manually reviewed in KiCad, especially USB D+/D-, fan current path, GND return, antenna keepout, and connector placement.
