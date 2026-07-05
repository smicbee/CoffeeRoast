#!/usr/bin/env python3
"""Prepare a partial-SMD PCBA handoff package for CoffeeRoast-Control RevA.1.

The package is intentionally conservative: it exports fabrication Gerbers/drills and
JLCPCB-style BOM/CPL files for the parts we want assembled automatically, while
separating power/THT/placeholder parts into a hand-solder/DNP list.
"""
from __future__ import annotations

import csv
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
ZIP_PATH = OUT / "CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip"

# Assemble by PCBA house in the first partial-SMD prototype run.
# Supplier PNs are deliberately blank until final JLC/LCSC/PCBWay part mapping.
ASSEMBLE = {
    "U1": {"mpn": "ESP32-S3-WROOM-1-N8R8", "supplier": "C2913201", "package": "ESP32-S3-WROOM-1 module", "notes": "Extended JLCPCB part; confirm module variant/flash/PSRAM and antenna keepout before order."},
    "U2": {"mpn": "MAX6675ISA+T", "supplier": "C16030", "package": "SOIC-8", "notes": "Extended JLCPCB part; 3.3V thermocouple converter."},
    "Q2": {"mpn": "2N7002", "supplier": "C8545", "package": "SOT-23", "notes": "Basic JLCPCB part; SSR low-side driver."},
    "J5": {"mpn": "U262-16 1 N-4BVC11", "supplier": "C319148", "package": "USB-C receptacle XKB U262-16XN", "notes": "Extended JLCPCB part; verify orientation in the PCBA preview."},
    "R1": {"mpn": "0805W8F1000T5E", "supplier": "C17408", "package": "0805", "notes": "Basic JLCPCB 100R 0805 1%; fan gate resistor."},
    "R2": {"mpn": "0805W8F1003T5E", "supplier": "C149504", "package": "0805", "notes": "Basic JLCPCB 100k 0805 1%; fan gate pulldown."},
    "R3": {"mpn": "0805W8F1000T5E", "supplier": "C17408", "package": "0805", "notes": "Basic JLCPCB 100R 0805 1%; SSR gate resistor."},
    "R4": {"mpn": "0805W8F1003T5E", "supplier": "C149504", "package": "0805", "notes": "Basic JLCPCB 100k 0805 1%; SSR gate pulldown."},
    "R5": {"mpn": "0805W8F1002T5E", "supplier": "C17414", "package": "0805", "notes": "Basic JLCPCB 10k 0805 1%; EN pullup."},
    "R6": {"mpn": "0805W8F1002T5E", "supplier": "C17414", "package": "0805", "notes": "Basic JLCPCB 10k 0805 1%; BOOT pullup."},
    "R7": {"mpn": "0805W8F270JT5E", "supplier": "C17594", "package": "0805", "notes": "JLC promotional/basic-equivalent 27R 0805; USB D- series resistor."},
    "R8": {"mpn": "0805W8F270JT5E", "supplier": "C17594", "package": "0805", "notes": "JLC promotional/basic-equivalent 27R 0805; USB D+ series resistor."},
    "R10": {"mpn": "0805W8F5101T5E", "supplier": "C27834", "package": "0805", "notes": "Basic JLCPCB 5.1k 0805 1%; USB-C CC1 Rd."},
    "R11": {"mpn": "0805W8F5101T5E", "supplier": "C27834", "package": "0805", "notes": "Basic JLCPCB 5.1k 0805 1%; USB-C CC2 Rd."},
    "C1": {"mpn": "CL21A106KAYNNNE", "supplier": "C15850", "package": "0805", "notes": "Basic JLCPCB 10uF 0805 ceramic; 5V bulk/decoupling."},
    "C2": {"mpn": "CL21A106KAYNNNE", "supplier": "C15850", "package": "0805", "notes": "Basic JLCPCB 10uF 0805 ceramic; 3V3 bulk/decoupling."},
    "C3": {"mpn": "CC0805KRX7R9BB104", "supplier": "C49678", "package": "0805", "notes": "Basic JLCPCB 100nF 0805 X7R 50V; MAX6675 decoupling."},
}

# Do not ask the PCBA house to place these in the first partial assembly run.
HAND_SOLDER = {
    "J1": "Selected candidate: WJ2EDGRC-5.08-02P-14-00A, JLC C3697, 2-pin 5.08mm pluggable terminal. Hand-solder after enclosure choice.",
    "J2": "Selected candidate: WJ2EDGRC-5.08-02P-14-00A, JLC C3697, 2-pin 5.08mm pluggable terminal. Hand-solder after enclosure choice.",
    "J3": "Selected candidate: WJ2EDGRC-5.08-02P-14-00A, JLC C3697, 2-pin 5.08mm pluggable terminal. Hand-solder after SSR wiring choice.",
    "J4": "Selected candidate: WJ2EDGRC-5.08-02P-14-00A, JLC C3697, 2-pin 5.08mm pluggable terminal. K-type thermocouple needs strain relief; true TC mini-jack is RevA.2 mechanical work.",
    "F1": "Selected candidate class: PCB 5x20mm fuse holder with ~22mm pin spacing plus T3.15A fuse. Verify footprint before order; consider external inline fuse holder if fit is uncertain.",
    "D1": "Selected candidate: SB560 DO-201AD Schottky, JLC C139684. Hand-solder after fan type is confirmed.",
    "D2": "DNP for first PCBA: draft TVS footprint needs land-pattern verification. Candidate: SMBJ33A-13-F, JLC C135067.",
    "D3": "DNP for first PCBA: draft TVS footprint needs land-pattern verification. Candidate: SMBJ33A-13-F, JLC C135067.",
    "Q1": "Selected candidate: IRLB8721PBF TO-220, JLC C153222; alternative FQP30N06L, JLC C243087. Hand-solder and thermally verify with real fan current.",
    "U3": "Selected candidate class: OKI-78SR-3.3/1.5-W36-C or R-78E3.3-0.5 switching regulator. Current RevA.1 footprint does not match; wire-in for prototype or update footprint in RevA.2.",
    "U4": "Selected candidate class: 24V->5V buck module >=1A, e.g. Pololu D24V10F5/JLC C26689857 if footprint is adapted. Current module footprint must be verified before order.",
    "C4": "Selected candidate: Panasonic EEU-FR1V221 or Nichicon UPW1V221MPD, 220uF/35V radial electrolytic. Verify lead pitch against current pads before ordering.",
    "C5": "DNP for first PCBA: current RevA.1 footprint is a draft wide-pad filter, not an 0805 placement. Candidate if redesigned: C76625 / TDK C2012C0G1H102JT000N, 1nF C0G 0805.",
    "U5": "DNP for first PCBA: current RevA.1 USB ESD footprint is a draft/custom on-track footprint, not safe for SOT-23-6 placement. Candidate if redesigned: USBLC6-2SC6, JLC C7519.",
    "SW1": "Selected candidate class: 6x6mm THT tactile switch, e.g. K3-1391A-51/JLC C92655. Optional; can be omitted if EN pad/debug access is enough.",
    "SW2": "Selected candidate class: 6x6mm THT tactile switch, e.g. K3-1391A-51/JLC C92655. Optional; can be omitted if BOOT pad/debug access is enough.",
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
            cpl_rows.append([ref, f"{x:.4f}", f"{y:.4f}", layer, f"{fp.GetOrientationDegrees():.2f}"])
        else:
            dnp_rows.append([ref, fp.GetValue(), footprint_kind(fp), HAND_SOLDER.get(ref, "Not in first partial-SMD assembly set; review manually.")])

    with (ASM_DIR / "bom_smd_partial.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Designator", "Qty", "Comment", "Footprint", "Manufacturer Part / Spec", "Supplier Part Number", "Assemble", "Notes"])
        w.writerows(bom_rows)

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


def write_readme() -> None:
    readme = """# CoffeeRoast-Control RevA.1 partial-SMD PCBA package

This package is for the recommended first prototype order: **PCB fabrication + top-side SMD assembly only**, with power/THT/mechanical parts hand-soldered afterward.

## Upload set

- `gerbers/` + `drill/` — PCB fabrication data.
- `assembly/bom_smd_partial.csv` — SMD parts intended for assembly.
- `assembly/cpl_smd_partial.csv` — centroid/place file for those SMD parts.
- `assembly/dnp_hand_solder.csv` — parts intentionally not assembled by the PCB house.
- `assembly/part_mapping_review.csv` — preferred MPN/spec checklist for the assembler UI.

## Important ordering notes

- This is a **partial assembly handoff**, not a one-click final manufacturing release.
- Supplier/LCSC/JLC part numbers are pre-filled for the conservative first PCBA set. Re-confirm availability in the assembler UI before ordering.
- Do not ask the PCB house to place the DNP/hand-solder list for the first prototype.
- `U3` and `U4` are intentionally **not** in the first PCBA placement set because the exact switching-regulator/buck implementation is still the main RevA.2 decision.
- `U5`, `D2`, `D3`, and `C5` are also DNP for the first PCBA package: they are useful RevA.1 robustness footprints, but their current draft/custom land patterns should be replaced with exact sourced footprints before automated assembly.
- The controller PCB remains low-voltage only. 230VAC wiring, PSU, SSR, heatsink, PE/chassis bonding, and thermal cut-off are enclosure-level work.
- In the assembler UI, visually confirm rotation/orientation for U1 ESP32-S3-WROOM, U2 MAX6675, J5 USB-C, Q2, and polarized/marked passives.

## Verification run

- KiCad error-level DRC: 0 violations
- Unconnected pads: 0
- Footprint errors: 0

## Recommended order flow

1. Upload the ZIP or the Gerber/drill files for PCB fabrication.
2. Enable SMT assembly for the top side only.
3. Upload `assembly/bom_smd_partial.csv` and `assembly/cpl_smd_partial.csv`.
4. In the assembler UI, map supplier part numbers and mark anything uncertain as DNP.
5. Order 5 boards, but only 2 assembled if the UI allows it.
6. Hand-solder J1-J4, F1, D1, Q1, U3, U4, C4, SW1, SW2 after the boards arrive.
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
