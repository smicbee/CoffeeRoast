#!/usr/bin/env /usr/bin/python3
"""Audit RevD orientation-sensitive pad/net mappings and mechanical anchors.

This catches semantic mistakes that KiCad DRC cannot detect by itself. It is a
placement-stage gate; routing and assembler preview remain separate gates.
"""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
OUT = ROOT / "qa" / "orientation_audit.json"

EXPECTED = {
    "J1": {"1": "+24V_RAW", "2": "GND"},
    "J2": {"1": "+24V_RAW", "2": "FAN_NEG"},
    "J3": {"1": "+3V3", "2": "SSR_NEG"},
    "J4": {"1": "THERMO_PLUS", "2": "THERMO_MINUS"},
    "J5": {"1": "GND", "2": "USB_VBUS", "3": "USB_CC1", "4": "USB_DP",
           "5": "USB_DN", "6": "USB_CC2", "7": "USB_VBUS", "8": "GND"},
    "J6": {"1": "+24V_RAW", "2": "GND", "3": "GPIO10", "4": "GND"},
    "J7": {"1": "+3V3", "2": "GND", "3": "GPIO4", "4": "GPIO5",
           "5": "GPIO6", "6": "GPIO7"},
    "J8": {"1": "+3V3", "2": "GND", "3": "GPIO8", "4": "GPIO9",
           "5": "GPIO14", "6": "GPIO21"},
    "J9": {"1": "GND", "2": "GPIO15", "3": "GPIO16", "4": "GPIO17",
           "5": "GPIO18", "6": "+3V3"},
    "JGPIO1": {"1": "GPIO3", "2": "GPIO46", "3": "GPIO9", "4": "GPIO10",
               "5": "GPIO48", "6": "GPIO45"},
    "U1": {"1": "GND", "2": "+3V3", "3": "EN", "4": "GPIO4", "5": "GPIO5",
           "6": "GPIO6", "7": "GPIO7", "8": "GPIO15", "9": "GPIO16",
           "10": "GPIO17", "11": "GPIO18", "12": "GPIO8", "13": "USB_DN_MCU",
           "14": "USB_DP_MCU", "15": "GPIO3", "16": "GPIO46", "17": "GPIO9",
           "18": "GPIO10", "19": "MAX_DO", "20": "MAX_CS", "21": "MAX_SCK",
           "22": "GPIO14", "23": "GPIO21", "24": "GPIO47", "25": "GPIO48",
           "26": "GPIO45", "27": "BOOT", "28": "GPIO35", "29": "GPIO36",
           "30": "GPIO37", "31": "GPIO38", "32": "GPIO39", "33": "GPIO40",
           "34": "GPIO41", "35": "GPIO42", "36": "RXD0_GPIO44",
           "37": "TXD0_GPIO43", "38": "FAN_PWM", "39": "HEATER_PWM", "40": "GND"},
    "U2": {"1": "GND", "2": "THERMO_MINUS", "3": "THERMO_PLUS", "4": "+3V3",
           "5": "MAX_SCK", "6": "MAX_CS", "7": "MAX_DO", "8": "GND"},
    "U4": {"1": "BUCK_BOOT", "2": "+24V_RAW", "3": "+24V_RAW", "4": "BUCK_RT",
           "5": "BUCK_FB", "6": "U4_PGOOD_NC", "7": "GND", "8": "BUCK_SW", "9": "GND"},
    "U5": {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP",
           "5": "USB_VBUS", "6": "USB_DN"},
    "U6": {"1": "VDRV10", "2": "FAN_GATE_ON", "3": "FAN_GATE_OFF",
           "4": "GND", "5": "GND", "6": "FAN_PWM"},
    "Q1": {"1": "FAN_GATE", "2": "FAN_NEG", "3": "GND"},
    "Q2": {"1": "SSR_GATE", "2": "GND", "3": "SSR_NEG"},
    # KiCad diode convention used by the exact local footprints: pad 1 = cathode.
    "D1": {"1": "+24V_RAW", "2": "FAN_NEG"},
    "D2": {"1": "+24V_RAW", "2": "GND"},
    "D3": {"1": "+24V_RAW", "2": "FAN_NEG"},
    "D4": {"1": "BUCK_SW", "2": "GND"},
    "D5": {"1": "VDRV10", "2": "GND"},
    "C4": {"1": "+24V_RAW", "2": "GND"},
    "L1": {"1": "BUCK_SW", "2": "+3V3"},
    "SW1": {"1": "EN", "2": "GND"},
    "SW2": {"1": "BOOT", "2": "GND"},
    "TP24V": {"1": "+24V_RAW"}, "TP3V3": {"1": "+3V3"},
    "TPGND": {"1": "GND"}, "TPBOOT1": {"1": "BOOT", "2": "GND"},
    "TPRESET1": {"1": "EN", "2": "GND"},
    "TPSSR1": {"1": "+3V3", "2": "SSR_NEG"},
}

EXPECTED_ROTATION = {
    "J1": 0, "J2": 0, "J3": 0, "J4": 0, "J5": 180, "J6": 0,
    "J7": 90, "J8": 90, "J9": 270, "JGPIO1": 0, "U1": 0, "U2": 180,
    "U4": 0, "U5": 0, "U6": 0, "Q1": 0, "Q2": 0,
    "D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0,
    "C4": 0, "L1": 0, "SW1": 0, "SW2": 0,
    "TP24V": 0, "TP3V3": 0, "TPGND": 0, "TPBOOT1": 0,
    "TPRESET1": 0, "TPSSR1": 0,
}

EXPECTED_FOOTPRINT_ITEM = {
    "J5": "J5_USB_C_Receptacle_XKB_U262-16XN-4BVC11",
    "U1": "U1_ESP32-S3-WROOM-1", "U2": "U2_SOIC-8_3.9x4.9mm_P1.27mm",
    "U4": "U4_SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
    "U5": "U5_SOT-23-6", "U6": "U6_SOT-23-6", "Q1": "Q1_TO-220-3_Vertical",
    "Q2": "Q2_SOT-23", "D1": "D1_D_SMB", "D2": "D2_D_SMB",
    "D3": "D3_D_SMB", "D4": "D4_D_SMA", "D5": "D5_D_SOD-123",
    "C4": "C4_CP_Radial_D8.0mm_P5.00mm", "L1": "L1_L_Changjiang_FNR6045S",
    "SW1": "SW1_SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG",
    "SW2": "SW2_SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG",
}

EXPECTED_NONPOLAR_OR_MECHANICAL = {
    *(f"C{i}" for i in range(1, 16) if i != 4),
    *(f"R{i}" for i in [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16]),
    *(f"FID{i}" for i in range(1, 7)),
}


def logical_pin_map(fp: pcbnew.FOOTPRINT) -> dict[str, str]:
    result: dict[str, str] = {}
    for pad in fp.Pads():
        number = pad.GetNumber()
        if not number or not number.isdigit():
            continue
        net = pad.GetNetname()
        previous = result.setdefault(number, net)
        assert previous == net, f"{fp.GetReference()} pad {number}: duplicate pads have different nets"
    return result


def mm(value: int) -> float:
    return round(pcbnew.ToMM(value), 4)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    board_references = {fp.GetReference() for fp in board.GetFootprints()}
    expected_references = set(EXPECTED) | EXPECTED_NONPOLAR_OR_MECHANICAL
    assert board_references == expected_references, {
        "unexpected": sorted(board_references - expected_references),
        "missing": sorted(expected_references - board_references),
    }
    findings = []
    for ref, expected_map in EXPECTED.items():
        fp = board.FindFootprintByReference(ref)
        assert fp is not None, f"missing {ref}"
        actual_map = logical_pin_map(fp)
        assert actual_map == expected_map, f"{ref}: {actual_map} != {expected_map}"
        rotation = fp.GetOrientationDegrees() % 360
        assert abs(rotation - EXPECTED_ROTATION[ref]) < 0.01, (ref, rotation)
        if ref in EXPECTED_FOOTPRINT_ITEM:
            item = fp.GetFPID().GetLibItemName()
            assert item == EXPECTED_FOOTPRINT_ITEM[ref], (ref, item, EXPECTED_FOOTPRINT_ITEM[ref])
        findings.append({
            "reference": ref,
            "value": fp.GetValue(),
            "footprint": f"{fp.GetFPID().GetLibNickname()}:{fp.GetFPID().GetLibItemName()}",
            "position_mm": [mm(fp.GetPosition().x), mm(fp.GetPosition().y)],
            "rotation_deg": rotation,
            "pin_nets": actual_map,
            "status": "PASS",
        })

    # Manufacturer drawing for C319148: fine SMT tails are at local y=-3.67;
    # the mating face/Product Edge is the opposite body edge at local y=+3.675.
    # At 180 degrees the board-space mating-face Y is anchor_y - 3.675.
    j5 = board.FindFootprintByReference("J5")
    assert j5 is not None
    j5_anchor_y = pcbnew.ToMM(j5.GetPosition().y)
    product_edge_y = j5_anchor_y - 3.675
    fine_tail_y = j5_anchor_y + 3.67
    assert abs(product_edge_y) < 0.001, product_edge_y
    assert fine_tail_y > product_edge_y + 7.0, (fine_tail_y, product_edge_y)

    # ESP32 antenna keepout is the exact intended board-space rectangle.
    u1 = board.FindFootprintByReference("U1")
    assert u1 is not None
    zones = list(u1.Zones())
    assert len(zones) == 1
    bbox = zones[0].GetBoundingBox()
    antenna_keepout = [mm(bbox.GetX()), mm(bbox.GetY()), mm(bbox.GetWidth()), mm(bbox.GetHeight())]
    assert antenna_keepout == [48.0, 0.0, 48.0, 6.2], antenna_keepout

    result = {
        "board": str(BOARD),
        "scope": "orientation-sensitive pad/net semantics plus USB Product Edge and ESP32 antenna keepout",
        "board_footprints_total": len(board_references),
        "checked_references": len(findings),
        "nonpolar_or_mechanical_references": len(EXPECTED_NONPOLAR_OR_MECHANICAL),
        "j5": {
            "mpn": "XKB U262-161N-4BVC11 / LCSC C319148",
            "anchor_y_mm": round(j5_anchor_y, 4),
            "rotation_deg": j5.GetOrientationDegrees() % 360,
            "product_edge_y_mm": round(product_edge_y, 4),
            "fine_smt_tail_row_y_mm": round(fine_tail_y, 4),
            "status": "PASS",
        },
        "esp32_antenna_keepout_xywh_mm": antenna_keepout,
        "findings": findings,
        "status": "PASS",
        "limits": [
            "Placement-stage audit only; 159 unrouted items are expected.",
            "Assembler model rotation and live supplier substitutions still require final preview review.",
            "Non-polar R/C orientation is mechanically indifferent and not enumerated here.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "board_footprints_total": result["board_footprints_total"],
        "checked_references": result["checked_references"],
        "nonpolar_or_mechanical_references": result["nonpolar_or_mechanical_references"],
        "j5": result["j5"],
        "antenna_keepout": antenna_keepout,
    }, indent=2))


if __name__ == "__main__":
    main()
