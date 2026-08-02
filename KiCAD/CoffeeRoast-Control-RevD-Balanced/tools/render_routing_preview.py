#!/usr/bin/env /usr/bin/python3
"""Render the RevD two-layer routing preview with functional net colours."""
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
OUT = ROOT / "render" / "routing-preview"
OUT.mkdir(parents=True, exist_ok=True)
SCALE = 20
MARGIN = 80
W, H = 96.0, 60.0
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT = ImageFont.truetype(FONT_PATH, 16)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 12)

board = pcbnew.LoadBoard(str(BOARD))


def xy(x_mm: float, y_mm: float) -> tuple[float, float]:
    return MARGIN + x_mm * SCALE, MARGIN + y_mm * SCALE


def colour(track) -> tuple[int, int, int]:
    net = track.GetNetname()
    if net == "+24V_RAW":
        return 255, 150, 20
    if net == "FAN_NEG":
        return 255, 225, 30
    if net == "BUCK_SW":
        return 255, 50, 190
    if net in {"USB_DP", "USB_DN", "USB_DP_MCU", "USB_DN_MCU"}:
        return 60, 255, 100
    if net in {"THERMO_PLUS", "THERMO_MINUS", "MAX_SCK", "MAX_CS", "MAX_DO"}:
        return 210, 100, 255
    if net == "GND":
        return 165, 165, 175
    if track.GetLayer() == pcbnew.F_Cu:
        return 255, 75, 75
    return 50, 200, 255


def render(name: str, layers: set[int]) -> None:
    image = Image.new("RGB", (int(W * SCALE + 2 * MARGIN), int(H * SCALE + 2 * MARGIN)), (15, 18, 23))
    draw = ImageDraw.Draw(image)
    draw.rectangle((*xy(0, 0), *xy(W, H)), fill=(34, 58, 50), outline=(245, 235, 130), width=3)

    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            pos = track.GetPosition()
            x, y = xy(pos.x / 1e6, pos.y / 1e6)
            radius = max(3, track.GetWidth(pcbnew.F_Cu) / 1e6 * SCALE / 2)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(210, 170, 40), outline=(255, 255, 255))
            continue
        if track.GetLayer() not in layers:
            continue
        start, end = track.GetStart(), track.GetEnd()
        width = max(2, round(track.GetWidth() / 1e6 * SCALE))
        draw.line((*xy(start.x / 1e6, start.y / 1e6), *xy(end.x / 1e6, end.y / 1e6)), fill=colour(track), width=width)

    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        if ref.startswith("FID"):
            continue
        for pad in footprint.Pads():
            pos = pad.GetPosition()
            x, y = xy(pos.x / 1e6, pos.y / 1e6)
            sx = max(3, pad.GetSize().x / 1e6 * SCALE / 2)
            sy = max(3, pad.GetSize().y / 1e6 * SCALE / 2)
            draw.ellipse((x - sx, y - sy, x + sx, y + sy), fill=(210, 165, 35), outline=(250, 215, 80))
            if pad.HasHole():
                drill = pad.GetDrillSize()
                radius = max(2, min(drill.x, drill.y) / 1e6 * SCALE / 2)
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(15, 18, 23))
        pos = footprint.GetPosition()
        x, y = xy(pos.x / 1e6, pos.y / 1e6)
        if ref.startswith(("J", "U", "Q", "SW", "L")):
            draw.text((x + 4, y + 4), ref, font=FONT_SMALL, fill=(255, 255, 255))

    draw.text((MARGIN, 18), f"CoffeeRoast RevD — Routing preview {name}", font=FONT, fill=(255, 255, 255))
    draw.text((MARGIN, 43), "orange=24V  yellow=FAN  magenta=BUCK_SW  green=USB  violet=THERMO/SPI  red=F.Cu  cyan=B.Cu", font=FONT_SMALL, fill=(210, 215, 225))
    draw.text((MARGIN, H * SCALE + MARGIN + 24), "PREVIEW: autorouted draft; open connections and critical-current widths still require review", font=FONT_SMALL, fill=(255, 190, 90))
    image.save(OUT / f"routing_{name.lower()}.png")


render("TOP", {pcbnew.F_Cu})
render("BOTTOM", {pcbnew.B_Cu})
render("COMBINED", {pcbnew.F_Cu, pcbnew.B_Cu})
print(OUT)
