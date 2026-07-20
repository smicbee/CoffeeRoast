#!/usr/bin/env /usr/bin/python3
"""Re-space and reroute the CoffeeRoast U2/MAX6675 block.

This ECO intentionally preserves U2 pin numbering/nets and the existing upstream routes.
It moves U2 3 mm toward J4, increases its diagonal separation from C3, and replaces only
the local U2 fanout segments and vias. The script is baseline-guarded and refuses a changed
board rather than guessing.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew


TRACK_SNAPSHOT: list[pcbnew.BOARD_ITEM] = []
REMOVALS: list[pcbnew.BOARD_ITEM] = []


def mm(v: float) -> int:
    return pcbnew.FromMM(v)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def xy(v: pcbnew.VECTOR2I) -> tuple[float, float]:
    return (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))


def close(a: tuple[float, float], b: tuple[float, float], tol: float = 0.004) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def segment_matches(track: pcbnew.PCB_TRACK, a: tuple[float, float], b: tuple[float, float]) -> bool:
    s, e = xy(track.GetStart()), xy(track.GetEnd())
    return (close(s, a) and close(e, b)) or (close(s, b) and close(e, a))


def remove_segment(board: pcbnew.BOARD, net: str, layer: int,
                   a: tuple[float, float], b: tuple[float, float]) -> None:
    hits = [t for t in TRACK_SNAPSHOT
            if isinstance(t, pcbnew.PCB_TRACK)
            and not isinstance(t, pcbnew.PCB_VIA)
            and t.GetNetname() == net and t.GetLayer() == layer
            and segment_matches(t, a, b) and t not in REMOVALS]
    if len(hits) != 1:
        raise RuntimeError(f"expected one {net} segment {a}->{b}, found {len(hits)}")
    REMOVALS.append(hits[0])


def remove_via(board: pcbnew.BOARD, net: str, at: tuple[float, float]) -> None:
    hits = [t for t in TRACK_SNAPSHOT
            if isinstance(t, pcbnew.PCB_VIA)
            and t.GetNetname() == net and close(xy(t.GetPosition()), at)
            and t not in REMOVALS]
    if len(hits) != 1:
        raise RuntimeError(f"expected one {net} via at {at}, found {len(hits)}")
    REMOVALS.append(hits[0])


def add_track(board: pcbnew.BOARD, net: pcbnew.NETINFO_ITEM,
              a: tuple[float, float], b: tuple[float, float],
              layer: int = pcbnew.F_Cu, width: float = 0.20) -> None:
    if close(a, b):
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(*a))
    t.SetEnd(pt(*b))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


def add_polyline(board: pcbnew.BOARD, net: pcbnew.NETINFO_ITEM,
                 points: list[tuple[float, float]],
                 layer: int = pcbnew.F_Cu, width: float = 0.20) -> None:
    for a, b in zip(points, points[1:]):
        add_track(board, net, a, b, layer, width)


def add_via(board: pcbnew.BOARD, net: pcbnew.NETINFO_ITEM,
            at: tuple[float, float]) -> None:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(*at))
    v.SetWidth(mm(0.55))
    v.SetDrill(mm(0.30))
    v.SetNet(net)
    board.Add(v)


def net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    n = board.FindNet(name)
    if not n:
        raise RuntimeError(f"missing net {name}")
    return n


def footprint_pos(fp: pcbnew.FOOTPRINT) -> tuple[float, float]:
    return xy(fp.GetPosition())


def main() -> None:
    global TRACK_SNAPSHOT, REMOVALS
    ap = argparse.ArgumentParser()
    ap.add_argument("board", type=Path)
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    u2 = board.FindFootprintByReference("U2")
    c3 = board.FindFootprintByReference("C3")
    if not u2 or not c3:
        raise RuntimeError("U2/C3 not found")
    if not close(footprint_pos(u2), (125.0, 60.0)) or abs(u2.GetOrientationDegrees() - 180.0) > 0.01:
        raise RuntimeError(f"unexpected U2 baseline: {footprint_pos(u2)} rot {u2.GetOrientationDegrees()}")
    if not close(footprint_pos(c3), (125.0, 64.0)) or abs(c3.GetOrientationDegrees()) > 0.01:
        raise RuntimeError(f"unexpected C3 baseline: {footprint_pos(c3)} rot {c3.GetOrientationDegrees()}")

    expected = {
        "1": "GND", "2": "THERMO_MINUS", "3": "THERMO_PLUS", "4": "+3V3",
        "5": "MAX_SCK", "6": "MAX_CS", "7": "MAX_DO", "8": "GND",
    }
    actual = {p.GetNumber(): p.GetNetname() for p in u2.Pads() if p.GetNumber().isdigit()}
    if actual != expected:
        raise RuntimeError(f"U2 pin/net mismatch before ECO: {actual}")

    # KiCad SWIG track iterators become invalid after a removal. Resolve every
    # object against one immutable snapshot, then remove the complete set.
    TRACK_SNAPSHOT = list(board.GetTracks())
    REMOVALS = []

    # Remove the old local fanout only. Upstream SPI and downstream J4 routes remain.
    for name, y in (("MAX_SCK", 58.095), ("MAX_CS", 59.365), ("MAX_DO", 60.635)):
        remove_segment(board, name, pcbnew.F_Cu, (113.0, y), (122.525, y))
    remove_segment(board, "THERMO_PLUS", pcbnew.F_Cu, (127.475, 59.365), (133.185, 54.873))
    remove_segment(board, "THERMO_MINUS", pcbnew.F_Cu, (127.475, 60.635), (136.893, 56.245))

    remove_segment(board, "+3V3", pcbnew.F_Cu, (127.475, 58.095), (127.475, 56.5))
    remove_segment(board, "+3V3", pcbnew.B_Cu, (127.475, 56.5), (127.475, 68.0))
    remove_via(board, "+3V3", (127.475, 56.5))

    remove_segment(board, "GND", pcbnew.F_Cu, (127.475, 61.905), (128.5, 61.905))
    remove_segment(board, "GND", pcbnew.F_Cu, (122.525, 61.905), (121.5, 61.905))
    remove_via(board, "GND", (128.5, 61.905))
    remove_via(board, "GND", (121.5, 61.905))

    for item in REMOVALS:
        board.Remove(item)

    # Move only U2. C3 retains its already verified short decoupling fanout.
    u2.SetPosition(pt(128.0, 60.0))

    nets = {name: net(board, name) for name in set(expected.values())}

    # Parallel SPI fanout: retain existing upstream endpoints, extend cleanly to moved pads.
    for name, y in (("MAX_SCK", 58.095), ("MAX_CS", 59.365), ("MAX_DO", 60.635)):
        add_track(board, nets[name], (113.0, y), (125.525, y))

    # Leave the pin field horizontally before bending, avoiding adjacent pads.
    add_polyline(board, nets["THERMO_PLUS"],
                 [(130.475, 59.365), (132.0, 59.365), (133.185, 54.873)])
    add_polyline(board, nets["THERMO_MINUS"],
                 [(130.475, 60.635), (133.5, 60.635), (136.893, 56.245)])

    # U2 power/GND local vias.
    add_track(board, nets["+3V3"], (130.475, 58.095), (130.475, 56.5))
    add_via(board, nets["+3V3"], (130.475, 56.5))
    add_polyline(board, nets["+3V3"], [(130.475, 56.5), (130.475, 68.0), (127.475, 68.0)], pcbnew.B_Cu)

    add_track(board, nets["GND"], (130.475, 61.905), (131.5, 61.905))
    add_via(board, nets["GND"], (131.5, 61.905))
    add_track(board, nets["GND"], (125.525, 61.905), (124.5, 61.905))
    add_via(board, nets["GND"], (124.5, 61.905))


    # Refill zones so moved vias/tracks get current clearances.
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.board), board)
    print(f"updated {args.board}")
    print("U2 -> (128.0, 60.0), C3 retained at (125.0, 64.0)")


if __name__ == "__main__":
    main()
