#!/usr/bin/env python3
"""Verify OpenSCAD exports using only Python's standard library."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_ascii_stl(path: Path) -> dict:
    vertices = []
    triangles = []
    current = []
    for raw in path.read_text(encoding="ascii", errors="strict").splitlines():
        line = raw.strip()
        if line.startswith("vertex "):
            _, x, y, z = line.split()
            vertex = (round(float(x), 6), round(float(y), 6), round(float(z), 6))
            vertices.append(vertex)
            current.append(vertex)
            if len(current) == 3:
                triangles.append(tuple(current))
                current = []
    if current or not triangles:
        raise ValueError(f"Invalid/empty ASCII STL: {path}")

    edge_counts = Counter()
    edge_to_faces = defaultdict(list)
    for face_index, tri in enumerate(triangles):
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edge = tuple(sorted((a, b)))
            edge_counts[edge] += 1
            edge_to_faces[edge].append(face_index)

    parent = list(range(len(triangles)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for faces in edge_to_faces.values():
        for face in faces[1:]:
            union(faces[0], face)

    components = len({find(i) for i in range(len(triangles))})
    xs, ys, zs = zip(*vertices)
    bbox = {
        "xmin": min(xs), "xmax": max(xs), "x": max(xs)-min(xs),
        "ymin": min(ys), "ymax": max(ys), "y": max(ys)-min(ys),
        "zmin": min(zs), "zmax": max(zs), "z": max(zs)-min(zs),
    }
    bad_edges = sum(1 for count in edge_counts.values() if count != 2)
    return {
        "triangles": len(triangles),
        "connected_components": components,
        "open_or_nonmanifold_edges": bad_edges,
        "bbox_mm": {key: round(value, 4) for key, value in bbox.items()},
    }


def valid_3mf(path: Path) -> bool:
    if not path.is_file() or not zipfile.is_zipfile(path):
        return False
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
    return "[Content_Types].xml" in members and any(
        member.lower().endswith(".model") for member in members
    )


def approx(actual: float, expected: float, tolerance=0.08) -> bool:
    return math.isclose(actual, expected, abs_tol=tolerance)


def main() -> int:
    checks = []

    def check(name, passed, evidence):
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    meshes = {}
    for name in (
        "tray",
        "lid_print",
        "lid_design",
        "board_proxy",
        "tray_rails_attached",
        "lid_rails_attached_print",
        "board_proxy_rails_attached",
    ):
        path = OUT / f"{name}.stl"
        meshes[name] = read_ascii_stl(path)

    check(
        "stl_meshes_closed_manifold",
        all(item["open_or_nonmanifold_edges"] == 0 for item in meshes.values()),
        meshes,
    )
    check(
        "print_parts_single_connected_component",
        meshes["tray"]["connected_components"] == 1
        and meshes["lid_print"]["connected_components"] == 1,
        {
            "tray": meshes["tray"]["connected_components"],
            "lid_print": meshes["lid_print"]["connected_components"],
        },
    )
    check(
        "rails_attached_print_parts_single_connected_component",
        meshes["tray_rails_attached"]["connected_components"] == 1
        and meshes["lid_rails_attached_print"]["connected_components"] == 1,
        {
            "tray": meshes["tray_rails_attached"]["connected_components"],
            "lid_print": meshes["lid_rails_attached_print"]["connected_components"],
        },
    )

    tray_box = meshes["tray"]["bbox_mm"]
    lid_box = meshes["lid_print"]["bbox_mm"]
    check(
        "expected_envelopes",
        approx(tray_box["x"], 100.4)
        and approx(tray_box["y"], 64.4)
        and approx(tray_box["z"], 30.0)
        and approx(lid_box["x"], 103.4)
        and approx(lid_box["y"], 67.4)
        and approx(lid_box["z"], 25.4),
        {"tray_mm": tray_box, "lid_print_mm": lid_box},
    )

    rails_tray_box = meshes["tray_rails_attached"]["bbox_mm"]
    rails_lid_box = meshes["lid_rails_attached_print"]["bbox_mm"]
    rails_board_box = meshes["board_proxy_rails_attached"]["bbox_mm"]
    check(
        "expected_rails_attached_envelopes",
        approx(rails_tray_box["x"], 100.4)
        and approx(rails_tray_box["y"], 74.4)
        and approx(rails_tray_box["z"], 30.0)
        and approx(rails_lid_box["x"], 103.4)
        and approx(rails_lid_box["y"], 77.4)
        and approx(rails_lid_box["z"], 25.4)
        and approx(rails_board_box["x"], 96.0)
        and approx(rails_board_box["y"], 70.0)
        and approx(rails_board_box["z"], 20.6),
        {
            "tray_mm": rails_tray_box,
            "lid_print_mm": rails_lid_box,
            "board_proxy_mm": rails_board_box,
        },
    )

    archives = {
        name: {
            "valid": valid_3mf(OUT / f"{name}.3mf"),
            "bytes": (OUT / f"{name}.3mf").stat().st_size,
        }
        for name in ("tray", "lid_print", "tray_rails_attached", "lid_rails_attached_print")
    }
    check("print_3mf_archives_valid", all(v["valid"] for v in archives.values()), archives)

    previews = {
        name: (OUT / name).stat().st_size
        for name in (
            "preview_closed.png",
            "preview_exploded.png",
            "preview_closed_rails_attached.png",
        )
    }
    check("previews_generated", all(size > 10000 for size in previews.values()), previews)

    production_geometry = json.loads((ROOT / "jlcpcb_y15_geometry.json").read_text())
    cam = production_geometry["jlcpcb_cam"]
    production_archive = (ROOT / production_geometry["archive_path"]).resolve()
    check(
        "jlcpcb_y15_production_geometry_and_archive",
        approx(cam["outer_width_mm"], 96.0, 0.001)
        and approx(cam["outer_height_mm"], 70.0, 0.001)
        and approx(cam["lower_vscore_y_mm"], 5.0, 0.001)
        and approx(cam["upper_vscore_y_mm"], 65.0, 0.001)
        and approx(cam["functional_core_height_mm"], 60.0, 0.001)
        and production_archive.is_file()
        and sha256(production_archive) == production_geometry["sha256"],
        {
            "cam_mm": cam,
            "archive": str(production_archive),
            "archive_sha256": sha256(production_archive) if production_archive.is_file() else None,
        },
    )

    report = {
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "scope": "OpenSCAD digital prototype geometry",
        "openscad_version": subprocess.check_output(
            ["openscad", "--version"], text=True, stderr=subprocess.STDOUT
        ).strip(),
        "design": {
            "functional_pcb_mm": [96.0, 60.0, 1.6],
            "jlcpcb_y15_as_delivered_mm": [96.0, 70.0, 1.6],
            "jlcpcb_process_rails": "two 5 mm V-scored rails; remove for operation",
            "tray_body_mm": [100.4, 64.4, 30.0],
            "rails_attached_tray_body_mm": [100.4, 74.4, 30.0],
            "corner_radius_mm": 3.0,
            "snap": "two opposed side cantilevers; no screws or corner towers",
            "pcb_retention": "four floor supports plus four lid hold-down pads",
        },
        "release_blockers": [
            "Remove both JLCPCB process rails at the V-scores before using the functional enclosure.",
            "Print the snap coupon/first lid in final material and tune snap depth/clearance.",
            "Measure manufactured Q1 and C4 installed heights.",
            "Fit-test J5 with the exact USB-C plug and cable bend.",
            "Measure J1-J4/J6 cable diameters and add final strain relief.",
            "Measure worst-case enclosure temperatures before material release.",
        ],
        "checks": checks,
    }
    (OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")

    files = {}
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            files[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest = {
        "status": "PROTOTYPE_NOT_RELEASED",
        "source": "CoffeeRoast_RevD_enclosure.scad",
        "openscad_version": report["openscad_version"],
        "files": files,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
