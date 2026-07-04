# CoffeeRoast RevA enclosure power wiring

This document intentionally keeps 230VAC off the controller PCB.

## One-plug power architecture

```text
IEC C14 fused inlet / appliance cable
  L ── main switch ──┬── certified 230VAC→24VDC PSU L
                     └── external SSR AC input ── SSR AC output ── heater L
  N ─────────────────┬── certified 230VAC→24VDC PSU N
                     └──────────────────────────────────────────── heater N
  PE ─────────────────── chassis / any exposed metal / PSU PE if present

24V PSU + ──> CoffeeRoast-Control RevA J1.1 +24V_RAW
24V PSU - ──> CoffeeRoast-Control RevA J1.2 GND

CoffeeRoast-Control RevA J2 ──> 24V fan
CoffeeRoast-Control RevA J3 ──> external SSR DC input
CoffeeRoast-Control RevA J4 ──> K-type thermocouple
CoffeeRoast-Control RevA J5 ──> USB data panel connector
```

## Safety design notes

- Use a certified, enclosed or encapsulated **24V / 3A isolated PSU**.
- Keep mains wiring physically separated from the controller PCB and thermocouple wiring.
- Use strain relief for the mains cable and fan/heater cables.
- Keep the SSR module on a heatsink; do not enclose it tightly without airflow.
- Add/retain a manual heater cut-off such that the fan/controller can continue cooling after heater-off.
- Add a thermal fuse/thermal cut-off near the heater path if the popcorn maker does not already have a reliable one.
- Fuse the mains inlet according to the heater/PSU load and local rules; F1 on the PCB is only for the low-voltage 24V branch.

## RevA boundary

The PCB only sees SELV/low-voltage rails: 24V, 5V, 3.3V, thermocouple, USB data, SSR input. It does **not** route 230VAC.
