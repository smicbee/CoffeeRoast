# CoffeeRoast-Control RevA routing notes

## Status after exact USB-C routing

Routing was performed with KiCad 9 + Freerouting from a Specctra DSN export, then the dense USB-C D+/D- fanout was manually cleaned with `pcbnew` tracks/vias.

Selected J5 footprint:

```text
Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11
```

Generated artifacts:

- `render/coffeeroast_exact_usb.dsn` — DSN exported from KiCad after placing the real USB-C footprint.
- `render/coffeeroast_exact_usb.ses` — Freerouting session result.
- `render/drc_report_errors_only.txt` — KiCad DRC, errors only.
- `render/drc_report_full.txt` — full DRC including silkscreen warnings.
- `render/kicad_top.png` / `render/kicad_bottom.png` — KiCad-rendered board views.

DRC summary:

```text
Error-level DRC: 0 violations
Unconnected pads: 0
Footprint errors: 0
Full DRC still has silkscreen warnings only.
```

## Important caveats

- The USB-C placeholder has been replaced by a real KiCad library footprint for XKB U262-16XN-4BVC11. Still confirm the exact purchasable variant, connector height, mounting style, and enclosure cutout before fabrication.
- USB-C is configured as data-only/device mode: D+/D- to ESP32-S3 native USB through 27R series resistors, CC1/CC2 via 5.1k Rd pulldowns, and VBUS as sense-only. The board is still powered from the internal 24V PSU, not USB.
- Default low-voltage netclass clearance is set to 0.10 mm for the dense USB-C routing. Confirm this with the chosen PCB manufacturer. The board intentionally has no 230VAC copper.
- Freerouting is useful for a first route, but the final board should still be manually reviewed in KiCad, especially USB D+/D-, fan current path, GND return, antenna keepout, and connector placement.

## ESP32 debug/test pads

Added `TPESP1` through `TPESP40` around U1. They are copper probe/solder pads connected to the ESP32-S3-WROOM-1 side pins. Most are tiny pad extensions immediately outside the castellated module pads to avoid disturbing the existing route; `TPESP30` is intentionally tucked onto the U1 pad because the USB D+ route/via runs close to that pin.

Mapping is in `docs/esp32_debug_pads.csv`.
