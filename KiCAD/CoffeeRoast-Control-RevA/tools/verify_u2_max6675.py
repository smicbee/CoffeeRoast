#!/usr/bin/env /usr/bin/python3
"""Verify the CoffeeRoast MAX6675 block and write reproducible results.

This is a topology + numeric sanity check, not a transistor-level MAX6675 model.
KiCad DRC remains the authority for copper clearance and unconnected items.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevA.kicad_pcb"
OUT = ROOT / "sim" / "results" / "u2_max6675_verification.json"

EXPECTED_U2 = {
    "1": "GND",
    "2": "THERMO_MINUS",
    "3": "THERMO_PLUS",
    "4": "+3V3",
    "5": "MAX_SCK",
    "6": "MAX_CS",
    "7": "MAX_DO",
    "8": "GND",
}
EXPECTED_J4 = {"1": "THERMO_PLUS", "2": "THERMO_MINUS"}
EXPECTED_C3 = {"1": "+3V3", "2": "GND"}


def mm(v: int) -> float:
    return pcbnew.ToMM(v)


def pos(item) -> tuple[float, float]:
    p = item.GetPosition()
    return (mm(p.x), mm(p.y))


def same_point(a, b) -> bool:
    return a == b


def routed_pad_contacts(board: pcbnew.BOARD, fp: pcbnew.FOOTPRINT) -> dict[str, int]:
    tracks = list(board.GetTracks())
    result: dict[str, int] = {}
    for pad in fp.Pads():
        number = pad.GetNumber()
        if not number.isdigit():
            continue
        center = pad.GetPosition()
        contacts = 0
        for item in tracks:
            if item.GetNetname() != pad.GetNetname():
                continue
            if isinstance(item, pcbnew.PCB_VIA):
                points = [item.GetPosition()]
            else:
                points = [item.GetStart(), item.GetEnd()]
            contacts += sum(1 for p in points if same_point(p, center))
        result[number] = contacts
    return result


def net_track_length_mm(board: pcbnew.BOARD, name: str) -> float:
    total = 0.0
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != name:
            continue
        a, b = item.GetStart(), item.GetEnd()
        total += math.hypot(mm(a.x - b.x), mm(a.y - b.y))
    return total


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    u2 = board.FindFootprintByReference("U2")
    j4 = board.FindFootprintByReference("J4")
    c3 = board.FindFootprintByReference("C3")
    assert u2 and j4 and c3

    u2_map = {p.GetNumber(): p.GetNetname() for p in u2.Pads() if p.GetNumber().isdigit()}
    j4_map = {p.GetNumber(): p.GetNetname() for p in j4.Pads() if p.GetNumber().isdigit()}
    c3_map = {p.GetNumber(): p.GetNetname() for p in c3.Pads() if p.GetNumber().isdigit()}
    contacts = routed_pad_contacts(board, u2)

    assert u2_map == EXPECTED_U2, (u2_map, EXPECTED_U2)
    assert j4_map == EXPECTED_J4, (j4_map, EXPECTED_J4)
    assert c3_map == EXPECTED_C3, (c3_map, EXPECTED_C3)
    assert all(contacts.get(str(n), 0) >= 1 for n in range(1, 9)), contacts
    assert abs(u2.GetOrientationDegrees() - 180.0) < 0.01
    assert all(abs(a - b) < 0.001 for a, b in zip(pos(u2), (128.0, 60.0)))

    # MAX6675 resolution is 0.25 °C/count. The approximate Type-K EMF below
    # uses 41 µV/°C only as an order-of-magnitude input sanity check.
    temperature_rows = []
    for temp_c in (0.0, 25.0, 100.0, 250.0, 500.0, 800.0, 1023.75):
        temperature_rows.append({
            "temperature_c": temp_c,
            "ideal_max6675_count": int(round(temp_c / 0.25)),
            "approx_type_k_emf_mv_at_41uv_per_c": round(temp_c * 0.041, 4),
        })

    # C5 is DNP by default. If later populated with 1 nF, these values bound
    # the simple source-R/differential-C pole; they are not a full input model.
    c5_rows = []
    for source_ohm in (10, 100, 1000, 10_000):
        tau = source_ohm * 1e-9
        c5_rows.append({
            "source_ohm": source_ohm,
            "tau_us_with_1nf": tau * 1e6,
            "fc_hz_with_1nf": 1.0 / (2.0 * math.pi * tau),
        })

    result = {
        "scope": "topology and numeric sanity; no transistor-level MAX6675 or firmware simulation",
        "board": str(BOARD),
        "u2_position_mm": pos(u2),
        "u2_rotation_deg": u2.GetOrientationDegrees(),
        "u2_pin_nets": u2_map,
        "j4_pin_nets": j4_map,
        "c3_pin_nets": c3_map,
        "u2_routed_contacts_per_pad": contacts,
        "net_total_track_length_mm": {
            name: round(net_track_length_mm(board, name), 4)
            for name in ("THERMO_PLUS", "THERMO_MINUS", "MAX_SCK", "MAX_CS", "MAX_DO")
        },
        "ideal_temperature_sanity": temperature_rows,
        "optional_c5_1nf_sanity": c5_rows,
        "status": "PASS",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
