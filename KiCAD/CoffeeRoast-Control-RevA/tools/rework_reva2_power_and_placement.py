#!/usr/bin/env python3
"""RevA.2: direct 24V→3V3 rail and accessible controls/test pads."""
from pathlib import Path
import pcbnew

BOARD=Path(__file__).resolve().parents[1]/'CoffeeRoast-Control-RevA.kicad_pcb'

def mm(v): return pcbnew.FromMM(v)
def pos(x,y): return pcbnew.VECTOR2I(mm(x),mm(y))

def add_track(board,a,b,net,width=0.2,layer=pcbnew.F_Cu):
    if a==b: return
    t=pcbnew.PCB_TRACK(board);t.SetStart(a);t.SetEnd(b);t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(net);board.Add(t)

def add_via(board,p,net):
    v=pcbnew.PCB_VIA(board);v.SetPosition(p);v.SetWidth(mm(0.55));v.SetDrill(mm(0.30));v.SetNet(net);board.Add(v)

def move_and_extend_back(board,ref,x,y,width=0.2):
    fp=board.FindFootprintByReference(ref)
    old=[(p.GetPosition(),p.GetNet()) for p in fp.Pads()]
    fp.SetPosition(pos(x,y))
    for (op,net),pad in zip(old,fp.Pads()):
        add_via(board,op,net);add_track(board,pad.GetPosition(),op,net,width,pcbnew.B_Cu)

def move_and_extend(board,ref,x,y,width=0.2):
    fp=board.FindFootprintByReference(ref)
    if not fp: raise SystemExit(f'Missing {ref}')
    old=[(p.GetNumber(),p.GetPosition(),p.GetNet()) for p in fp.Pads()]
    fp.SetPosition(pos(x,y))
    new=list(fp.Pads())
    if len(old)!=len(new): raise SystemExit(f'Pad count changed for {ref}')
    for (_,op,net),pad in zip(old,new): add_track(board,pad.GetPosition(),op,net,width,pcbnew.F_Cu)

def main():
    b=pcbnew.LoadBoard(str(BOARD)); n5=b.FindNet('+5V'); n33=b.FindNet('+3V3')
    if not n33: raise SystemExit('Missing +3V3')
    if n5:
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname()=='+5V': p.SetNet(n33)
        for tr in b.GetTracks():
            if tr.GetNetname()=='+5V': tr.SetNet(n33)
        for z in b.Zones():
            if z.GetNetname()=='+5V': z.SetNet(n33)

    # Remove the redundant 5V→3V3 stage; retain C1 as additional 3V3 bulk decoupling.
    u3=b.FindFootprintByReference('U3')
    if u3: b.Remove(u3)
    tp5=b.FindFootprintByReference('TP5V')
    if tp5: b.Remove(tp5)
    # Remove short copper/vias that belonged only to U3 or the deleted 5V test pad.
    stale={(65.7,80.8),(70.3,80.8),(50.0,72.0),(68.4,76.4),(67.6,76.4),(67.6,80.8),(68.4,80.8),(67.2,75.7),(65.7,81.902),(50.3,81.902)}
    def key(p): return (round(pcbnew.ToMM(p.x),3),round(pcbnew.ToMM(p.y),3))
    discard=[]
    for tr in b.GetTracks():
        if isinstance(tr,pcbnew.PCB_VIA):
            if key(tr.GetPosition()) in stale: discard.append(tr)
        elif key(tr.GetStart()) in stale or key(tr.GetEnd()) in stale: discard.append(tr)
    for tr in discard: b.Remove(tr)
    c1=b.FindFootprintByReference('C1'); c1.SetValue('10uF_3V3_BULK_A'); c1.Value().SetText(c1.GetValue())
    c2=b.FindFootprintByReference('C2'); c2.SetValue('10uF_3V3_BULK_B'); c2.Value().SetText(c2.GetValue())
    u4=b.FindFootprintByReference('U4'); u4.SetValue('24V_TO_3V3_BUCK_MODULE_>=1A_LOW_NOISE');u4.Value().SetText(u4.GetValue())
    j3=b.FindFootprintByReference('J3'); j3.SetValue('SSR_INPUT_3V3_TO_EXTERNAL_SSR');j3.Value().SetText(j3.GetValue())
    c7=b.FindFootprintByReference('C7'); c7.SetValue('100nF_U4_3V3_OUTPUT_DECOUPLING_0603');c7.Value().SetText(c7.GetValue())
    tp=b.FindFootprintByReference('TPSSR1'); tp.SetValue('SSR_3V3_OUT_MEAS_PADS');tp.Value().SetText(tp.GetValue())

    # Move the large TO-220 fan MOSFET down, increasing clearance to Reset/Boot.
    move_and_extend_back(b,'Q1',45.0,58.0,0.45)
    # Move the tweezer test pads left so R5/R6 no longer cover them.
    move_and_extend(b,'TPRESET1',35.0,32.0,0.20)
    move_and_extend(b,'TPBOOT1',35.0,42.0,0.20)

    # TPESP/PADESP remain as two access options; the larger PADESP row is the
    # intended wire/test interface and sits outside the ESP32 module body.

    # Relocate rail test pads out from underneath the former regulator/module area.
    move_and_extend(b,'TP24V',15.0,69.0,0.30)
    move_and_extend(b,'TP3V3',60.0,72.0,0.25)
    move_and_extend(b,'TPGND',58.0,84.0,0.25)

    # Trim two obsolete branch segments left by the removed regulator/test pad.
    trim={frozenset({(47.0,84.0),(47.601,84.0)}),frozenset({(47.601,84.0),(48.202,84.0)}),frozenset({(75.795,81.902),(70.3,81.902)})}
    remove=[]
    for tr in b.GetTracks():
        if isinstance(tr,pcbnew.PCB_VIA): continue
        pair=frozenset({key(tr.GetStart()),key(tr.GetEnd())})
        if pair in trim: remove.append(tr)
    for tr in remove: b.Remove(tr)

    tb=b.GetTitleBlock();tb.SetRevision('A.2-draft')
    tb.SetComment(1,'RevA.2: direct 24V→3V3 buck, 3V3 SSR supply, accessible reset/boot/test pads')
    b.BuildConnectivity()
    for zone in b.Zones(): zone.SetMinThickness(mm(0.20))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(BOARD),b)
    print('Applied RevA.2 power and placement rework')
if __name__=='__main__': main()
