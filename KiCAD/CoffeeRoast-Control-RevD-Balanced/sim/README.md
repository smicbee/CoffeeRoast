# CoffeeRoast RevD electrical sanity simulation

Run:

```bash
python3 sim/electrical_sanity_sim.py
```

## Scope

This is a block-level electrical simulation based on the current BOM/schematic values. It includes:

- switched buck L/C power-stage cases at 18 V, 24 V and 30 V input;
- 0.2 A, 0.7 A and 0.9 A 3.3 V loads;
- feedback-divider/full-temperature corner calculation;
- fan MOSFET conduction-loss sweep;
- 10 V gate-supply resistor/zener current and dissipation;
- 24 V PSU budget and input-bulk-capacitor estimate;
- USB-C CC resistor current;
- external SSR input-resistance sweep.

It does **not** model the LMR16010 internal compensation/control loop, ESP32 firmware/RF/USB protocol, MAX6675 conversion internals, BLDC fan electronics, PCB parasitics/thermal enclosure behavior, or the external SSR/230 V heater circuit.

## Main results

- Feedback divider (`100 kΩ / 29.4 kΩ`, `VFB=0.750 V`) gives **3.301 V typical**.
- Combined full-temperature VFB and ±1% resistor corners give **3.185–3.420 V**.
- Representative switched model at `24 V -> 3.3 V / 0.7 A`:
  - mean output: **3.300 V**;
  - modeled ripple: **3.21 mVpp**;
  - inductor current: **0.556–0.844 A**.
- At `30 V / 0.9 A`, modeled inductor peak reaches **1.054 A**. This is close to the 1 A regulator operating envelope; continuous loading should retain margin.
- Fan MOSFET conduction loss at 2.5 A is approximately **0.113–0.138 W** for the modeled 18–22 mΩ range.
- 10 V gate supply at nominal 24 V:
  - R16 current: **5.19 mA**;
  - R16 loss: **72.6 mW**;
  - modeled current margin after 1 mA driver quiescent current and a 60 nC gate at 20 kHz: **2.99 mA**.
- The same gate-supply assumption leaves only **0.76 mA margin at 18 V**; this is the weakest modeled corner and should be checked against the exact MOSFET gate charge, chosen PWM frequency and UCC27511 operating current.
- With a 2.5 A fan and assumed 0.75 A 3.3 V load at 85% buck efficiency, estimated 24 V input is **2.621 A**, leaving **0.379 A** to a 3 A PSU. Fan startup/inrush is not modeled.
- The 220 µF input capacitor provides only about **73 µs per volt of droop at 3 A**; it is transient bulk capacitance, not meaningful hold-up energy.
- The SSR driver itself is lightly loaded in the 3.3–15 mA sweep, but the external SSR cannot be approved without its exact input specification. A generic “3–32 V” marking is not proof of reliable switching at 3.3 V.

## Outputs

- `results/electrical_sanity.json` — complete machine-readable report
- `results/buck_24v_0p7a_waveform.csv` — representative switching waveform
- `results/buck_24v_0p7a_waveform.svg` — quick waveform plot
- `results/fan_mosfet_loss.csv` — MOSFET current/loss sweep
- `results/run_output.json` — captured console report
