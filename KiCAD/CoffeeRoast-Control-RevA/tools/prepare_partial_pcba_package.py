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
    "U1": {"mpn": "ESP32-S3-WROOM-1-N8R8", "package": "ESP32-S3-WROOM-1 module", "notes": "Confirm module variant/flash/PSRAM and antenna keepout before order."},
    "U2": {"mpn": "MAX6675ISA+T or compatible 3.3V SOIC-8 thermocouple converter", "package": "SOIC-8", "notes": "Confirm genuine/compatible part and 3.3V operation."},
    "Q2": {"mpn": "2N7002,215 (Nexperia) or equivalent 2N7002", "package": "SOT-23", "notes": "SOT-23 SSR low-side driver."},
    "J5": {"mpn": "XKB U262-16XN-4BVC11", "package": "USB-C receptacle XKB U262-16XN", "notes": "USB-C data connector; verify assembly catalog footprint/height."},
    "U5": {"mpn": "USBLC6-2SC6 (STMicro) or equivalent USB2 ESD array", "package": "SOT-23-6 / USB2 ESD", "notes": "Replace draft/custom footprint with exact library footprint before production order."},
    "R1": {"mpn": "Yageo RC0805FR-07100RL or equivalent 100R 0805 1%", "package": "0805", "notes": "Fan gate resistor."},
    "R2": {"mpn": "Yageo RC0805FR-07100KL or equivalent 100k 0805 1%", "package": "0805", "notes": "Fan gate pulldown."},
    "R3": {"mpn": "Yageo RC0805FR-07100RL or equivalent 100R 0805 1%", "package": "0805", "notes": "SSR gate resistor."},
    "R4": {"mpn": "Yageo RC0805FR-07100KL or equivalent 100k 0805 1%", "package": "0805", "notes": "SSR gate pulldown."},
    "R5": {"mpn": "Yageo RC0805FR-0710KL or equivalent 10k 0805 1%", "package": "0805", "notes": "EN pullup."},
    "R6": {"mpn": "Yageo RC0805FR-0710KL or equivalent 10k 0805 1%", "package": "0805", "notes": "BOOT pullup."},
    "R7": {"mpn": "Yageo RC0805FR-0727RL or equivalent 27R 0805 1%", "package": "0805", "notes": "USB D- series resistor."},
    "R8": {"mpn": "Yageo RC0805FR-0727RL or equivalent 27R 0805 1%", "package": "0805", "notes": "USB D+ series resistor."},
    "R10": {"mpn": "Yageo RC0805FR-075K1L or equivalent 5.1k 0805 1%", "package": "0805", "notes": "USB-C CC1 Rd."},
    "R11": {"mpn": "Yageo RC0805FR-075K1L or equivalent 5.1k 0805 1%", "package": "0805", "notes": "USB-C CC2 Rd."},
    "C1": {"mpn": "Murata GRM21BR61C106KE15L or equivalent 10uF 0805 X5R/X7R >=16V", "package": "0805", "notes": "5V bulk/decoupling."},
    "C2": {"mpn": "Murata GRM21BR61C106KE15L or equivalent 10uF 0805 X5R/X7R >=16V", "package": "0805", "notes": "3V3 bulk/decoupling."},
    "C3": {"mpn": "Murata GRM21BR71H104KA01L or equivalent 100nF 0805 X7R >=50V", "package": "0805", "notes": "MAX6675 decoupling."},
    "C5": {"mpn": "Murata GRM2165C1H102JA01D or equivalent 1nF 0805 C0G/NP0", "package": "0805", "notes": "Optional thermocouple filter; mark DNP if concerned about measurement bias."},
    "D2": {"mpn": "SMBJ33A-13-F / SMBJ33A or SMAJ33A-class 24V TVS", "package": "SMB/SMA TVS draft", "notes": "Input TVS; exact package must match footprint."},
    "D3": {"mpn": "SMBJ33A-13-F / SMBJ33A or SMAJ33A-class 24V TVS", "package": "SMB/SMA TVS draft", "notes": "Fan clamp TVS; exact package must match footprint."},
}

# Do not ask the PCBA house to place these in the first partial assembly run.
HAND_SOLDER = {
    "J1": "24V input screw terminal / mechanical connector, hand-solder after enclosure choice.",
    "J2": "24V fan screw terminal / mechanical connector, hand-solder after enclosure choice.",
    "J3": "External SSR input screw terminal, hand-solder after SSR wiring choice.",
    "J4": "K-type thermocouple connector, hand-solder after mechanical/strain relief choice.",
    "F1": "24V-side fuse holder, choose exact holder/current rating before soldering.",
    "D1": "Fan flyback diode, THT/power part, hand-solder after fan type is confirmed.",
    "Q1": "Fan power MOSFET, choose final 3.3V-logic package/thermal style; hand-solder for RevA prototype.",
    "U3": "3V3 regulator exact switching-regulator footprint still TBD; do not PCBA-place until RevA.2 regulator is finalized.",
    "U4": "24V->5V buck module exact module/footprint TBD; hand-solder for RevA prototype.",
    "C4": "220uF/35V input bulk capacitor, THT/mechanical part, hand-solder.",
    "SW1": "Reset tactile switch: optional hand-solder; can be omitted if EN pad/debug access is enough.",
    "SW2": "Boot tactile switch: optional hand-solder; can be omitted if BOOT pad/debug access is enough.",
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


def write_assembly_files() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
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
            layer = "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom"
            bom_rows.append([
                ref,
                "1",
                fp.GetValue(),
                ASSEMBLE[ref]["package"],
                ASSEMBLE[ref]["mpn"],
                "MAP_IN_ASSEMBLER_UI",
                "YES",
                ASSEMBLE[ref]["notes"],
            ])
            mapping_rows.append([
                ref,
                fp.GetValue(),
                ASSEMBLE[ref]["package"],
                ASSEMBLE[ref]["mpn"],
                "Use this exact MPN/spec if the assembler catalog has it; otherwise pick same value/package/rating.",
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
- Supplier/LCSC/Mouser part numbers are still blank in the BOM. Map them in the assembler UI before ordering.
- Do not ask the PCB house to place the DNP/hand-solder list for the first prototype.
- `U3` and `U4` are intentionally **not** in the first PCBA placement set because the exact switching-regulator/buck implementation is still the main RevA.2 decision.
- The controller PCB remains low-voltage only. 230VAC wiring, PSU, SSR, heatsink, PE/chassis bonding, and thermal cut-off are enclosure-level work.
- In the assembler UI, visually confirm rotation/orientation for U1 ESP32-S3-WROOM, U2 MAX6675, J5 USB-C, U5 USB ESD, Q2, and TVS diodes.

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
