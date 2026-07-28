#!/usr/bin/python3
"""Route compact RevB reproducibly with pinned Freerouting, then rebuild power nets."""
from pathlib import Path
import hashlib
import subprocess
import tempfile
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevB-Compact.kicad_pcb"
JAR = Path.home() / ".cache/freerouting/freerouting-2.2.4.jar"
JAR_SHA256 = "f5ed374182900ccc78e473518bbb9f6b869f4a07159495f663a76f52bb10523b"

if not JAR.exists():
    raise SystemExit(f"Missing pinned Freerouting jar: {JAR}")
if hashlib.sha256(JAR.read_bytes()).hexdigest() != JAR_SHA256:
    raise SystemExit("Freerouting jar SHA-256 mismatch")

board = pcbnew.LoadBoard(str(BOARD))
if not board:
    raise SystemExit(f"Cannot load {BOARD}")

# A completed board is deliberately left unchanged; --force is not provided because
# accidental rerouting of a reviewed production board is worse than an explicit reset.
if len(list(board.GetTracks())) > 100:
    print("Compact RevB already contains routed copper; no changes made")
    raise SystemExit(0)

with tempfile.TemporaryDirectory(prefix="coffeeroast-revb-route-") as td:
    dsn = Path(td) / "revb.dsn"
    ses = Path(td) / "revb.ses"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("KiCad DSN export failed")
    subprocess.run([
        "java", "-jar", str(JAR), "--gui.enabled=false",
        "-de", str(dsn), "-do", str(ses), "-mp", "30",
    ], check=True)
    if not ses.exists() or not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit("Freerouting SES import failed")
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)

subprocess.run(["/usr/bin/python3", str(ROOT / "tools" / "rebuild_critical_routes.py")], check=True)
print("Routed compact RevB and rebuilt critical-current nets")
