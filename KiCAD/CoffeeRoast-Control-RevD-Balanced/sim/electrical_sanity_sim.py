#!/usr/bin/env python3
"""Block-level electrical sanity simulation for CoffeeRoast RevD.

This is intentionally not a transistor-level model of the ESP32, LMR16010,
MAX6675, USB PHY, fan electronics, or external SSR. It combines a switched
buck power-stage model with tolerance/corner and loss calculations.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sim" / "results"
OUT.mkdir(parents=True, exist_ok=True)

# Values from docs/bom.csv / current schematic.
VOUT_TARGET = 3.3
VFB_TYP = 0.750
VFB_MIN = 0.735
VFB_MAX = 0.765
RFB_TOP = 100_000.0
RFB_BOTTOM = 29_400.0
RES_TOL = 0.01
F_SW = 500_000.0
L = 22e-6
COUT_NOM = 22e-6 + 22e-6 + 0.1e-6
ESR_EQ_ASSUMED = 0.010
DIODE_DROP = 0.45
SWITCH_DROP = 0.10


def feedback_output(vfb: float, rtop: float, rbottom: float) -> float:
    return vfb * (1.0 + rtop / rbottom)


def simulate_buck(vin: float, load_a: float, cycles: int = 3000, steps_per_cycle: int = 500):
    """Fixed-duty switched CCM model at the regulator's equilibrium duty.

    Includes an assumed catch-diode and switch drop. The control loop is not
    modeled; duty is chosen at its steady-state equilibrium for 3.3 V.
    """
    period = 1.0 / F_SW
    dt = period / steps_per_cycle
    duty = (VOUT_TARGET + DIODE_DROP) / (vin - SWITCH_DROP + DIODE_DROP)
    on_steps = int(round(duty * steps_per_cycle))
    load_resistance = VOUT_TARGET / load_a
    i_l = load_a
    v_c = VOUT_TARGET
    final = []
    for k in range(cycles * steps_per_cycle):
        phase = k % steps_per_cycle
        if phase < on_steps:
            di = (vin - SWITCH_DROP - v_c) / L
        else:
            di = (-DIODE_DROP - v_c) / L
        i_l = max(0.0, i_l + di * dt)
        load_instant = v_c / load_resistance
        dv = (i_l - load_instant) / COUT_NOM
        v_c += dv * dt
        if k >= (cycles - 10) * steps_per_cycle:
            v_out = v_c + ESR_EQ_ASSUMED * (i_l - load_instant)
            final.append((k * dt, v_out, i_l, 1 if phase < on_steps else 0))
    a = np.asarray(final)
    return {
        "vin_v": vin,
        "load_a": load_a,
        "duty": duty,
        "vout_mean_v": float(np.mean(a[:, 1])),
        "vout_min_v": float(np.min(a[:, 1])),
        "vout_max_v": float(np.max(a[:, 1])),
        "vout_pp_mv": float((np.max(a[:, 1]) - np.min(a[:, 1])) * 1000.0),
        "inductor_mean_a": float(np.mean(a[:, 2])),
        "inductor_min_a": float(np.min(a[:, 2])),
        "inductor_max_a": float(np.max(a[:, 2])),
        "inductor_pp_a": float(np.max(a[:, 2]) - np.min(a[:, 2])),
        "waveform": a,
    }


# Feedback-divider corner analysis.
vout_typ = feedback_output(VFB_TYP, RFB_TOP, RFB_BOTTOM)
vout_corner_min = feedback_output(VFB_MIN, RFB_TOP * (1 - RES_TOL), RFB_BOTTOM * (1 + RES_TOL))
vout_corner_max = feedback_output(VFB_MAX, RFB_TOP * (1 + RES_TOL), RFB_BOTTOM * (1 - RES_TOL))

# Switched power-stage cases. 0.2 A, 0.7 A and 0.9 A cover light operation,
# a realistic Wi-Fi-heavy load, and near the 1 A regulator limit.
buck_cases = []
waveform_case = None
for vin in (18.0, 24.0, 30.0):
    for load in (0.2, 0.7, 0.9):
        result = simulate_buck(vin, load)
        waveform = result.pop("waveform")
        buck_cases.append(result)
        if vin == 24.0 and load == 0.7:
            waveform_case = waveform

# Fan MOSFET conduction loss sweep. STP55NF06L is driven from the 10 V VDRV rail;
# use 18 mOhm typical and 22 mOhm conservative hot/part corner assumptions.
mosfet_rows = []
for current in np.arange(0.0, 3.01, 0.25):
    mosfet_rows.append({
        "current_a": round(float(current), 3),
        "loss_typ_18mohm_w": float(current * current * 0.018),
        "loss_conservative_22mohm_w": float(current * current * 0.022),
    })

# 10 V gate-supply resistor/zener budget. Gate-charge assumption is explicit.
qg_assumed_c = 60e-9
pwm_assumed_hz = 20_000.0
driver_iq_assumed_a = 1.0e-3
gate_avg_a = qg_assumed_c * pwm_assumed_hz
gate_supply = []
for vin in (18.0, 24.0, 30.0):
    current = max(0.0, (vin - 10.0) / 2700.0)
    gate_supply.append({
        "vin_v": vin,
        "r16_current_ma": current * 1000,
        "r16_power_mw": current * current * 2700.0 * 1000,
        "assumed_driver_plus_gate_ma": (driver_iq_assumed_a + gate_avg_a) * 1000,
        "current_margin_ma": (current - driver_iq_assumed_a - gate_avg_a) * 1000,
    })

# Other block-level checks.
fan_a = 2.5
buck_load_a = 0.75
buck_eff_assumed = 0.85
board_input_a = (VOUT_TARGET * buck_load_a) / (24.0 * buck_eff_assumed)
total_24v_a = fan_a + board_input_a
psu_margin_a = 3.0 - total_24v_a
hold_up_us_per_volt_at_3a = 220e-6 / 3.0 * 1e6
cc_current_ma = 5.0 / 5100.0 * 1000

ssr_sweep = []
for resistance in (220.0, 330.0, 470.0, 680.0, 1000.0):
    current = 3.3 / resistance
    ssr_sweep.append({
        "equivalent_ssr_input_ohm": resistance,
        "input_current_ma": current * 1000,
        "q2_loss_at_0p1v_mw": current * 0.1 * 1000,
    })

report = {
    "scope": {
        "type": "block-level electrical sanity simulation",
        "not_modeled": [
            "LMR16010 internal compensation/control-loop transient response",
            "ESP32 firmware/RF/USB protocol",
            "MAX6675 conversion internals",
            "real 2-wire BLDC fan commutation",
            "external SSR and 230 V heater path",
            "PCB parasitics and thermal enclosure model",
        ],
    },
    "feedback_divider": {
        "typical_vout_v": vout_typ,
        "full_temp_plus_1pct_resistor_corner_min_v": vout_corner_min,
        "full_temp_plus_1pct_resistor_corner_max_v": vout_corner_max,
    },
    "buck_power_stage": {
        "f_sw_hz": F_SW,
        "inductor_h": L,
        "nominal_output_capacitance_f": COUT_NOM,
        "assumed_equivalent_esr_ohm": ESR_EQ_ASSUMED,
        "cases": buck_cases,
    },
    "fan_mosfet": {
        "device": "STP55NF06L",
        "drive_v": 10.0,
        "loss_at_2p5a_typ_w": fan_a * fan_a * 0.018,
        "loss_at_2p5a_conservative_w": fan_a * fan_a * 0.022,
    },
    "gate_supply": {
        "zener_v": 10.0,
        "r16_ohm": 2700.0,
        "assumed_gate_charge_nc": qg_assumed_c * 1e9,
        "assumed_pwm_hz": pwm_assumed_hz,
        "assumed_driver_iq_ma": driver_iq_assumed_a * 1000,
        "cases": gate_supply,
    },
    "power_budget_24v": {
        "fan_a": fan_a,
        "assumed_3v3_load_a": buck_load_a,
        "assumed_buck_efficiency": buck_eff_assumed,
        "board_input_a": board_input_a,
        "total_input_a": total_24v_a,
        "margin_to_3a_psu_a": psu_margin_a,
    },
    "input_bulk_cap": {
        "capacitance_uF": 220.0,
        "hold_up_us_per_1v_droop_at_3a": hold_up_us_per_volt_at_3a,
    },
    "usb_cc": {"each_5p1k_current_at_5v_ma": cc_current_ma},
    "ssr_input_sweep": ssr_sweep,
}

(OUT / "electrical_sanity.json").write_text(json.dumps(report, indent=2) + "\n")

assert waveform_case is not None
with (OUT / "buck_24v_0p7a_waveform.csv").open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["time_s", "vout_v", "inductor_current_a", "switch_on"])
    for row in waveform_case:
        w.writerow([f"{row[0]:.12g}", f"{row[1]:.9g}", f"{row[2]:.9g}", int(row[3])])

with (OUT / "fan_mosfet_loss.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=mosfet_rows[0].keys(), lineterminator="\n")
    w.writeheader(); w.writerows(mosfet_rows)

# Dependency-free SVG for quick visual inspection of the representative case.
def svg_polyline(values, x0, y0, width, height, vmin, vmax):
    points = []
    count = len(values)
    for idx, value in enumerate(values):
        x = x0 + width * idx / max(1, count - 1)
        y = y0 + height * (vmax - value) / max(1e-12, vmax - vmin)
        points.append(f"{x:.2f},{y:.2f}")
    return " ".join(points)

wave_v = waveform_case[:, 1]
wave_i = waveform_case[:, 2]
vmin, vmax = float(np.min(wave_v)), float(np.max(wave_v))
imin, imax = float(np.min(wave_i)), float(np.max(wave_i))
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#10151c"/>
<text x="60" y="45" fill="white" font-family="sans-serif" font-size="24">CoffeeRoast RevD — Buck model, 24 V in / 3.3 V / 0.7 A</text>
<text x="60" y="78" fill="#aeb8c5" font-family="sans-serif" font-size="16">Last 10 switching cycles, 500 kHz, L=22 uH, Cout=44.1 uF</text>
<rect x="80" y="110" width="1060" height="220" fill="none" stroke="#637083"/>
<polyline points="{svg_polyline(wave_v,80,110,1060,220,vmin,vmax)}" fill="none" stroke="#5ee38d" stroke-width="2"/>
<text x="90" y="135" fill="#5ee38d" font-family="monospace" font-size="16">Vout {vmin:.4f}..{vmax:.4f} V ({(vmax-vmin)*1000:.2f} mVpp)</text>
<rect x="80" y="410" width="1060" height="220" fill="none" stroke="#637083"/>
<polyline points="{svg_polyline(wave_i,80,410,1060,220,imin,imax)}" fill="none" stroke="#55c7ff" stroke-width="2"/>
<text x="90" y="435" fill="#55c7ff" font-family="monospace" font-size="16">Inductor {imin:.3f}..{imax:.3f} A</text>
<text x="80" y="670" fill="#aeb8c5" font-family="sans-serif" font-size="14">Model scope: switched L/C power stage only; regulator control loop, PCB parasitics and thermal behavior are not modeled.</text>
</svg>'''
(OUT / "buck_24v_0p7a_waveform.svg").write_text(svg + "\n")

print(json.dumps(report, indent=2))
