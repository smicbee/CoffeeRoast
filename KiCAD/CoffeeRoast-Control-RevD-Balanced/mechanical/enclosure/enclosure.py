#!/usr/bin/env python3
"""Parametric RevD enclosure prototype.

The PCB is retained by the printed enclosure itself: a fitted lateral pocket,
four underside supports and four lid hold-down pads. No PCB mounting holes,
separate guide rails or insertion snap-clips are used.

All component/cable Z envelopes marked PROVISIONAL must be checked against the
manufactured PCBA, real wires and plugs before a final print.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict, dataclass
from pathlib import Path

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parent
GENERATED = ROOT / "generated"


@dataclass(frozen=True)
class Parameters:
    # Exact PCB contract from KiCad RevD.
    pcb_x: float = 96.0
    pcb_y: float = 60.0
    pcb_t: float = 1.6

    # FDM start values for a calibrated 0.4 mm nozzle.
    wall: float = 1.6
    floor: float = 1.6
    lid_t: float = 1.6
    pcb_xy_clearance: float = 0.60
    support_h: float = 2.8
    clear_above_pcb: float = 24.0  # PROVISIONAL: Q1/C4 must be measured.
    corner_radius: float = 3.0

    # PCB retention: pocket + lid hold-down pads, not guide rails/snap clips.
    support_size: float = 5.0
    hold_down_width: float = 6.0
    hold_down_depth: float = 3.0
    hold_down_gap: float = 0.20

    # Lid screws are outside the PCB envelope; these do not alter the PCB.
    tower_radius: float = 4.0
    tower_offset: float = 2.0
    insert_bore: float = 4.20  # PROVISIONAL: tune to the chosen M3 insert coupon.
    insert_depth: float = 8.0
    lid_screw_clearance: float = 3.40

    # Connector/wire openings. These are printable prototypes, not released dimensions.
    usb_cutout_w: float = 10.5
    usb_cutout_h: float = 5.2
    usb_cutout_z_from_board_bottom: float = 0.2
    field_cutout_h: float = 7.0
    field_cutout_z_from_board_bottom: float = 0.4

    # Closed-case passive ventilation, outside the antenna keepout.
    vent_w: float = 2.5
    vent_l: float = 14.0
    vent_count: int = 6
    vent_pitch: float = 5.0


P = Parameters()


def box(x: float, y: float, z: float, at=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z, centered=(False, False, False)).translate(at)


def cyl(radius: float, height: float, at=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").center(at[0], at[1]).circle(radius).extrude(height).translate((0, 0, at[2]))


def dims() -> dict[str, float]:
    inner_x = P.pcb_x + 2 * P.pcb_xy_clearance
    inner_y = P.pcb_y + 2 * P.pcb_xy_clearance
    outer_x = inner_x + 2 * P.wall
    outer_y = inner_y + 2 * P.wall
    board_z = P.floor + P.support_h
    board_top = board_z + P.pcb_t
    tray_h = board_top + P.clear_above_pcb
    return {
        "inner_x": inner_x,
        "inner_y": inner_y,
        "outer_x": outer_x,
        "outer_y": outer_y,
        "board_x0": P.wall + P.pcb_xy_clearance,
        "board_y0": P.wall + P.pcb_xy_clearance,
        "board_z": board_z,
        "board_top": board_top,
        "tray_h": tray_h,
    }


def board_xy(kicad_x: float, kicad_y: float) -> tuple[float, float]:
    """Map KiCad top-left/Y-down board coordinates into enclosure XY/Y-up."""
    d = dims()
    return d["board_x0"] + kicad_x, d["board_y0"] + (P.pcb_y - kicad_y)


def tower_centres() -> list[tuple[float, float]]:
    d = dims()
    o = P.tower_offset
    return [
        (-o, -o),
        (d["outer_x"] + o, -o),
        (-o, d["outer_y"] + o),
        (d["outer_x"] + o, d["outer_y"] + o),
    ]


def hold_down_specs() -> list[dict[str, float | str]]:
    """Contact rectangles in the authoritative KiCad top-left coordinate frame."""
    return [
        {"name": "usb_edge", "kx": 30.0, "ky": 1.5,
         "sx": P.hold_down_width, "sy": P.hold_down_depth},
        {"name": "field_edge", "kx": 26.5, "ky": 58.5,
         "sx": P.hold_down_width, "sy": P.hold_down_depth},
        {"name": "left_edge", "kx": 1.5, "ky": 25.0,
         "sx": P.hold_down_depth, "sy": P.hold_down_width},
        {"name": "right_edge", "kx": 94.5, "ky": 40.0,
         "sx": P.hold_down_depth, "sy": P.hold_down_width},
    ]


def build_tray() -> cq.Workplane:
    d = dims()
    tray = box(d["outer_x"], d["outer_y"], d["tray_h"])
    cavity = box(
        d["inner_x"],
        d["inner_y"],
        d["tray_h"] - P.floor + 0.2,
        (P.wall, P.wall, P.floor),
    )
    tray = tray.cut(cavity)

    # External full-height towers keep lid screws entirely outside the PCB pocket.
    for cx, cy in tower_centres():
        tray = tray.union(cyl(P.tower_radius, d["tray_h"], (cx, cy, 0)))
        bore = cyl(
            P.insert_bore / 2,
            P.insert_depth + 0.2,
            (cx, cy, d["tray_h"] - P.insert_depth),
        )
        tray = tray.cut(bore)

    # Four isolated support pads avoid through-hole solder joints on the underside.
    # Coordinates are in KiCad XY and deliberately avoid known J1-J9/Q1/C4 drills.
    support_points = [(25.0, 50.0), (25.0, 15.0), (75.0, 30.0), (88.0, 32.0)]
    for kx, ky in support_points:
        x, y = board_xy(kx, ky)
        tray = tray.union(
            box(
                P.support_size,
                P.support_size,
                P.support_h,
                (x - P.support_size / 2, y - P.support_size / 2, P.floor),
            )
        )


    # USB-C J5 wall opening on KiCad y=0. Width/height are provisional until a
    # physical U262-161N-4BVC11 and cable plug pass the connector coupon.
    usb_x, _ = board_xy(15.0, 0.0)
    usb_z = d["board_z"] + P.usb_cutout_z_from_board_bottom
    tray = tray.cut(
        box(P.usb_cutout_w, P.wall + 2.0, P.usb_cutout_h,
            (usb_x - P.usb_cutout_w / 2, d["outer_y"] - P.wall - 1.0, usb_z))
    )

    # Individual wall openings for direct-soldered SELV harnesses. The values are
    # starting envelopes; actual cable OD/bend radius and strain relief remain gates.
    field_slots = [
        ("THERMO", 5.5, 10.0),
        ("SSR", 18.0, 10.0),
        ("ESC_AUX", 41.62, 20.0),
        ("FAN", 62.0, 10.0),
        ("24V_IN", 82.0, 10.0),
    ]
    slot_z = d["board_z"] + P.field_cutout_z_from_board_bottom
    for _, kx, width in field_slots:
        x, _ = board_xy(kx, 60.0)
        tray = tray.cut(box(width, P.wall + 2.0, P.field_cutout_h,
                            (x - width / 2, -1.0, slot_z)))

    return tray


def build_lid() -> cq.Workplane:
    d = dims()
    lid = box(d["outer_x"], d["outer_y"], P.lid_t)
    for cx, cy in tower_centres():
        lid = lid.union(cyl(P.tower_radius, P.lid_t, (cx, cy, 0)))
        lid = lid.cut(cyl(P.lid_screw_clearance / 2, P.lid_t + 0.4, (cx, cy, -0.2)))

    # Four broad pads descend from the closed lid to the bare PCB-edge zones.
    # The PCB can therefore be dropped vertically into the pocket without flexing
    # tall enclosure walls or forcing it past snap lips. The small gap is intended
    # for a thin TPU/foam pad after physical fit validation.
    post_h = P.clear_above_pcb - P.hold_down_gap
    for spec in hold_down_specs():
        sx, sy = float(spec["sx"]), float(spec["sy"])
        x, y = board_xy(float(spec["kx"]), float(spec["ky"]))
        lid = lid.union(box(sx, sy, post_h, (x - sx / 2, y - sy / 2, -post_h)))

    # Access holes for SW1 RESET and SW2 BOOT. Nonconductive plungers can be added
    # after the real switch cap height has been measured.
    for kx, ky in [(42.0, 27.0), (46.0, 36.0)]:
        x, y = board_xy(kx, ky)
        lid = lid.cut(cyl(2.0, P.lid_t + 0.4, (x, y, -0.2)))

    # Vents over Q1/buck/L1, never over the ESP32 antenna keepout (KiCad y=0..6.2).
    vent_start_x, vent_y = board_xy(52.0, 43.0)
    for i in range(P.vent_count):
        x = vent_start_x + i * P.vent_pitch
        lid = lid.cut(
            box(P.vent_w, P.vent_l, P.lid_t + 0.4,
                (x, vent_y - P.vent_l / 2, -0.2))
        )
    return lid


def build_board_proxy() -> cq.Workplane:
    """Mechanical proxy only; all component heights except PCB are provisional."""
    d = dims()
    proxy = box(P.pcb_x, P.pcb_y, P.pcb_t,
                (d["board_x0"], d["board_y0"], d["board_z"]))

    # J5 USB-C provisional body.
    x, y = board_xy(15.0, 3.675)
    proxy = proxy.union(box(9.0, 7.4, 3.3, (x - 4.5, y - 3.7, d["board_top"])))
    # Q1 vertical TO-220 provisional body.
    x, y = board_xy(56.54, 47.0)
    proxy = proxy.union(box(10.5, 4.8, 16.0, (x - 5.25, y - 2.4, d["board_top"] + 3.0)))
    # C4 provisional radial capacitor proxy.
    x, y = board_xy(66.5, 46.5)
    proxy = proxy.union(cq.Workplane("XY").center(x, y).circle(4.0).extrude(16.0).translate((0, 0, d["board_top"])))
    # ESP32 module and antenna body proxy.
    x, y = board_xy(72.0, 15.9)
    proxy = proxy.union(box(18.0, 25.5, 3.2, (x - 9.0, y - 12.75, d["board_top"])))
    # L1 proxy.
    x, y = board_xy(89.0, 41.0)
    proxy = proxy.union(box(6.2, 6.2, 4.8, (x - 3.1, y - 3.1, d["board_top"])))
    # Reset/boot button bodies.
    for kx, ky in [(42.0, 27.0), (46.0, 36.0)]:
        x, y = board_xy(kx, ky)
        proxy = proxy.union(box(6.0, 6.0, 3.6, (x - 3.0, y - 3.0, d["board_top"])))
    return proxy


def shape_stats(name: str, shape: cq.Workplane) -> dict:
    bb = shape.val().BoundingBox()
    return {
        "name": name,
        "bbox_mm": {
            "x": round(bb.xlen, 4),
            "y": round(bb.ylen, 4),
            "z": round(bb.zlen, 4),
            "xmin": round(bb.xmin, 4),
            "ymin": round(bb.ymin, 4),
            "zmin": round(bb.zmin, 4),
            "xmax": round(bb.xmax, 4),
            "ymax": round(bb.ymax, 4),
            "zmax": round(bb.zmax, 4),
        },
        "volume_mm3": round(shape.val().Volume(), 3),
        "solid_count": len(shape.solids().vals()),
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def export_all() -> dict:
    GENERATED.mkdir(parents=True, exist_ok=True)
    tray = build_tray()
    lid = build_lid()
    d = dims()
    # Print orientation: outer lid face flat on the bed, hold-down posts upward.
    lid_print = lid.rotate((0, 0, 0), (1, 0, 0), 180).translate(
        (0, d["outer_y"], P.lid_t)
    )
    board = build_board_proxy()

    shapes = {
        "tray": tray,
        "lid": lid,
        "lid_print": lid_print,
        "board_proxy": board,
    }
    files: list[Path] = []
    for name, shape in shapes.items():
        step = GENERATED / f"{name}.step"
        stl = GENERATED / f"{name}.stl"
        exporters.export(shape, str(step))
        exporters.export(shape, str(stl), tolerance=0.05, angularTolerance=0.15)
        files.extend([step, stl])
        if name in {"tray", "lid_print"}:
            three_mf = GENERATED / f"{name}.3mf"
            exporters.export(shape, str(three_mf))
            files.append(three_mf)

    # Closed assembly for interchange/inspection; printable pieces remain separate.
    assembly = cq.Assembly(name="CoffeeRoast_RevD_Enclosure")
    assembly.add(tray, name="tray", color=cq.Color(0.16, 0.20, 0.25))
    assembly.add(board, name="board_proxy", color=cq.Color(0.05, 0.55, 0.16))
    assembly.add(lid.translate((0, 0, d["tray_h"])), name="lid", color=cq.Color(0.30, 0.35, 0.42))
    assembly_step = GENERATED / "assembly_closed.step"
    assembly.save(str(assembly_step))
    files.append(assembly_step)

    manifest = {
        "status": "PROTOTYPE_NOT_RELEASED",
        "notes": [
            "No PCB mounting holes and no separate guide rails are used.",
            "PCB is retained by a fitted pocket, four underside supports and four lid hold-down pads.",
            "Use lid_print.stl for FDM: outer lid face on the bed, hold-down pads upward.",
            "USB, cable, Q1, C4, switch and insert dimensions marked provisional require physical coupons/measurement.",
            "The enclosure is SELV-only; mains, PSU mains side and SSR load side remain outside/separated.",
        ],
        "cadquery_version": cq.__version__,
        "python_version": platform.python_version(),
        "parameters": asdict(P),
        "derived": {**dims(), "hold_downs_kicad": hold_down_specs()},
        "shapes": [shape_stats(name, shape) for name, shape in shapes.items()],
        "files": {},
    }
    for path in files:
        manifest["files"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}

    manifest_path = GENERATED / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = export_all()
    print(json.dumps(result, indent=2))
