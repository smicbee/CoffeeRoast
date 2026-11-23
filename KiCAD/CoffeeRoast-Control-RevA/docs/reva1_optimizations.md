# CoffeeRoast-Control RevA.2 power and placement update

RevA.2 keeps the controller PCB low-voltage only, removes the redundant 5V rail and improves mechanical access.

## Applied to the PCB

- **U3 and the +5V rail were removed.** U4 is now the sole **24V→3.3V switching converter, >=1 A**; its exact sourced module/footprint must still be verified before fabrication.
- **J3/TPSSR1 now use +3V3** for the external SSR input. The chosen SSR must be bench-verified to switch reliably at 3.3V.
- **Q1 was moved down by 10 mm**, increasing the mechanical gap to Reset/Boot; TPRESET1/TPBOOT1 and the rail test pads were moved out from under adjacent footprints.
- **Q1 part intent remains** an IRLB8721-class or equivalent **3.3V-logic N-MOSFET with low Rds_on at Vgs=2.5/3.3V**.
- **C4** added as 220 µF / 35V input bulk capacitance across `+24V_RAW` and `GND` near J1.
- **D2** added as a 24V-input TVS clamp across `+24V_RAW` and `GND` near J1.
- **D3** added as a fan clamp/TVS across `+24V_FUSED` and `FAN_NEG` near J2.
- **U5** added as a USB2 D+/D- ESD footprint on existing connector-side USB/GND routing.
- **C5** added as an optional/draft thermocouple differential filter across `THERMO_PLUS`/`THERMO_MINUS` at J4. Mark DNP unless testing shows noise that justifies it.
- **TP24V, TP3V3, TPGND** are the bring-up rail test pads; TPRESET1/TPBOOT1 provide accessible control test points.

## Deliberately not added yet

- A true reverse-polarity ideal-diode/P-MOSFET stage was left as RevB candidate because doing it properly requires rerouting the 24V input path through a series element and selecting the exact connector/fuse/protection stack.
- Status LEDs were not added to this routed draft to avoid extra GPIO/rail loading and layout churn. They remain easy to add after exact footprint selection if wanted.
- 230VAC remains off the controller PCB. Mains wiring remains enclosure-level only through the certified PSU and external SSR module.

## Verification

`kicad-cli pcb drc --severity-error --format report --output render/drc_report_errors_only.txt CoffeeRoast-Control-RevA.kicad_pcb`

Latest result: 0 error-level DRC violations, 0 unconnected pads, 0 footprint errors.
