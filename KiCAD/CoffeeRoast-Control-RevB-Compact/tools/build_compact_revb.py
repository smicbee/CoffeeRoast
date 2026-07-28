#!/usr/bin/python3
"""Create the compact RevB placement/outline from the proven ordered RevA.2.

The script intentionally removes all old copper and redundant per-pin ESP32 probe
pads. It preserves the proven schematic, exact footprints and net assignments,
then creates the mechanically constrained compact placement for rerouting.
"""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "CoffeeRoast-Control-RevB-Compact.kicad_pcb"
W, H = 105.0, 75.0
MARKER = "CoffeeRoast RevB COMPACT"

b = pcbnew.LoadBoard(str(BOARD_PATH))
if not b:
    raise SystemExit(f"Cannot load {BOARD_PATH}")

for d in b.GetDrawings():
    if isinstance(d, pcbnew.PCB_TEXT) and MARKER in d.GetText():
        print(f"Compact RevB placement already applied to {BOARD_PATH}; no changes made")
        raise SystemExit(0)

# All routed copper belongs to the larger RevA.2 placement and is invalid here.
for item in list(b.GetTracks()):
    b.Delete(item)

# Preserve the existing GND-zone settings object, but remove any extra zones.
zones = list(b.Zones())
zone = zones[0] if zones else None
for extra in zones[1:]:
    b.Delete(extra)

# Redundant all-pin probe/solder arrays dominated the old board area. RevB keeps
# the purposeful JGPIO1 spare-GPIO row plus RESET/BOOT/rail test pads.
for fp in list(b.GetFootprints()):
    ref = fp.GetReference()
    if ref.startswith("TPESP") or ref.startswith("PADESP"):
        b.Delete(fp)

# Board-level notes and the old 160 x 100 mm outline are rebuilt from scratch.
for drawing in list(b.GetDrawings()):
    b.Delete(drawing)

placements = {
    # One external wiring edge (left), ordered by signal sensitivity/function.
    "J4": (5.5, 6.0, 0),
    "C5": (15.0, 8.0, 0),
    "U2": (25.0, 8.0, 180),
    "C3": (31.0, 13.0, 0),
    "J3": (5.5, 16.0, 0),
    "Q2": (18.0, 18.0, 0),
    "R3": (23.0, 16.0, 0),
    "R4": (23.0, 21.0, 0),
    "TPSSR1": (30.0, 19.0, 0),
    "J6": (5.0, 36.0, 90),
    "J2": (5.5, 52.0, 0),
    "D1": (14.0, 51.0, 0),
    "D3": (17.0, 46.0, 0),
    "Q1": (36.0, 49.0, 0),
    "U6": (28.0, 48.0, 0),
    "R1": (30.0, 43.0, 0),
    "R15": (34.0, 43.0, 0),
    "R2": (48.0, 44.0, 90),
    "R16": (20.0, 42.0, 0),
    "D5": (20.0, 38.0, 0),
    "C13": (25.0, 39.0, 0),
    "C14": (29.0, 39.0, 0),
    "J1": (5.5, 66.0, 0),
    "C4": (14.0, 66.0, 0),
    "D2": (19.0, 58.0, 0),
    # Compact 24V -> 3V3 power stage.
    "U4": (34.0, 64.0, 0),
    "C8": (25.0, 60.0, 0),
    "C9": (25.0, 66.0, 0),
    "C12": (25.0, 71.0, 0),
    "C10": (34.0, 58.0, 0),
    "D4": (41.0, 58.0, 0),
    "L1": (44.0, 65.0, 0),
    "C11": (52.0, 63.0, 0),
    "C15": (52.0, 69.0, 0),
    "R12": (40.0, 71.0, 0),
    "R13": (35.0, 71.0, 90),
    "R14": (31.0, 71.0, 90),
    "C7": (55.0, 59.0, 0),
    "C1": (60.0, 62.0, 0),
    "C2": (65.0, 62.0, 0),
    "TP24V": (19.0, 72.0, 0),
    "TP3V3": (58.0, 68.0, 0),
    "TPGND": (63.0, 68.0, 0),
    # ESP32 with its antenna keepout on the top edge.
    "U1": (79.5, 33.75, 0),
    "C6": (69.0, 27.0, 0),
    "SW1": (60.0, 28.0, 0),
    "SW2": (60.0, 37.0, 0),
    "R5": (68.0, 31.0, 0),
    "R6": (68.0, 35.0, 0),
    "TPRESET1": (54.0, 28.0, 0),
    "TPBOOT1": (54.0, 37.0, 0),
    # USB is the opposite external edge.
    "J5": (101.3, 40.0, 90),
    "U5": (94.0, 51.0, 0),
    "R7": (76.0, 47.0, 0),
    "R8": (82.0, 47.0, 0),
    "R10": (94.0, 34.0, 0),
    "R11": (94.0, 46.0, 0),
    # Secondary expansion row; all primary field wiring remains on the left.
    "JGPIO1": (77.0, 72.0, 0),
}

present = {fp.GetReference(): fp for fp in b.GetFootprints()}
missing = sorted(set(placements) - set(present))
if missing:
    raise SystemExit(f"Required footprints missing: {missing}")
functional = sorted(r for r in present if not r.startswith("FID"))
unplaced = sorted(set(functional) - set(placements))
if unplaced:
    raise SystemExit(f"Functional footprints lack compact placement: {unplaced}")

for ref, (x, y, rot) in placements.items():
    fp = present[ref]
    fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    fp.SetOrientationDegrees(rot)
    show_ref = not (
        ref.startswith("R") or (ref.startswith("C") and ref != "C4")
        or ref in {"U1", "TPRESET1", "TPBOOT1", "JGPIO1"}
    )
    fp.Reference().SetVisible(show_ref)
    fp.Reference().SetPosition(fp.GetPosition() + pcbnew.VECTOR2I_MM(0, -3.0))
    fp.Reference().SetTextSize(pcbnew.VECTOR2I_MM(0.8, 0.8))
    fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
    fp.Value().SetVisible(False)

# Three global fiducials per assembly side; top-right antenna region is avoided.
fid_positions = [(3.0, 3.0), (50.0, 72.0), (102.0, 72.0)]
for i, ref in enumerate(("FID1", "FID2", "FID3")):
    if ref in present:
        present[ref].SetPosition(pcbnew.VECTOR2I_MM(*fid_positions[i]))
        present[ref].Reference().SetVisible(False)
for i, ref in enumerate(("FID4", "FID5", "FID6")):
    if ref in present:
        present[ref].SetPosition(pcbnew.VECTOR2I_MM(*fid_positions[i]))
        present[ref].Reference().SetVisible(False)


def segment(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(pcbnew.FromMM(0.15))
    s.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
    s.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
    b.Add(s)

segment(0, 0, W, 0)
segment(W, 0, W, H)
segment(W, H, 0, H)
segment(0, H, 0, 0)


def add_text(text, x, y, layer=pcbnew.F_SilkS, size=0.8, angle=0, justify=pcbnew.GR_TEXT_H_ALIGN_CENTER):
    size = max(size, 0.8)
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
    t.SetTextThickness(pcbnew.FromMM(max(0.12, size * 0.15)))
    t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    t.SetHorizJustify(justify)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    b.Add(t)

# Front labels: field wiring edge and service functions.
front = [
    ("THERMO", 12.5, 4.2, 0.9), ("TC+   TC-", 12.5, 11.8, 0.65),
    ("SSR OUT", 13.5, 14.0, 0.85), ("3V3   SSR-", 14.0, 22.2, 0.65),
    ("ESC", 12.0, 17.5, 0.9),
    ("24V", 10.5, 36.0, 0.8), ("GND", 10.5, 30.92, 0.8),
    ("PWM", 10.5, 25.84, 0.8), ("GND", 10.5, 20.76, 0.8),
    ("FAN OUT", 7.0, 57.0, 0.9), ("24V   FAN-", 14.0, 54.8, 0.65),
    ("24V IN", 12.5, 61.7, 0.9), ("24V   GND", 14.0, 69.8, 0.65),
    ("RESET", 60.0, 23.5, 0.75), ("BOOT", 60.0, 41.8, 0.75),
    ("USB-C DATA", 96.0, 55.0, 0.75),
    ("MAX6675", 25.0, 3.2, 0.65), ("FAN DRIVER", 34.0, 53.5, 0.65),
    ("24V -> 3V3 BUCK", 41.0, 73.3, 0.65),
    (MARKER, 79.0, 56.0, 0.95), ("24V SELV ONLY - NO 230V", 79.0, 58.2, 0.65),
    ("GPIO BREAKOUT", 77.0, 69.7, 0.6),
]
for text, x, y, size in front:
    add_text(text, x, y, size=size)

# Back side repeats every external connector pinout and the safety identity.
back = [
    ("THERMO: TC+ | TC-", 18.0, 5.0, 0.7),
    ("SSR: 3V3 | SSR-", 18.0, 15.0, 0.7),
    ("ESC: 24V | GND | PWM | GND", 22.0, 26.0, 0.65),
    ("FAN: 24V | FAN-", 18.0, 47.0, 0.7),
    ("POWER: 24V | GND", 18.0, 61.5, 0.7),
    ("USB-C DATA / FLASH", 89.0, 50.0, 0.7),
    ("RESET", 54.0, 28.0, 0.65), ("BOOT", 54.0, 37.0, 0.65),
    (MARKER, 75.0, 56.0, 0.9), ("24V SELV ONLY - NO 230V", 75.0, 58.0, 0.65),
    ("GPIO3  46  9  10  48  45", 77.0, 69.5, 0.55),
]
for text, x, y, size in back:
    add_text(text, x, y, layer=pcbnew.B_SilkS, size=size)

# Resize/recreate the B.Cu GND zone to the compact outline.
if zone is None:
    zone = pcbnew.ZONE(b)
    zone.SetLayer(pcbnew.B_Cu)
    gnd = b.FindNet("GND")
    if gnd:
        zone.SetNet(gnd)
    b.Add(zone)
poly = zone.Outline()
poly.RemoveAllContours()
poly.NewOutline()
for x, y in ((0.5, 0.5), (W-0.5, 0.5), (W-0.5, H-0.5), (0.5, H-0.5)):
    poly.Append(pcbnew.VECTOR2I_MM(x, y))
zone.SetLayer(pcbnew.B_Cu)
zone.SetLocalClearance(pcbnew.FromMM(0.25))
zone.SetMinThickness(pcbnew.FromMM(0.25))

b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I_MM(0, H))
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(str(BOARD_PATH), b)
print(f"Placed compact RevB: {W:.0f} x {H:.0f} mm, {len(list(b.GetFootprints()))} footprints")
