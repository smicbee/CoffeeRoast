#!/usr/bin/python3
"""Replace autorouter copper for RevB critical-current nets with deliberate wide routes."""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevB-Compact.kicad_pcb"
b = pcbnew.LoadBoard(str(BOARD))
MARKER = "CRITICAL_ROUTES_REVB_V1"

for drawing in b.GetDrawings():
    if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText() == MARKER:
        print("Critical RevB routes already rebuilt; no changes made")
        raise SystemExit(0)

CRITICAL = {"+24V_RAW", "FAN_NEG"}
for item in list(b.GetTracks()):
    if item.GetNetname() in CRITICAL:
        b.Delete(item)


def add(net_name, points, layer, width):
    net = b.FindNet(net_name)
    if not net:
        raise RuntimeError(f"Missing net {net_name}")
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetNet(net)
        t.SetLayer(layer)
        t.SetWidth(pcbnew.FromMM(width))
        t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
        t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
        b.Add(t)


def add_via(net_name, x, y, diameter=1.2, drill=0.6):
    v = pcbnew.PCB_VIA(b)
    v.SetNet(b.FindNet(net_name))
    v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    v.SetWidth(pcbnew.FromMM(diameter))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)

# 24 V field-wiring spine on B.Cu, connected through the PTH pads.
add("+24V_RAW", [(2.96, 66.0), (2.96, 38.04), (5.0, 36.0)], pcbnew.B_Cu, 1.2)

# Input/buck branch on F.Cu. Routes go around the adjacent GND connector pad.
add("+24V_RAW", [(2.96, 66.0), (2.96, 69.0), (14.0, 69.0), (14.0, 66.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(14.0, 66.0), (14.0, 63.0), (23.525, 63.0), (29.5, 63.0), (30.5, 64.0), (31.525, 64.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(31.525, 63.365), (31.525, 64.635)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(23.525, 66.0), (23.525, 60.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(23.525, 60.0), (16.85, 60.0), (16.85, 58.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(23.525, 66.0), (23.525, 70.475), (24.05, 71.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(24.05, 71.0), (23.05, 72.0), (19.0, 72.0)], pcbnew.F_Cu, 1.2)

# Fan supply/protection branch. The horizontal leg stays on B.Cu and changes
# layer at x=11.85 so it cannot cross the FAN_NEG route on F.Cu.
add("+24V_RAW", [(2.96, 52.0), (2.96, 58.0), (11.85, 58.0), (11.85, 49.0)], pcbnew.B_Cu, 1.2)
add_via("+24V_RAW", 11.85, 49.0)
add("+24V_RAW", [(11.85, 49.0), (11.85, 51.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(11.85, 51.0), (11.85, 47.0), (14.85, 47.0), (14.85, 46.0)], pcbnew.F_Cu, 1.2)
add("+24V_RAW", [(14.85, 46.0), (18.538, 42.312), (18.538, 42.0)], pcbnew.F_Cu, 1.2)

# FAN_NEG loop from connector/flyback/TVS to MOSFET. The long lower run
# approaches Q1 pad 2 from below, avoiding adjacent gate pad 1.
add("FAN_NEG", [(8.04, 52.0), (8.04, 55.0), (16.15, 55.0), (16.15, 51.0)], pcbnew.F_Cu, 1.0)
add("FAN_NEG", [(16.15, 51.0), (19.15, 51.0), (19.15, 46.0)], pcbnew.F_Cu, 1.0)
add("FAN_NEG", [(19.15, 46.0), (19.15, 55.0), (38.54, 55.0), (38.54, 49.0)], pcbnew.F_Cu, 1.0)

# Other power/switching nets get conservative but routable widths.
for item in b.GetTracks():
    if isinstance(item, pcbnew.PCB_VIA):
        continue
    if item.GetNetname() == "BUCK_SW":
        item.SetWidth(pcbnew.FromMM(0.8))

b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())

marker = pcbnew.PCB_TEXT(b)
marker.SetText(MARKER)
marker.SetLayer(b.GetLayerID("User.Comments"))
marker.SetPosition(pcbnew.VECTOR2I_MM(1.0, 74.0))
marker.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
b.Add(marker)
pcbnew.SaveBoard(str(BOARD), b)
print("Rebuilt critical-current routes for compact RevB")
