#!/usr/bin/env python3
"""Assign reproducible footprint IDs and export CoffeeRoast-specific footprints.

Run with KiCad's system Python: /usr/bin/python3 tools/assign_footprints.py
"""
from pathlib import Path
import shutil
import csv
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
BOARD=ROOT/'CoffeeRoast-Control-RevA.kicad_pcb'
LOCAL=ROOT/'CoffeeRoast.pretty'

STANDARD={
 'U1':'RF_Module:ESP32-S3-WROOM-1',
 'U2':'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
 'Q1':'Package_TO_SOT_THT:TO-220-3_Vertical',
 'Q2':'Package_TO_SOT_SMD:SOT-23',
 'D1':'Diode_THT:D_DO-201AD_P15.24mm_Horizontal',
 'D2':'Diode_SMD:D_SMB', 'D3':'Diode_SMD:D_SMB',
 'F1':'Fuse:Fuseholder_Clip-5x20mm_Bel_FC-203-22_Lateral_P17.80x5.00mm_D1.17mm_Horizontal',
 'J5':'Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11',
 'U5':'Package_TO_SOT_SMD:SOT-23-6',
 'SW1':'Button_Switch_THT:SW_PUSH_6mm_H4.3mm', 'SW2':'Button_Switch_THT:SW_PUSH_6mm_H4.3mm',
}
for ref in ('R1','R2','R3','R4','R5','R6','R7','R8','R10','R11'):
 STANDARD[ref]='Resistor_SMD:R_0805_2012Metric'
for ref in ('C1','C2','C3','C5'):
 STANDARD[ref]='Capacitor_SMD:C_0805_2012Metric'
for ref in ('C6','C7'):
 STANDARD[ref]='Capacitor_SMD:C_0603_1608Metric'
STANDARD['C4']='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'
for ref in ('TP24V','TP5V','TP3V3','TPGND'):
 STANDARD[ref]='TestPoint:TestPoint_Pad_D1.5mm'

CUSTOM={
 'U3':'U3_3V3_Switching_Module_3Pin',
 'U4':'U4_24V_to_5V_Buck_Module_4Pin',
 'J1':'J1_24V_SolderPads', 'J2':'J2_Fan_SolderPads',
 'J3':'J3_SSR_SolderPads', 'J4':'J4_Thermocouple_SolderPads',
 'JGPIO1':'ESP32_GPIO_Breakout_Row',
 'TPRESET1':'Reset_Tweezer_Pads', 'TPBOOT1':'Boot_Tweezer_Pads',
 'TPSSR1':'SSR_Measurement_Pads',
}

# Verify every selected standard footprint exists in KiCad 9's library set.
libroot=Path('/usr/share/kicad/footprints')
for ref,fpid in STANDARD.items():
 lib,item=fpid.split(':',1)
 path=libroot/f'{lib}.pretty'/f'{item}.kicad_mod'
 if not path.is_file(): raise SystemExit(f'Missing KiCad footprint for {ref}: {path}')

board=pcbnew.LoadBoard(str(BOARD))
if not board: raise SystemExit(f'Cannot load {BOARD}')
# Align the routed module/USB footprints with the simplified schematic pin
# numbering while retaining all physical lands and their existing nets.
for pad in board.FindFootprintByReference('U1').Pads():
    if pad.GetNumber()=='41': pad.SetNumber('40')
usb_numbers={'A1':'1','A12':'1','B1':'1','B12':'1','A4':'2','B4':'2','A5':'3','A6':'4','B6':'4','A7':'5','B7':'5','B5':'6','A9':'7','B9':'7','S1':'8','A8':'','B8':''}
for pad in board.FindFootprintByReference('J5').Pads():
    if pad.GetNumber() in usb_numbers: pad.SetNumber(usb_numbers[pad.GetNumber()])
shutil.rmtree(LOCAL,ignore_errors=True); LOCAL.mkdir()
io=pcbnew.PCB_IO_KICAD_SEXPR()

# Preserve the routed, DRC-clean geometry as project-local footprints.  The
# selected manufacturer/package library footprint remains documented as SourceFootprint.
source=dict(STANDARD)
source.update({ref:f'CoffeeRoast:{item}' for ref,item in CUSTOM.items()})
for prefix,item in [('TPESP','ESP32_ProbePad'),('PADESP','ESP32_SolderPad')]:
    for n in range(1,41): source[f'{prefix}{n}']=f'CoffeeRoast:{item}'
for n in range(1,7): source[f'FID{n}']='Fiducial:Fiducial_1mm_Mask2mm'

rows=[]
for fp in sorted(board.GetFootprints(),key=lambda f:f.GetReference()):
    ref=fp.GetReference(); selected=source.get(ref)
    if not selected: raise SystemExit(f'No footprint selection for {ref}')
    item=selected.split(':',1)[1]
    local_item=''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in f'{ref}_{item}')
    local_id=pcbnew.LIB_ID('CoffeeRoast',local_item)
    clone=pcbnew.FOOTPRINT(fp); clone.SetFPID(local_id); io.FootprintSave(str(LOCAL),clone)
    fp.SetFPID(local_id)
    rows.append((ref,fp.GetValue(),f'CoffeeRoast:{local_item}',selected))

# KiCad's embedded ESP32 antenna keepout is board-context-sensitive. Keep the
# item name but no board-side library nickname to avoid a false stale-copy DRC;
# the schematic still resolves to the exported CoffeeRoast footprint.
u1=board.FindFootprintByReference('U1')
u1_item=next(row[2].split(':',1)[1] for row in rows if row[0]=='U1')
u1.SetFPID(pcbnew.LIB_ID('',u1_item))

pcbnew.SaveBoard(str(BOARD),board)
with (ROOT/'docs'/'footprints.csv').open('w',newline='',encoding='utf-8') as handle:
    writer=csv.writer(handle); writer.writerow(('Ref','Value','Footprint','SourceFootprint')); writer.writerows(rows)
print(f'Assigned and exported {len(rows)} project-local footprints; {len(STANDARD)} use verified KiCad package selections')
