#!/usr/bin/python3
"""Apply the reviewed pinned RevC routing session and deterministic finish routes."""
from pathlib import Path
import hashlib, subprocess
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
BOARD=ROOT/'CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb'
SES=ROOT/'routing'/'freerouting-wide.ses'
EXPECTED='a1631c8342d2f7ba24f94addacc6787d0b86ffb8a6571e19b39cbfd43866734d'
if hashlib.sha256(SES.read_bytes()).hexdigest()!=EXPECTED:raise SystemExit('Pinned routing session hash mismatch')
b=pcbnew.LoadBoard(str(BOARD))
if len(list(b.GetTracks()))>100:
 print('RevC is already routed; no changes made');raise SystemExit(0)
if not pcbnew.ImportSpecctraSES(b,str(SES)):raise SystemExit('Failed to import pinned routing session')
b.BuildConnectivity();pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(BOARD),b)
subprocess.run(['/usr/bin/python3',str(ROOT/'tools'/'finish_routing.py')],check=True,cwd=ROOT)
print('Pinned RevC routing applied')
