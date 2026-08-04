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
    for name in ("tray", "lid_print", "lid_design", "board_proxy"):
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

    archives = {
        name: {
            "valid": valid_3mf(OUT / f"{name}.3mf"),
            "bytes": (OUT / f"{name}.3mf").stat().st_size,
        }
        for name in ("tray", "lid_print")
    }
    check("print_3mf_archives_valid", all(v["valid"] for v in archives.values()), archives)

    previews = {
        name: (OUT / name).stat().st_size
        for name in ("preview_closed.png", "preview_exploded.png")
    }
    check("previews_generated", all(size > 10000 for size in previews.values()), previews)

    report = {
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "scope": "OpenSCAD digital prototype geometry",
        "openscad_version": subprocess.check_output(
            ["openscad", "--version"], text=True, stderr=subprocess.STDOUT
        ).strip(),
        "design": {
            "pcb_mm": [96.0, 60.0, 1.6],
            "tray_body_mm": [100.4, 64.4, 30.0],
            "corner_radius_mm": 3.0,
            "snap": "two opposed side cantilevers; no screws or corner towers",
            "pcb_retention": "four floor supports plus four lid hold-down pads",
        },
        "release_blockers": [
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
        if path.is_file():
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
