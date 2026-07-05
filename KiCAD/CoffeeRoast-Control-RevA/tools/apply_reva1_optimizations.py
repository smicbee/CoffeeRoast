#!/usr/bin/env python3
"""Apply CoffeeRoast-Control RevA.1 robustness optimizations to the KiCad PCB.

Idempotently adds conservative, hand-reviewable RevA.1 hardware improvements that do
not put 230VAC on the PCB: concrete better part selections, 24V surge protection,
input bulk capacitance, fan clamp, thermocouple input filtering, USB ESD footprint,
and bring-up test points.
"""
from __future__ import annotations

from pathlib import Path

import pcbnew

BOARD_PATH = Path(__file__).resolve().parents[1] / "CoffeeRoast-Control-RevA.kicad_pcb"
ADDED_REFS = ["C4", "C5", "D2", "D3", "U5", "TP24V", "TP5V", "TP3V3", "TPGND"]


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def layer_set(*layers: int) -> pcbnew.LSET:
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    return ls


F_SMD = layer_set(pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste)
F_SMD_NOPASTE = layer_set(pcbnew.F_Cu, pcbnew.F_Mask)
F_THT = layer_set(pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask)


def net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def remove_added_refs(board: pcbnew.BOARD) -> None:
    for ref in ADDED_REFS:
        fp = board.FindFootprintByReference(ref)
        if fp:
            board.Remove(fp)


def set_fp_text(fp: pcbnew.FOOTPRINT, ref: str, value: str, x: float, y: float) -> None:
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.Reference().SetText(ref)
    fp.Value().SetText(value)
    fp.Reference().SetPosition(pt(x, y - 1.4))
    fp.Value().SetPosition(pt(x, y + 1.4))
    fp.Reference().SetLayer(pcbnew.F_SilkS)
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    fp.Value().SetTextSize(pcbnew.VECTOR2I(mm(0.65), mm(0.65)))
    fp.Reference().SetTextThickness(mm(0.12))
    fp.Value().SetTextThickness(mm(0.10))


def add_smd_pad(fp: pcbnew.FOOTPRINT, num: str, net_item: pcbnew.NETINFO_ITEM, x: float, y: float,
                sx: float = 1.2, sy: float = 1.2, shape: int = pcbnew.PAD_SHAPE_RECT,
                layers: pcbnew.LSET = F_SMD) -> None:
    pad = pcbnew.PAD(fp)
    pad.SetName(num)
    pad.SetNumber(num)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(shape)
    pad.SetLayerSet(layers)
    pad.SetPosition(pt(x, y))
    pad.SetSize(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    pad.SetNet(net_item)
    fp.Add(pad)


def add_tht_pad(fp: pcbnew.FOOTPRINT, num: str, net_item: pcbnew.NETINFO_ITEM, x: float, y: float,
                sx: float = 2.0, sy: float = 2.0, drill: float = 0.9) -> None:
    pad = pcbnew.PAD(fp)
    pad.SetName(num)
    pad.SetNumber(num)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetLayerSet(F_THT)
    pad.SetPosition(pt(x, y))
    pad.SetSize(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    pad.SetDrillSize(pcbnew.VECTOR2I(mm(drill), mm(drill)))
    pad.SetNet(net_item)
    fp.Add(pad)


def add_line(board: pcbnew.BOARD, net_item: pcbnew.NETINFO_ITEM, a: tuple[float, float], b: tuple[float, float],
             width: float = 0.25, layer: int = pcbnew.F_Cu) -> None:
    tr = pcbnew.PCB_TRACK(board)
    tr.SetStart(pt(*a))
    tr.SetEnd(pt(*b))
    tr.SetWidth(mm(width))
    tr.SetLayer(layer)
    tr.SetNet(net_item)
    board.Add(tr)


def add_polyline(board: pcbnew.BOARD, net_item: pcbnew.NETINFO_ITEM, points: list[tuple[float, float]],
                 width: float = 0.25, layer: int = pcbnew.F_Cu) -> None:
    for a, b in zip(points, points[1:]):
        if a != b:
            add_line(board, net_item, a, b, width, layer)


def add_two_pad_smd(board: pcbnew.BOARD, ref: str, value: str, p1_net: str, p2_net: str,
                    p1: tuple[float, float], p2: tuple[float, float], pad_size=(1.5, 1.2)) -> None:
    fp = pcbnew.FOOTPRINT(board)
    set_fp_text(fp, ref, value, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    # Keep FPID empty for generated custom pads so full DRC does not depend on a missing local library.
    add_smd_pad(fp, "1", net(board, p1_net), *p1, sx=pad_size[0], sy=pad_size[1])
    add_smd_pad(fp, "2", net(board, p2_net), *p2, sx=pad_size[0], sy=pad_size[1])
    board.Add(fp)


def add_testpoint(board: pcbnew.BOARD, ref: str, value: str, netname: str, x: float, y: float) -> None:
    fp = pcbnew.FOOTPRINT(board)
    set_fp_text(fp, ref, value, x, y)
    # Keep FPID empty for generated custom pads so full DRC does not depend on a missing local library.
    add_smd_pad(fp, "1", net(board, netname), x, y, sx=1.8, sy=1.8,
                shape=pcbnew.PAD_SHAPE_CIRCLE, layers=F_SMD_NOPASTE)
    board.Add(fp)


def update_existing_values(board: pcbnew.BOARD) -> None:
    # Keep the current routed placeholder footprint, but make the RevA.1 BOM intent explicit.
    updates = {
        "U3": "3V3_SWITCHING_REGULATOR_>=600mA_5V_IN_REPLACES_AMS1117",
        "Q1": "IRLB8721_OR_3V3_LOGIC_NMOS_RDS_ON_LOW",
        "U4": "24V_TO_5V_BUCK_MODULE_>=1A_LOW_NOISE",
    }
    for ref, value in updates.items():
        fp = board.FindFootprintByReference(ref)
        if fp:
            fp.SetValue(value)
            fp.Value().SetText(value)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    remove_added_refs(board)
    update_existing_values(board)

    n24raw = net(board, "+24V_RAW")
    n24 = net(board, "+24V_FUSED")
    gnd = net(board, "GND")
    n5 = net(board, "+5V")
    n33 = net(board, "+3V3")
    fan_neg = net(board, "FAN_NEG")
    usb_dn = net(board, "USB_DN")
    usb_dp = net(board, "USB_DP")
    th_p = net(board, "THERMO_PLUS")
    th_m = net(board, "THERMO_MINUS")

    # 24V input: bulk cap and TVS connected directly at J1-side rails.
    c4 = pcbnew.FOOTPRINT(board)
    set_fp_text(c4, "C4", "220uF_35V_INPUT_BULK", 10.0, 23.2)
    # Keep FPID empty for generated custom pads so full DRC does not depend on a missing local library.
    add_tht_pad(c4, "1", n24raw, 7.46, 23.2)
    add_tht_pad(c4, "2", gnd, 12.54, 23.2)
    board.Add(c4)
    add_two_pad_smd(board, "D2", "SMBJ33A_24V_INPUT_TVS", "+24V_RAW", "GND",
                    (7.46, 26.2), (12.54, 26.2), (2.0, 1.4))
    add_polyline(board, n24raw, [(7.46, 18.0), (7.46, 23.2), (7.46, 26.2)], width=0.45)
    add_polyline(board, gnd, [(12.54, 18.0), (12.54, 23.2), (12.54, 26.2)], width=0.45)

    # Fan clamp above J2 to avoid crossing the existing +24V_FUSED fan route below J2.
    add_two_pad_smd(board, "D3", "SMBJ33A_FAN_TVS", "+24V_FUSED", "FAN_NEG",
                    (7.46, 43.0), (12.54, 43.0), (2.0, 1.4))
    add_line(board, n24, (7.46, 48.0), (7.46, 43.0), width=0.45)
    add_line(board, fan_neg, (12.54, 48.0), (12.54, 43.0), width=0.45)

    # Thermocouple differential filter at the connector side, above J4 to avoid existing routed traces.
    add_two_pad_smd(board, "C5", "1nF_C0G_THERMO_DIFF_FILTER_DNP_IF_NOISY", "THERMO_PLUS", "THERMO_MINUS",
                    (137.46, 47.0), (142.54, 47.0), (1.2, 1.0))
    add_line(board, th_p, (137.46, 52.0), (137.46, 47.0), width=0.18)
    add_line(board, th_m, (142.54, 52.0), (142.54, 47.0), width=0.18)

    # USB ESD footprint: pads sit on existing connector-side USB/GND tracks so the routed USB pair is not disturbed.
    u5 = pcbnew.FOOTPRINT(board)
    set_fp_text(u5, "U5", "USBLC6-2SC6_OR_USB2_ESD", 133.0, 28.0)
    # Keep FPID empty for generated custom pads so full DRC does not depend on a missing local library.
    add_smd_pad(u5, "1", usb_dn, 133.0, 27.0, sx=0.65, sy=0.65)
    add_smd_pad(u5, "2", usb_dp, 133.0, 31.0, sx=0.65, sy=0.65)
    add_smd_pad(u5, "3", gnd, 133.0, 26.0, sx=0.65, sy=0.65)
    add_smd_pad(u5, "4", gnd, 134.4, 26.0, sx=0.65, sy=0.65)
    add_smd_pad(u5, "5", usb_dp, 134.4, 31.0, sx=0.65, sy=0.65)
    add_smd_pad(u5, "6", usb_dn, 134.4, 27.0, sx=0.65, sy=0.65)
    board.Add(u5)

    # Bring-up/test pads placed on/near existing nets with short routes.
    add_testpoint(board, "TP24V", "+24V_FUSED_TEST", "+24V_FUSED", 22.0, 72.0)
    add_testpoint(board, "TP5V", "+5V_TEST", "+5V", 50.0, 72.0)
    add_testpoint(board, "TP3V3", "+3V3_TEST", "+3V3", 72.0, 76.0)
    add_testpoint(board, "TPGND", "GND_TEST", "GND", 50.0, 84.0)
    add_line(board, n24, (22.0, 72.0), (25.0, 72.0), width=0.35)
    add_line(board, n5, (50.0, 72.0), (47.0, 72.0), width=0.25)
    add_line(board, n33, (72.0, 76.0), (68.0, 75.70), width=0.22)
    add_line(board, gnd, (50.0, 84.0), (47.0, 84.0), width=0.25)

    tb = board.GetTitleBlock()
    tb.SetRevision("A.1-draft")
    tb.SetComment(1, "RevA.1: switching 3V3 recommendation, concrete fan MOSFET, TVS/ESD, bulk cap, testpoints")
    tb.SetComment(2, "230V stays off this PCB: certified internal 24V PSU + external SSR module/heatsink")

    pcbnew.SaveBoard(str(BOARD_PATH), board)
    print(f"Updated {BOARD_PATH}")


if __name__ == "__main__":
    main()
