# CoffeeRoast-Control RevA.2 PCB Draft

This is the current RevA.2 hardware draft for moving the CoffeeRoast electronics onto a PCB. It includes the simplified direct 24V→3.3V power tree and the layout-quality pass: explicit critical-current rules, widened 24V/fan paths, deliberate 45° routing on revised branches, and a clean full KiCad DRC. Exact power/protection footprints and manual engineering review are still required before fabrication.

## Design decision captured from chat

- Use **one 230V appliance inlet for the whole roaster enclosure**.
- Inside the enclosure use a **certified isolated 230VAC -> 24VDC / 3A PSU**.
- The controller PCB itself is **low-voltage only** and accepts the PSU's 24VDC output.
- The PCB generates 5V via a buck module and 3.3V via a RevA.1 switching-regulator footprint/selection for the ESP32-S3 module.
- The heater's 230V path is still switched by an **external SSR module with heatsink**; 230V is intentionally not routed on this PCB.
- RevA.1 adds low-voltage robustness features: input bulk capacitor, 24V input TVS, fan TVS, USB ESD footprint, thermocouple filter footprint, and rail test pads.

## Files

- `CoffeeRoast-Control-RevA.kicad_pcb` — KiCad board draft with real on-board USB-C footprint and reviewed mixed manual/autorouted tracks.
- `CoffeeRoast-Control-RevA.kicad_dru` — project-specific KiCad rules enforcing at least 1.0 mm on the 24V/fan current nets and a 0.6 mm drill/0.30 mm annular ring on future critical-current vias.
- `CoffeeRoast-Control-RevA.kicad_sch` — vollständiger, editierbarer KiCad-Schaltplan mit Funktionsblöcken für Versorgung, Lüfter/SSR, ESP32, MAX6675, USB und Testzugänge; die benannten Netze entsprechen dem gerouteten PCB.
- `tools/generate_full_schematic.py` — reproduzierbarer Generator für den Schaltplanentwurf; die native `.kicad_sch`-Datei wurde mit KiCad 9 konvertiert und geprüft.
- `render/schematic/CoffeeRoast-Control-RevA.pdf` und `.svg` — exportierte Schaltplanansichten; `render/schematic/erc.json` enthält den aktuellen ERC-Bericht.
- `docs/netlist.csv` — tabellarische Referenz der beabsichtigten elektrischen Verbindungen.
- `docs/footprints.csv` — vollständige Referenz-zu-Footprint-Zuordnung inklusive der geprüften KiCad-Quellpakete.
- `CoffeeRoast.pretty/` — projektlokale, reproduzierbare Kopien sämtlicher 129 Board-Footprints; dadurch bleibt das geroutete Layout unabhängig von installierten Bibliotheksversionen.
- `fp-lib-table` — bindet die projektlokale Footprintbibliothek automatisch in KiCad ein.
- `docs/bom.csv` — Stückliste des aktuellen PCB-Entwurfs.
- `docs/esp32_debug_pads.csv` — ESP32-S3 TPESP1-40 tiny probe pad mapping.
- `docs/esp32_solder_pads.csv` — larger labeled bottom-side PADESP1-40 solder pad mapping for attaching wires later.
- `docs/routing_notes.md` — routing/DRC status and fabrication caveats.
- `docs/layout_quality_review.md` — measured before/after review of route geometry, current-path widths, GND-zone quality, DRC and visual QA.
- `tools/improve_layout_quality.py` — idempotent pcbnew ECO script for the RevA.2 layout-quality pass.
- `docs/reva1_optimizations.md` — RevA.1 robustness changes and what was deliberately left for RevB.
- `tools/apply_reva1_optimizations.py` — idempotent pcbnew script that applies the RevA.1 PCB additions.
- `production/partial-smd-pcba/` — generated Gerber/drill + partial SMD assembly BOM/CPL package for first prototype ordering.
- `tools/prepare_partial_pcba_package.py` — regenerates the partial-SMD PCBA handoff package.
- `symbols/` and `footprints.pretty/` — local ESP32-S3-WROOM-1 and USB-C library files copied from KiCad upstream.

## Firmware pin mapping preserved

| Function | ESP32-S3-WROOM-1 pin | GPIO | Firmware variable |
|---|---:|---:|---|
| Heater/SSR PWM | 39 | GPIO1 | `relayPin` |
| Fan PWM | 38 | GPIO2 | `fanPin` |
| MAX6675 DO/SO | 19 | GPIO11 | `thermoDO` |
| MAX6675 CS | 20 | GPIO12 | `thermoCS` |
| MAX6675 CLK/SCK | 21 | GPIO13 | `thermoCLK` |
| USB D- | 13 | native USB D- | serial/flash |
| USB D+ | 14 | native USB D+ | serial/flash |
| BOOT | 27 | GPIO0 | flash mode |
| EN/RESET | 3 | EN | reset |

## ESP32 debug pads

All ESP32-S3-WROOM-1 side pins 1-40 are exposed twice: tiny local probe pads named `TPESP1` through `TPESP40` around U1, and larger labeled bottom-side solder pads named `PADESP1` through `PADESP40` routed outward for attaching wires later. The mappings are in `docs/esp32_debug_pads.csv` and `docs/esp32_solder_pads.csv`. These include the spare GPIOs plus already-used signals such as USB D+/D-, MAX6675 SPI, BOOT/EN, fan PWM, heater/SSR PWM, 3V3, and GND.

## Power tree

```text
230VAC inlet in enclosure
  +--> certified 230VAC -> 24VDC / 3A PSU
          +--> J1 on this PCB
                +--> C4 input bulk + D2 24V TVS protection
                +--> F1 24V-side fuse placeholder
                +--> J2 24V fan via Q1 low-side MOSFET + D1/D3 fan clamp
                +--> U4 24V -> 3.3V buck module
                        +--> ESP32-S3-WROOM-1 + MAX6675
                        +--> 3.3V SSR input driver supply

230VAC heater line: external SSR module only, not on this PCB.
```

## Important limitations before fabrication

This board loads in KiCad 9.0.8 and the current full DRC (errors, warnings and exclusions) is clean with 0 violations and 0 unconnected items. Before ordering boards:

1. Open the project in KiCad.
2. Replace remaining generic placeholders with exact sourced parts: fuse holder, U4 24V→3.3V buck module, TVS packages, USB ESD package and MOSFET variants. J1-J4 are deliberately large hand-solder pads now, not PCBA connector placements.
3. Re-run ERC/DRC after any mechanical/footprint changes.
4. Confirm ESP32-S3-WROOM-1 antenna keepout has no copper and is at board edge.
5. Confirm the fan path, D3 TVS choice, Q1 MOSFET, and hand-solder pad/wire strain-relief scheme are rated for the real 24V/2.5A fan current.
6. Confirm J5 enclosure cutout/edge placement for the exact USB-C part and replace U5 with an exact USB2 ESD footprint.
7. Review USB CC pulldowns: R10/R11 = 5.1k to GND, VBUS is sense-only.
8. Decide whether C5 should be populated after thermocouple noise testing; leave DNP if it biases readings.
9. Review mains wiring separately: fused IEC inlet, PE/strain relief, certified 24V PSU, external SSR heatsink, thermal cut-off.

## RevB candidates

- Replace the generic U4 buck module with an integrated switch-mode converter.
- Add reverse-polarity ideal-diode/P-MOSFET input protection if final wiring risk justifies the extra footprint/reroute.
- Add current/thermal sensing for fan/heater diagnostics.
