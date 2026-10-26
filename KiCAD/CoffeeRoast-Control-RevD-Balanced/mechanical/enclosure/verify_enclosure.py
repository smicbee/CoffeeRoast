#!/usr/bin/env python3
"""Mechanical checks for the RevD enclosure prototype.

This verifies CAD integrity and digital clearances. It deliberately does not claim
physical connector/cable/Q1/C4 fit; those remain coupon and real-PCBA gates.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import vtk

import enclosure


ROOT = Path(__file__).resolve().parent
GEN = ROOT / "generated"


def stl_open_edges(path: Path) -> tuple[int, int]:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    edges = vtk.vtkFeatureEdges()
    edges.SetInputConnection(reader.GetOutputPort())
    edges.BoundaryEdgesOn()
    edges.NonManifoldEdgesOn()
    edges.FeatureEdgesOff()
    edges.ManifoldEdgesOff()
    edges.Update()
    return reader.GetOutput().GetNumberOfCells(), edges.GetOutput().GetNumberOfCells()


def intersection_volume(a, b) -> float:
    result = a.intersect(b)
    solids = result.solids().vals()
    if not solids:
        return 0.0
    return float(sum(s.Volume() for s in solids))


def main() -> int:
    p = enclosure.P
    d = enclosure.dims()
    tray = enclosure.build_tray()
    lid_design = enclosure.build_lid()
    lid_closed = lid_design.translate((0, 0, d["tray_h"]))
    board = enclosure.build_board_proxy()

    checks: list[dict] = []

    def check(name: str, passed: bool, evidence) -> None:
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    check("tray_valid_single_solid", tray.val().isValid() and len(tray.solids().vals()) == 1,
          {"valid": tray.val().isValid(), "solids": len(tray.solids().vals())})
    check("lid_valid_single_solid", lid_design.val().isValid() and len(lid_design.solids().vals()) == 1,
          {"valid": lid_design.val().isValid(), "solids": len(lid_design.solids().vals())})

    collisions = {
        "tray_board_mm3": round(intersection_volume(tray, board), 6),
        "lid_board_mm3": round(intersection_volume(lid_closed, board), 6),
        "tray_lid_mm3": round(intersection_volume(tray, lid_closed), 6),
    }
    check("no_digital_collisions", all(v == 0.0 for v in collisions.values()), collisions)

    board_proxy_top = board.val().BoundingBox().zmax
    closed_lid_underside = d["tray_h"]
    check("proxy_height_clearance_positive", board_proxy_top < closed_lid_underside,
          {"proxy_top_z_mm": round(board_proxy_top, 3),
           "lid_underside_z_mm": round(closed_lid_underside, 3),
           "clearance_mm": round(closed_lid_underside - board_proxy_top, 3)})

    hold_down_bottom_z = d["tray_h"] - (p.clear_above_pcb - p.hold_down_gap)
    check("hold_down_gap_matches_parameter",
          abs((hold_down_bottom_z - d["board_top"]) - p.hold_down_gap) < 1e-6,
          {"board_top_z_mm": d["board_top"],
           "hold_down_bottom_z_mm": round(hold_down_bottom_z, 3),
           "gap_mm": round(hold_down_bottom_z - d["board_top"], 3)})

    check("pcb_lateral_clearance", p.pcb_xy_clearance >= 0.5,
          {"per_side_mm": p.pcb_xy_clearance,
           "pocket_minus_pcb_x_mm": round(d["inner_x"] - p.pcb_x, 3),
           "pocket_minus_pcb_y_mm": round(d["inner_y"] - p.pcb_y, 3)})

    # Vents are around KiCad y=43 mm (CAD lower-half); antenna keepout is KiCad
    # y=0..6.2 mm (CAD top edge), so their 2D envelopes must not overlap.
    _, vent_center_y = enclosure.board_xy(52.0, 43.0)
    vent_y = (vent_center_y - p.vent_l / 2, vent_center_y + p.vent_l / 2)
    _, antenna_y_min = enclosure.board_xy(48.0, 6.2)
    _, antenna_y_max = enclosure.board_xy(96.0, 0.0)
    vent_antenna_overlap = max(vent_y[0], antenna_y_min) < min(vent_y[1], antenna_y_max)
    check("vents_outside_antenna_keepout", not vent_antenna_overlap,
          {"vent_y_mm": [round(x, 3) for x in vent_y],
           "antenna_keepout_y_mm": [round(antenna_y_min, 3), round(antenna_y_max, 3)]})

    mesh_results = {}
    for name in ("tray", "lid", "lid_print", "board_proxy"):
        path = GEN / f"{name}.stl"
        triangles, open_edges = stl_open_edges(path)
        mesh_results[name] = {
            "file": str(path.relative_to(ROOT)),
            "triangles": triangles,
            "open_or_nonmanifold_edges": open_edges,
        }
    check("stl_meshes_closed_manifold",
          all(v["open_or_nonmanifold_edges"] == 0 for v in mesh_results.values()),
          mesh_results)

    three_mf_results = {}
    for name in ("tray", "lid_print"):
        path = GEN / f"{name}.3mf"
        valid = False
        members: list[str] = []
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                members = archive.namelist()
            valid = "[Content_Types].xml" in members and any(
                member.lower().endswith(".model") for member in members
            )
        three_mf_results[name] = {
            "file": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size if path.is_file() else 0,
            "valid_3mf_archive": valid,
        }
    check("print_3mf_archives_valid",
          all(v["valid_3mf_archive"] for v in three_mf_results.values()),
          three_mf_results)

    report = {
        "status": "PASS" if all(c["passed"] for c in checks) else "FAIL",
        "scope": "digital prototype geometry only",
        "release_blockers": [
            "Measure manufactured Q1 and C4 heights and mounting standoff.",
            "Fit-test J5 USB-C opening with the exact connector and a real cable plug.",
            "Measure J1-J4/J6 wire OD, bend radius and choose strain relief hardware.",
            "Tune M3 insert bore with a material/printer-specific coupon.",
            "Measure enclosure temperatures under worst-case roaster operation before material release.",
        ],
        "checks": checks,
    }
    out = GEN / "verification.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
