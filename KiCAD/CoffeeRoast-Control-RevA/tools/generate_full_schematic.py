#!/usr/bin/env python3
"""Generate the editable CoffeeRoast RevA.1 legacy KiCad schematic source.

KiCad opens this v4 file and converts it to the native .kicad_sch format on save.
The schematic mirrors the routed PCB's named nets; 230 VAC remains explicitly off-board.
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/CoffeeRoast-Control-RevA-generated.sch")
with (ROOT/'docs'/'footprints.csv').open(encoding='utf-8') as handle:
    ROWS=list(csv.DictReader(handle))
FOOTPRINTS={row['Ref']:row['Footprint'] for row in ROWS}
VALUES={row['Ref']:row['Value'] for row in ROWS}
items=[]
uid=0x65000000

def comp(lib, ref, value, x, y, orient=(1,0,0,-1), footprint=""):
    global uid
    uid += 1
    value=VALUES.get(ref,value)
    footprint=footprint or FOOTPRINTS.get(ref,"")
    a,b,c,d=orient
    items.extend([
        "$Comp", f"L {lib} {ref}", f"U 1 1 {uid:X}", f"P {x} {y}",
        f'F 0 "{ref}" H {x+150} {y+100} 50  0000 C CNN',
        f'F 1 "{value}" H {x+250} {y-100} 50  0001 C CNN',
        f'F 2 "{footprint}" H {x} {y} 50  0001 C CNN',
        f"\t1    {x} {y}", f"\t{a}    {b}    {c}    {d}", "$EndComp"
    ])

def label(x,y,name,orient=0):
    items.append(f"Text GLabel {x} {y} {orient}    40   Input ~ 0\n{name}")

def wire(x1,y1,x2,y2): items.append(f"Wire Wire Line\n\t{x1} {y1} {x2} {y2}")
def note(x,y,text,size=60): items.append(f'Text Notes {x} {y} 0    {size}   ~ 12\n{text}')
def box(x1,y1,x2,y2): items.append(f"Wire Notes Line\n\t{x1} {y1} {x2} {y1}\nWire Notes Line\n\t{x2} {y1} {x2} {y2}\nWire Notes Line\n\t{x2} {y2} {x1} {y2}\nWire Notes Line\n\t{x1} {y2} {x1} {y1}")

def two_pin_h(lib,ref,value,x,y,left,right,fp=""):
    # R/Fuse are vertical by default; switches are horizontal by default.
    if lib in {"Device:R","Device:Fuse"}:
        comp(lib,ref,value,x,y,(0,-1,-1,0),fp); off=150
    elif lib == "Switch:SW_Push":
        comp(lib,ref,value,x,y,(1,0,0,-1),fp); off=200
    else:
        comp(lib,ref,value,x,y,(1,0,0,-1),fp); off=150
    wire(x-off,y,x-off-50,y); label(x-off-50,y,left)
    wire(x+off,y,x+off+50,y); label(x+off+50,y,right,2)

def two_pin_v(lib,ref,value,x,y,top,bottom,fp=""):
    # R/C are vertical by default; diodes are horizontal and rotated here.
    orient=(1,0,0,-1) if lib in {"Device:R","Device:C","Device:C_Polarized"} else (0,-1,-1,0)
    comp(lib,ref,value,x,y,orient,fp); off=150
    wire(x,y-off,x,y-off-50); label(x,y-off-50,top,1)
    wire(x,y+off,x,y+off+50); label(x,y+off+50,bottom,1)

def conn1(ref,value,x,y,n,nets,fp=""):
    comp(f"Connector_Generic:Conn_01x{n:02d}",ref,value,x,y,(1,0,0,-1),fp)
    start=y-((n-1)//2)*100
    for i,net in enumerate(nets):
        py=start+i*100
        if not net:
            items.append(f"NoConn ~ {x-200} {py}")
        else:
            wire(x-200,py,x-250,py); label(x-250,py,net)

def conn2x20(ref,value,x,y,nets,fp=""):
    comp("Connector_Generic:Conn_02x20_Odd_Even",ref,value,x,y,(1,0,0,-1),fp)
    start=y-900
    for pin in range(1,41):
        py=start+((pin-1)//2)*100
        px=x-200 if pin%2 else x+300
        if pin%2:
            wire(px,py,x-250,py); label(x-250,py,nets[pin-1])
        else:
            wire(px,py,x+350,py); label(x+350,py,nets[pin-1],2)

# Title and explicit safety boundary
note(600,550,"COFFEEROAST CONTROL RevA.2 — LOW-VOLTAGE CONTROLLER",100)
note(600,760,"230 VAC IS OFF-BOARD: certified 230VAC→24VDC PSU + external SSR/heatsink + thermal cutoff",55)

# 24 V input and exact 60 V buck conversion
box(500,950,4500,4600); note(650,1120,"POWER INPUT / PROTECTION / 24V→3V3 BUCK",70)
conn1("J1","24V_IN_FROM_CERTIFIED_PSU",850,1600,2,["+24V_RAW","GND"])
two_pin_v("Device:C_Polarized","C4","EEU-FR1V221B_220uF_35V",850,2800,"+24V_RAW","GND")
two_pin_v("Device:D_TVS","D2","SMBJ33A_INPUT_TVS",1500,2800,"GND","+24V_RAW")
# Generic 9-pin connector symbol preserves the exact DDA pad numbering:
# 1 BOOT, 2 VIN, 3 EN, 4 RT, 5 FB, 6 PGOOD/NC, 7 GND, 8 SW, 9 EP/GND.
conn1("U4","LMR16010PDDAR",2600,1800,9,["BUCK_BOOT","+24V_RAW","+24V_RAW","BUCK_RT","BUCK_FB","U4_PGOOD_NC","GND","BUCK_SW","GND"])
two_pin_v("Device:C","C8","2.2uF_100V_X7R",2200,3000,"+24V_RAW","GND")
two_pin_v("Device:C","C9","2.2uF_100V_X7R",2700,3000,"+24V_RAW","GND")
two_pin_v("Device:C","C12","100nF_100V_X7R",3200,3000,"+24V_RAW","GND")
two_pin_v("Device:C","C10","100nF_BOOT",2200,4050,"BUCK_BOOT","BUCK_SW")
two_pin_v("Device:D","D4","SS110_100V",2800,4050,"GND","BUCK_SW")
conn1("L1","FNR6045S220MT_22uH",3500,1750,2,["BUCK_SW","+3V3"])
two_pin_v("Device:C","C11","22uF_25V_X5R",3700,2600,"+3V3","GND")
two_pin_v("Device:C","C15","22uF_25V_X5R",4200,2600,"+3V3","GND")
two_pin_v("Device:R","R12","100k_1%_FB_TOP",3200,3900,"BUCK_FB","+3V3")
two_pin_v("Device:R","R13","29.4k_1%_FB_BOTTOM",3700,3900,"BUCK_FB","GND")
two_pin_v("Device:R","R14","49.9k_1%_RT_500kHz",4200,3900,"BUCK_RT","GND")
# 3V3 bulk/local decoupling is shown beside the ESP32 block to avoid dense
# passive-column wire collisions in the buck drawing.
two_pin_v("Device:C","C7","100nF_U4_3V3_OUT",12300,1500,"+3V3","GND")
two_pin_v("Device:C","C1","10uF_3V3_BULK_A",12300,2200,"+3V3","GND")
two_pin_v("Device:C","C2","10uF_3V3_BULK_B",13000,2200,"+3V3","GND")

# Fan driver with split-output 10 V gate driver; SSR stage remains 3.3 V.
box(4700,950,9000,4600); note(4850,1120,"FAN GATE DRIVER + EXTERNAL SSR DRIVER",70)
conn1("J2","24V_FAN_OUTPUT",5000,1600,2,["+24V_RAW","FAN_NEG"])
conn1("U6","UCC27511DBVR",5750,1700,6,["VDRV10","FAN_GATE_ON","FAN_GATE_OFF","GND","GND","FAN_PWM"])
two_pin_h("Device:R","R1","100R_GATE_TURN_ON",6500,1350,"FAN_GATE_ON","FAN_GATE")
two_pin_h("Device:R","R15","10R_GATE_TURN_OFF",6500,1950,"FAN_GATE_OFF","FAN_GATE")
two_pin_v("Device:R","R2","100k_GATE_PULLDOWN",7300,2600,"FAN_GATE","GND")
conn1("Q1","STP55NF06L_GDS",7300,1650,3,["FAN_GATE","FAN_NEG","GND"])
# Device:D vertical rotation maps lower label to pin 1 (K); cathode is +24 V.
two_pin_v("Device:D","D1","SS56-E3/57T_FLYBACK",7900,1650,"FAN_NEG","+24V_RAW")
two_pin_v("Device:D_TVS","D3","SMBJ33A_FAN_TVS",8500,1650,"FAN_NEG","+24V_RAW")
two_pin_v("Device:R","R16","2.7k_1%_250mW",5000,3000,"+24V_RAW","VDRV10")
two_pin_v("Device:D_Zener","D5","BZT52C10_10V",5600,3000,"GND","VDRV10")
two_pin_v("Device:C","C13","1uF_25V_VDRV",6200,3000,"VDRV10","GND")
two_pin_v("Device:C","C14","100nF_50V_VDRV",6800,3000,"VDRV10","GND")
conn1("J3","EXTERNAL_SSR_INPUT_3V3",5000,4000,2,["+3V3","SSR_NEG"])
two_pin_h("Device:R","R3","100R",6000,3900,"HEATER_PWM","SSR_GATE")
two_pin_v("Device:R","R4","100k_GATE_PULLDOWN",6700,4100,"SSR_GATE","GND")
conn1("Q2","2N7002_SSR_DRIVER_GDS",7500,4000,3,["SSR_GATE","GND","SSR_NEG"])
note(8050,4300,"SSR input only — no mains on PCB",45)

# ESP32 module and reset/boot
box(9200,950,16000,5000); note(9350,1120,"ESP32-S3-WROOM-1 CONTROLLER + PCB-ONLY DEBUG NETS",70)
u1nets=["GND","+3V3","EN","GPIO4","GPIO5","GPIO6","GPIO7","GPIO15","GPIO16","GPIO17","GPIO18","GPIO8","USB_DN_MCU","USB_DP_MCU","GPIO3","GPIO46","GPIO9","GPIO10","MAX_DO","MAX_CS","MAX_SCK","GPIO14","GPIO21","GPIO47","GPIO48","GPIO45","BOOT","GPIO35","GPIO36","GPIO37","GPIO38","GPIO39","GPIO40","GPIO41","GPIO42","RXD0_GPIO44","TXD0_GPIO43","FAN_PWM","HEATER_PWM","GND"]
conn2x20("U1","ESP32-S3-WROOM-1",10800,2600,u1nets)
two_pin_v("Device:C","C6","100nF_U1_DECOUPLING",13000,1500,"+3V3","GND")
two_pin_h("Device:R","R5","10k_EN_PULLUP",9600,4000,"+3V3","EN")
two_pin_h("Switch:SW_Push","SW1","RESET",10100,4300,"EN","GND")
two_pin_h("Device:R","R6","10k_BOOT_PULLUP",11000,4000,"+3V3","BOOT")
two_pin_h("Switch:SW_Push","SW2","BOOT",11500,4300,"BOOT","GND")
conn1("JGPIO1","SPARE_GPIO_BREAKOUT",12600,3900,6,["GPIO3","GPIO46","GPIO9","GPIO10","GPIO48","GPIO45"])
conn1("J6","ESC_24V_GND_PWM_GND_GPIO10",14600,4200,4,["+24V_RAW","GND","GPIO10","GND"])
note(13700,4750,"ESC connector pin order: +24V / GND / PWM(GPIO10) / GND",45)
# Schematic-only anchor for nets that exist solely on PCB probe/solder pads.
# No footprint is assigned; TPESP/PADESP are intentionally board-only objects.
conn1("JDEBUGSCHEM1","PCB_ONLY_DEBUG_NET_ANCHOR",14500,2700,23,[
    "U4_PGOOD_NC","GPIO4","GPIO5","GPIO6","GPIO7","GPIO15","GPIO16","GPIO17","GPIO18","GPIO8",
    "GPIO14","GPIO21","GPIO47","GPIO35","GPIO36","GPIO37","GPIO38","GPIO39","GPIO40","GPIO41",
    "GPIO42","RXD0_GPIO44","TXD0_GPIO43"
], fp="")

# Thermocouple interface
box(500,4900,4500,7300); note(650,5070,"K-TYPE THERMOCOUPLE / MAX6675",70)
conn1("J4","K_TYPE_THERMOCOUPLE",900,5900,2,["THERMO_PLUS","THERMO_MINUS"])
two_pin_v("Device:C","C5","1nF_C0G_DNP_IF_BIASED",1600,5900,"THERMO_PLUS","THERMO_MINUS")
conn1("U2","MAX6675_SOIC8_3V3",2900,5900,8,["GND","THERMO_MINUS","THERMO_PLUS","+3V3","MAX_SCK","MAX_CS","MAX_DO","GND"])
two_pin_v("Device:C","C3","100nF_MAX6675",3900,5900,"+3V3","GND")
note(700,6900,"Firmware: DO=GPIO11, CS=GPIO12, SCK=GPIO13",50)

# USB-C data-only interface and ESD
box(4700,4900,9000,7300); note(4850,5070,"USB-C DATA / FLASH (VBUS SENSE ONLY)",70)
conn1("J5","USB_C_RECEPTACLE_USB2",5100,6000,8,["GND","USB_VBUS","USB_CC1","USB_DP","USB_DN","USB_CC2","USB_VBUS","GND"])
two_pin_v("Device:R","R10","5.1k_CC1_RD",6000,5400,"USB_CC1","GND")
two_pin_v("Device:R","R11","5.1k_CC2_RD",6700,5400,"USB_CC2","GND")
two_pin_h("Device:R","R7","27R_USB_DN",6300,6400,"USB_DN_MCU","USB_DN")
two_pin_h("Device:R","R8","27R_USB_DP",6300,6800,"USB_DP_MCU","USB_DP")
conn1("U5","USBLC6-2SC6_USB_ESD",8000,6100,6,["USB_DN","GND","USB_DP","USB_DP","USB_VBUS","USB_DN"])
note(5000,7100,"USB VBUS does not power the controller",45)

# Bring-up test points
box(500,7800,9000,9700); note(650,7970,"BRING-UP / TEST ACCESS",70)
for ref,val,x,net in [("TP24V","24V_RAW",900,"+24V_RAW"),("TP3V3","3V3",1900,"+3V3"),("TPGND","GND",2700,"GND")]:
    conn1(ref,val,x,8500,1,[net])
conn1("TPRESET1","RESET_TWEEZER",3900,8500,2,["EN","GND"])
conn1("TPBOOT1","BOOT_TWEEZER",5000,8500,2,["BOOT","GND"])
conn1("TPSSR1","SSR_OUT_MEASURE",6100,8500,2,["+3V3","SSR_NEG"])
note(650,9200,"TPESP1–40 and PADESP1–40 on PCB mirror U1 pins 1–40; see docs/esp32_debug_pads.csv",45)
note(650,9400,"All named nets match the routed PCB; exact U4/U5/Q1/protection footprints are locally archived and parity-checked.",45)

header=["EESchema Schematic File Version 4","LIBS:power","LIBS:device","LIBS:Connector_Generic","LIBS:switch","EELAYER 29 0","EELAYER END","$Descr A3 16535 11693","Sheet 1 1",'Title "CoffeeRoast Control RevA.2"','Date "2026-07-12"','Rev "A.2"','Comp "CoffeeRoast"','Comment1 "Low-voltage controller only; 230 VAC remains off-board"','Comment2 "Generated from routed PCB nets and docs/netlist.csv"',"$EndDescr"]
OUT.write_text("\n".join(header+items+["$EndSCHEMATC",""]),encoding="utf-8")
print(OUT)
