#!/usr/bin/env python3
"""Audit lid hold-down rectangles against the live RevD KiCad footprint geometry.

Run with the distribution Python that provides pcbnew, normally `/usr/bin/python3`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD = ROOT.parents[1] / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
MANIFEST = ROOT / "generated" / "manifest.json"
OUT = ROOT / "generated" / "kicad_clearance_verification.json"


def overlaps(a, b) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    specs = manifest["derived"]["hold_downs_kicad"]

    footprints = []
    for fp in board.GetFootprints():
        bbox = fp.GetBoundingBox(False, False)
        footprints.append({
            "reference": fp.GetReference(),
            "bbox_mm": [
                bbox.GetLeft() / 1e6,
                bbox.GetTop() / 1e6,
                bbox.GetRight() / 1e6,
                bbox.GetBottom() / 1e6,
            ],
        })

    contacts = []
    passed = True
    for spec in specs:
        rect = [
            float(spec["kx"]) - float(spec["sx"]) / 2,
            float(spec["ky"]) - float(spec["sy"]) / 2,
            float(spec["kx"]) + float(spec["sx"]) / 2,
            float(spec["ky"]) + float(spec["sy"]) / 2,
        ]
        hits = [fp for fp in footprints if overlaps(rect, fp["bbox_mm"])]
        if hits:
            passed = False
        contacts.append({
            "name": spec["name"],
            "rect_kicad_mm": rect,
            "overlapping_footprints": hits,
        })

    report = {
        "status": "PASS" if passed else "FAIL",
        "board": str(BOARD.relative_to(ROOT.parents[3])),
        "method": "conservative overlap against pcbnew footprint bounding boxes",
        "contacts": contacts,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
