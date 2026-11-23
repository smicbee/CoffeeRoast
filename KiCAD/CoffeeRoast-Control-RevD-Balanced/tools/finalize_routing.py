#!/usr/bin/env /usr/bin/python3
"""Generate the deterministic final two-layer RevD routing candidate.

The script rebuilds placement, routes with pinned Freerouting while preserving
critical net widths, closes the split USB-C VBUS pads, adds real GND planes and
keeps routing/copper away from all optical fiducials.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
JAR = Path.home() / ".cache/freerouting/freerouting-2.2.4.jar"
JAR_SHA256 = "f5ed374182900ccc78e473518bbb9f6b869f4a07159495f663a76f52bb10523b"


def add_track(board: pcbnew.BOARD, net: str, points: list[tuple[float, float]], layer: int, width: float) -> None:
    for start, end in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetNet(board.FindNet(net))
        track.SetLayer(layer)
        track.SetWidth(pcbnew.FromMM(width))
        track.SetStart(pcbnew.VECTOR2I_MM(*start))
        track.SetEnd(pcbnew.VECTOR2I_MM(*end))
        board.Add(track)


def add_via(board: pcbnew.BOARD, net: str, point: tuple[float, float], size: float = 0.8, drill: float = 0.4) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet(net))
    via.SetPosition(pcbnew.VECTOR2I_MM(*point))
    via.SetWidth(pcbnew.FromMM(size))
    via.SetDrill(pcbnew.FromMM(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)


def add_rule_keepout(board: pcbnew.BOARD, layer: int, cx: float, cy: float, half: float = 1.7) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowCopperPour(True)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowFootprints(False)
    outline = zone.Outline()
    outline.NewOutline()
    for point in ((cx-half, cy-half), (cx+half, cy-half), (cx+half, cy+half), (cx-half, cy+half)):
        outline.Append(pcbnew.VECTOR2I_MM(*point))
    board.Add(zone)


def add_ground_plane(board: pcbnew.BOARD, layer: int) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetNet(board.FindNet("GND"))
    zone.SetLayer(layer)
    zone.SetLocalClearance(pcbnew.FromMM(0.25))
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    outline.NewOutline()
    for point in ((0.5, 0.5), (95.5, 0.5), (95.5, 59.5), (0.5, 59.5)):
        outline.Append(pcbnew.VECTOR2I_MM(*point))
    board.Add(zone)


def remove_duplicate_routes(board: pcbnew.BOARD) -> int:
    """Remove exact SES duplicates of pre-seeded tracks and vias."""
    seen: set[tuple] = set()
    duplicates: list[pcbnew.BOARD_ITEM] = []
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            pos = item.GetPosition()
            key = (
                "via", item.GetNetCode(), pos.x, pos.y,
                item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(),
            )
        else:
            start = item.GetStart()
            end = item.GetEnd()
            ends = tuple(sorted(((start.x, start.y), (end.x, end.y))))
            key = ("track", item.GetNetCode(), item.GetLayer(), item.GetWidth(), ends)
        if key in seen:
            duplicates.append(item)
        else:
            seen.add(key)
    for item in duplicates:
        board.Delete(item)
    return len(duplicates)


if not JAR.exists():
    raise SystemExit(f"Missing pinned Freerouting jar: {JAR}")
if hashlib.sha256(JAR.read_bytes()).hexdigest() != JAR_SHA256:
    raise SystemExit("Freerouting jar SHA-256 mismatch")

existing = pcbnew.LoadBoard(str(BOARD))
if "--force" not in sys.argv and existing.GetTitleBlock().GetRevision() == "D-FINAL":
    print("RevD final routing already present; no changes made")
    raise SystemExit(0)

subprocess.run(["/usr/bin/python3", str(ROOT / "tools" / "build_balanced_revd.py"), "--force"], cwd=ROOT, check=True)
board = pcbnew.LoadBoard(str(BOARD))

# Routing starts without copper planes.  The planes are restored only after the
# signal/current routes are fixed, so DSN cannot turn them into layer keepouts.
for zone in list(board.Zones()):
    board.Delete(zone)

# Keep all tracks, vias and subsequent pours away from the optical fiducials.
for fp in board.GetFootprints():
    if not fp.GetReference().startswith("FID"):
        continue
    # Fiducials are optical fabrication marks, not electrical GND nodes.  The
    # inherited GND assignment made intentionally isolated fiducials appear as
    # unresolved electrical connections.
    for pad in fp.Pads():
        pad.SetNetCode(0)
    p = fp.GetPosition()
    add_rule_keepout(board, fp.GetLayer(), p.x / 1e6, p.y / 1e6)

settings = board.GetDesignSettings().m_NetSettings
settings.ClearNetclassPatternAssignments()
classes = (
    ("CriticalPower", 1.0, 0.25, 1.2, 0.6, ("+24V_RAW", "FAN_NEG")),
    # USB_VBUS keeps the fine-pitch connector's default 0.2/0.1 mm escape
    # geometry.  Applying the 0.5/0.2 mm power class at J5 is impossible without
    # violating the exact footprint's 0.3 mm pad pitch.
    ("Power", 0.5, 0.20, 0.8, 0.4, ("+3V3", "VDRV10")),
    ("Sensitive", 0.25, 0.20, 0.8, 0.4, ("THERMO_PLUS", "THERMO_MINUS", "MAX_DO", "MAX_CS", "MAX_SCK")),
    ("USB", 0.25, 0.20, 0.8, 0.4, ("USB_DN", "USB_DP", "USB_DN_MCU", "USB_DP_MCU")),
)
for name, width, clearance, via, drill, patterns in classes:
    netclass = pcbnew.NETCLASS(name)
    netclass.SetTrackWidth(pcbnew.FromMM(width))
    netclass.SetClearance(pcbnew.FromMM(clearance))
    netclass.SetViaDiameter(pcbnew.FromMM(via))
    netclass.SetViaDrill(pcbnew.FromMM(drill))
    settings.SetNetclass(name, netclass)
    for pattern in patterns:
        settings.SetNetclassPatternAssignment(pattern, name)
settings.RecomputeEffectiveNetclasses()

# Seed the otherwise unroutable split VBUS groups before DSN export.  J5's
# locating holes leave only a 0.1 mm escape corridor beside the fine pads.  Once
# clear of the connector, vias lead to a 0.5 mm B.Cu trunk and a side escape at
# U5.  Freerouting then treats this geometry as an obstacle and routes USB data,
# CC and GND around it instead of requiring an unsafe post-route overlay.
add_track(board, "USB_VBUS", [(12.45, 7.345), (12.75, 7.345), (12.75, 12.50)], pcbnew.F_Cu, 0.1)
add_via(board, "USB_VBUS", (12.75, 12.50), size=0.6, drill=0.3)
add_track(board, "USB_VBUS", [(17.25, 7.345), (17.55, 7.345), (17.25, 7.345), (17.25, 12.50)], pcbnew.F_Cu, 0.1)
add_via(board, "USB_VBUS", (17.25, 12.50), size=0.6, drill=0.3)
add_track(board, "USB_VBUS", [(27.1375, 10.0), (28.50, 10.0)], pcbnew.F_Cu, 0.2)
add_via(board, "USB_VBUS", (28.50, 10.0), size=0.6, drill=0.3)
add_track(board, "USB_VBUS", [(12.75, 12.50), (26.00, 12.50), (28.50, 10.0)], pcbnew.B_Cu, 0.5)
# R8 was moved beside U1 so its MCU-side D+ segment can be fixed before the
# general router; GPIO3 and neighbouring breakouts are then routed around it.
add_track(board, "USB_DP_MCU", [(60.95, 25.10), (61.90, 24.15), (63.25, 24.15)], pcbnew.F_Cu, 0.25)

with tempfile.TemporaryDirectory(prefix="coffeeroast-revd-final-") as temp_dir:
    temp = Path(temp_dir)
    dsn = temp / "revd.dsn"
    ses = temp / "revd.ses"
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("KiCad DSN export failed")
    subprocess.run([
        "java", "-jar", str(JAR), "--gui.enabled=false",
        "-de", str(dsn), "-do", str(ses), "-mp", "100",
    ], check=True)
    if not ses.exists() or not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit("Freerouting SES import failed")

removed_duplicates = remove_duplicate_routes(board)
add_ground_plane(board, pcbnew.F_Cu)
add_ground_plane(board, pcbnew.B_Cu)
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
title = board.GetTitleBlock()
title.SetRevision("D-FINAL")
title.SetComment(1, "RevD final routed two-layer candidate; MIC/LCD/buttons HAND-DNP")
pcbnew.SaveBoard(str(BOARD), board)
print(
    f"RevD final routing generated: {len(list(board.GetTracks()))} tracks/vias; "
    f"removed {removed_duplicates} exact SES duplicates"
)