# CoffeeRoast-Control RevA.1 optimizations

RevA.1 keeps the controller PCB low-voltage only and adds practical robustness features before a board-order review.

## Applied to the PCB

- **U3 part intent changed** from AMS1117-style linear regulator to a **3.3V switching regulator, >=600 mA, 5V input**. The currently routed footprint is still a draft placeholder; choose the exact regulator/module footprint before fabrication.
- **Q1 part intent tightened** to an IRLB8721-class or equivalent **3.3V-logic N-MOSFET with low Rds_on at Vgs=2.5/3.3V**.
- **C4** added as 220 µF / 35V input bulk capacitance across `+24V_RAW` and `GND` near J1.
- **D2** added as a 24V-input TVS clamp across `+24V_RAW` and `GND` near J1.
- **D3** added as a fan clamp/TVS across `+24V_FUSED` and `FAN_NEG` near J2.
- **U5** added as a USB2 D+/D- ESD footprint on existing connector-side USB/GND routing.
- **C5** added as an optional/draft thermocouple differential filter across `THERMO_PLUS`/`THERMO_MINUS` at J4. Mark DNP unless testing shows noise that justifies it.
- **TP24V, TP5V, TP3V3, TPGND** added as bring-up test pads.

## Deliberately not added yet

- A true reverse-polarity ideal-diode/P-MOSFET stage was left as RevB candidate because doing it properly requires rerouting the 24V input path through a series element and selecting the exact connector/fuse/protection stack.
- Status LEDs were not added to this routed draft to avoid extra GPIO/rail loading and layout churn. They remain easy to add after exact footprint selection if wanted.
- 230VAC remains off the controller PCB. Mains wiring remains enclosure-level only through the certified PSU and external SSR module.

## Verification

`kicad-cli pcb drc --severity-error --format report --output render/drc_report_errors_only.txt CoffeeRoast-Control-RevA.kicad_pcb`

Latest result: 0 error-level DRC violations, 0 unconnected pads, 0 footprint errors.
