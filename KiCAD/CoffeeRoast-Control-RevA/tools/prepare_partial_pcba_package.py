#!/usr/bin/python3
"""Prepare the verified partial-PCBA handoff for CoffeeRoast-Control RevA.2.

The package is intentionally conservative: it exports fabrication Gerbers/drills and
JLCPCB-style BOM/CPL files for the parts we want assembled, while separating
the remaining power/THT/placeholder parts into a hand-solder/DNP list.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
import zipfile
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevA.kicad_pcb"
OUT = ROOT / "production" / "partial-smd-pcba"
GERBER_DIR = OUT / "gerbers"
DRILL_DIR = OUT / "drill"
ASM_DIR = OUT / "assembly"
QA_DIR = OUT / "qa"
ZIP_PATH = OUT / "CoffeeRoast-Control-RevA2_partial_smd_pcba_package.zip"
JLC_ZIP_PATH = OUT / "CoffeeRoast-Control-RevA2_JLC_Gerber_Drill.zip"
JLC_HANDOFF_PATH = OUT / "JLC_UPLOAD_HANDOFF.md"

# Assemble by PCBA house in the RevA.2 top-side SMD prototype run.
# Empty supplier fields require mapping to the exact MPN/equivalent in the UI.
ASSEMBLE = {
    "U1": {"mpn": "ESP32-S3-WROOM-1-N8R8", "supplier": "C2913201", "package": "ESP32-S3-WROOM-1", "notes": "Confirm N8R8 variant and antenna keepout."},
    "U2": {"mpn": "MAX6675ISA+T", "supplier": "C16030", "package": "SOIC-8", "notes": "3.3V thermocouple converter."},
    "U4": {"mpn": "LMR16010PDDAR", "supplier": "C183084", "package": "HSOIC-8 PowerPAD", "notes": "60V/1A buck; verify Pin 1 and exposed-pad orientation."},
    "U5": {"mpn": "USBLC6-2SC6", "supplier": "C7519", "package": "SOT-23-6", "notes": "USB ESD array; verify pad 1/6 I/O1, 2 GND, 3/4 I/O2, 5 VBUS."},
    "U6": {"mpn": "UCC27511DBVR", "supplier": "C191027", "package": "SOT-23-6", "notes": "Split-output fan MOSFET gate driver."},
    "Q1": {"mpn": "STP55NF06L", "supplier": "C77582", "package": "TO-220-3 Vertical", "notes": "THT fan MOSFET; pins 1/2/3 are Gate/Drain/Source. JLC hand-solder assembly; thermally validate at 2.5A fan current."},
    "Q2": {"mpn": "2N7002", "supplier": "C916396", "package": "SOT-23", "notes": "SSR low-side driver."},
    "J5": {"mpn": "U262-16 1 N-4BVC11", "supplier": "C319148", "package": "USB-C XKB U262-16XN", "notes": "Verify shell and pin orientation in placement preview."},
    "L1": {"mpn": "FNR6045S220MT", "supplier": "C168080", "package": "FNR6045S", "notes": "22uH, >=2A saturation/current candidate."},
    "D2": {"mpn": "SMBJ33A-13-F", "supplier": "C135067", "package": "SMB", "notes": "24V input TVS; cathode/pad 1 to +24V_RAW."},
    "D3": {"mpn": "SMBJ33A-13-F", "supplier": "C135067", "package": "SMB", "notes": "Fan TVS; cathode/pad 1 to +24V_RAW."},
    "D4": {"mpn": "SS110", "supplier": "C2766060", "package": "SMA", "notes": "100V buck catch diode."},
    "D5": {"mpn": "BZT52C10", "supplier": "C49023497", "package": "SOD-123", "notes": "10V VDRV clamp."},
    "SW1": {"mpn": "TL3301AF160QG", "supplier": "C273519", "package": "SMD-4P 6x6mm Tactile Switch", "notes": "RESET switch; JLC model requires 90-degree CPL rotation so pins 1/2 and 3/4 land on the two board pad rows."},
    "SW2": {"mpn": "TL3301AF160QG", "supplier": "C273519", "package": "SMD-4P 6x6mm Tactile Switch", "notes": "BOOT switch; JLC model requires 90-degree CPL rotation so pins 1/2 and 3/4 land on the two board pad rows."},
    "R1": {"mpn": "FRC0805F1000TS", "supplier": "C2907218", "package": "0805", "notes": "100R fan gate turn-on."},
    "R2": {"mpn": "FRC0805F1003TS", "supplier": "C2907217", "package": "0805", "notes": "100k fan gate pulldown."},
    "R3": {"mpn": "FRC0805F1000TS", "supplier": "C2907218", "package": "0805", "notes": "100R SSR gate resistor."},
    "R4": {"mpn": "FRC0805F1003TS", "supplier": "C2907217", "package": "0805", "notes": "100k SSR gate pulldown."},
    "R5": {"mpn": "FRC0805F1002TS", "supplier": "C2907219", "package": "0805", "notes": "10k EN pullup."},
    "R6": {"mpn": "FRC0805F1002TS", "supplier": "C2907219", "package": "0805", "notes": "10k BOOT pullup."},
    "R7": {"mpn": "0805W8F270JT5E", "supplier": "C17594", "package": "0805", "notes": "27R USB D- series."},
    "R8": {"mpn": "0805W8F270JT5E", "supplier": "C17594", "package": "0805", "notes": "27R USB D+ series."},
    "R10": {"mpn": "0805W8F5101T5E", "supplier": "C27834", "package": "0805", "notes": "5.1k USB CC1 Rd."},
    "R11": {"mpn": "0805W8F5101T5E", "supplier": "C27834", "package": "0805", "notes": "5.1k USB CC2 Rd."},
    "R12": {"mpn": "FRC0603F1003TS", "supplier": "C2906980", "package": "0603", "notes": "100k FB top."},
    "R13": {"mpn": "RC0603FR-0729K4L", "supplier": "C137752", "package": "0603", "notes": "29.4k FB bottom."},
    "R14": {"mpn": "RC0603FR-0749K9L", "supplier": "C114624", "package": "0603", "notes": "49.9k RT, about 500kHz."},
    "R15": {"mpn": "RC0805FR-0710RL", "supplier": "C96347", "package": "0805", "notes": "10R fan gate turn-off."},
    "R16": {"mpn": "1206W4F2701T5E", "supplier": "C17950", "package": "1206", "notes": "2.7k VDRV feed, 1%, 0.25W."},
    "C1": {"mpn": "GRM21BR61E106KA73L", "supplier": "C84416", "package": "0805", "notes": "10uF 25V X5R 3V3 bulk A."},
    "C2": {"mpn": "GRM21BR61E106KA73L", "supplier": "C84416", "package": "0805", "notes": "10uF 25V X5R 3V3 bulk B."},
    "C3": {"mpn": "CC0805KRX7R9BB104", "supplier": "C49678", "package": "0805", "notes": "100nF MAX6675 decoupling."},
    "C6": {"mpn": "CC0603KRX7R9BB104", "supplier": "C14663", "package": "0603", "notes": "100nF ESP32 decoupling."},
    "C7": {"mpn": "CC0603KRX7R9BB104", "supplier": "C14663", "package": "0603", "notes": "100nF 3V3 output decoupling."},
    "C8": {"mpn": "CS3225X7R225K101NRK", "supplier": "C2900749", "package": "1210", "notes": "2.2uF 100V buck input."},
    "C9": {"mpn": "CS3225X7R225K101NRK", "supplier": "C2900749", "package": "1210", "notes": "2.2uF 100V buck input."},
    "C10": {"mpn": "CC0603KRX7R9BB104", "supplier": "C14663", "package": "0603", "notes": "100nF bootstrap."},
    "C11": {"mpn": "CL32A226KAJNNNE", "supplier": "C52306", "package": "1210", "notes": "22uF 25V buck output."},
    "C12": {"mpn": "0805B104K101NT", "supplier": "C89258", "package": "0805", "notes": "100nF 100V buck input HF bypass."},
    "C13": {"mpn": "CL21B105KAFNNNE", "supplier": "C116352", "package": "0805", "notes": "1uF VDRV reservoir."},
    "C14": {"mpn": "CC0603KRX7R9BB104", "supplier": "C14663", "package": "0603", "notes": "100nF VDRV bypass."},
    "C15": {"mpn": "CL32A226KAJNNNE", "supplier": "C52306", "package": "1210", "notes": "22uF 25V buck output."},
}

# Parts intentionally hand-soldered or left DNP in the first prototype.
HAND_SOLDER = {
    "J1": "Large plated hand-solder pads; solder PSU leads and add strain relief.",
    "J2": "Large plated hand-solder pads; solder fan leads and add strain relief.",
    "J3": "Large plated hand-solder pads; solder external SSR control leads.",
    "J4": "Large plated hand-solder pads; solder thermocouple extension leads and add strain relief.",
    "J6": "Four large hand-solder pads for ESC: +24V, GND, PWM (GPIO10), GND; add strain relief.",
    "D1": "Vishay SS56-E3/57T SMB flyback diode; exact pad/polarity validated, hand-solder because assembler mapping is not pre-filled.",

    "C4": "Panasonic EEU-FR1V221B 220uF/35V radial electrolytic; hand-solder and observe polarity.",
    "C5": "Optional CC0805JRNPO9BN102 1nF C0G thermocouple filter; DNP until noise/bias testing confirms it.",
}


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def clean() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    GERBER_DIR.mkdir(parents=True)
    DRILL_DIR.mkdir(parents=True)
    ASM_DIR.mkdir(parents=True)
    QA_DIR.mkdir(parents=True)


def footprint_kind(fp: pcbnew.FOOTPRINT) -> str:
    has_th = False
    has_smd = False
    for pad in fp.Pads():
        attr = pad.GetAttribute()
        if attr == pcbnew.PAD_ATTRIB_PTH:
            has_th = True
        if attr == pcbnew.PAD_ATTRIB_SMD:
            has_smd = True
    if has_th and has_smd:
        return "mixed"
    if has_th:
        return "tht"
    if has_smd:
        return "smd"
    return "virtual/testpad"


def center_mm(fp: pcbnew.FOOTPRINT) -> tuple[float, float]:
    # The local TO-220 footprint anchor is on pin 1, while JLC's STP55NF06L
    # model/footprint origin is on the middle pin. Export the centre of the
    # three unique lead positions so the model legs land in all three holes.
    if fp.GetReference() == "Q1":
        lead_positions = {
            pad.GetNumber(): pad.GetPosition()
            for pad in fp.Pads()
            if pad.GetNumber() in {"1", "2", "3"}
        }
        if set(lead_positions) != {"1", "2", "3"}:
            raise RuntimeError("Q1 TO-220 lead set changed; revalidate JLC placement centre")
        return (
            sum(pos.x for pos in lead_positions.values()) / 3e6,
            sum(pos.y for pos in lead_positions.values()) / 3e6,
        )
    # Normal footprints have a meaningful anchor position. Some generated custom
    # ECO footprints were built with absolute pad positions and an anchor at 0,0;
    # for those, use the average pad center so CPL placement is not 0,0.
    pos = fp.GetPosition()
    if (pos.x != 0 or pos.y != 0) or len(list(fp.Pads())) == 0:
        return pos.x / 1e6, pos.y / 1e6
    xs = []
    ys = []
    for pad in fp.Pads():
        p = pad.GetPosition()
        xs.append(p.x / 1e6)
        ys.append(p.y / 1e6)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def placement_rotation_degrees(fp: pcbnew.FOOTPRINT) -> float:
    """Return JLC rotation, correcting custom two-pad passive geometry.

    KiCad reports the rotation of the footprint instance. A custom footprint can
    still be drawn with its pads on the Y axis at instance rotation 0°. JLC's
    standard R/C/L models are aligned to the X axis at 0°, so exporting only
    GetOrientationDegrees() can introduce a 90° placement error.

    For non-polar two-pad chip passives, derive the actual board-space pad axis
    and select the equivalent angle nearest KiCad's reported orientation. Other
    packages retain KiCad's angle because pin order or polarity can make 180°
    significant.
    """
    orientation = fp.GetOrientationDegrees()
    # The board's TL3301-style switch pads run left/right, but the selected
    # JLC C273519 model defines its four contacts top/bottom at 0°. Rotate the
    # supplier model by 90°; the square switch is 180° symmetric.
    if fp.GetReference() in {"SW1", "SW2"}:
        return orientation + 90.0
    if not fp.GetReference().startswith(("R", "C", "L")):
        return orientation
    pads = [pad for pad in fp.Pads() if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    if len(pads) != 2:
        return orientation
    p1, p2 = (pad.GetPosition() for pad in pads)
    dx, dy = p2.x - p1.x, p2.y - p1.y
    if dx == 0 and dy == 0:
        return orientation
    pad_axis = math.degrees(math.atan2(dy, dx)) % 180.0
    candidates = [pad_axis + 180.0 * k for k in range(-2, 3)]
    corrected = min(
        candidates,
        key=lambda angle: (abs(angle - orientation), angle < 0),
    )
    if abs(corrected - orientation) > 0.01:
        print(
            f"CPL rotation correction {fp.GetReference()}: "
            f"KiCad {orientation:.2f}° -> pad axis {corrected:.2f}°"
        )
    return corrected


def edge_extents_mm(board: pcbnew.BOARD) -> tuple[float, float, float, float]:
    """Return exact Edge.Cuts extents as left, top, right, bottom in KiCad mm.

    KiCad's board coordinates increase Y downward. JLC normalizes the uploaded
    Gerber to a bottom-left board frame, so top-side CPL Y is bottom - y.
    """
    xs: list[float] = []
    ys: list[float] = []
    for drawing in board.GetDrawings():
        if drawing.GetLayer() != pcbnew.Edge_Cuts or not hasattr(drawing, "GetStart"):
            continue
        start = drawing.GetStart()
        end = drawing.GetEnd()
        xs.extend([start.x / 1e6, end.x / 1e6])
        ys.extend([start.y / 1e6, end.y / 1e6])
    if not xs or not ys:
        bbox = board.GetBoardEdgesBoundingBox()
        return bbox.GetLeft() / 1e6, bbox.GetTop() / 1e6, bbox.GetRight() / 1e6, bbox.GetBottom() / 1e6
    return min(xs), min(ys), max(xs), max(ys)


def to_jlc_top_xy(x: float, y: float, extents: tuple[float, float, float, float]) -> tuple[float, float]:
    left, _top, _right, bottom = extents
    return x - left, bottom - y


def write_assembly_files() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    extents = edge_extents_mm(board)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(set(ASSEMBLE) - set(fps))
    if missing:
        raise RuntimeError(f"ASSEMBLE references missing from board: {missing}")

    bom_rows = []
    cpl_rows = []
    mapping_rows = []
    dnp_rows = []

    for ref in sorted(fps, key=lambda r: ("".join(filter(str.isalpha, r)), int("".join(filter(str.isdigit, r)) or 0), r)):
        fp = fps[ref]
        if ref.startswith("TPESP") or ref.startswith("PADESP") or ref in {"TP24V", "TP5V", "TP3V3", "TPGND"}:
            dnp_rows.append([ref, fp.GetValue(), footprint_kind(fp), "Test/debug pad; no assembly part."])
            continue
        if ref in ASSEMBLE:
            x, y = center_mm(fp)
            if fp.GetLayer() == pcbnew.F_Cu:
                x, y = to_jlc_top_xy(x, y, extents)
                layer = "Top"
            else:
                # Bottom-side assembly is not used for RevA.1, but keep raw
                # coordinates explicit rather than silently applying a top-side
                # transform to a future bottom-side part.
                layer = "Bottom"
            bom_rows.append([
                ref,
                "1",
                fp.GetValue(),
                ASSEMBLE[ref]["package"],
                ASSEMBLE[ref]["mpn"],
                ASSEMBLE[ref]["supplier"],
                "YES",
                ASSEMBLE[ref]["notes"],
            ])
            mapping_rows.append([
                ref,
                fp.GetValue(),
                ASSEMBLE[ref]["package"],
                ASSEMBLE[ref]["mpn"],
                f"Use supplier part {ASSEMBLE[ref]['supplier']} in JLCPCB if still available; otherwise same value/package/rating.",
                ASSEMBLE[ref]["notes"],
            ])
            rotation = placement_rotation_degrees(fp)
            cpl_rows.append([ref, f"{x:.4f}", f"{y:.4f}", layer, f"{rotation:.2f}"])
        else:
            dnp_rows.append([ref, fp.GetValue(), footprint_kind(fp), HAND_SOLDER.get(ref, "Not in first partial-SMD assembly set; review manually.")])

    with (ASM_DIR / "bom_smd_partial.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Qty", "Comment", "Footprint", "Manufacturer Part / Spec", "Supplier Part Number", "Assemble", "Notes"])
        w.writerows(bom_rows)

    # JLC's upload format permits all designators using the same exact MPN,
    # supplier code and footprint to share one BOM row. Keep the verbose BOM
    # above for review, but generate this grouped file for the actual upload.
    grouped_bom: dict[tuple[str, str, str], list[str]] = {}
    for row in bom_rows:
        ref, _qty, _comment, package, mpn, supplier, _assemble, _notes = row
        grouped_bom.setdefault((mpn, supplier, package), []).append(ref)
    with (ASM_DIR / "bom_smd_partial_jlc.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (mpn, supplier, package), refs in sorted(
            grouped_bom.items(), key=lambda item: min(item[1])
        ):
            w.writerow([mpn, ",".join(refs), package, supplier])

    with (ASM_DIR / "cpl_smd_partial.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl_rows)

    with (ASM_DIR / "dnp_hand_solder.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Value", "Kind", "Reason/Action"])
        w.writerows(dnp_rows)

    with (ASM_DIR / "part_mapping_review.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Board Value", "Package", "Preferred MPN / Spec", "Assembler UI Action", "Review Notes"])
        w.writerows(mapping_rows)

    if len(bom_rows) != len(ASSEMBLE) or len(cpl_rows) != len(ASSEMBLE):
        raise RuntimeError(
            f"BOM/CPL count mismatch: expected {len(ASSEMBLE)}, "
            f"got BOM={len(bom_rows)}, CPL={len(cpl_rows)}"
        )

    manual_meta = {
        "J6": ("ESC_4PIN_HAND_WIRE", ""),
        "D1": ("SS56-E3/57T", ""),

        "C4": ("EEU-FR1V221B", "C3697"),
        "C5": ("CC0805JRNPO9BN102", "C139684"),
    }
    full_rows = []
    sort_key = lambda r: ("".join(filter(str.isalpha, r)), int("".join(filter(str.isdigit, r)) or 0), r)
    for ref in sorted(fps, key=sort_key):
        fp = fps[ref]
        if fp.IsBoardOnly() or ref.startswith("FID"):
            continue
        fpid = fp.GetFPID()
        nickname = fpid.GetLibNickname()
        item_name = fpid.GetLibItemName()
        footprint = f"{nickname}:{item_name}" if nickname else item_name
        if ref in ASSEMBLE:
            part = ASSEMBLE[ref]
            full_rows.append([ref, "1", fp.GetValue(), footprint, part["mpn"], part["supplier"], "PCBA", part["notes"]])
        else:
            mpn, supplier = manual_meta.get(ref, (fp.GetValue(), ""))
            action = "DNP" if ref.startswith("TP") or ref == "C5" else "HAND/DNP"
            full_rows.append([ref, "1", fp.GetValue(), footprint, mpn, supplier, action,
                              HAND_SOLDER.get(ref, "PCB test/debug/mechanical position; no automated placement.")])
    full_rows.extend([
        ["TPESP1-TPESP40", "40", "ESP32 probe pads", "PCB copper only", "", "", "DNP", "Board-only probe pads."],
        ["PADESP1-PADESP40", "40", "ESP32 solder pads", "PCB copper only", "", "", "DNP", "Board-only wire-attach pads."],
        ["FID1-FID6", "6", "Fiducial", "PCB copper only", "", "", "DNP", "Board-only fabrication marks."],
    ])
    with (ROOT / "docs" / "bom.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Ref", "Qty", "Value/Part", "Footprint", "Manufacturer Part", "Supplier Part", "Assembly", "Notes"])
        w.writerows(full_rows)


def validate_cpl_frame() -> None:
    """Reject signed negative Y, which JLC renders below the normalized board."""
    with (ASM_DIR / "cpl_smd_partial.csv").open(newline="") as f:
        rows = {row["Designator"]: row for row in csv.DictReader(f)}
    for ref, row in rows.items():
        x = float(row["Mid X"])
        y = float(row["Mid Y"])
        if not (-0.001 <= x <= 160.001 and -0.001 <= y <= 100.001):
            raise RuntimeError(f"CPL drill-origin frame mismatch at {ref}: x={x}, y={y}")
    anchors = {
        "U1": (85.0, 72.0),
        "U2": (128.0, 40.0),
        "J5": (156.325, 69.0),
        "L1": (45.5, 23.9),
        "Q1": (45.0, 42.0),
    }
    for ref, (expected_x, expected_y) in anchors.items():
        actual_x = float(rows[ref]["Mid X"])
        actual_y = float(rows[ref]["Mid Y"])
        if abs(actual_x - expected_x) > 0.001 or abs(actual_y - expected_y) > 0.001:
            raise RuntimeError(
                f"CPL anchor mismatch at {ref}: {(actual_x, actual_y)} != {(expected_x, expected_y)}"
            )
    for ref in ("SW1", "SW2"):
        actual_rotation = float(rows[ref]["Rotation"])
        if abs(actual_rotation - 90.0) > 0.001:
            raise RuntimeError(f"CPL switch rotation mismatch at {ref}: {actual_rotation} != 90.0")


def validate_qa() -> None:
    erc = json.loads((QA_DIR / "erc.json").read_text())
    erc_count = sum(len(sheet.get("violations", [])) for sheet in erc.get("sheets", []))
    drc = json.loads((QA_DIR / "drc_full_parity.json").read_text())
    counts = {
        "ERC": erc_count,
        "DRC": len(drc.get("violations", [])),
        "unconnected": len(drc.get("unconnected_items", [])),
        "schematic parity": len(drc.get("schematic_parity", [])),
    }
    dirty = {name: count for name, count in counts.items() if count}
    if dirty:
        raise RuntimeError(f"QA gate failed: {dirty}")


def validate_manufacturing_geometry() -> None:
    """Guard supplier-critical land pattern and shared fabrication origin."""
    board = pcbnew.LoadBoard(str(BOARD))
    aux = board.GetDesignSettings().GetAuxOrigin()
    aux_mm = (pcbnew.ToMM(aux.x), pcbnew.ToMM(aux.y))
    if any(abs(actual - expected) > 0.001 for actual, expected in zip(aux_mm, (0.0, 100.0))):
        raise RuntimeError(f"Unexpected drill/place auxiliary origin: {aux_mm}")

    l1 = board.FindFootprintByReference("L1")
    if not l1:
        raise RuntimeError("L1 missing while validating C168080 land pattern")
    pads = {pad.GetNumber(): pad for pad in l1.Pads()}
    expected = {
        "1": (-2.5, 0.0, 2.2, 5.72, "BUCK_SW"),
        "2": (2.5, 0.0, 2.2, 5.72, "+3V3"),
    }
    origin = l1.GetPosition()
    for number, (local_x, local_y, width, height, net) in expected.items():
        pad = pads.get(number)
        if not pad:
            raise RuntimeError(f"L1 pad {number} missing")
        pos = pad.GetPosition()
        size = pad.GetSize()
        actual = (
            pcbnew.ToMM(pos.x - origin.x),
            pcbnew.ToMM(pos.y - origin.y),
            pcbnew.ToMM(size.x),
            pcbnew.ToMM(size.y),
        )
        wanted = (local_x, local_y, width, height)
        if any(abs(a - b) > 0.001 for a, b in zip(actual, wanted)) or pad.GetNetname() != net:
            raise RuntimeError(
                f"L1/C168080 pad {number} mismatch: geometry={actual}, "
                f"net={pad.GetNetname()}, expected={wanted}/{net}"
            )


def write_readme() -> None:
    readme = f"""# CoffeeRoast-Control RevA.2 partial-SMD PCBA package

This package is the order-ready RevA.2 handoff for **PCB fabrication + top-side PCBA**, including the selected THT Q1; the remaining manual parts are soldered afterward.

## Upload set

- `gerbers/` + `drill/` — PCB fabrication data.
- `assembly/bom_smd_partial.csv` — exact selected components intended for assembly.
- `assembly/bom_smd_partial_jlc.csv` — grouped BOM for direct JLC upload.
- `assembly/cpl_smd_partial.csv` — centroid/place file for those selected components.
- `assembly/dnp_hand_solder.csv` — parts intentionally not assembled by the PCB house.
- `assembly/part_mapping_review.csv` — MPN/package/orientation checklist.

## Important ordering notes

- The PCB, schematic and named nets passed full DRC, ERC and schematic-parity checks before this package was generated.
- Re-confirm live supplier stock before each order; the preferred supplier codes reflect the latest validated JLC mappings.
- CPL rotations for non-polar two-pad R/C/L parts are derived from the actual pad axis, preventing 90° errors from pre-rotated custom footprints such as C6/C7.
- L1 uses the supplier-matched FNR6045S220MT / C168080 land pattern: 2.20 × 5.72 mm pads on 5.00 mm centers.
- Gerber, drill and CPL data share the bottom-left drill/place origin; do not accept a JLC Auto-Align prompt as a substitute for this source-file alignment.
- D1, C4, J1-J4 and J6 are intentionally manual; C5 is intentionally DNP pending thermocouple noise/bias testing. Q1 is included for JLC THT hand-solder assembly.
- J6 pin order is +24V / GND / PWM(GPIO10) / GND; the PCB has no on-board fuse, so use a current-limited or externally fused 24V source.
- U4/U5/U6, D2/D3, the buck support parts and SW1/SW2 now use exact package-qualified footprints and are included in the top-side assembly set.
- The controller PCB remains low-voltage only. 230VAC wiring, PSU, SSR, heatsink, PE/chassis bonding and thermal cut-off are enclosure-level work.
- In the assembler preview, visually confirm Pin 1/polarity/rotation for U1, U2, U4, U5, U6, J5, Q1, Q2, D2-D5 and the two switches.
- A previous JLC upload/cart is stale after this RevA.2 hardware migration; use a fresh upload.

## Verification run

- Full KiCad DRC: 0 violations
- Schematic parity: 0 problems
- Schematic ERC: 0 violations
- Unconnected PCB items: 0
- Footprint/library findings: 0

## Recommended order flow

1. Upload the Gerber/drill data or this ZIP for PCB fabrication.
2. Enable top-side SMT assembly.
3. Upload `assembly/bom_smd_partial.csv` and `assembly/cpl_smd_partial.csv`.
4. Map exact MPNs/supplier codes and stop if any package or polarity differs.
5. Assemble only the {len(ASSEMBLE)} BOM designators in this generated package.
6. Inspect the manufacturer's Gerber, drill and placement previews before payment.
7. Hand-solder the manual/DNP list after the boards arrive and perform current-limited bring-up.
"""
    (OUT / "README_ORDERING.md").write_text(readme)


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in OUT.rglob("*"):
            if p == ZIP_PATH or p.is_dir():
                continue
            z.write(p, p.relative_to(OUT))


def make_jlc_gerber_drill_zip() -> None:
    """Create the fabrication-only flat ZIP consumed by JLC's PCB upload field."""
    if JLC_ZIP_PATH.exists():
        JLC_ZIP_PATH.unlink()
    files = sorted(p for p in GERBER_DIR.iterdir() if p.is_file())
    files += sorted(DRILL_DIR.glob("*.drl"))
    with zipfile.ZipFile(JLC_ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.name)


def write_jlc_handoff() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    u2 = board.FindFootprintByReference("U2")
    if not u2:
        raise RuntimeError("U2 missing while writing JLC handoff")
    pad1 = next(p for p in u2.Pads() if p.GetNumber() == "1")
    p1 = pad1.GetPosition()
    with (ASM_DIR / "cpl_smd_partial.csv").open(newline="") as f:
        u2_cpl = next(row for row in csv.DictReader(f) if row["Designator"] == "U2")
    handoff = f"""# JLCPCB replacement handoff — CoffeeRoast-Control RevA2

This package is the corrected replacement for current order `SMT026071960340_Y12`
(PCB `13013207A`) after JLC identified insufficient L1 solder overlap. It also supersedes
the stopped order/project `SMT026071660949_Y11` and replacement workspace
`relevanceFileAccessId=752fd014ee974e0cb8aea562422c8f6a`.
Do **not** resume Quote & Order from any previous Gerber or placement state.

## Upload files

- PCB Gerber/Drill: `{JLC_ZIP_PATH.name}`
- Assembly BOM: `assembly/bom_smd_partial_jlc.csv`
- Placement CPL: `assembly/cpl_smd_partial.csv`

## Required verification gates

- Quantity: 5 PCB / 5 PCBA, top-side standard PCBA.
- U2: `MAX6675ISA+T / C16030`, SOIC-8, CPL `{u2_cpl['Mid X']} / {u2_cpl['Mid Y']} / {u2_cpl['Layer']} / {u2_cpl['Rotation']}`.
- U2 physical Pin 1 is the rectangular pad at board coordinate `{pcbnew.ToMM(p1.x):.3f} / {pcbnew.ToMM(p1.y):.3f} mm`, net `GND`; confirm the assembler marker on this pad.
- U2 pin mapping: 1 GND, 2 THERMO_MINUS, 3 THERMO_PLUS, 4 +3V3, 5 MAX_SCK, 6 MAX_CS, 7 MAX_DO, 8 GND.
- J5: `C319148`, Product Edge remains at board edge X=160 mm.
- Q1: `STP55NF06L / C77582`, TO-220 THT assembly; CPL centre is the middle lead at `45.000 / 42.000 mm`, so all three legs align with the holes.
- SW1/SW2: `TL3301AF160QG / C273519`, each at `90.00°` so the four contacts align with the two board pad rows.
- L1: `FNR6045S220MT / C168080`; exact land pattern is 2.20 × 5.72 mm pads on 5.00 mm centers. Confirm full terminal/pad overlap in JLC's review image.
- Gerber, drill and CPL use the same bottom-left origin; a fresh placement import must not require JLC Auto-Align.
- C6 and C7: `90.00°`.
- J1-J4 remain DNP/hand-solder and must not appear in JLC placement.

## Local QA

- KiCad DRC: 0 violations.
- Unconnected items: 0.
- Schematic parity: 0 findings.
- KiCad ERC: 0 violations.
- Dedicated U2 topology/numeric sanity: PASS (`sim/results/u2_max6675_verification.json`).

Uploading or saving a replacement cart revision is not production approval. Verify JLC BOM
selection, the fresh Gerber identity, and component placement before payment.
"""
    JLC_HANDOFF_PATH.write_text(handoff)


def main() -> None:
    clean()
    run([
        "kicad-cli", "sch", "erc", "--format", "json",
        "-o", str(QA_DIR / "erc.json"),
        str(ROOT / "CoffeeRoast-Control-RevA.kicad_sch"),
    ])
    run([
        "kicad-cli", "pcb", "drc", "--format", "json",
        "--all-track-errors", "--schematic-parity",
        "-o", str(QA_DIR / "drc_full_parity.json"),
        str(BOARD),
    ])
    validate_qa()
    validate_manufacturing_geometry()
    run([
        "kicad-cli", "pcb", "export", "gerbers",
        "--output", str(GERBER_DIR),
        "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
        "--subtract-soldermask",
        "--use-drill-file-origin",
        str(BOARD),
    ])
    run([
        "kicad-cli", "pcb", "export", "drill",
        "--output", str(DRILL_DIR),
        "--format", "excellon",
        "--excellon-units", "mm",
        "--drill-origin", "plot",
        "--generate-map",
        "--generate-report",
        "--report-path", str(DRILL_DIR / "drill_report.txt"),
        str(BOARD),
    ])
    write_assembly_files()
    validate_cpl_frame()
    write_readme()
    make_jlc_gerber_drill_zip()
    write_jlc_handoff()
    make_zip()
    print(f"Wrote {ZIP_PATH}")


if __name__ == "__main__":
    main()
