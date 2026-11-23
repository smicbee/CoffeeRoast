#!/usr/bin/env python3
"""Apply the RevA.2 PCB layout-quality pass.

The pass is intentionally limited to low-risk geometry improvements:
- widen the 24 V and 2.5 A fan current paths,
- replace the FAN_NEG autorouter dogleg with a deliberate 45-degree route,
- enlarge the fan-current layer-transition via and Q1 source return,
- straighten short test/control extensions,
- remove a dangling 3V3 via pair and stale 5V/U3 silkscreen,
- refill the GND zone with a less sliver-prone minimum thickness.

Run with the system Python that provides pcbnew, normally /usr/bin/python3.
"""
from pathlib import Path
import pcbnew

BOARD = Path(__file__).resolve().parents[1] / "CoffeeRoast-Control-RevA.kicad_pcb"


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def xy(p: pcbnew.VECTOR2I) -> tuple[float, float]:
    return round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)


def segment_key(track: pcbnew.PCB_TRACK) -> tuple[str, frozenset, int]:
    return track.GetNetname(), frozenset({xy(track.GetStart()), xy(track.GetEnd())}), track.GetLayer()


def ensure_track(board: pcbnew.BOARD, net_name: str, start: tuple[float, float],
                 end: tuple[float, float], width: float, layer: int) -> None:
    wanted = (net_name, frozenset({start, end}), layer)
    for track in list(board.GetTracks()):
        if isinstance(track, pcbnew.PCB_VIA):
            continue
        if segment_key(track) == wanted:
            track.SetWidth(mm(width))
            return
    net = board.FindNet(net_name)
    if not net:
        raise RuntimeError(f"Missing net: {net_name}")
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(point(*start))
    track.SetEnd(point(*end))
    track.SetWidth(mm(width))
    track.SetLayer(layer)
    track.SetNet(net)
    board.Add(track)


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))

    obsolete_segments = {
        ("FAN_NEG", frozenset({(22.92, 48.0), (24.022, 48.0)}), pcbnew.F_Cu),
        ("FAN_NEG", frozenset({(24.022, 48.0), (25.252, 46.769)}), pcbnew.F_Cu),
        ("FAN_NEG", frozenset({(25.252, 46.769), (43.544, 46.769)}), pcbnew.F_Cu),
        ("FAN_NEG", frozenset({(43.544, 46.769), (43.798, 47.024)}), pcbnew.F_Cu),
        ("FAN_NEG", frozenset({(43.798, 47.024), (43.798, 48.0)}), pcbnew.F_Cu),
        ("FAN_NEG", frozenset({(43.798, 48.0), (45.0, 48.0)}), pcbnew.F_Cu),
        ("+24V_FUSED", frozenset({(15.0, 69.0), (22.0, 72.0)}), pcbnew.F_Cu),
        ("+3V3", frozenset({(60.0, 72.0), (72.0, 76.0)}), pcbnew.F_Cu),
        ("+3V3", frozenset({(72.0, 76.0), (68.0, 75.7)}), pcbnew.F_Cu),
        ("+3V3", frozenset({(68.0, 75.7), (68.8, 75.7)}), pcbnew.B_Cu),
        ("EN", frozenset({(45.25, 29.75), (49.0, 30.75)}), pcbnew.F_Cu),
        ("GND", frozenset({(45.25, 34.25), (49.0, 33.25)}), pcbnew.F_Cu),
        ("BOOT", frozenset({(45.25, 39.75), (49.0, 40.75)}), pcbnew.F_Cu),
        ("GND", frozenset({(45.25, 44.25), (49.0, 43.25)}), pcbnew.F_Cu),
    }

    tracks = list(board.GetTracks())
    remove = []
    for track in tracks:
        if isinstance(track, pcbnew.PCB_VIA):
            if track.GetNetname() == "+3V3" and xy(track.GetPosition()) in {
                (68.0, 75.7), (68.8, 75.7)
            }:
                remove.append(track)
            continue
        if segment_key(track) in obsolete_segments:
            remove.append(track)
    for item in remove:
        board.Remove(item)

    # FAN_NEG: keep the flyback diode in the current loop while clearing D1's
    # opposite-net pad with an exact 45-degree / horizontal / 45-degree route.
    ensure_track(board, "FAN_NEG", (22.92, 48.0), (24.42, 46.5), 1.0, pcbnew.F_Cu)
    ensure_track(board, "FAN_NEG", (24.42, 46.5), (43.5, 46.5), 1.0, pcbnew.F_Cu)
    ensure_track(board, "FAN_NEG", (43.5, 46.5), (45.0, 48.0), 1.0, pcbnew.F_Cu)

    # Deliberate 45-degree access/control extensions replacing arbitrary angles.
    desired_extensions = [
        ("+24V_FUSED", (15.0, 69.0), (18.0, 72.0), 1.0),
        ("+24V_FUSED", (18.0, 72.0), (22.0, 72.0), 1.0),
        ("+3V3", (60.0, 72.0), (63.7, 75.7), 0.25),
        ("+3V3", (63.7, 75.7), (68.0, 75.7), 0.25),
        ("EN", (45.25, 29.75), (46.25, 30.75), 0.2),
        ("EN", (46.25, 30.75), (49.0, 30.75), 0.2),
        ("GND", (45.25, 34.25), (46.25, 33.25), 0.2),
        ("GND", (46.25, 33.25), (49.0, 33.25), 0.2),
        ("BOOT", (45.25, 39.75), (46.25, 40.75), 0.2),
        ("BOOT", (46.25, 40.75), (49.0, 40.75), 0.2),
        ("GND", (45.25, 44.25), (46.25, 43.25), 0.2),
        ("GND", (46.25, 43.25), (49.0, 43.25), 0.2),
    ]
    for net, start, end, width in desired_extensions:
        ensure_track(board, net, start, end, width, pcbnew.F_Cu)

    # Conservative 1 oz external-layer target: 1.0 mm for FAN_NEG and
    # 1.2 mm for the 24 V distribution. The latter also covers the U4 branch.
    for track in list(board.GetTracks()):
        net = track.GetNetname()
        if net in {"+24V_RAW", "+24V_FUSED"}:
            if isinstance(track, pcbnew.PCB_VIA):
                track.SetWidth(mm(1.2))
                track.SetDrill(mm(0.6))
            else:
                track.SetWidth(mm(1.2))
        elif net == "FAN_NEG":
            if isinstance(track, pcbnew.PCB_VIA):
                track.SetWidth(mm(1.2))
                track.SetDrill(mm(0.6))
            else:
                track.SetWidth(mm(1.0))

        # Q1 source-to-GND return: widen the explicit stub and transition via.
        if net == "GND":
            if isinstance(track, pcbnew.PCB_VIA) and xy(track.GetPosition()) == (47.54, 48.0):
                track.SetWidth(mm(1.2))
                track.SetDrill(mm(0.6))
            elif (not isinstance(track, pcbnew.PCB_VIA)
                  and track.GetLayer() == pcbnew.B_Cu
                  and frozenset({xy(track.GetStart()), xy(track.GetEnd())})
                  == frozenset({(47.54, 58.0), (47.54, 48.0)})):
                track.SetWidth(mm(1.0))

    # Remove labels from the deleted 5 V/U3 stage and correct the surviving buck label.
    for drawing in list(board.GetDrawings()):
        if not isinstance(drawing, pcbnew.PCB_TEXT):
            continue
        text = drawing.GetText()
        if text in {"TP5V", "U3 3V3 REG", "+5V TP"}:
            board.Remove(drawing)
        elif text == "U4 24V->5V":
            drawing.SetText("U4 24V->3V3")
        elif text == "+5V":
            drawing.SetText("+3V3")

    title = board.GetTitleBlock()
    title.SetRevision("A.2-layout-quality-draft")
    title.SetComment(1, "RevA.2: widened 24V/fan paths, deliberate 45-degree routing, cleaned GND zone")

    # 0.25 mm suppresses fragile copper slivers while remaining well within the
    # chosen fabricator's ordinary process capability; refill before saving.
    for zone in board.Zones():
        zone.SetMinThickness(mm(0.25))
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Applied layout-quality pass to {BOARD}")


if __name__ == "__main__":
    main()
