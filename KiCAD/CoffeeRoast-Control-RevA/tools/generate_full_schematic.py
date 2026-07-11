#!/usr/bin/env python3
"""Generate the editable CoffeeRoast RevA.1 legacy KiCad schematic source.

KiCad opens this v4 file and converts it to the native .kicad_sch format on save.
The schematic mirrors the routed PCB's named nets; 230 VAC remains explicitly off-board.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/CoffeeRoast-Control-RevA-generated.sch")
items=[]
uid=0x65000000

def comp(lib, ref, value, x, y, orient=(1,0,0,-1), footprint=""):
    global uid
    uid += 1
    a,b,c,d=orient
    items.extend([
        "$Comp", f"L {lib} {ref}", f"U 1 1 {uid:X}", f"P {x} {y}",
        f'F 0 "{ref}" H {x+150} {y+100} 50  0000 C CNN',
        f'F 1 "{value}" H {x+250} {y-100} 50  0000 C CNN',
        f'F 2 "{footprint}" H {x} {y} 50  0001 C CNN',
        f"\t1    {x} {y}", f"\t{a}    {b}    {c}    {d}", "$EndComp"
    ])

def label(x,y,name,orient=0):
    items.append(f"Text Label {x} {y} {orient}    40   ~ 0\n{name}")

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
        py=start+i*100; wire(x-200,py,x-250,py); label(x-250,py,net)

def conn2x20(ref,value,x,y,nets,fp=""):
    comp("Connector_Generic:Conn_02x20_Odd_Even",ref,value,x,y,(1,0,0,-1),fp)
    used={"GND","+3V3","EN","USB_DN_MCU","USB_DP_MCU","GPIO3","GPIO46","GPIO9","GPIO10","MAX_DO","MAX_CS","MAX_SCK","GPIO48","GPIO45","BOOT","FAN_PWM","HEATER_PWM"}
    start=y-900
    for pin in range(1,41):
        py=start+((pin-1)//2)*100
        px=x-200 if pin%2 else x+300
        if nets[pin-1] not in used:
            items.append(f"NoConn ~ {px} {py}")
        elif pin%2:
            wire(px,py,x-250,py); label(x-250,py,nets[pin-1])
        else:
            wire(px,py,x+350,py); label(x+350,py,nets[pin-1],2)

# Title and explicit safety boundary
note(600,550,"COFFEEROAST CONTROL RevA.1 — LOW-VOLTAGE CONTROLLER",100)
note(600,760,"230 VAC IS OFF-BOARD: certified 230VAC→24VDC PSU + external SSR/heatsink + thermal cutoff",55)

# 24 V input and power conversion
box(500,950,3900,2750); note(650,1120,"POWER INPUT / PROTECTION / CONVERSION",70)
conn1("J1","24V_IN_FROM_CERTIFIED_PSU",900,1550,2,["+24V_RAW","GND"])
two_pin_h("Device:Fuse","F1","T3.15A_24V_SIDE",1600,1450,"+24V_RAW","+24V_FUSED")
two_pin_v("Device:C_Polarized","C4","220uF_35V",1250,2050,"+24V_RAW","GND")
two_pin_v("Device:D_TVS","D2","SMBJ33A_INPUT_TVS",1650,2050,"GND","+24V_RAW")
conn1("U4","24V_TO_5V_BUCK_MODULE",2350,1600,4,["+24V_FUSED","GND","+5V","GND"])
two_pin_v("Device:C","C7","100nF_U4_OUT",2750,2100,"+5V","GND")
conn1("U3","3V3_SWITCHING_REGULATOR",3250,1600,3,["GND","+3V3","+5V"])
two_pin_v("Device:C","C1","10uF_5V",3100,2200,"+5V","GND")
two_pin_v("Device:C","C2","10uF_3V3",3550,2200,"+3V3","GND")

# Fan and SSR output stages
box(4200,950,7350,2750); note(4350,1120,"FAN + EXTERNAL SSR DRIVERS",70)
conn1("J2","24V_FAN_OUTPUT",4550,1500,2,["+24V_FUSED","FAN_NEG"])
two_pin_h("Device:R","R1","100R",5200,1350,"FAN_PWM","FAN_GATE")
two_pin_v("Device:R","R2","100k_GATE_PULLDOWN",5500,1900,"FAN_GATE","GND")
conn1("Q1","3V3_LOGIC_NMOS_FAN_GDS",6000,1550,3,["FAN_GATE","FAN_NEG","GND"])
two_pin_v("Device:D","D1","SB560_FLYBACK",6500,1550,"+24V_FUSED","FAN_NEG")
two_pin_v("Device:D_TVS","D3","SMBJ33A_FAN_TVS",6900,1550,"FAN_NEG","+24V_FUSED")
conn1("J3","EXTERNAL_SSR_INPUT",4550,2350,2,["+5V","SSR_NEG"])
two_pin_h("Device:R","R3","100R",5200,2250,"HEATER_PWM","SSR_GATE")
two_pin_v("Device:R","R4","100k_GATE_PULLDOWN",5500,2450,"SSR_GATE","GND")
conn1("Q2","2N7002_SSR_DRIVER_GDS",6000,2350,3,["SSR_GATE","GND","SSR_NEG"])
note(6250,2520,"SSR input only — no mains on PCB",45)

# ESP32 module and reset/boot
box(7600,950,11200,4400); note(7750,1120,"ESP32-S3-WROOM-1 CONTROLLER",70)
u1nets=["GND","+3V3","EN","GPIO4","GPIO5","GPIO6","GPIO7","GPIO15","GPIO16","GPIO17","GPIO18","GPIO8","USB_DN_MCU","USB_DP_MCU","GPIO3","GPIO46","GPIO9","GPIO10","MAX_DO","MAX_CS","MAX_SCK","GPIO14","GPIO21","GPIO47","GPIO48","GPIO45","BOOT","GPIO35","GPIO36","GPIO37","GPIO38","GPIO39","GPIO40","GPIO41","GPIO42","RXD0_GPIO44","TXD0_GPIO43","FAN_PWM","HEATER_PWM","GND"]
conn2x20("U1","ESP32-S3-WROOM-1",9300,2450,u1nets,"RF_Module:ESP32-S3-WROOM-1")
two_pin_v("Device:C","C6","100nF_U1_DECOUPLING",10800,1500,"+3V3","GND")
two_pin_h("Device:R","R5","10k_EN_PULLUP",8000,3500,"+3V3","EN")
two_pin_h("Switch:SW_Push","SW1","RESET",8500,3750,"EN","GND")
two_pin_h("Device:R","R6","10k_BOOT_PULLUP",9600,3500,"+3V3","BOOT")
two_pin_h("Switch:SW_Push","SW2","BOOT",10100,3750,"BOOT","GND")
conn1("JGPIO1","SPARE_GPIO_BREAKOUT",10800,3300,6,["GPIO3","GPIO46","GPIO9","GPIO10","GPIO48","GPIO45"])

# Thermocouple interface
box(500,3000,3900,5000); note(650,3170,"K-TYPE THERMOCOUPLE / MAX6675",70)
conn1("J4","K_TYPE_THERMOCOUPLE",900,3900,2,["THERMO_PLUS","THERMO_MINUS"])
two_pin_v("Device:C","C5","1nF_C0G_DNP_IF_BIASED",1450,3900,"THERMO_PLUS","THERMO_MINUS")
conn1("U2","MAX6675_SOIC8_3V3",2550,3900,8,["GND","THERMO_MINUS","THERMO_PLUS","+3V3","MAX_SCK","MAX_CS","MAX_DO","GND"],"Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
two_pin_v("Device:C","C3","100nF_MAX6675",3300,3900,"+3V3","GND")
note(700,4700,"Firmware: DO=GPIO11, CS=GPIO12, SCK=GPIO13",50)

# USB-C data-only interface and ESD
box(4200,3000,7350,5000); note(4350,3170,"USB-C DATA / FLASH (VBUS SENSE ONLY)",70)
conn1("J5","USB_C_RECEPTACLE_USB2",4550,3950,8,["GND","USB_VBUS","USB_CC1","USB_DP","USB_DN","USB_CC2","USB_VBUS","GND"],"Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11")
two_pin_v("Device:R","R10","5.1k_CC1_RD",5150,3500,"USB_CC1","GND")
two_pin_v("Device:R","R11","5.1k_CC2_RD",5550,3500,"USB_CC2","GND")
two_pin_h("Device:R","R7","27R_USB_DN",5350,4300,"USB_DN","USB_DN_MCU")
two_pin_h("Device:R","R8","27R_USB_DP",5350,4600,"USB_DP","USB_DP_MCU")
conn1("U5","USBLC6-2SC6_USB_ESD",6500,4050,6,["USB_DN","USB_DP","GND","GND","USB_DP","USB_DN"])
note(4400,4820,"USB VBUS does not power the controller",45)

# Bring-up test points
box(500,5350,7350,6900); note(650,5520,"BRING-UP / TEST ACCESS",70)
for ref,val,x,net in [("TP24V","24V_FUSED",900,"+24V_FUSED"),("TP5V","5V",1500,"+5V"),("TP3V3","3V3",2100,"+3V3"),("TPGND","GND",2700,"GND")]:
    conn1(ref,val,x,6000,1,[net])
conn1("TPRESET1","RESET_TWEEZER",3550,5900,2,["EN","GND"])
conn1("TPBOOT1","BOOT_TWEEZER",4350,5900,2,["BOOT","GND"])
conn1("TPSSR1","SSR_OUT_MEASURE",5150,5900,2,["+5V","SSR_NEG"])
note(650,6500,"TPESP1–40 and PADESP1–40 on PCB mirror U1 pins 1–40; see docs/esp32_debug_pads.csv",45)
note(650,6660,"All named nets here match the routed PCB. Exact U3/U4/U5/Q1/D2/D3 sourced parts remain pre-fabrication review items.",45)

header=["EESchema Schematic File Version 4","LIBS:power","LIBS:device","LIBS:Connector_Generic","LIBS:switch","EELAYER 29 0","EELAYER END","$Descr A3 16535 11693","Sheet 1 1",'Title "CoffeeRoast Control RevA.1"','Date "2026-07-11"','Rev "A.1"','Comp "CoffeeRoast"','Comment1 "Low-voltage controller only; 230 VAC remains off-board"','Comment2 "Generated from routed PCB nets and docs/netlist.csv"',"$EndDescr"]
OUT.write_text("\n".join(header+items+["$EndSCHEMATC",""]),encoding="utf-8")
print(OUT)
