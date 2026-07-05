# CoffeeRoast RevA.1 simulation summary

Scope: lightweight numeric simulation/calculation of analog/power blocks. This does **not** simulate ESP32 firmware, MAX6675 digital conversion, USB protocol, or the external 230VAC heater/SSR mains path.

## Key results

- Fan MOSFET loss is tiny if Q1 is a real 3.3V logic MOSFET around 20 mΩ: at 3A DC it is about `0.18 W`; at 50 mΩ it is `0.45 W`, already worth thermal review.
- The R-L fan PWM approximation at 20 kHz shows low MOSFET heat but potentially non-trivial flyback-diode dissipation at partial duty. Real 2-wire BLDC fans may behave differently; bench-test with the actual fan.
- AMS1117-style 5V→3.3V regulation would dissipate 0.43 W at 250 mA and 0.85 W at 500 mA, which supports the RevA.1 decision to use a 3.3V switching regulator.
- Q2 SSR low-side driver has negligible transistor heat for typical SSR input currents. The real check is whether the selected SSR reliably turns on from the board's +5V SSR output.
- C5=1nF on the thermocouple input is electrically fast for reasonable source impedance; still keep it DNP unless noise testing shows benefit because thermocouple front-ends can be sensitive to leakage/bias.
- C4=220uF is a local transient buffer, not meaningful power hold-up for a 2.5–3A fan; it only slows 1V sag by tens to hundreds of microseconds under amp-level load.

## Generated CSVs

- `fan_pwm_rl_model.csv`
- `mosfet_loss_sweep.csv`
- `regulator_heat_comparison.csv`
- `ssr_driver_current_sweep.csv`
- `input_bulk_holdup.csv`
- `thermocouple_c5_filter.csv`

## Practical conclusion

The architecture is sane for a low-voltage controller PCB. Simulation mainly confirms the previous decisions: use a switching 3.3V regulator, use a low-Rds_on 3.3V-logic fan MOSFET, treat C4 as transient suppression not energy storage, and bench-test the real fan/SSR before trusting thermal behavior.
