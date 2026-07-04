# CoffeeRoast-Control RevA PCB Draft

This is the generated RevA hardware draft for moving the CoffeeRoast electronics onto a PCB. The current board has been autorouted with KiCad/Freerouting and has zero KiCad error-level DRC violations, but it still needs manual engineering review before fabrication.

## Design decision captured from chat

- Use **one 230V appliance inlet for the whole roaster enclosure**.
- Inside the enclosure use a **certified isolated 230VAC -> 24VDC / 3A PSU**.
- The controller PCB itself is **low-voltage only** and accepts the PSU's 24VDC output.
- The PCB generates 5V via a buck module and 3.3V for the ESP32-S3 module.
- The heater's 230V path is still switched by an **external SSR module with heatsink**; 230V is intentionally not routed on this PCB.

## Files

- `CoffeeRoast-Control-RevA.kicad_pcb` — KiCad board draft with on-board USB-C placeholder and autorouted tracks.
- `CoffeeRoast-Control-RevA.kicad_sch` — notes-only schematic placeholder; detailed netlist is in `docs/netlist.csv`.
- `docs/bom.csv` — draft bill of materials.
- `docs/netlist.csv` — intended electrical connectivity.
- `docs/routing_notes.md` — routing/DRC status and fabrication caveats.
- `symbols/` and `footprints.pretty/` — local ESP32-S3-WROOM-1 and USB-C library files copied from KiCad upstream.

## Firmware pin mapping preserved

| Function | ESP32-S3-WROOM-1 pin | GPIO | Firmware variable |
|---|---:|---:|---|
| Heater/SSR PWM | 39 | GPIO1 | `relayPin` |
| Fan PWM | 38 | GPIO2 | `fanPin` |
| MAX6675 DO/SO | 19 | GPIO11 | `thermoDO` |
| MAX6675 CS | 20 | GPIO12 | `thermoCS` |
| MAX6675 CLK/SCK | 21 | GPIO13 | `thermoCLK` |
| USB D- | 13 | native USB D- | serial/flash |
| USB D+ | 14 | native USB D+ | serial/flash |
| BOOT | 27 | GPIO0 | flash mode |
| EN/RESET | 3 | EN | reset |

## Power tree

```text
230VAC inlet in enclosure
  +--> certified 230VAC -> 24VDC / 3A PSU
          +--> J1 on this PCB
                +--> F1 24V-side fuse placeholder
                +--> J2 24V fan via Q1 low-side MOSFET
                +--> U4 24V -> 5V buck module
                        +--> SSR input driver supply
                        +--> U3 3.3V regulator
                                +--> ESP32-S3-WROOM-1 + MAX6675

230VAC heater line: external SSR module only, not on this PCB.
```

## Important limitations before fabrication

This was generated in the Hermes environment where KiCad is **not installed**, so ERC/DRC and Gerber export could not be run here. Before ordering boards:

1. Open the project in KiCad.
2. Replace any placeholder footprints with your exact sourced parts.
3. Run ERC/DRC.
4. Confirm ESP32-S3-WROOM-1 antenna keepout has no copper and is at board edge.
5. Confirm the fan path and screw terminals are rated for the real 24V/2.5A fan current.
6. Replace the routed draft USB-C placeholder with the exact sourced USB-C connector footprint and enclosure cutout.
7. Review USB CC pulldowns: R10/R11 = 5.1k to GND, VBUS is sense-only.
8. Review mains wiring separately: fused IEC inlet, PE/strain relief, certified 24V PSU, external SSR heatsink, thermal cut-off.

## RevB candidates

- Replace the generic buck module with an integrated switch-mode converter.
- Add ESD protection for USB D+/D- and optional VBUS TVS/polyfuse.
- Add TVS/ESD protection on 24V fan input.
- Add current/thermal sensing for fan/heater diagnostics.
