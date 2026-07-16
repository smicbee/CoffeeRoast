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
    "SW1": {"mpn": "TL3301AF160QG", "supplier": "C273519", "package": "TL3301 6x6mm SMD", "notes": "RESET switch."},
    "SW2": {"mpn": "TL3301AF160QG", "supplier": "C273519", "package": "TL3301 6x6mm SMD", "notes": "BOOT switch."},
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

    KiCad's board file coordinates increase Y downward. JLC's placement preview
    for this Gerber upload interprets CPL coordinates from the bottom-left board
    edge, so top-side CPL export must mirror Y using bottom - y.
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
    run([
        "kicad-cli", "pcb", "export", "gerbers",
        "--output", str(GERBER_DIR),
        "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
        "--subtract-soldermask",
        str(BOARD),
    ])
    run([
        "kicad-cli", "pcb", "export", "drill",
        "--output", str(DRILL_DIR),
        "--format", "excellon",
        "--excellon-units", "mm",
        "--generate-map",
        "--generate-report",
        "--report-path", str(DRILL_DIR / "drill_report.txt"),
        str(BOARD),
    ])
    write_assembly_files()
    write_readme()
    make_zip()
    print(f"Wrote {ZIP_PATH}")


if __name__ == "__main__":
    main()
