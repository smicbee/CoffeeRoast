#!/usr/bin/env python3
"""Run lightweight simulations/calculations for CoffeeRoast RevA.1 analog/power blocks.

This is not a full MCU/MAX6675/USB digital simulation. It models the parts that are
meaningful at schematic level: fan MOSFET losses/PWM current, SSR driver current,
linear-vs-switching 3V3 heat, input bulk capacitor hold-up, and thermocouple C5 RC
sanity. Uses only Python stdlib + numpy so it runs in the repo environment.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sim" / "results"


def fan_pwm_sim(duty: float, freq: float = 20_000.0, cycles: int = 80, dt: float = 1e-6,
                supply: float = 24.0, r_motor: float = 9.6, l_motor: float = 1e-3,
                rds: float = 0.02, vf: float = 0.7) -> dict[str, float]:
    """Approximate 24V/2.5A fan as an R-L load with flyback diode across the fan.

    This ignores back-EMF and fan controller behavior, so it is a conservative
    electrical-switching sanity model rather than a real BLDC fan model.
    """
    period = 1.0 / freq
    total = cycles * period
    n = int(total / dt)
    i = 0.0
    currents = []
    mos_p = []
    diode_p = []
    for k in range(n):
        t = k * dt
        phase = t % period
        on = phase < duty * period
        if on:
            # supply -> motor R/L -> MOSFET -> ground
            v_l = supply - i * (r_motor + rds)
            p_m = i * i * rds
            p_d = 0.0
        else:
            # current recirculates through flyback diode and motor resistance
            v_l = -(vf + i * r_motor)
            p_m = 0.0
            p_d = max(i, 0.0) * vf
        i += (v_l / l_motor) * dt
        if i < 0:
            i = 0.0
        currents.append(i)
        mos_p.append(p_m)
        diode_p.append(p_d)
    # last 10 cycles as steady-ish window
    win = int(10 * period / dt)
    arr = np.array(currents[-win:])
    pmos = np.array(mos_p[-win:])
    pdio = np.array(diode_p[-win:])
    return {
        "duty": duty,
        "freq_hz": freq,
        "i_avg_a": float(arr.mean()),
        "i_min_a": float(arr.min()),
        "i_max_a": float(arr.max()),
        "i_ripple_a": float(arr.max() - arr.min()),
        "mosfet_p_avg_w": float(pmos.mean()),
        "flyback_diode_p_avg_w": float(pdio.mean()),
    }


def write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    fan_rows = [fan_pwm_sim(d) for d in [0.25, 0.5, 0.75, 1.0]]
    write_csv(OUT / "fan_pwm_rl_model.csv", fan_rows)

    mos_rows = []
    for current in [1.0, 2.0, 2.5, 3.0]:
        for r_mohm in [5, 10, 20, 50, 100]:
            mos_rows.append({
                "current_a": current,
                "rds_on_mohm": r_mohm,
                "mosfet_power_w": current * current * r_mohm / 1000.0,
            })
    write_csv(OUT / "mosfet_loss_sweep.csv", mos_rows)

    regulator_rows = []
    for current in [0.15, 0.25, 0.35, 0.50]:
        regulator_rows.append({
            "load_current_a": current,
            "ams1117_heat_w_5v_to_3v3": (5.0 - 3.3) * current,
            "switcher_input_power_w_at_90pct": (3.3 * current) / 0.90,
            "switcher_heat_w_at_90pct": (3.3 * current) / 0.90 - 3.3 * current,
        })
    write_csv(OUT / "regulator_heat_comparison.csv", regulator_rows)

    ssr_rows = []
    for r_in in [330, 680, 1000, 1500, 2200]:
        v_led = 1.2
        current = (5.0 - v_led) / r_in
        ssr_rows.append({
            "ssr_input_equiv_ohm": r_in,
            "estimated_ssr_led_current_ma": current * 1000,
            "q2_power_mw_at_vsat_0p1": current * 0.1 * 1000,
            "gpio_gate_static_current_ma": 3.3 / (100_000 + 100),
        })
    write_csv(OUT / "ssr_driver_current_sweep.csv", ssr_rows)

    input_rows = []
    for current in [0.2, 0.5, 1.0, 2.5, 3.0]:
        for cap_u in [220, 470, 1000]:
            # Time for capacitor to sag 1V under constant load. Very crude hold-up/ripple sanity.
            input_rows.append({
                "load_current_a": current,
                "bulk_cap_uf": cap_u,
                "time_for_1v_sag_ms": (cap_u * 1e-6 * 1.0 / current) * 1000,
            })
    write_csv(OUT / "input_bulk_holdup.csv", input_rows)

    thermo_rows = []
    for r_source in [10, 100, 1000, 10_000]:
        c = 1e-9
        fc = 1.0 / (2 * math.pi * r_source * c)
        thermo_rows.append({
            "thermocouple_source_or_added_series_ohm": r_source,
            "c5_f": c,
            "rc_cutoff_hz": fc,
            "time_constant_us": r_source * c * 1e6,
        })
    write_csv(OUT / "thermocouple_c5_filter.csv", thermo_rows)

    summary = f"""# CoffeeRoast RevA.1 simulation summary

Scope: lightweight numeric simulation/calculation of analog/power blocks. This does **not** simulate ESP32 firmware, MAX6675 digital conversion, USB protocol, or the external 230VAC heater/SSR mains path.

## Key results

- Fan MOSFET loss is tiny if Q1 is a real 3.3V logic MOSFET around 20 mΩ: at 3A DC it is about `{3*3*0.02:.2f} W`; at 50 mΩ it is `{3*3*0.05:.2f} W`, already worth thermal review.
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
"""
    (OUT / "summary.md").write_text(summary)
    print(summary)


if __name__ == "__main__":
    main()
