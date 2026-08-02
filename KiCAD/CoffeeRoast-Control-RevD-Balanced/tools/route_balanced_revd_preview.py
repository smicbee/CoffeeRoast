#!/usr/bin/env /usr/bin/python3
"""Create a reproducible two-layer Freerouting preview for RevD Balanced.

This is a routing-review artifact, not a fabrication release. Critical-current,
USB, thermocouple and return-path review is required after import.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
JAR = Path.home() / ".cache/freerouting/freerouting-2.2.4.jar"
JAR_SHA256 = "f5ed374182900ccc78e473518bbb9f6b869f4a07159495f663a76f52bb10523b"

if not JAR.exists():
    raise SystemExit(f"Missing pinned Freerouting jar: {JAR}")
if hashlib.sha256(JAR.read_bytes()).hexdigest() != JAR_SHA256:
    raise SystemExit("Freerouting jar SHA-256 mismatch")

board = pcbnew.LoadBoard(str(BOARD))
if not board:
    raise SystemExit(f"Cannot load {BOARD}")
if len(list(board.GetTracks())) > 100:
    print("RevD routing preview already present; no changes made")
    raise SystemExit(0)

with tempfile.TemporaryDirectory(prefix="coffeeroast-revd-route-") as td:
    dsn = Path(td) / "revd.dsn"
    ses = Path(td) / "revd.ses"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("KiCad DSN export failed")
    subprocess.run([
        "java", "-jar", str(JAR),
        "--gui.enabled=false",
        "-de", str(dsn),
        "-do", str(ses),
        "-mp", "20",
    ], check=True)
    if not ses.exists() or not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit("Freerouting SES import failed")

board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
print(f"RevD routing preview imported: {len(list(board.GetTracks()))} tracks/vias")
