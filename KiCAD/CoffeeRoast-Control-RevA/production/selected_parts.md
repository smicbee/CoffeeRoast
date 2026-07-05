# CoffeeRoast-Control RevA.1 selected parts

Search date: 2026-07-05. Source used for PCBA parts: JLCPCB Parts search pages. Re-confirm in the JLCPCB/PCBWay UI before paying because stock/basic/extended status can change.

## Conservative first SMD-PCBA set

These are the parts to let the PCB house assemble now. Their footprints are known-good enough for the current RevA.1 partial assembly package.

| Refs | Qty | Function | Selected part | JLC/LCSC code | Status seen | Notes |
|---|---:|---|---|---|---|---|
| U1 | 1 | ESP32 module | ESP32-S3-WROOM-1-N8R8 | C2913201 | Extended | Confirm antenna keepout/orientation in preview. |
| U2 | 1 | Thermocouple IC | MAX6675ISA+T | C16030 | Extended | SOIC-8; 3.3V operation. |
| J5 | 1 | USB-C receptacle | XKB U262-16 1 N-4BVC11 | C319148 | Extended | Exact footprint family currently used. Verify rotation. |
| Q2 | 1 | SSR low-side driver | 2N7002 | C8545 | Basic | SOT-23. |
| R1,R3 | 2 | Gate resistors | 0805W8F1000T5E, 100R 0805 1% | C17408 | Basic | JLC basic resistor. |
| R2,R4 | 2 | Pulldowns | 0805W8F1003T5E, 100k 0805 1% | C149504 | Basic | JLC basic resistor. |
| R5,R6 | 2 | EN/BOOT pullups | 0805W8F1002T5E, 10k 0805 1% | C17414 | Basic | JLC basic resistor. |
| R7,R8 | 2 | USB series resistors | 0805W8F270JT5E, 27R 0805 | C17594 | Promo/basic-equivalent | JLC listed as promotional no-feeder-charge part. |
| R10,R11 | 2 | USB-C CC Rd | 0805W8F5101T5E, 5.1k 0805 1% | C27834 | Basic | JLC basic resistor. |
| C1,C2 | 2 | 5V/3V3 bulk | Samsung CL21A106KAYNNNE, 10uF 0805 | C15850 | Basic | Enough for 5V/3.3V local bulk. |
| C3 | 1 | MAX6675 bypass | CC0805KRX7R9BB104, 100nF 0805 50V X7R | C49678 | Basic | JLC basic capacitor. |

## DNP / hand-solder candidates for RevA.1 prototype

These have been selected as candidates, but should not be included in automated SMD assembly in the current RevA.1 package.

| Refs | Function | Candidate part | Code/source | Why not PCBA-place now |
|---|---|---|---|---|
| J1-J4 | 2-pin 5.08mm terminals | WJ2EDGRC-5.08-02P-14-00A | JLC C3697 | THT/mechanical; hand-solder. |
| D1 | Fan flyback diode | SB560 DO-201AD | JLC C139684 | THT/power; hand-solder after real fan is confirmed. |
| Q1 | Fan MOSFET | IRLB8721PBF TO-220 | JLC C153222 | THT/power; thermal check with real fan. Alternative: FQP30N06L / C243087. |
| D2,D3 | 24V/fan TVS | SMBJ33A-13-F | JLC C135067 | Draft land pattern; verify/replace footprint in RevA.2 before automated assembly. |
| U5 | USB ESD | USBLC6-2SC6 | JLC C7519 | Current RevA.1 footprint is draft/custom on-track, not safe for SOT-23-6 PCBA. |
| C5 | Thermocouple filter | TDK C2012C0G1H102JT000N, 1nF C0G 0805 | JLC C76625 | Current RevA.1 footprint is not an 0805 land pattern; also keep DNP unless noise test needs it. |
| C4 | Input bulk cap | Panasonic EEU-FR1V221 or Nichicon UPW1V221MPD, 220uF/35V radial | Mouser/DigiKey class | Verify lead pitch/current pads before buying. |
| F1 | 24V fuse holder | 5x20mm PCB fuse holder + T3.15A fuse | verify mechanically | Current footprint has ~22mm pad spacing; verify exact holder or use external inline fuse. |
| U3 | 3.3V switcher | OKI-78SR-3.3/1.5-W36-C or R-78E3.3-0.5 | JLC search found OKI/R-78 variants | Current RevA.1 footprint does not match; wire-in for prototype or update footprint in RevA.2. |
| U4 | 24V->5V buck | Pololu D24V10F5 class, >=36V input, 5V/1A | JLC C26689857 for Pololu module listing | Current module footprint must be verified/adapted. |
| SW1,SW2 | Reset/Boot buttons | K3-1391A-51 6x6mm THT tactile | JLC C92655 | Optional; hand-solder or omit if debug pads suffice. |

## Decision made after footprint review

I removed `U5`, `D2`, `D3`, and `C5` from the automated SMD assembly set for RevA.1. They are electrically useful, but their current generated/draft land patterns are not reliable enough for paid PCBA placement. The safer first order is: assemble only U1/U2/J5/Q2/R/C known-good parts, then hand-solder or leave protection/filter parts DNP, and roll exact footprints into RevA.2.
