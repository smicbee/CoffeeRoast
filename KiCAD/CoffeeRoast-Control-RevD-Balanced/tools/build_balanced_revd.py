#!/usr/bin/python3
"""Create the visually balanced 96 x 60 mm, two-layer RevD placement from RevC."""
from pathlib import Path
import sys
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_pcb"
W, H = 96.0, 60.0
MARKER = "CoffeeRoast RevD BALANCED V4 UI"
b = pcbnew.LoadBoard(str(P))
if "--force" not in sys.argv and any(
    isinstance(d, pcbnew.PCB_TEXT) and d.GetText() == MARKER for d in b.GetDrawings()
):
    print("RevD edge-antenna placement already applied; no changes made")
    raise SystemExit(0)

# Start from the exact RevC circuit/footprints but not its placement-dependent copper.
for t in list(b.GetTracks()):
    b.Delete(t)
zones = list(b.Zones())
if not zones:
    raise SystemExit("No baseline GND zone found")
zone = zones[0]
for z in zones[1:]:
    b.Delete(z)
for d in list(b.GetDrawings()):
    b.Delete(d)

# Future local UI: compact 1.27 mm through-hole headers. These reserve only
# hardware connectivity; firmware ownership remains deliberately deferred.
ui_connectors = {
    "J7": ("MIC_I2S_FUTURE", ("+3V3", "GND", "GPIO4", "GPIO5", "GPIO6", "GPIO7")),
    "J8": ("LCD_I2C_FUTURE", ("+3V3", "GND", "GPIO8", "GPIO9", "GPIO14", "GPIO21")),
    "J9": ("BUTTONS_4_FUTURE", ("GND", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "+3V3")),
}
fp_by_ref = {f.GetReference(): f for f in b.GetFootprints()}
for ref, (value, nets) in ui_connectors.items():
    if ref not in fp_by_ref:
        f = pcbnew.FootprintLoad(
            "/usr/share/kicad/footprints/Connector_PinHeader_1.27mm.pretty",
            "PinHeader_1x06_P1.27mm_Vertical",
        )
        if f is None:
            raise SystemExit("KiCad 1.27 mm pin-header footprint library is unavailable")
        f.SetReference(ref)
        f.SetValue(value)
        b.Add(f)
        fp_by_ref[ref] = f
    f = fp_by_ref[ref]
    f.SetFPID(pcbnew.LIB_ID(
        "Connector_PinHeader_1.27mm", "PinHeader_1x06_P1.27mm_Vertical"
    ))
    f.SetValue(value)
    f.Value().SetVisible(False)
    pads = sorted(f.Pads(), key=lambda p: int(p.GetNumber()))
    if len(pads) != 6:
        raise SystemExit(f"{ref}: expected six pads, got {len(pads)}")
    for pad, net_name in zip(pads, nets):
        net = b.FindNet(net_name)
        if net is None:
            raise SystemExit(f"{ref}: missing board net {net_name}")
        pad.SetNet(net)

# Functional blocks use the full board while the ESP32 antenna ends flush at the top edge.
pl = {
    # Bottom installation edge, unchanged for field wiring.
    "J4": (5.5, 56.2, 0), "J3": (18.0, 56.2, 0), "J6": (34.0, 56.2, 0),
    "J2": (62.0, 56.2, 0), "J1": (82.0, 56.2, 0),
    # USB and service access occupy the upper-left usable area.
    "J5": (15.0, 6.0, 0), "U5": (26.0, 10.0, 0),
    "R10": (22.0, 15.0, 0), "R11": (30.0, 15.0, 0),
    "JGPIO1": (34.0, 20.0, 0),
    # Thermocouple block moved upward and opened out around U2.
    "U2": (10.0, 35.0, 180), "C5": (16.0, 35.0, 0), "C3": (16.0, 30.5, 0),
    # SSR block between sensor and fan blocks, with generous probing/soldering space.
    "Q2": (22.0, 39.0, 0), "R3": (27.0, 36.0, 0), "R4": (28.0, 43.0, 0),
    "TPSSR1": (20.0, 49.5, 0),
    # Gate-drive support uses the formerly empty centre-left region.
    "R16": (26.0, 30.0, 0), "D5": (29.0, 26.0, 0),
    "C13": (34.0, 31.0, 0), "C14": (38.0, 31.0, 0),
    # Fan driver/current loop remains compact but no longer crowds the sensor block.
    "D3": (37.0, 50.0, 0), "D1": (45.0, 50.0, 0), "Q1": (54.0, 47.0, 0),
    "U6": (36.0, 41.5, 0), "R1": (41.5, 43.0, 0), "R15": (46.0, 41.0, 0),
    "R2": (59.0, 51.0, 0),
    # 24 V input and buck stage moved upward into the space recovered below U1.
    "C4": (64.0, 46.5, 0), "D2": (64.0, 37.0, 0), "U4": (80.0, 41.0, 0),
    "C8": (70.0, 34.0, 90), "C9": (73.0, 41.0, 180), "C12": (74.0, 48.0, 0),
    "C10": (78.0, 48.0, 0), "D4": (84.0, 35.0, 0), "L1": (89.0, 41.0, 0),
    "C11": (91.0, 32.0, 0), "C15": (91.0, 47.0, 0), "R12": (82.0, 48.5, 0),
    "R13": (84.5, 48.5, 90), "R14": (87.0, 48.5, 90), "C7": (86.0, 31.0, 0),
    "C1": (83.0, 28.5, 0), "C2": (89.0, 28.5, 0),
    # U1 is pulled to the top edge: its 18 x 6.2 mm antenna ends flush at y=0.
    "U1": (72.0, 15.9, 0), "C6": (61.0, 27.0, 0),
    "SW1": (42.0, 27.0, 0), "SW2": (46.0, 36.0, 0),
    "R5": (56.0, 30.0, 0), "R6": (56.0, 35.0, 0),
    "TPRESET1": (34.0, 27.0, 0), "TPBOOT1": (39.0, 36.0, 0),
    "R7": (65.0, 45.0, 0), "R8": (69.0, 45.0, 0),
    # Accessible rail probes.
    "TP24V": (29.0, 48.0, 0), "TP3V3": (52.0, 31.0, 0), "TPGND": (52.0, 40.0, 0),
    # Future UI headers at otherwise unused board-edge regions.
    "J7": (3.0, 14.0, 0), "J8": (44.0, 9.0, 0), "J9": (93.0, 12.0, 0),
}
fp = {f.GetReference(): f for f in b.GetFootprints()}
missing = sorted(set(pl) - set(fp))
unplaced = sorted(r for r in fp if not r.startswith("FID") and r not in pl)
if missing or unplaced:
    raise SystemExit(f"missing={missing} unplaced={unplaced}")
for ref, (x, y, angle) in pl.items():
    f = fp[ref]
    f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    f.SetOrientationDegrees(angle)
    show = not (ref.startswith(("R", "C", "J")) or ref in {"U1", "TPRESET1", "TPBOOT1", "TP3V3", "TPGND"})
    f.Reference().SetVisible(show)
    f.Reference().SetPosition(f.GetPosition() + pcbnew.VECTOR2I_MM(0, -2.5))
    f.Reference().SetTextSize(pcbnew.VECTOR2I_MM(0.8, 0.8))
    f.Reference().SetTextThickness(pcbnew.FromMM(0.12))
    f.Value().SetVisible(False)
for refs in (("FID1", "FID2", "FID3"), ("FID4", "FID5", "FID6")):
    for ref, pos in zip(refs, ((3, 3), (92, 58), (40, 3))):
        fp[ref].SetPosition(pcbnew.VECTOR2I_MM(*pos))
        fp[ref].Reference().SetVisible(False)

# Espressif's antenna area is 18 x 6.2 mm. Keep the conservative 15 mm
# side clearance (48 mm total width), but place the antenna's front edge at
# the PCB edge so its forward clearance lies outside the board.
antenna_zones = list(fp["U1"].Zones())
if len(antenna_zones) != 1:
    raise SystemExit(f"expected one U1 antenna keepout, got {len(antenna_zones)}")
antenna = antenna_zones[0]
outline = antenna.Outline(); outline.RemoveAllContours(); outline.NewOutline()
for x, y in ((48.0, 0.0), (96.0, 0.0), (96.0, 6.2), (48.0, 6.2)):
    outline.Append(pcbnew.VECTOR2I_MM(x, y))

def edge(a, c):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(0.15))
    s.SetStart(pcbnew.VECTOR2I_MM(*a))
    s.SetEnd(pcbnew.VECTOR2I_MM(*c))
    b.Add(s)
for a, c in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
    edge(a, c)

def text(s, x, y, layer=pcbnew.F_SilkS, size=0.8):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s); t.SetLayer(layer); t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    t.SetTextSize(pcbnew.VECTOR2I_MM(max(size, 0.8), max(size, 0.8)))
    t.SetTextThickness(pcbnew.FromMM(0.12))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    b.Add(t)

for s, x, y in (("THERMO", 5.5, 51.8), ("SSR", 18.0, 52.5), ("ESC", 29.5, 52.5),
                ("FAN", 62, 52.5), ("24V IN", 82, 52.5), ("GPIO", 34, 23.0)):
    text(s, x, y)
for s, x, y in (("TC+ TC-", 5.5, 59), ("3V3 SSR-", 18.0, 59), ("24 G P G", 34, 59),
                ("24 FAN-", 62, 59), ("24 GND", 82, 59), ("3 46 9 10 48 45", 34, 17)):
    text(s, x, y)
text("USB-C DATA", 15, 10.5, size=0.85)
text("RESET", 49, 22.5); text("BOOT", 49, 41.0)
text("3V3", 49.5, 29.0); text("GND", 54.5, 40.0)
text("USB + ESD", 15, 18.5)
text("MAX6675 THERMO", 10, 28.5)
text("SSR DRIVER", 21, 32.5)
text("10V GATE SUPPLY", 30, 34.0)
text("FAN DRIVER", 39, 45.5)
text("FAN MOSFET", 54, 42.0)
text("ESP32-S3", 70, 27.0)
text("BUCK 24V > 3V3", 85, 51.0)
text("MIC / I2S", 7.0, 24.5)
text("LCD / I2C", 44.0, 17.5)
text("BUTTONS 1-4", 88.0, 9.0); text("G 1 2 3 4 3V", 88.0, 21.5)
# Revision/safety identity is kept on the bottom silkscreen where it remains legible.
for s, x in (("THERMO TC+ TC-", 7), ("SSR 3V3 SSR-", 18), ("ESC 24 GND PWM GND", 34),
             ("FAN 24 FAN-", 62), ("POWER 24 GND", 82)):
    text(s, x, 52, pcbnew.B_SilkS)
text("GPIO 3 46 9 10 48 45", 34, 24, pcbnew.B_SilkS)
text("USB-C DATA / FLASH", 15, 11, pcbnew.B_SilkS)
text("USB + ESD", 15, 18.5, pcbnew.B_SilkS)
text("MAX6675 THERMO", 10, 30.0, pcbnew.B_SilkS)
text("SSR DRIVER", 22, 37.0, pcbnew.B_SilkS)
text("FAN GATE DRIVER", 38, 44.0, pcbnew.B_SilkS)
text("ESP32-S3 WIFI / BT", 70, 24.0, pcbnew.B_SilkS)
text("BUCK 24V > 3V3", 85, 35.0, pcbnew.B_SilkS)
text("ANTENNA - KEEP CLEAR", 72, 4.0, pcbnew.B_SilkS)
text("MIC/I2S 3V G B W D S", 10.0, 25.0, pcbnew.B_SilkS)
text("LCD/I2C 3V G SDA SCL INT RST", 47.0, 22.5, pcbnew.B_SilkS)
text("BUTTONS G 1 2 3 4 3V", 87.0, 23.5, pcbnew.B_SilkS)
text(MARKER, 28, 27.0, pcbnew.B_SilkS, 0.8)
text("24V SELV ONLY - NO 230V", 28, 29.0, pcbnew.B_SilkS)

poly = zone.Outline(); poly.RemoveAllContours(); poly.NewOutline()
for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):
    poly.Append(pcbnew.VECTOR2I_MM(x, y))
zone.SetLayer(pcbnew.B_Cu)
zone.SetLocalClearance(pcbnew.FromMM(0.25)); zone.SetMinThickness(pcbnew.FromMM(0.25))
tb = b.GetTitleBlock(); tb.SetRevision("D-UI")
tb.SetComment(1, "RevD Balanced UI: MIC, I2C LCD and four-button headers reserved; firmware deferred")
b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I_MM(0, H))
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(P), b)
print(f"Placed RevD Balanced {W} x {H} mm")
