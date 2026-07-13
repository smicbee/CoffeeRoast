#!/usr/bin/env python3
"""Replace RevA.2 draft land patterns and add exact 60 V buck / fan gate drive.

Run with KiCad's system Python.  The optional first argument is a board copy to
modify; by default the project board is updated.  This pass intentionally keeps
J1-J4 as documented hand-solder wire pads rather than pretending a connector is
fitted.
"""
from __future__ import annotations

from pathlib import Path
import csv
import shutil
import sys
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "CoffeeRoast-Control-RevA.kicad_pcb"
LOCAL = ROOT / "CoffeeRoast.pretty"
LIBROOT = Path("/usr/share/kicad/footprints")


def nm(mm: float) -> int:
    return pcbnew.FromMM(mm)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(nm(x), nm(y))


def xy(item) -> tuple[float, float]:
    p = item.GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def std(spec: str) -> pcbnew.FOOTPRINT:
    lib, name = spec.split(":", 1)
    fp = pcbnew.FootprintLoad(str(LIBROOT / f"{lib}.pretty"), name)
    if not fp:
        raise RuntimeError(f"Footprint not found: {spec}")
    return fp


board = pcbnew.LoadBoard(str(BOARD))
if not board:
    raise SystemExit(f"Cannot load {BOARD}")

# Idempotent no-op after a completed pass.
if board.FindFootprintByReference("U6") or board.FindFootprintByReference("L1"):
    print(f"Exact-hardware pass already present on {BOARD}; no changes made")
    raise SystemExit(0)

nets = {n.GetNetname(): n for n in board.GetNetInfo().NetsByNetcode().values()}


def net(name: str) -> pcbnew.NETINFO_ITEM:
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]


def pads(fp, number: str):
    return [p for p in fp.Pads() if p.GetNumber() == str(number)]


def pad(fp, number: str):
    found = pads(fp, number)
    if not found:
        raise RuntimeError(f"{fp.GetReference()} has no pad {number}")
    return found[0]


def set_pad_nets(fp, mapping: dict[str, str]) -> None:
    for p in fp.Pads():
        number = p.GetNumber()
        if number in mapping:
            p.SetNet(net(mapping[number]))
        elif number:
            p.SetNetCode(0)


def add_fp(ref: str, value: str, spec: str, x: float, y: float, angle: float, mapping: dict[str, str]):
    fp = std(spec)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pt(x, y))
    fp.SetOrientationDegrees(angle)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    set_pad_nets(fp, mapping)
    board.Add(fp)
    return fp


def strip_front_silk(fp) -> None:
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() == pcbnew.F_SilkS:
            fp.Delete(item)


def add_track(net_name: str, points: list[tuple[float, float]], width: float = 0.25, layer=pcbnew.F_Cu):
    n = net(net_name)
    for a, b in zip(points, points[1:]):
        if a == b:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(*a)); t.SetEnd(pt(*b)); t.SetWidth(nm(width)); t.SetLayer(layer); t.SetNet(n)
        board.Add(t)


def add_via(net_name: str, x: float, y: float, diameter: float = 0.6, drill: float = 0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y)); v.SetWidth(nm(diameter)); v.SetDrill(nm(drill)); v.SetNet(net(net_name))
    board.Add(v)
    return v


def ground_pad_to_via(fp, number: str, vx: float, vy: float) -> None:
    add_track("GND", [xy(pad(fp, number)), (vx, vy)], 0.35)
    add_via("GND", vx, vy, 0.6, 0.3)


def remove_tracks(net_name: str, x1: float, y1: float, x2: float, y2: float) -> None:
    while True:
        victim = None
        for item in board.GetTracks():
            if item.GetNetname() != net_name:
                continue
            points = [item.GetPosition()] if isinstance(item, pcbnew.PCB_VIA) else [item.GetStart(), item.GetEnd()]
            if all(x1 <= pcbnew.ToMM(p.x) <= x2 and y1 <= pcbnew.ToMM(p.y) <= y2 for p in points):
                victim = item; break
        if victim is None:
            return
        board.Delete(victim)


def remove_tracks_intersecting(net_name: str, x1: float, y1: float, x2: float, y2: float) -> None:
    while True:
        victim = None
        for item in board.GetTracks():
            if item.GetNetname() != net_name:
                continue
            points = [item.GetPosition()] if isinstance(item, pcbnew.PCB_VIA) else [item.GetStart(), item.GetEnd()]
            if any(x1 <= pcbnew.ToMM(p.x) <= x2 and y1 <= pcbnew.ToMM(p.y) <= y2 for p in points):
                victim = item; break
        if victim is None:
            return
        board.Delete(victim)


def remove_all_tracks(net_name: str) -> None:
    while True:
        victim = next((item for item in board.GetTracks() if item.GetNetname() == net_name), None)
        if victim is None:
            return
        board.Delete(victim)


def remove_tracks_on_layer(net_name: str, layer: int, x1: float, y1: float, x2: float, y2: float) -> None:
    while True:
        victim = None
        for item in board.GetTracks():
            if item.GetNetname() != net_name or isinstance(item, pcbnew.PCB_VIA) or item.GetLayer() != layer:
                continue
            points = [item.GetStart(), item.GetEnd()]
            if any(x1 <= pcbnew.ToMM(p.x) <= x2 and y1 <= pcbnew.ToMM(p.y) <= y2 for p in points):
                victim = item; break
        if victim is None:
            return
        board.Delete(victim)


def replace_std(ref: str, value: str, spec: str, origin: tuple[float, float], angle: float,
                mapping: dict[str, str] | None = None, link_width: float = 0.25):
    old = board.FindFootprintByReference(ref)
    if not old:
        raise RuntimeError(f"Missing {ref}")
    old_by_num: dict[str, list[tuple[float, float, str]]] = {}
    for p in old.Pads():
        old_by_num.setdefault(p.GetNumber(), []).append((*xy(p), p.GetNetname()))
    if mapping is None:
        mapping = {num: entries[0][2] for num, entries in old_by_num.items() if num and entries[0][2]}
    board.Remove(old)
    fp = add_fp(ref, value, spec, *origin, angle, mapping)
    # Preserve routed copper by linking each moved land to the nearest former
    # same-number/same-net land.  DRC catches any unsafe link geometry.
    for p in fp.Pads():
        candidates = [q for q in old_by_num.get(p.GetNumber(), []) if q[2] == p.GetNetname()]
        if not candidates:
            continue
        px, py = xy(p)
        ox, oy, _ = min(candidates, key=lambda q: (q[0]-px)**2 + (q[1]-py)**2)
        if abs(px-ox) > 0.001 or abs(py-oy) > 0.001:
            add_track(p.GetNetname(), [(ox, oy), (px, py)], link_width)
    return fp, old_by_num


# Exact package replacements.  Origin is the library footprint origin (usually pin 1).
f1_old = board.FindFootprintByReference("F1")
f1_old_pads = {p.GetNumber(): (*xy(p), p.GetNetname()) for p in f1_old.Pads()}
board.Remove(f1_old)

# Littelfuse 65600001009: 22.5 mm pitch, 0.4 x 1.1 mm solder tabs.
f1 = pcbnew.FOOTPRINT(board)
f1.SetReference("F1"); f1.SetValue("Littelfuse_65600001009")
f1.SetFPID(pcbnew.LIB_ID("", "F1_Littelfuse_65600001009"))
for num, x in (("1", 0.0), ("2", 22.5)):
    p = pcbnew.PAD(f1); p.SetNumber(num); p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(pcbnew.PAD_SHAPE_OVAL); p.SetSize(pt(2.4, 1.8)); p.SetDrillSize(pt(1.4, 0.8)); p.SetPosition(pt(x, 0))
    p.SetNet(net("+24V_RAW" if num == "1" else "+24V_FUSED")); f1.Add(p)
for y in (-4.8, 4.8):
    s = pcbnew.PCB_SHAPE(f1); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(pt(-1.5, y)); s.SetEnd(pt(24.0, y)); s.SetLayer(pcbnew.F_Fab); s.SetWidth(nm(0.1)); f1.Add(s)
for x in (-1.5, 24.0):
    s = pcbnew.PCB_SHAPE(f1); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(pt(x, -4.8)); s.SetEnd(pt(x, 4.8)); s.SetLayer(pcbnew.F_Fab); s.SetWidth(nm(0.1)); f1.Add(s)
f1.SetPosition(pt(21.0, 18.0))
f1.Reference().SetLayer(pcbnew.F_Fab)
board.Add(f1)
for num, old in f1_old_pads.items():
    p = pad(f1, num); add_track(p.GetNetname(), [(old[0], old[1]), xy(p)], 1.2)

# Correct flyback polarity: KiCad diode pad 1 is K and therefore belongs on +24 V.
remove_all_tracks("FAN_NEG")
remove_all_tracks("FAN_GATE")
remove_tracks_intersecting("GND", 34.0, 38.0, 70.0, 67.0)
remove_tracks_intersecting("+24V_FUSED", 5.0, 39.0, 40.0, 47.0)
remove_tracks_on_layer("+24V_FUSED", pcbnew.F_Cu, 5.0, 45.0, 35.0, 55.0)
d1, _ = replace_std("D1", "SS56-E3/57T", "Diode_SMD:D_SMB", (10.0, 53.0), 0,
                    {"1": "+24V_FUSED", "2": "FAN_NEG"}, link_width=1.0)
d2, _ = replace_std("D2", "SMBJ33A", "Diode_SMD:D_SMB", (15.0, 29.5), 0, link_width=1.0)
d3, _ = replace_std("D3", "SMBJ33A", "Diode_SMD:D_SMB", (20.0, 39.0), 0,
                    {"1": "+24V_FUSED", "2": "FAN_NEG"}, link_width=1.0)
# Replacements can add compatibility links; this stage is routed deliberately below.
remove_all_tracks("FAN_NEG")
remove_tracks_intersecting("+24V_FUSED", 5.0, 37.0, 32.0, 46.0)
c4, _ = replace_std("C4", "EEU-FR1V221B_220uF_35V", "Capacitor_THT:CP_Radial_D8.0mm_P5.00mm", (7.46, 23.2), 0, link_width=1.0)
strip_front_silk(c4)
replace_std("C5", "CC0805JRNPO9BN102_1nF_C0G", "Capacitor_SMD:C_0805_2012Metric", (140.0, 47.0), 0, link_width=0.25)

# Exact SMT tact switches are moved into the clear top-edge service area.
old_sw1 = board.FindFootprintByReference("SW1"); old_sw2 = board.FindFootprintByReference("SW2")
board.Remove(old_sw1); board.Remove(old_sw2)
sw1 = add_fp("SW1", "TL3301AF160QG_RESET", "Button_Switch_SMD:SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG", 50.0, 8.0, 0,
             {"1": "EN", "2": "GND"})
sw2 = add_fp("SW2", "TL3301AF160QG_BOOT", "Button_Switch_SMD:SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG", 28.0, 28.0, 0,
             {"1": "BOOT", "2": "GND"})
add_track("EN", [(40.75, 29.75), (37.0, 26.0), (37.0, 10.0), (43.0, 6.0), (45.45, 5.75)], 0.25)
add_track("BOOT", [(40.75, 39.75), (30.0, 39.75), (20.0, 35.0), (20.0, 25.75), (23.45, 25.75)], 0.25)

q1, _ = replace_std("Q1", "STP55NF06L", "Package_TO_SOT_THT:TO-220-3_Vertical", (42.46, 58.0), 0,
            {"1": "FAN_GATE", "2": "FAN_NEG", "3": "GND"}, link_width=1.0)
add_track("+24V_FUSED", [(7.46, 48.0), xy(pad(d1, "1"))], 1.0)
add_track("FAN_NEG", [(12.54, 48.0), xy(pad(d1, "2"))], 1.0)
add_track("FAN_NEG", [(12.54, 48.0), (18.0, 44.0), (30.0, 44.0), (36.0, 50.0), (45.0, 50.0), (45.0, 58.0)], 1.0)
add_track("FAN_NEG", [xy(pad(d3, "2")), (16.0, 43.0), (12.54, 48.0)], 1.0)
add_track("+24V_FUSED", [xy(pad(d3, "1")), (14.0, 41.0), (7.46, 48.0)], 1.0)
# Restore the fan-output high-side feed on B.Cu after clearing the old crossing.
add_track("+24V_FUSED", [(7.46, 48.0), (7.46, 58.0), (18.0, 68.0), (25.0, 70.798)], 1.0, pcbnew.B_Cu)

# USBLC6-2SC6 pinout: 1/6 I/O1, 2 GND, 3/4 I/O2, 5 VBUS.
old_u5 = board.FindFootprintByReference("U5")
board.Remove(old_u5)
u5 = add_fp("U5", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", 142.0, 22.0, 0,
            {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "USB_VBUS", "6": "USB_DN"})
# Join each duplicated pass-through pair on F.Cu, then leave the dense USB
# corridor on separate B.Cu paths.
add_track("USB_DN", [xy(pad(u5, "1")), xy(pad(u5, "6")), (145.0, 21.05)], 0.2)
add_via("USB_DN", 145.0, 21.05, 0.55, 0.3)
add_track("USB_DN", [(145.0, 21.05), (143.5, 25.0), (143.5, 29.0), (139.894, 31.625)], 0.2, pcbnew.B_Cu)
add_track("USB_DP", [xy(pad(u5, "3")), xy(pad(u5, "4")), (139.5, 22.95)], 0.2)
add_via("USB_DP", 139.5, 22.95, 0.55, 0.3)
add_track("USB_DP", [(139.5, 22.95), (136.0, 25.0), (136.0, 31.0)], 0.2, pcbnew.B_Cu)
add_via("USB_DP", 136.0, 31.0, 0.55, 0.3)
add_track("GND", [xy(pad(u5, "2")), (138.5, 22.0)], 0.2)
add_via("GND", 138.5, 22.0, 0.55, 0.3)
add_track("USB_VBUS", [xy(pad(u5, "5")), (146.0, 23.0), (148.0, 23.0)], 0.2)
add_via("USB_VBUS", 148.0, 23.0, 0.55, 0.3)
add_track("USB_VBUS", [(148.0, 23.0), (148.0, 29.341), (151.454, 29.341)], 0.2, pcbnew.B_Cu)
add_via("USB_VBUS", 151.454, 29.341, 0.55, 0.3)

# Remove the generic four-pin buck footprint, retaining its routed rail anchors.
old_u4 = board.FindFootprintByReference("U4")
old_u4_pads = {p.GetNumber(): (*xy(p), p.GetNetname()) for p in old_u4.Pads()}
board.Remove(old_u4)
# Old module ground straps crossed the compact regulator land pattern; the F.Cu
# ground zone is the intended return plane for the new stage.
remove_tracks("GND", 20.0, 70.0, 60.0, 89.0)
for name in ("BUCK_BOOT", "BUCK_SW", "BUCK_FB", "BUCK_RT", "VDRV10", "FAN_GATE_ON", "FAN_GATE_OFF"):
    net(name)

# 60 V / 1 A buck, TI datasheet's 24 V -> 3.3 V, 500 kHz, 22 uH, 47 uF design.
u4 = add_fp("U4", "LMR16010PDDAR", "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm", 36.0, 78.0, 0,
            {"1": "BUCK_BOOT", "2": "+24V_FUSED", "3": "+24V_FUSED", "4": "BUCK_RT", "5": "BUCK_FB", "6": "U4_PGOOD_NC", "7": "GND", "8": "BUCK_SW", "9": "GND"})
for vx in (35.4, 36.6):
    for vy in (77.2, 78.8):
        add_via("GND", vx, vy, 0.6, 0.3)
l1 = add_fp("L1", "FNR6045S220MT_22uH_2A", "Inductor_SMD:L_Changjiang_FNR6045S", 45.5, 76.1, 0, {"1": "BUCK_SW", "2": "+3V3"})
d4 = add_fp("D4", "SS110_100V", "Diode_SMD:D_SMA", 41.0, 70.0, 0, {"1": "BUCK_SW", "2": "GND"})
c8 = add_fp("C8", "2.2uF_100V_X7R", "Capacitor_SMD:C_1210_3225Metric", 29.0, 74.0, 0, {"1": "+24V_FUSED", "2": "GND"})
c9 = add_fp("C9", "2.2uF_100V_X7R", "Capacitor_SMD:C_1210_3225Metric", 29.0, 80.0, 0, {"1": "+24V_FUSED", "2": "GND"})
c12 = add_fp("C12", "100nF_100V_X7R", "Capacitor_SMD:C_0805_2012Metric", 29.0, 84.5, 0, {"1": "+24V_FUSED", "2": "GND"})
c10 = add_fp("C10", "100nF_50V_X7R_BOOT", "Capacitor_SMD:C_0603_1608Metric", 35.0, 73.0, 0, {"1": "BUCK_BOOT", "2": "BUCK_SW"})
c11 = add_fp("C11", "22uF_25V_X5R", "Capacitor_SMD:C_1210_3225Metric", 50.0, 68.0, 0, {"1": "+3V3", "2": "GND"})
c15 = add_fp("C15", "22uF_25V_X5R", "Capacitor_SMD:C_1210_3225Metric", 55.0, 68.0, 0, {"1": "+3V3", "2": "GND"})
r12 = add_fp("R12", "100k_1%_FB_TOP", "Resistor_SMD:R_0603_1608Metric", 42.0, 82.0, 0, {"1": "BUCK_FB", "2": "+3V3"})
r13 = add_fp("R13", "29.4k_1%_FB_BOTTOM", "Resistor_SMD:R_0603_1608Metric", 39.0, 85.5, 270, {"1": "BUCK_FB", "2": "GND"})
r14 = add_fp("R14", "49.9k_1%_RT_500kHz", "Resistor_SMD:R_0603_1608Metric", 33.0, 85.5, 270, {"1": "BUCK_RT", "2": "GND"})

# Buck routing: short hot loop, feedback kept below/away from SW node.
add_track("+24V_FUSED", [(old_u4_pads["1"][0], old_u4_pads["1"][1]), xy(pad(c8, "1")), xy(pad(c9, "1")), xy(pad(c12, "1"))], 1.0)
add_track("+24V_FUSED", [(27.525, 77.365), xy(pad(u4, "2")), xy(pad(u4, "3"))], 1.0)
add_track("BUCK_BOOT", [xy(pad(u4, "1")), xy(pad(c10, "1"))], 0.3)
add_track("BUCK_SW", [xy(pad(c10, "2")), xy(pad(u4, "8")), xy(pad(l1, "1"))], 0.8)
add_track("BUCK_SW", [xy(pad(u4, "8")), xy(pad(d4, "1"))], 0.8)
add_track("+3V3", [xy(pad(l1, "2")), (48.0, 74.0), (old_u4_pads["3"][0], old_u4_pads["3"][1])], 0.8)
add_track("+3V3", [(47.0, 72.0), (47.0, 68.0), xy(pad(c11, "1"))], 0.8)
add_track("+3V3", [(53.0, 72.0), xy(pad(c15, "1"))], 0.8)
add_track("BUCK_FB", [xy(pad(u4, "5")), (40.0, 82.0), xy(pad(r12, "1"))], 0.25)
add_track("BUCK_FB", [(40.0, 82.0), xy(pad(r13, "1"))], 0.25)
add_track("+3V3", [xy(pad(r12, "2")), (45.0, 82.0), (47.0, 80.0), (47.0, 68.0)], 0.25)
add_track("BUCK_RT", [xy(pad(u4, "4")), (33.0, 82.0), xy(pad(r14, "1"))], 0.25)

# Gate driver: 3.3 V MCU input, 10 V local bias derived from fused 24 V.
old_r1 = board.FindFootprintByReference("R1"); old_r2 = board.FindFootprintByReference("R2")
board.Remove(old_r1); board.Remove(old_r2)
r1 = add_fp("R1", "100R_GATE_TURN_ON", "Resistor_SMD:R_0805_2012Metric", 37.0, 55.0, 0, {"1": "FAN_GATE_ON", "2": "FAN_GATE"})
r15 = add_fp("R15", "10R_GATE_TURN_OFF", "Resistor_SMD:R_0805_2012Metric", 39.0, 61.0, 0, {"1": "FAN_GATE_OFF", "2": "FAN_GATE"})
r2 = add_fp("R2", "100k_GATE_PULLDOWN", "Resistor_SMD:R_0805_2012Metric", 42.0, 64.0, 270, {"1": "FAN_GATE", "2": "GND"})
u6 = add_fp("U6", "UCC27511DBVR", "Package_TO_SOT_SMD:SOT-23-6", 35.0, 59.0, 0,
            {"1": "VDRV10", "2": "FAN_GATE_ON", "3": "FAN_GATE_OFF", "4": "GND", "5": "GND", "6": "FAN_PWM"})
r16 = add_fp("R16", "2.7k_1%_250mW", "Resistor_SMD:R_1206_3216Metric", 24.0, 66.0, 0, {"1": "+24V_FUSED", "2": "VDRV10"})
d5 = add_fp("D5", "BZT52C10_10V", "Diode_SMD:D_SOD-123", 29.0, 66.0, 0, {"1": "VDRV10", "2": "GND"})
c13 = add_fp("C13", "1uF_25V_X7R_VDRV", "Capacitor_SMD:C_0805_2012Metric", 34.0, 66.0, 0, {"1": "VDRV10", "2": "GND"})
c14 = add_fp("C14", "100nF_50V_X7R_VDRV", "Capacitor_SMD:C_0603_1608Metric", 30.0, 60.0, 0, {"1": "VDRV10", "2": "GND"})
add_track("FAN_PWM", [(64.05, 48.0), (70.0, 44.0), (52.0, 44.0)], 0.25)
add_via("FAN_PWM", 52.0, 44.0, 0.55, 0.3)
add_track("FAN_PWM", [(52.0, 44.0), (44.0, 50.0), (37.0, 57.0)], 0.25, pcbnew.B_Cu)
add_via("FAN_PWM", 37.0, 57.0, 0.55, 0.3)
add_track("FAN_PWM", [(37.0, 57.0), xy(pad(u6, "6"))], 0.25)
add_track("FAN_GATE_ON", [xy(pad(u6, "2")), (35.0, 59.0), (35.0, 55.0), xy(pad(r1, "1"))], 0.35)
add_track("FAN_GATE_OFF", [xy(pad(u6, "3")), (35.0, 61.0), xy(pad(r15, "1"))], 0.35)
add_track("FAN_GATE", [xy(pad(r1, "2")), (40.0, 55.0), (42.46, 58.0)], 0.35)
add_track("FAN_GATE", [xy(pad(r15, "2")), (41.0, 61.0), (42.46, 58.0)], 0.35)
add_track("FAN_GATE", [xy(pad(r2, "1")), (42.0, 60.0), (42.46, 58.0)], 0.35)
add_track("+24V_FUSED", [(7.46, 58.0), (18.0, 68.0), xy(pad(r16, "1"))], 1.0, pcbnew.B_Cu)
add_via("+24V_FUSED", *xy(pad(r16, "1")), 1.2, 0.6)
add_track("VDRV10", [xy(pad(r16, "2")), xy(pad(d5, "1"))], 0.35)
add_track("VDRV10", [xy(pad(d5, "1")), (27.35, 63.0), (33.05, 63.0), xy(pad(c13, "1"))], 0.35)
add_track("VDRV10", [(27.35, 63.0), (29.225, 63.0), xy(pad(c14, "1"))], 0.35)
add_track("VDRV10", [xy(pad(c14, "1")), (29.225, 58.05), xy(pad(u6, "1"))], 0.35)

# Remove old switch/module ground remnants before adding the replacement
# stitching network; otherwise they form diagonal copper obstacles.
remove_tracks_on_layer("GND", pcbnew.F_Cu, 13.0, 17.0, 31.0, 35.0)
remove_tracks_intersecting("GND", 12.4, 23.0, 12.7, 26.3)
remove_tracks_intersecting("GND", 35.0, 33.0, 50.0, 35.5)
remove_tracks_intersecting("GND", 48.0, 84.0, 80.0, 89.0)
remove_tracks_on_layer("EN", pcbnew.B_Cu, 45.0, 26.0, 55.0, 31.0)

# Explicit GND stitching.  This avoids isolated F.Cu-zone islands around the
# dense switcher and driver while keeping the signal/power return topology clear.
for p in pads(sw1, "2"):
    add_track("GND", [xy(p), (50.0, 10.25)], 0.35)
add_via("GND", 50.0, 12.0, 0.6, 0.3)
add_track("GND", [(50.0, 10.25), (50.0, 12.0)], 0.35)
for p in pads(sw2, "2"):
    add_track("GND", [xy(p), (28.0, 30.25)], 0.35)
add_via("GND", 28.0, 32.0, 0.6, 0.3)
add_track("GND", [(28.0, 30.25), (28.0, 32.0)], 0.35)
ground_pad_to_via(d2, "2", 18.0, 31.5)
add_track("GND", [(12.46, 23.2), (18.0, 31.5), (28.0, 32.0)], 0.5, pcbnew.B_Cu)
add_track("GND", [(12.46, 23.2), (20.0, 8.0), (40.0, 8.0), (50.0, 12.0)], 0.5, pcbnew.B_Cu)

# Gate-driver ground cluster to Q1 source.
add_track("GND", [xy(pad(u6, "5")), (38.0, 59.0), (40.0, 59.0)], 0.35)
add_track("GND", [xy(pad(u6, "4")), (38.0, 60.0), (40.0, 59.0)], 0.35)
add_via("GND", 40.0, 59.0, 0.6, 0.3)
ground_pad_to_via(c14, "2", 30.8, 61.5)
ground_pad_to_via(d5, "2", 30.65, 67.5)
ground_pad_to_via(c13, "2", 34.95, 67.5)
ground_pad_to_via(r2, "2", 42.0, 66.0)
add_track("GND", [(30.65, 67.5), (34.95, 67.5), (42.0, 66.0), (47.54, 58.0)], 0.5, pcbnew.B_Cu)
add_track("GND", [(30.8, 61.5), (24.0, 56.0), (18.0, 45.0), (18.0, 31.5)], 0.5, pcbnew.B_Cu)
add_track("GND", [(40.0, 59.0), (42.0, 66.0)], 0.5, pcbnew.B_Cu)

# Buck/input/output ground cluster to the existing TPGND through-hole.
ground_pad_to_via(c8, "2", 31.5, 73.0)
ground_pad_to_via(c9, "2", 31.5, 81.0)
ground_pad_to_via(c12, "2", 31.0, 85.5)
ground_pad_to_via(r13, "2", 39.0, 87.5)
ground_pad_to_via(r14, "2", 33.0, 87.5)
ground_pad_to_via(d4, "2", 44.0, 69.0)
ground_pad_to_via(c11, "2", 51.5, 69.5)
ground_pad_to_via(c15, "2", 56.5, 69.5)
add_track("GND", [xy(pad(u4, "7")), (36.6, 77.2)], 0.5)
add_track("GND", [(31.5, 73.0), (31.5, 81.0), (31.0, 85.5), (33.0, 87.5), (39.0, 87.5), (58.0, 84.0)], 0.5, pcbnew.B_Cu)
add_track("GND", [(36.6, 77.2), (44.0, 69.0), (51.5, 69.5), (56.5, 69.5), (53.0, 73.4), (58.0, 84.0)], 0.5, pcbnew.B_Cu)
add_track("GND", [(42.0, 66.0), (44.0, 69.0)], 0.5, pcbnew.B_Cu)

# Tie duplicated switch contacts and the remaining debug/test ground islands.
add_track("EN", [xy(pads(sw1, "1")[0]), xy(pads(sw1, "1")[1])], 0.25)
add_track("BOOT", [xy(pads(sw2, "1")[0]), xy(pads(sw2, "1")[1])], 0.25)
tpboot = board.FindFootprintByReference("TPBOOT1")
tpreset = board.FindFootprintByReference("TPRESET1")
ground_pad_to_via(tpboot, "2", 37.0, 43.25)
ground_pad_to_via(tpreset, "2", 37.0, 33.25)
add_track("GND", [(37.0, 43.25), (37.0, 33.25), (40.0, 25.0), (50.0, 12.0)], 0.5, pcbnew.B_Cu)
c7 = board.FindFootprintByReference("C7")
add_via("GND", *xy(pad(c7, "2")), 0.6, 0.3)
tpgnd = board.FindFootprintByReference("TPGND")
add_via("GND", *xy(pad(tpgnd, "1")), 0.6, 0.3)
c1 = board.FindFootprintByReference("C1")
ground_pad_to_via(c1, "2", 64.0, 87.5)
add_track("GND", [(64.0, 87.5), xy(pad(tpgnd, "1"))], 0.5, pcbnew.B_Cu)
c2 = board.FindFootprintByReference("C2")
ground_pad_to_via(c2, "2", 79.0, 87.5)
add_track("GND", [(79.0, 87.5), (64.0, 87.5)], 0.5, pcbnew.B_Cu)
# Restore the PCB-only EN debug pad branch without a via-in-resistor-pad.
r5 = board.FindFootprintByReference("R5"); padesp3 = board.FindFootprintByReference("PADESP3")
add_track("EN", [xy(pad(r5, "2")), (57.0, 31.0)], 0.25)
add_via("EN", 57.0, 31.0, 0.55, 0.3)
add_track("EN", [(57.0, 31.0), xy(pad(padesp3, "1"))], 0.25, pcbnew.B_Cu)

# The retired EN branch is now intentionally reused for PADESP3; no broad
# cleanup is applied here because it would also remove the restored branch.
add_via("+24V_FUSED", 25.0, 72.0, 1.2, 0.6)

# Keep the original human-readable board labels, but move those whose old
# locations belonged to the replaced draft footprints.
text_positions = {
    "D2 24V TVS": (12.0, 35.0),
    "D3 FAN TVS": (20.0, 35.5),
    "Q1 FAN MOSFET": (55.0, 60.0),
    "U4 24V->3V3": (45.0, 90.0),
    "U5 USB ESD": (139.0, 18.0),
    "THERMO": (140.0, 44.0),
}
for drawing in board.GetDrawings():
    if isinstance(drawing, pcbnew.PCB_TEXT) and drawing.GetText() in text_positions:
        drawing.SetPosition(pt(*text_positions[drawing.GetText()]))

# PCB-only RF breakout/probe pads and fiducials intentionally have no
# schematic symbols; flag them explicitly so parity does not hide real extras.
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("FID") or ref.startswith("TPESP") or ref.startswith("PADESP"):
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    elif ref in {"TPRESET1", "TPBOOT1", "TPSSR1"}:
        # Keep electrical test symbols parity-visible; manufacturing exports
        # filter these references explicitly rather than via symbol attributes.
        fp.SetExcludedFromBOM(False)

# Export exact project-local copies and footprint provenance.  The board is
# self-contained; SourceFootprint remains the auditable manufacturer/library source.
source = {
    "F1": "datasheet:Littelfuse_65600001009",
    "D1": "Diode_SMD:D_SMB", "D2": "Diode_SMD:D_SMB", "D3": "Diode_SMD:D_SMB",
    "C4": "Capacitor_THT:CP_Radial_D8.0mm_P5.00mm", "C5": "Capacitor_SMD:C_0805_2012Metric",
    "SW1": "Button_Switch_SMD:SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG", "SW2": "Button_Switch_SMD:SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG",
    "Q1": "Package_TO_SOT_THT:TO-220-3_Vertical", "U5": "Package_TO_SOT_SMD:SOT-23-6",
    "U4": "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
    "L1": "Inductor_SMD:L_Changjiang_FNR6045S", "D4": "Diode_SMD:D_SMA", "D5": "Diode_SMD:D_SOD-123",
    "U6": "Package_TO_SOT_SMD:SOT-23-6",
}
for ref in ("C8", "C9", "C11", "C15"): source[ref] = "Capacitor_SMD:C_1210_3225Metric"
for ref in ("C12", "C13"): source[ref] = "Capacitor_SMD:C_0805_2012Metric"
for ref in ("C10", "C14"): source[ref] = "Capacitor_SMD:C_0603_1608Metric"
for ref in ("R12", "R13", "R14"): source[ref] = "Resistor_SMD:R_0603_1608Metric"
source["R15"] = "Resistor_SMD:R_0805_2012Metric"; source["R16"] = "Resistor_SMD:R_1206_3216Metric"

# Existing references retain their already audited project-local footprint source.
old_rows = {}
fp_csv = ROOT / "docs" / "footprints.csv"
if fp_csv.exists():
    with fp_csv.open(encoding="utf-8") as h:
        old_rows = {r["Ref"]: r for r in csv.DictReader(h)}

# For a trial board outside the project, do not overwrite the project's library/CSV.
if BOARD.parent == ROOT:
    shutil.rmtree(LOCAL, ignore_errors=True); LOCAL.mkdir()
    io = pcbnew.PCB_IO_KICAD_SEXPR(); rows = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        selected = source.get(ref) or old_rows.get(ref, {}).get("SourceFootprint") or fp.GetFPID().Format()
        item = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in f"{ref}_{selected.split(':',1)[-1]}")
        local_id = pcbnew.LIB_ID("CoffeeRoast", item)
        clone = pcbnew.FOOTPRINT(fp); clone.SetFPID(local_id); io.FootprintSave(str(LOCAL), clone); fp.SetFPID(local_id)
        rows.append((ref, fp.GetValue(), f"CoffeeRoast:{item}", selected))
    with fp_csv.open("w", newline="", encoding="utf-8") as h:
        w = csv.writer(h, lineterminator="\n"); w.writerow(("Ref", "Value", "Footprint", "SourceFootprint")); w.writerows(rows)

    # U1's antenna keepout was originally authored in board coordinates.  A
    # library footprint needs those vertices relative to the module origin.
    u1_mod = LOCAL / "U1_ESP32-S3-WROOM-1.kicad_mod"
    u1_text = u1_mod.read_text(encoding="utf-8")
    u1_text = u1_text.replace(
        "(xy 61 15.25) (xy 109 15.25) (xy 109 -5.75) (xy 61 -5.75)",
        "(xy -24 -12.75) (xy 24 -12.75) (xy 24 -33.75) (xy -24 -33.75)",
    )
    u1_mod.write_text(u1_text, encoding="utf-8")
    old_u1 = board.FindFootprintByReference("U1")
    u1_pos, u1_angle, u1_value = old_u1.GetPosition(), old_u1.GetOrientationDegrees(), old_u1.GetValue()
    u1_nets = {p.GetNumber(): p.GetNet() for p in old_u1.Pads() if p.GetNumber()}
    new_u1 = pcbnew.FootprintLoad(str(LOCAL), "U1_ESP32-S3-WROOM-1")
    new_u1.SetPosition(u1_pos); new_u1.SetOrientationDegrees(u1_angle)
    new_u1.SetReference("U1"); new_u1.SetValue(u1_value)
    new_u1.SetFPID(pcbnew.LIB_ID("CoffeeRoast", "U1_ESP32-S3-WROOM-1"))
    for p in new_u1.Pads():
        if p.GetNumber() in u1_nets:
            p.SetNet(u1_nets[p.GetNumber()])
    board.Remove(old_u1); board.Add(new_u1)

board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.SaveBoard(str(BOARD), board)
print(f"Finalized exact hardware on {BOARD}: {len(list(board.GetFootprints()))} footprints")
