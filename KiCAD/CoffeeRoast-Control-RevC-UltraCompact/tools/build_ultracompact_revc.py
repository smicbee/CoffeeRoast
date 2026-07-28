#!/usr/bin/python3
"""Repack the proven RevB circuit onto a 96 x 60 mm RevC board."""
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'CoffeeRoast-Control-RevC-UltraCompact.kicad_pcb'
W,H=96.0,60.0
MARKER='CoffeeRoast RevC ULTRACOMPACT'
b=pcbnew.LoadBoard(str(P))
if any(isinstance(d,pcbnew.PCB_TEXT) and d.GetText()==MARKER for d in b.GetDrawings()):
 print('RevC placement already applied; no changes made');raise SystemExit(0)
for t in list(b.GetTracks()): b.Delete(t)
zones=list(b.Zones()); zone=zones[0]
for z in zones[1:]: b.Delete(z)
for d in list(b.GetDrawings()): b.Delete(d)

pl={
 # Common field-connector edge (bottom).
 'J4':(5.5,56.2,0),'J3':(16.5,56.2,0),'J6':(32.0,56.2,0),
 'J2':(53.5,56.2,0),'J1':(64.0,56.2,0),'JGPIO1':(32.0,20.0,0),
 # Thermocouple and SSR close to their connectors.
 'U2':(10.0,43.0,180),'C5':(16.0,43.0,0),'C3':(16.0,39.0,0),
 'Q2':(22.0,45.0,0),'R3':(26.0,42.0,0),'R4':(27.0,48.0,0),'TPSSR1':(20.0,51.0,0),
 # Fan driver/current loop.
 'D1':(44.0,51.0,0),'D3':(36.0,51.0,0),'Q1':(54.0,48.0,0),'U6':(34.0,44.0,0),
 'R1':(39.0,41.0,0),'R15':(43.0,43.0,0),'R2':(58.0,52.0,0),
 'R16':(25.0,38.0,0),'D5':(25.0,34.0,0),'C13':(31.0,36.0,0),'C14':(35.0,36.0,0),
 # 24V -> 3V3 power stage above J1/JGPIO.
 'C4':(64.0,50.0,0),'D2':(57.0,40.0,0),'U4':(81.0,50.0,0),
 'C8':(41.0,18.0,90),'C9':(74.0,50.0,180),'C12':(73.0,57.0,0),
 'C10':(78.0,56.0,0),'D4':(86.0,43.0,0),'L1':(89.0,50.0,0),
 'C11':(91.0,39.0,0),'C15':(91.0,55.0,0),'R12':(82.0,57.0,0),
 'R13':(84.5,57.0,90),'R14':(87.0,57.0,90),'C7':(86.0,39.0,0),
 'C1':(84.0,35.0,0),'C2':(90.0,35.0,0),'TP24V':(36.0,30.0,0),
 'TP3V3':(88.0,32.0,0),'TPGND':(93.0,32.0,0),
 # ESP32/controls; antenna keepout occupies x45..93, y0..21.
 'U1':(72.0,33.75,0),'C6':(61.0,27.0,0),'SW1':(47.0,28.0,0),'SW2':(46.0,36.0,0),
 'R5':(56.0,31.0,0),'R6':(56.0,35.0,0),'TPRESET1':(40.0,28.0,0),'TPBOOT1':(40.0,37.0,0),
 # USB opposite the field-connector edge.
 'J5':(15.0,6.0,0),'U5':(26.0,10.0,0),'R10':(22.0,15.0,0),'R11':(30.0,15.0,0),
 'R7':(65.0,46.0,0),'R8':(69.0,46.0,0),
}
fp={f.GetReference():f for f in b.GetFootprints()}
missing=sorted(set(pl)-set(fp));unplaced=sorted(r for r in fp if not r.startswith('FID') and r not in pl)
if missing or unplaced: raise SystemExit(f'missing={missing} unplaced={unplaced}')
for ref,(x,y,a) in pl.items():
 f=fp[ref];f.SetPosition(pcbnew.VECTOR2I_MM(x,y));f.SetOrientationDegrees(a)
 show=not(ref.startswith(('R','C','J')) or ref in {'U1','TPRESET1','TPBOOT1'})
 f.Reference().SetVisible(show);f.Reference().SetPosition(f.GetPosition()+pcbnew.VECTOR2I_MM(0,-2.5))
 f.Reference().SetTextSize(pcbnew.VECTOR2I_MM(.8,.8));f.Reference().SetTextThickness(pcbnew.FromMM(.12));f.Value().SetVisible(False)
for refs in [('FID1','FID2','FID3'),('FID4','FID5','FID6')]:
 for ref,p in zip(refs,[(3,3),(92,58),(40,3)]):
  fp[ref].SetPosition(pcbnew.VECTOR2I_MM(*p));fp[ref].Reference().SetVisible(False)

def seg(a,c):
 s=pcbnew.PCB_SHAPE(b);s.SetShape(pcbnew.SHAPE_T_SEGMENT);s.SetLayer(pcbnew.Edge_Cuts);s.SetWidth(pcbnew.FromMM(.15));s.SetStart(pcbnew.VECTOR2I_MM(*a));s.SetEnd(pcbnew.VECTOR2I_MM(*c));b.Add(s)
for a,c in [((0,0),(W,0)),((W,0),(W,H)),((W,H),(0,H)),((0,H),(0,0))]:seg(a,c)
def text(s,x,y,layer=pcbnew.F_SilkS,size=.8):
 t=pcbnew.PCB_TEXT(b);t.SetText(s);t.SetLayer(layer);t.SetPosition(pcbnew.VECTOR2I_MM(x,y));t.SetTextSize(pcbnew.VECTOR2I_MM(max(size,.8),max(size,.8)));t.SetTextThickness(pcbnew.FromMM(.12));
 if layer==pcbnew.B_SilkS:t.SetMirrored(True)
 b.Add(t)
# Front: connector name above, pin order below/along edge.
for s,x,y in [('THERMO',5.5,51.8),('SSR',14.0,52.5),('ESC',30,52.5),('FAN',52,52.5),('24V IN',64,53.0),('GPIO',32,23.0)]:text(s,x,y,size=.8)
for s,x,y in [('TC+ TC-',5.5,59),('3V3 SSR-',16.5,59),('24 G P G',32,59),('24 FAN-',53.5,59),('24 GND',64,59),('3 46 9 10 48 45',32,17)]:text(s,x,y,size=.8)
text('USB-C DATA',15,10.5,size=.85);text('RESET',48,23.5);text('BOOT',48,41.5)
text(MARKER,15,25,size=1.0);text('24V SELV ONLY - NO 230V',15,27,size=.8)
# Back repeats the connection map.
for s,x in [('THERMO TC+ TC-',7),('SSR 3V3 SSR-',20),('ESC 24 GND PWM GND',36),('FAN 24 FAN-',52),('POWER 24 GND',66)]:text(s,x,52,pcbnew.B_SilkS,.8)
text('GPIO 3 46 9 10 48 45',32,24,pcbnew.B_SilkS,.8)
text('USB-C DATA / FLASH',15,11,pcbnew.B_SilkS,.8);text(MARKER,15,27,pcbnew.B_SilkS,1.0);text('24V SELV ONLY - NO 230V',15,29,pcbnew.B_SilkS,.8)
poly=zone.Outline();poly.RemoveAllContours();poly.NewOutline()
for x,y in ((.5,.5),(W-.5,.5),(W-.5,H-.5),(.5,H-.5)):poly.Append(pcbnew.VECTOR2I_MM(x,y))
zone.SetLayer(pcbnew.B_Cu);zone.SetLocalClearance(pcbnew.FromMM(.25));zone.SetMinThickness(pcbnew.FromMM(.25))
tb=b.GetTitleBlock();tb.SetRevision('C-UltraCompact');tb.SetComment(1,'RevC UltraCompact: 96x60 mm, field connectors on one edge, USB opposite, 45-degree routing')
b.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I_MM(0,H));b.BuildConnectivity();pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(P),b)
print(f'Placed RevC {W} x {H} mm')
