# CoffeeRoast-Control RevA.2 routing notes

## Status after the RevA.2 layout-quality pass

Routing was originally performed with KiCad 9 + Freerouting from a Specctra DSN export, then manually cleaned. The current pass keeps direct routes that are electrically justified, but replaces arbitrary-angle ECO branches with 45° geometry, widens the 24V/fan current path, enlarges the FAN_NEG transition via, and tightens the B.Cu GND-zone fill against copper slivers.

Selected J5 footprint:

```text
Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11
```

Generated artifacts:

- `render/coffeeroast_debug_breakout.dsn` — DSN exported from KiCad after adding the routed ESP32 solder-pad breakout.
- `render/coffeeroast_debug_breakout.ses` — Freerouting session result for the pre-RevA.1 routed board; keep as route history, not current source of truth.
- `render/layout-quality-post/drc_errors.json` — current error-only KiCad DRC.
- `render/layout-quality-post/drc_full.json` — current full DRC including warnings and exclusions.
- `render/layout-quality-post/top.png` / `bottom.png` — current KiCad copper/mask/silkscreen review views.

DRC summary:

```text
Full DRC (error + warning + exclusion): 0 violations
Error-level DRC: 0 violations
Unconnected pads: 0
Footprint errors: 0
```

The project rule file enforces a 1.0 mm minimum track width on `+24V_RAW`, `+24V_FUSED`, and `FAN_NEG`. The current board uses 1.2 mm on both 24V rails, 1.0 mm on `FAN_NEG`, and a 1.2/0.6 mm FAN_NEG via. The explicit Q1 source-return stub is 1.0 mm with a 1.2/0.6 mm via into the GND structure.

## RevA.1 added robustness footprints

- `C4` 220 µF / 35V input bulk capacitor across `+24V_RAW` and `GND` near J1.
- `D2` TVS across `+24V_RAW` and `GND` for 24V input surge clamping.
- `D3` TVS across `+24V_FUSED` and `FAN_NEG` for fan/motor transient clamping.
- `U5` USB2 ESD footprint on the existing connector-side USB D+/D-/GND routing.
- `C5` optional thermocouple differential filter across `THERMO_PLUS`/`THERMO_MINUS` at J4. Treat as DNP unless testing shows benefit.
- `TP24V`, `TP3V3`, and `TPGND` bring-up pads; Reset/Boot tweezer pads were moved clear of R5/R6.
- `U3` and `+5V` were removed; U4 is now the only 24V→3.3V switching stage and needs an exact sourced footprint.
- `Q1` value/intent updated to an IRLB8721-class or equivalent low-Rds_on 3.3V-logic fan MOSFET.

## Important caveats

- The USB-C placeholder has been replaced by a real KiCad library footprint for XKB U262-16XN-4BVC11. Still confirm the exact purchasable variant, connector height, mounting style, and enclosure cutout before fabrication.
- USB-C is configured as data-only/device mode: D+/D- to ESP32-S3 native USB through 27R series resistors, CC1/CC2 via 5.1k Rd pulldowns, and VBUS as sense-only. The board is still powered from the internal 24V PSU, not USB.
- Default low-voltage netclass clearance remains 0.10 mm for the dense USB-C routing. Confirm this with the chosen PCB manufacturer. The board intentionally has no 230VAC copper.
- `CoffeeRoast-Control-RevA.kicad_dru` adds stricter width/via constraints only for the critical 24V/fan current nets; ordinary GPIO/USB/sensor tracks retain their existing rules.
- Freerouting is useful for a first route, but the final board should still be manually reviewed in KiCad, especially USB D+/D-, fan current path, GND return, antenna keepout, and connector placement.

## ESP32 debug/test pads

Added `TPESP1` through `TPESP40` around U1. They are copper probe/solder pads connected to the ESP32-S3-WROOM-1 side pins. Most are tiny pad extensions immediately outside the castellated module pads to avoid disturbing the existing route; `TPESP30` is intentionally tucked onto the U1 pad because the USB D+ route/via runs close to that pin.

Mapping is in `docs/esp32_debug_pads.csv`.

## Larger wire-attach ESP32 solder pads

Added `PADESP1` through `PADESP40` as larger bottom-side solder pads with B.Silk labels, routed outward from the ESP32-S3-WROOM-1 side pins for later wire attach/debugging. These are in addition to the tiny local `TPESP1` through `TPESP40` probe pads around U1.

- Pads are on `B.Cu/B.Mask` with no paste and labels on `B.SilkS`.
- Mapping is in `docs/esp32_solder_pads.csv`.
- Routing was regenerated with KiCad DSN + Freerouting and via sizes normalized to 0.50/0.30 mm for ordinary signal access; the critical FAN_NEG transition is now 1.20/0.60 mm.
- Current full DRC is clean with 0 violations and 0 unconnected items.
