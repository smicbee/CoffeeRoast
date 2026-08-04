#!/usr/bin/env /usr/bin/python3
"""Fail-closed geometric audit for the final RevD routing."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
OUT = ROOT / "qa" / "routing-final-audit.json"

board = pcbnew.LoadBoard(str(BOARD))
off_angle = []
net_stats = defaultdict(lambda: {"segments": 0, "length_mm": 0.0, "vias": 0, "widths_mm": Counter()})

for item in board.GetTracks():
    net = item.GetNetname()
    stats = net_stats[net]
    if isinstance(item, pcbnew.PCB_VIA):
        stats["vias"] += 1
        continue
    start, end = item.GetStart(), item.GetEnd()
    dx = (end.x - start.x) / 1e6
    dy = (end.y - start.y) / 1e6
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    deviation = min(abs(angle - target) for target in (0.0, 45.0, 90.0, 135.0, 180.0))
    stats["segments"] += 1
    stats["length_mm"] += length
    stats["widths_mm"][round(item.GetWidth() / 1e6, 3)] += 1
    if length > 0.15 and deviation > 0.3:
        off_angle.append({
            "net": net,
            "layer": item.GetLayerName(),
            "angle_deg": round(angle, 4),
            "length_mm": round(length, 4),
        })

for net in ("+24V_RAW", "FAN_NEG"):
    widths = net_stats[net]["widths_mm"]
    if not widths or min(widths) < 1.0:
        raise SystemExit(f"{net}: final current route contains width below 1.0 mm: {dict(widths)}")

if off_angle:
    raise SystemExit(f"Final routing contains non-45/90 segments: {off_angle}")

usb_dn = net_stats["USB_DN"]["length_mm"] + net_stats["USB_DN_MCU"]["length_mm"]
usb_dp = net_stats["USB_DP"]["length_mm"] + net_stats["USB_DP_MCU"]["length_mm"]
report = {
    "board": BOARD.name,
    "revision": board.GetTitleBlock().GetRevision(),
    "tracks_and_vias": len(list(board.GetTracks())),
    "vias": sum(v["vias"] for v in net_stats.values()),
    "off_angle_segments": off_angle,
    "usb_total_length_mm": {
        "D-": round(usb_dn, 3),
        "D+": round(usb_dp, 3),
        "absolute_skew_mm": round(abs(usb_dp - usb_dn), 3),
    },
    "critical_nets": {
        net: {
            "length_mm": round(net_stats[net]["length_mm"], 3),
            "segments": net_stats[net]["segments"],
            "vias": net_stats[net]["vias"],
            "widths_mm": dict(net_stats[net]["widths_mm"]),
        }
        for net in ("+24V_RAW", "FAN_NEG", "BUCK_SW", "THERMO_PLUS", "THERMO_MINUS")
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))