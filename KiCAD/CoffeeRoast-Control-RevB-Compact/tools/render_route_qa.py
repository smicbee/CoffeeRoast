#!/usr/bin/python3
"""Render exact RevB copper for visual route QA without KiCad GUI."""
from pathlib import Path
import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "CoffeeRoast-Control-RevB-Compact.kicad_pcb"
OUT = ROOT / "render" / "final"
OUT.mkdir(parents=True, exist_ok=True)
SCALE = 18
MARGIN = 70
W, H = 105.0, 75.0
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT = ImageFont.truetype(FONT_PATH, 14)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 11)

b = pcbnew.LoadBoard(str(BOARD))

def xy(x_mm, y_mm):
    return MARGIN + x_mm * SCALE, MARGIN + y_mm * SCALE

def color_for(t):
    n = t.GetNetname()
    if n == "+24V_RAW": return (255, 150, 20)
    if n == "FAN_NEG": return (255, 225, 30)
    if n == "BUCK_SW": return (255, 50, 190)
    if n in {"USB_DP", "USB_DN", "USB_DP_MCU", "USB_DN_MCU"}: return (60, 255, 100)
    if n == "GND": return (155, 155, 165)
    if t.GetLayer() == pcbnew.F_Cu: return (255, 75, 75)
    return (50, 200, 255)

def render(name, layers):
    img = Image.new("RGB", (int(W*SCALE+2*MARGIN), int(H*SCALE+2*MARGIN)), (15,18,23))
    d = ImageDraw.Draw(img)
    d.rectangle((*xy(0,0),*xy(W,H)), fill=(35,55,48), outline=(245,235,130), width=3)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p=t.GetPosition(); x,y=xy(p.x/1e6,p.y/1e6); r=max(3,t.GetWidth(pcbnew.F_Cu)/1e6*SCALE/2)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(210,170,40),outline=(255,255,255))
            continue
        if t.GetLayer() not in layers: continue
        s,e=t.GetStart(),t.GetEnd(); width=max(2,round(t.GetWidth()/1e6*SCALE))
        d.line((*xy(s.x/1e6,s.y/1e6),*xy(e.x/1e6,e.y/1e6)),fill=color_for(t),width=width)
    for fp in b.GetFootprints():
        ref=fp.GetReference()
        if ref.startswith("FID"): continue
        for p in fp.Pads():
            q=p.GetPosition(); x,y=xy(q.x/1e6,q.y/1e6)
            sx=max(3,p.GetSize().x/1e6*SCALE/2); sy=max(3,p.GetSize().y/1e6*SCALE/2)
            d.ellipse((x-sx,y-sy,x+sx,y+sy),fill=(210,165,35),outline=(250,215,80))
            if p.HasHole():
                hs=p.GetDrillSize(); hr=max(2,min(hs.x,hs.y)/1e6*SCALE/2)
                d.ellipse((x-hr,y-hr,x+hr,y+hr),fill=(15,18,23))
        pos=fp.GetPosition(); x,y=xy(pos.x/1e6,pos.y/1e6)
        if ref.startswith(("J","U","Q","SW","L")):
            d.text((x+4,y+4),ref,font=FONT_SMALL,fill=(255,255,255))
    d.text((MARGIN,20),f"CoffeeRoast RevB Compact — {name}",font=FONT,fill=(255,255,255))
    d.text((MARGIN,42),"orange=24V  yellow=FAN_NEG  magenta=BUCK_SW  green=USB  red=F.Cu  cyan=B.Cu",font=FONT_SMALL,fill=(210,215,225))
    img.save(OUT/f"routing_{name.lower()}.png")

render("TOP", {pcbnew.F_Cu})
render("BOTTOM", {pcbnew.B_Cu})
render("COMBINED", {pcbnew.F_Cu, pcbnew.B_Cu})
print(OUT)
