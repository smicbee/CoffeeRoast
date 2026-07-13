#!/usr/bin/env python3
"""Remove the on-board 24 V fuse and add a four-wire ESC hand-solder header.

J6 pin order is deliberately +24V, GND, ESC_PWM, GND. ESC_PWM uses the
already exposed, output-capable GPIO10; GPIO3/45/46 are avoided because they
are ESP32-S3 strap/input-sensitive pins.
"""
from __future__ import annotations

from pathlib import Path
import sys
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "CoffeeRoast-Control-RevA.kicad_pcb"
LOCAL = ROOT / "CoffeeRoast.pretty"


def nm(value: float) -> int:
    return pcbnew.FromMM(value)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(nm(x), nm(y))


def add_track(board, net, points, width, layer):
    for start, end in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(pt(*start))
        track.SetEnd(pt(*end))
        track.SetWidth(nm(width))
        track.SetLayer(layer)
        track.SetNet(net)
        board.Add(track)


def add_via(board, net, x, y, diameter=0.6, drill=0.3):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pt(x, y))
    via.SetWidth(nm(diameter))
    via.SetDrill(nm(drill))
    via.SetNet(net)
    board.Add(via)


def remove_exact_track(board, net_name, start, end, layer):
    wanted = {start, end}
    for item in list(board.GetTracks()):
        if isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != net_name or item.GetLayer() != layer:
            continue
        a = item.GetStart(); b = item.GetEnd()
        actual = {(round(pcbnew.ToMM(a.x), 4), round(pcbnew.ToMM(a.y), 4)),
                  (round(pcbnew.ToMM(b.x), 4), round(pcbnew.ToMM(b.y), 4))}
        if actual == wanted:
            board.Delete(item)
            return
    raise RuntimeError(f"Expected track not found: {net_name} {start}->{end}")


def add_line(fp, start, end, layer=pcbnew.F_Fab, width=0.1):
    line = pcbnew.PCB_SHAPE(fp)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pt(*start))
    line.SetEnd(pt(*end))
    line.SetLayer(layer)
    line.SetWidth(nm(width))
    fp.Add(line)


def add_text(board, text, x, y, size=1.0):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(pt(x, y))
    item.SetLayer(pcbnew.F_SilkS)
    item.SetTextSize(pt(size, size))
    item.SetTextThickness(nm(0.15))
    item.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(item)


def make_j6(board, nets):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference("J6")
    fp.SetValue("ESC_24V_GND_PWM_GND_GPIO10")
    fp.SetFPID(pcbnew.LIB_ID("CoffeeRoast", "J6_ESC_4Pin_P5.08mm"))
    mapping = {"1": "+24V_RAW", "2": "GND", "3": "GPIO10", "4": "GND"}
    for number, x in (("1", 0.0), ("2", 5.08), ("3", 10.16), ("4", 15.24)):
        pad = pcbnew.PAD(fp)
        pad.SetNumber(number)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT if number == "1" else pcbnew.PAD_SHAPE_CIRCLE)
        if number == "1":
            pad.SetRoundRectRadiusRatio(0.2)
        pad.SetSize(pt(3.2, 3.2))
        pad.SetDrillSize(pt(1.3, 1.3))
        pad.SetPosition(pt(x, 0.0))
        pad.SetNet(nets[mapping[number]])
        fp.Add(pad)
    # Body/courtyard deliberately generous for hand wiring and strain relief.
    add_line(fp, (-2.0, -2.5), (17.24, -2.5))
    add_line(fp, (17.24, -2.5), (17.24, 2.5))
    add_line(fp, (17.24, 2.5), (-2.0, 2.5))
    add_line(fp, (-2.0, 2.5), (-2.0, -2.5))
    fp.Reference().SetLayer(pcbnew.F_SilkS)
    fp.Reference().SetPosition(pt(7.62, -3.8))
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.SetPosition(pt(128.0, 92.0))
    board.Add(fp)
    return fp


def save_local_footprint(fp):
    local = BOARD.parent / "CoffeeRoast.pretty"
    if not local.exists():
        return
    local.mkdir(parents=True, exist_ok=True)
    clone = pcbnew.FOOTPRINT(fp)
    clone.SetPosition(pt(0, 0))
    pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(str(local), clone)


board = pcbnew.LoadBoard(str(BOARD))
if not board:
    raise SystemExit(f"Cannot load board: {BOARD}")

f1 = board.FindFootprintByReference("F1")
j6 = board.FindFootprintByReference("J6")
if not f1 and j6:
    removed = False
    for drawing in list(board.GetDrawings()):
        if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText().strip().upper() == "F1 FUSE":
            board.Delete(drawing)
            removed = True
    if removed:
        pcbnew.SaveBoard(str(BOARD), board)
        print(f"Removed stale F1 silkscreen label from {BOARD}")
    else:
        print(f"Fuse removal / ESC connector pass already present on {BOARD}; no changes made")
    raise SystemExit(0)
if not f1:
    raise RuntimeError("F1 is already absent but J6 is missing; refusing an ambiguous partial migration")
if j6:
    raise RuntimeError("J6 already exists while F1 is still present")

nets = {n.GetNetname(): n for n in board.GetNetInfo().NetsByNetcode().values()}
raw = nets["+24V_RAW"]
fused = nets["+24V_FUSED"]
gpio10 = nets["GPIO10"]
gnd = nets["GND"]

# Merge the former post-fuse rail into the protected-at-enclosure +24 V rail.
for fp in board.GetFootprints():
    if fp.GetReference() == "F1":
        continue
    for pad in fp.Pads():
        if pad.GetNetCode() == fused.GetNetCode():
            pad.SetNet(raw)
for item in board.GetTracks():
    if item.GetNetCode() == fused.GetNetCode():
        item.SetNet(raw)
for zone in board.Zones():
    if zone.GetNetCode() == fused.GetNetCode():
        zone.SetNet(raw)

board.Remove(f1)
for drawing in list(board.GetDrawings()):
    if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText().strip().upper() == "F1 FUSE":
        board.Delete(drawing)
# Bridge the old fuse terminals with a continuous 1.2 mm 24 V path. The former
# vertical EN route crossed this corridor, so move only that segment to B.Cu.
remove_exact_track(board, "EN", (37.0, 10.0), (37.0, 26.0), pcbnew.F_Cu)
add_track(board, nets["EN"], [(37.0, 10.0), (37.0, 16.0)], 0.25, pcbnew.F_Cu)
add_via(board, nets["EN"], 37.0, 16.0)
add_via(board, nets["EN"], 37.0, 20.0)
add_track(board, nets["EN"], [(37.0, 16.0), (37.0, 20.0)], 0.25, pcbnew.B_Cu)
add_track(board, nets["EN"], [(37.0, 20.0), (37.0, 26.0)], 0.25, pcbnew.F_Cu)
add_track(board, raw, [(21.0, 18.0), (43.5, 18.0)], 1.2, pcbnew.F_Cu)
add_via(board, raw, 43.0, 18.0, 1.2, 0.6)

j6 = make_j6(board, {"+24V_RAW": raw, "GPIO10": gpio10, "GND": gnd})
# High-current feed stays on B.Cu near the lower edge; PWM stays on F.Cu.
add_track(board, raw, [(25.0, 72.0), (25.0, 96.0), (124.0, 96.0), (128.0, 92.0)], 1.2, pcbnew.B_Cu)
add_track(board, gpio10, [(111.62, 92.0), (111.62, 88.0), (138.16, 88.0), (138.16, 92.0)], 0.25, pcbnew.F_Cu)
add_text(board, "+24   GND   PWM   GND", 135.62, 87.0, 0.9)

for zone in board.Zones():
    zone.SetNeedRefill(True)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(BOARD), board)
save_local_footprint(j6)
print(f"Removed F1, merged +24V_FUSED into +24V_RAW and added J6 ESC on GPIO10: {BOARD}")
