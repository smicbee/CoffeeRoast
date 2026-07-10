#!/usr/bin/env python3
"""Render CoffeeRoast RevA.1 visual-review PNGs from the KiCad board.

The output is intentionally human-facing rather than a manufacturing plot:
- component placement with JLC PCBA vs DNP/hand-solder colors
- JLC-PCBA-only placement/callout view
- trace/net overlay grouped by functional nets
- functional block diagram for order/build review
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pcbnew  # type: ignore[import-not-found]
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "CoffeeRoast-Control-RevA.kicad_pcb"
ASM_DIR = ROOT / "production" / "partial-smd-pcba" / "assembly"
RENDER_DIR = ROOT / "render"

BG = (0, 0, 0)
PANEL = (28, 33, 40)
PANEL_DARK = (12, 14, 17)
TEXT = (238, 240, 245)
MUTED = (190, 196, 205)
BOARD_EDGE = (244, 238, 132)
PAD = (205, 72, 255)
PAD_HOLE = (255, 255, 255)
PCBA = (0, 190, 100)
DNP = (245, 145, 25)
DEBUG = (120, 120, 130)
GRID = (40, 45, 52)
WHITE = (255, 255, 255)

NET_COLORS = {
    "24V": (255, 140, 0),
    "5V": (255, 225, 30),
    "3V3": (25, 230, 80),
    "USB": (30, 195, 245),
    "MAX": (170, 80, 255),
    "PWM": (240, 85, 190),
    "GND": (150, 150, 150),
    "TOP": (255, 70, 70),
    "BOTTOM": (0, 205, 225),
}

DESCRIPTIONS = {
    "C1": "10uF 5V",
    "C2": "10uF 3V3",
    "C3": "100nF MAX6675",
    "C4": "220uF input bulk",
    "C5": "thermocouple filter DNP",
    "D1": "flyback diode",
    "D2": "24V input TVS",
    "D3": "fan TVS",
    "F1": "fuse holder",
    "J1": "24V input terminal",
    "J2": "24V fan terminal",
    "J3": "external SSR terminal",
    "J4": "K-type thermocouple",
    "J5": "USB-C receptacle",
    "Q1": "fan MOSFET",
    "Q2": "2N7002 SSR driver",
    "R1": "100R fan gate",
    "R2": "100k fan pulldown",
    "R3": "100R SSR gate",
    "R4": "100k SSR pulldown",
    "R5": "10k EN pullup",
    "R6": "10k BOOT pullup",
    "R7": "27R USB D-",
    "R8": "27R USB D+",
    "R10": "5.1k CC1 Rd",
    "R11": "5.1k CC2 Rd",
    "SW1": "RESET/EN button",
    "SW2": "BOOT button",
    "U1": "ESP32-S3 module",
    "U2": "MAX6675 SOIC-8",
    "U3": "3V3 regulator footprint",
    "U4": "24V->5V buck module",
    "U5": "USB ESD DNP",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUB = font(22)
F_LABEL = font(19, True)
F_SMALL = font(16)
F_TABLE = font(16)
F_TABLE_BOLD = font(17, True)
F_BLOCK = font(22, True)
F_BLOCK_SMALL = font(16)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def ref_sort_key(ref: str) -> tuple[str, int, str]:
    prefix = "".join(ch for ch in ref if ch.isalpha())
    digits = "".join(ch for ch in ref if ch.isdigit())
    return prefix, int(digits or 0), ref


def is_debug_ref(ref: str) -> bool:
    return ref.startswith("TPESP") or ref.startswith("PADESP") or ref in {"TP24V", "TP5V", "TP3V3", "TPGND"}


def center_mm(fp: pcbnew.FOOTPRINT) -> tuple[float, float]:
    pos = fp.GetPosition()
    if (pos.x != 0 or pos.y != 0) or len(list(fp.Pads())) == 0:
        return pos.x / 1e6, pos.y / 1e6
    xs: list[float] = []
    ys: list[float] = []
    for pad in fp.Pads():
        p = pad.GetPosition()
        xs.append(p.x / 1e6)
        ys.append(p.y / 1e6)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def rect_mm_from_bbox(bb) -> tuple[float, float, float, float]:
    return bb.GetX() / 1e6, bb.GetY() / 1e6, (bb.GetX() + bb.GetWidth()) / 1e6, (bb.GetY() + bb.GetHeight()) / 1e6


def footprint_rect_mm(fp: pcbnew.FOOTPRINT) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for pad in fp.Pads():
        try:
            x1, y1, x2, y2 = rect_mm_from_bbox(pad.GetBoundingBox())
            xs.extend([x1, x2])
            ys.extend([y1, y2])
        except Exception:
            p = pad.GetPosition()
            xs.append(p.x / 1e6)
            ys.append(p.y / 1e6)
    if xs and ys:
        pad_margin = 0.6
        return min(xs) - pad_margin, min(ys) - pad_margin, max(xs) + pad_margin, max(ys) + pad_margin
    try:
        return rect_mm_from_bbox(fp.GetBoundingBox())
    except Exception:
        x, y = center_mm(fp)
        return x - 1, y - 1, x + 1, y + 1


@dataclass
class Component:
    ref: str
    value: str
    x: float
    y: float
    rect: tuple[float, float, float, float]
    status: str
    description: str
    rotation: float


class BoardCanvas:
    def __init__(self, width: int, height: int, board_bbox, *, right_panel: int = 0, top_space: int = 145, bottom_space: int = 95):
        self.width = width
        self.height = height
        self.right_panel = right_panel
        self.top_space = top_space
        self.bottom_space = bottom_space
        self.left = 90
        self.right_margin = 70
        self.board_x = board_bbox.GetX() / 1e6
        self.board_y = board_bbox.GetY() / 1e6
        self.board_w = board_bbox.GetWidth() / 1e6
        self.board_h = board_bbox.GetHeight() / 1e6
        drawable_w = width - self.left - self.right_margin - right_panel
        drawable_h = height - top_space - bottom_space
        self.scale = min(drawable_w / self.board_w, drawable_h / self.board_h)
        self.image = Image.new("RGB", (width, height), BG)
        self.draw = ImageDraw.Draw(self.image)

    def xy(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        return self.left + (x_mm - self.board_x) * self.scale, self.top_space + (y_mm - self.board_y) * self.scale

    def rect(self, r: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        x1, y1 = self.xy(r[0], r[1])
        x2, y2 = self.xy(r[2], r[3])
        return x1, y1, x2, y2

    def draw_text(self, pos: tuple[float, float], text: str, fill=TEXT, font_obj=F_SMALL, anchor: str | None = None):
        self.draw.text(pos, text, fill=fill, font=font_obj, anchor=anchor)

    def label_bubble(self, x: float, y: float, text: str, color: tuple[int, int, int], *, radius: int = 23):
        px, py = self.xy(x, y)
        px = max(radius + 4, min(self.width - self.right_panel - radius - 8, px))
        py = max(self.top_space + radius, min(self.height - self.bottom_space - radius, py))
        self.draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color, outline=WHITE, width=2)
        self.draw.text((px, py), text, font=F_LABEL, fill=WHITE, anchor="mm")

    def callout_label(self, x: float, y: float, text: str, color: tuple[int, int, int], *, dx: int = 18, dy: int = -18):
        px, py = self.xy(x, y)
        tx = max(10, min(self.width - self.right_panel - 180, px + dx))
        ty = max(self.top_space + 5, min(self.height - self.bottom_space - 34, py + dy))
        bbox = self.draw.textbbox((tx, ty), text, font=F_LABEL)
        pad = 6
        self.draw.rounded_rectangle((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad), radius=7, fill=(18, 22, 27), outline=color, width=2)
        self.draw.text((tx, ty), text, font=F_LABEL, fill=WHITE)
        self.draw.line((px, py, bbox[0] - pad, (bbox[1] + bbox[3]) / 2), fill=color, width=2)


def load_data() -> tuple[pcbnew.BOARD, list[Component], set[str], set[str]]:
    board = pcbnew.LoadBoard(str(BOARD_PATH))
    assembled = {row["Designator"] for row in read_csv(ASM_DIR / "bom_smd_partial.csv") if row.get("Assemble", "").upper() == "YES"}
    dnp_rows = read_csv(ASM_DIR / "dnp_hand_solder.csv")
    dnp = {row["Designator"] for row in dnp_rows if row.get("Designator")}
    dnp_reason = {row["Designator"]: row.get("Reason/Action", "") for row in dnp_rows}
    comps: list[Component] = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if is_debug_ref(ref):
            continue
        if ref in assembled:
            status = "PCBA"
        elif ref in dnp:
            status = "DNP"
        else:
            status = "Review"
        x, y = center_mm(fp)
        desc = DESCRIPTIONS.get(ref) or fp.GetValue() or ref
        if status == "DNP" and "Test/debug" in dnp_reason.get(ref, ""):
            status = "Debug"
        comps.append(Component(ref, fp.GetValue(), x, y, footprint_rect_mm(fp), status, desc, fp.GetOrientationDegrees()))
    comps.sort(key=lambda c: ref_sort_key(c.ref))
    return board, comps, assembled, dnp


def draw_grid(c: BoardCanvas):
    # 10 mm orientation grid; subtle enough not to hide traces.
    for x in range(0, 161, 10):
        x1, y1 = c.xy(x, 0)
        x2, y2 = c.xy(x, 100)
        c.draw.line((x1, y1, x2, y2), fill=GRID, width=1)
    for y in range(0, 101, 10):
        x1, y1 = c.xy(0, y)
        x2, y2 = c.xy(160, y)
        c.draw.line((x1, y1, x2, y2), fill=GRID, width=1)


def draw_edges(c: BoardCanvas, board: pcbnew.BOARD, *, color=BOARD_EDGE, width=3):
    drew = False
    for d in board.GetDrawings():
        try:
            if d.GetLayer() != pcbnew.Edge_Cuts:
                continue
            if hasattr(d, "GetStart") and hasattr(d, "GetEnd"):
                s = d.GetStart(); e = d.GetEnd()
                c.draw.line((*c.xy(s.x / 1e6, s.y / 1e6), *c.xy(e.x / 1e6, e.y / 1e6)), fill=color, width=width)
                drew = True
        except Exception:
            continue
    if not drew:
        x1, y1 = c.xy(0, 0); x2, y2 = c.xy(160, 100)
        c.draw.rectangle((x1, y1, x2, y2), outline=color, width=width)


def draw_component_shape(c: BoardCanvas, comp: Component, *, emph: bool = False, muted: bool = False):
    outline = PCBA if comp.status == "PCBA" else DNP if comp.status == "DNP" else DEBUG
    fill = (26, 31, 36) if not muted else (10, 12, 14)
    width = 3 if emph else 2
    r = c.rect(comp.rect)
    c.draw.rounded_rectangle(r, radius=5, outline=outline if not muted else (75, 80, 86), fill=fill, width=width)
    # Pad dots make the plot easier to compare with JLC preview without redrawing exact CAD geometry.
    cx, cy = c.xy(comp.x, comp.y)
    rr = 4 if not emph else 5
    c.draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=PAD_HOLE, outline=outline)


def draw_title(c: BoardCanvas, title: str, subtitle: str):
    c.draw.text((26, 18), title, fill=WHITE, font=F_TITLE)
    c.draw.text((28, 72), subtitle, fill=MUTED, font=F_SUB)


def draw_status_legend(c: BoardCanvas, x: int, y: int):
    items = [(PCBA, "JLC PCBA / automatisch bestückt"), (DNP, "Handlöten / DNP / später prüfen"), (DEBUG, "Debug-/Testpads nicht gezählt")]
    cursor = x
    for color, label in items:
        c.draw.ellipse((cursor, y, cursor + 22, y + 22), fill=color, outline=WHITE)
        c.draw.text((cursor + 32, y - 1), label, fill=TEXT, font=F_SMALL)
        cursor += 370 if color != DEBUG else 280


def render_component_map(board: pcbnew.BOARD, comps: list[Component]) -> Path:
    out = RENDER_DIR / "coffeeroast_component_map_annotated.png"
    c = BoardCanvas(3600, 1650, board.GetBoardEdgesBoundingBox(), right_panel=1130, top_space=155, bottom_space=110)
    draw_title(c, "CoffeeRoast RevA.1 – Bauteil-Lageplan", "Alle sichtbaren Bauteile: grün = JLC bestücken lassen, orange = Handlöten/DNP/RevA.2 prüfen")
    draw_status_legend(c, 30, 112)
    draw_grid(c)
    draw_edges(c, board)
    for comp in comps:
        draw_component_shape(c, comp)
    for comp in comps:
        color = PCBA if comp.status == "PCBA" else DNP if comp.status == "DNP" else DEBUG
        c.label_bubble(comp.x, comp.y, comp.ref, color, radius=24 if len(comp.ref) <= 3 else 29)
    panel_x = c.width - c.right_panel + 30
    c.draw.rectangle((c.width - c.right_panel, 0, c.width, c.height), fill=PANEL)
    c.draw.text((panel_x, 26), "Legende / exakte Positionen", fill=WHITE, font=F_TITLE)
    c.draw.text((panel_x, 82), "Koordinaten in mm aus dem KiCad-Board. Status zeigt die JLC-Bestückung.", fill=MUTED, font=F_SUB)
    x_ref, x_desc, x_xy, x_status = panel_x, panel_x + 82, panel_x + 620, panel_x + 790
    y = 128
    c.draw.text((x_ref, y), "Ref", fill=WHITE, font=F_TABLE_BOLD)
    c.draw.text((x_desc, y), "Beschreibung", fill=WHITE, font=F_TABLE_BOLD)
    c.draw.text((x_xy, y), "x/y", fill=WHITE, font=F_TABLE_BOLD)
    c.draw.text((x_status, y), "Status", fill=WHITE, font=F_TABLE_BOLD)
    y += 34
    for comp in comps:
        color = PCBA if comp.status == "PCBA" else DNP if comp.status == "DNP" else DEBUG
        c.draw.rounded_rectangle((x_ref, y - 4, x_ref + 58, y + 20), radius=6, fill=color)
        c.draw.text((x_ref + 7, y - 3), comp.ref, fill=WHITE, font=F_TABLE_BOLD)
        c.draw.text((x_desc, y - 2), comp.description[:48], fill=TEXT, font=F_TABLE)
        c.draw.text((x_xy, y - 2), f"{comp.x:.1f}/{comp.y:.1f}", fill=MUTED, font=F_TABLE)
        c.draw.text((x_status, y - 2), comp.status, fill=color, font=F_TABLE_BOLD)
        y += 29
    note_y = c.height - 118
    c.draw.rectangle((panel_x, note_y, c.width - 42, c.height - 28), fill=PANEL_DARK, outline=(80, 86, 92))
    c.draw.text((panel_x + 18, note_y + 18), "Hinweis: TPESP/PADESP Debug-Pads sind nicht als Bauteile markiert.", fill=TEXT, font=F_SMALL)
    c.draw.text((panel_x + 18, note_y + 46), "U5/D2/D3/C5 bleiben DNP/Prüfpunkte für spätere Revision.", fill=TEXT, font=F_SMALL)
    c.draw.text((885, c.height - 58), "CoffeeRoast Control RevA – 24V/3A input, no 230V on PCB", fill=BOARD_EDGE, font=font(30, True))
    c.image.save(out)
    return out


def render_pcba_only(board: pcbnew.BOARD, comps: list[Component]) -> Path:
    out = RENDER_DIR / "coffeeroast_jlc_pcba_placement_annotated.png"
    pcba = [comp for comp in comps if comp.status == "PCBA"]
    dnp = [comp for comp in comps if comp.status != "PCBA"]
    c = BoardCanvas(2700, 1650, board.GetBoardEdgesBoundingBox(), right_panel=650, top_space=150, bottom_space=90)
    draw_title(c, "CoffeeRoast RevA.1 – JLC-PCBA Callout Map", "Nur diese Teile im ersten Standard-PCBA-Schritt bestücken lassen; alle grauen Umrisse bleiben Handlöten/DNP.")
    draw_status_legend(c, 30, 108)
    draw_grid(c)
    draw_edges(c, board)
    for comp in dnp:
        draw_component_shape(c, comp, muted=True)
    for comp in pcba:
        draw_component_shape(c, comp, emph=True)
        label = f"{comp.ref} {comp.description}"
        c.callout_label(comp.x, comp.y, label, PCBA, dx=24, dy=-26)
    c.draw.rectangle((c.width - c.right_panel, 0, c.width, c.height), fill=PANEL)
    px = c.width - c.right_panel + 28
    c.draw.text((px, 28), "JLC bestücken", fill=WHITE, font=F_TITLE)
    c.draw.text((px, 84), "BOM/CPL: production/partial-smd-pcba/assembly", fill=MUTED, font=F_SMALL)
    y = 128
    for group_title, members in [
        ("Module/IC/Connector", {"U1", "U2", "J5", "Q2"}),
        ("USB + Pullups", {"R5", "R6", "R7", "R8", "R10", "R11"}),
        ("Gate/Power Kleinteile", {"R1", "R2", "R3", "R4", "C1", "C2", "C3"}),
    ]:
        c.draw.text((px, y), group_title, fill=BOARD_EDGE, font=F_TABLE_BOLD)
        y += 30
        for comp in pcba:
            if comp.ref in members:
                c.draw.rounded_rectangle((px, y - 4, px + 58, y + 20), radius=6, fill=PCBA)
                c.draw.text((px + 7, y - 3), comp.ref, fill=WHITE, font=F_TABLE_BOLD)
                c.draw.text((px + 72, y - 2), comp.description[:42], fill=TEXT, font=F_TABLE)
                y += 27
        y += 18
    note = [
        "Nicht in PCBA hochziehen ohne neue Prüfung:",
        "J1-J4/F1/D1/Q1/C4/U3/U4 = Handlöten",
        "D2/D3/U5/C5 = Footprint/ESD/TVS prüfen",
        "Vor Checkout: Orientierung in JLC Preview prüfen.",
    ]
    y = c.height - 185
    c.draw.rectangle((px, y - 16, c.width - 35, c.height - 32), fill=PANEL_DARK, outline=(80, 86, 92))
    for line in note:
        c.draw.text((px + 14, y), line, fill=TEXT, font=F_SMALL)
        y += 30
    c.image.save(out)
    return out


def net_group(net: str, layer: int) -> str:
    if net in {"+24V_RAW", "+24V_FUSED", "FAN_NEG"}:
        return "24V"
    if net in {"+5V", "USB_VBUS"}:
        return "5V"
    if net == "+3V3":
        return "3V3"
    if net.startswith("USB"):
        return "USB"
    if net.startswith("MAX") or net.startswith("THERMO"):
        return "MAX"
    if net in {"FAN_PWM", "FAN_GATE", "HEATER_PWM", "SSR_GATE", "SSR_NEG"}:
        return "PWM"
    if net == "GND":
        return "GND"
    return "TOP" if layer == pcbnew.F_Cu else "BOTTOM"


def render_trace_overlay(board: pcbnew.BOARD, comps: list[Component]) -> Path:
    out = RENDER_DIR / "coffeeroast_actual_traces_overlay.png"
    c = BoardCanvas(2700, 1650, board.GetBoardEdgesBoundingBox(), top_space=155, bottom_space=95)
    draw_title(c, "CoffeeRoast RevA.1 – Leiterbahnen / Netze", "Farben gruppieren reale KiCad-Tracks nach Funktion; weiß = Vias/Anschluss-/Referenzpunkte.")
    legend = [("24V", "+24V/Fan"), ("5V", "+5V"), ("3V3", "+3V3"), ("USB", "USB"), ("MAX", "MAX6675/Thermo"), ("PWM", "PWM/Gates"), ("GND", "GND/Vias")]
    x = 30
    for group, label in legend:
        c.draw.line((x, 116, x + 42, 116), fill=NET_COLORS[group], width=7)
        c.draw.text((x + 52, 104), label, fill=TEXT, font=F_SMALL)
        x += 240
    draw_edges(c, board, color=(120, 126, 134), width=2)
    # Draw bottom first, then top, then grouped highlights.
    tracks = list(board.GetTracks())
    for tr in tracks:
        if type(tr).__name__ == "PCB_VIA" or not hasattr(tr, "GetStart") or not hasattr(tr, "GetEnd"):
            continue
        net = tr.GetNetname()
        group = net_group(net, tr.GetLayer())
        color = NET_COLORS[group]
        s = tr.GetStart(); e = tr.GetEnd()
        width = max(3, min(14, int((tr.GetWidth() / 1e6) * c.scale * 1.25)))
        c.draw.line((*c.xy(s.x / 1e6, s.y / 1e6), *c.xy(e.x / 1e6, e.y / 1e6)), fill=color, width=width)
    for tr in tracks:
        cls = tr.GetClass() if hasattr(tr, "GetClass") else ""
        if "VIA" in str(cls).upper() or not (hasattr(tr, "GetStart") and hasattr(tr, "GetEnd")):
            try:
                p = tr.GetPosition()
            except Exception:
                try:
                    p = tr.GetStart()
                except Exception:
                    continue
            px, py = c.xy(p.x / 1e6, p.y / 1e6)
            c.draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=WHITE, outline=(30, 30, 30), width=2)
    # Important component/connector labels only, so traces remain readable.
    label_refs = ["J1", "F1", "J2", "Q1", "U4", "U3", "U1", "U2", "J5", "J4", "Q2", "J3"]
    comp_by_ref = {comp.ref: comp for comp in comps}
    for ref in label_refs:
        comp = comp_by_ref.get(ref)
        if not comp:
            continue
        c.label_bubble(comp.x, comp.y, ref, (18, 18, 18), radius=20)
        c.callout_label(comp.x, comp.y, f"{ref} {comp.description}", WHITE, dx=20, dy=-22)
    c.image.save(out)
    return out


def rounded_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, lines: Iterable[str], fill: tuple[int, int, int], outline: tuple[int, int, int]):
    draw.rounded_rectangle(box, radius=20, fill=fill, outline=outline, width=3)
    x1, y1, x2, _ = box
    draw.text(((x1 + x2) / 2, y1 + 28), title, fill=WHITE, font=F_BLOCK, anchor="mm")
    y = y1 + 58
    for line in lines:
        draw.text((x1 + 20, y), line, fill=TEXT, font=F_BLOCK_SMALL)
        y += 25


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int], label: str | None = None):
    draw.line((*start, *end), fill=color, width=5)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(1, math.hypot(dx, dy))
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head = [(end[0], end[1]), (end[0] - 18 * ux + 9 * px, end[1] - 18 * uy + 9 * py), (end[0] - 18 * ux - 9 * px, end[1] - 18 * uy - 9 * py)]
    draw.polygon(head, fill=color)
    if label:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        bbox = draw.textbbox((mx, my), label, font=F_SMALL, anchor="mm")
        draw.rounded_rectangle((bbox[0] - 8, bbox[1] - 4, bbox[2] + 8, bbox[3] + 4), radius=7, fill=(16, 18, 22), outline=color)
        draw.text((mx, my), label, fill=WHITE, font=F_SMALL, anchor="mm")


def render_functional_diagram() -> Path:
    out = RENDER_DIR / "coffeeroast_functional_block_diagram.png"
    w, h = 2400, 1350
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.text((32, 22), "CoffeeRoast RevA.1 – Funktionsbild / Bestückungsentscheidung", fill=WHITE, font=F_TITLE)
    d.text((34, 82), "Low-voltage controller PCB: 24V/3A input, external PSU/SSR, no 230VAC on board.", fill=MUTED, font=F_SUB)

    boxes = {
        "in": (90, 210, 390, 345),
        "fuse": (520, 210, 820, 345),
        "fan": (980, 150, 1340, 310),
        "buck": (980, 415, 1340, 575),
        "esp": (1530, 300, 1900, 560),
        "usb": (1980, 195, 2305, 355),
        "thermo": (1980, 650, 2305, 810),
        "max": (1530, 690, 1900, 895),
        "ssr": (980, 760, 1340, 930),
        "heater": (520, 770, 820, 930),
    }
    rounded_box(d, boxes["in"], "J1 24V Input", ["Handlöten", "Pluggable terminal", "PSU/enclosure side"], (45, 32, 18), DNP)
    rounded_box(d, boxes["fuse"], "F1 + D2/C4", ["Fuse/TVS/bulk", "mostly hand/DNP", "24V_FUSED rail"], (45, 32, 18), DNP)
    rounded_box(d, boxes["fan"], "J2 Fan + Q1", ["24V fan output", "Q1 TO-220 handlöten", "R1/R2 JLC PCBA"], (35, 45, 22), DNP)
    rounded_box(d, boxes["buck"], "U4 24→5V / U3 3V3", ["Power modules/footprints", "hand/wire-in for RevA.1", "C1/C2/C3 JLC PCBA"], (40, 38, 20), DNP)
    rounded_box(d, boxes["esp"], "U1 ESP32-S3", ["JLC Standard PCBA", "USB native", "PWM + SPI control"], (18, 45, 32), PCBA)
    rounded_box(d, boxes["usb"], "J5 USB-C", ["JLC PCBA", "R7/R8/R10/R11 JLC", "U5 ESD DNP"], (18, 44, 48), PCBA)
    rounded_box(d, boxes["thermo"], "J4 Thermocouple", ["Handlöten terminal", "strain relief needed", "C5 DNP/noise option"], (45, 32, 18), DNP)
    rounded_box(d, boxes["max"], "U2 MAX6675", ["JLC PCBA", "3.3V SPI bridge", "near K-type input"], (18, 45, 32), PCBA)
    rounded_box(d, boxes["ssr"], "Q2 + J3 SSR Out", ["Q2/R3/R4 JLC PCBA", "terminal handlöten", "external SSR only"], (32, 42, 35), PCBA)
    rounded_box(d, boxes["heater"], "External heater/SSR", ["Not on PCB", "230VAC in enclosure", "checkout requires explicit OK"], (46, 20, 20), (255, 85, 85))

    arrow(d, (390, 278), (520, 278), NET_COLORS["24V"], "+24V_RAW")
    arrow(d, (820, 260), (980, 230), NET_COLORS["24V"], "+24V_FUSED")
    arrow(d, (820, 305), (980, 495), NET_COLORS["24V"], "24V input")
    arrow(d, (1340, 495), (1530, 430), NET_COLORS["3V3"], "+5V/+3V3")
    arrow(d, (1900, 430), (1980, 275), NET_COLORS["USB"], "USB D±/VBUS")
    arrow(d, (1980, 730), (1900, 790), NET_COLORS["MAX"], "K-type")
    arrow(d, (1530, 790), (1340, 840), NET_COLORS["MAX"], "SPI")
    arrow(d, (1530, 505), (1340, 235), NET_COLORS["PWM"], "FAN_PWM")
    arrow(d, (1530, 535), (1340, 840), NET_COLORS["PWM"], "HEATER_PWM")
    arrow(d, (980, 850), (820, 850), NET_COLORS["PWM"], "SSR input")

    # Assembly legend.
    d.rounded_rectangle((90, 1060, 2310, 1260), radius=18, fill=PANEL_DARK, outline=(80, 86, 92), width=2)
    d.ellipse((130, 1112, 160, 1142), fill=PCBA, outline=WHITE)
    d.text((176, 1108), "JLC PCBA: U1, U2, J5, Q2, C1-C3, R1-R8, R10/R11", fill=TEXT, font=F_BLOCK_SMALL)
    d.ellipse((130, 1165, 160, 1195), fill=DNP, outline=WHITE)
    d.text((176, 1161), "Hand/DNP: terminals, fuse, fan MOSFET, power modules, TVS/ESD/filter draft footprints", fill=TEXT, font=F_BLOCK_SMALL)
    d.text((90, 1290), "Use with component/trace maps and JLC preview; do not treat as ERC/DRC proof.", fill=BOARD_EDGE, font=F_SMALL)
    img.save(out)
    return out


def main() -> None:
    RENDER_DIR.mkdir(exist_ok=True)
    board, comps, _, _ = load_data()
    outputs = [
        render_component_map(board, comps),
        render_pcba_only(board, comps),
        render_trace_overlay(board, comps),
        render_functional_diagram(),
    ]
    for p in outputs:
        print(p)


if __name__ == "__main__":
    main()
