# CoffeeRoast-Control RevA.2

This is the finalized RevA.2 low-voltage controller design. It contains a discrete 60 V-rated 24V→3.3V buck, a 10 V fan gate driver, exact package-qualified protection parts, explicit critical-current rules, widened 24V/fan paths and a fully synchronized native KiCad schematic. Full ERC, DRC, unconnected-item and schematic-parity checks are clean.

## Design decision captured from chat

- Use **one 230V appliance inlet for the whole roaster enclosure**.
- Inside the enclosure use a **certified isolated 230VAC -> 24VDC / 3A PSU**.
- The controller PCB itself is **low-voltage only** and accepts the PSU's 24VDC output.
- The PCB generates 3.3V directly from 24V with `LMR16010PDDAR`; no intermediate 5V rail is used.
- The heater's 230V path is still switched by an **external SSR module with heatsink**; 230V is intentionally not routed on this PCB.
- RevA.2 includes input bulk capacitance, 24V and fan TVS protection, USB ESD, optional thermocouple filtering, rail test pads and a `UCC27511DBVR`/`STP55NF06L` fan-drive stage.
- The on-board 24V fuse holder was deliberately removed; overcurrent protection must come from a current-limited or externally fused 24V source.
- J6 is a four-wire ESC hand-solder connector: `+24V / GND / PWM(GPIO10) / GND`.

## Files

- `CoffeeRoast-Control-RevA.kicad_pcb` — KiCad board draft with real on-board USB-C footprint and reviewed mixed manual/autorouted tracks.
- `CoffeeRoast-Control-RevA.kicad_dru` — project-specific KiCad rules enforcing at least 1.0 mm on the 24V/fan current nets and a 0.6 mm drill/0.30 mm annular ring on future critical-current vias.
- `CoffeeRoast-Control-RevA.kicad_sch` — vollständiger, editierbarer KiCad-Schaltplan mit Funktionsblöcken für Versorgung, Lüfter/SSR, ESP32, MAX6675, USB und Testzugänge; die benannten Netze entsprechen dem gerouteten PCB.
- `tools/generate_full_schematic.py` — reproduzierbarer Generator für den Schaltplanentwurf.
- `tools/regenerate_native_schematic.py` — reproduzierbare KiCad-9-Konvertierung und Installation des nativen Schaltplans.
- `tools/finalize_exact_hardware.py` — idempotenter Exact-Hardware-Migrationspass für PCB, lokale Footprints und kritisches Routing.
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
| ESC PWM | 18 | GPIO10 | reserved for future ESC output |
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
                +--> direct +24V_RAW distribution (no on-board fuse)
                +--> J2 24V fan via Q1 low-side MOSFET + D1/D3 fan clamp
                +--> J6 ESC: +24V / GND / PWM(GPIO10) / GND
                +--> U4 LMR16010PDDAR discrete 24V -> 3.3V buck
                        +--> ESP32-S3-WROOM-1 + MAX6675
                        +--> 3.3V external-SSR input driver
                +--> R16/D5/U6 10V gate-driver rail + STP55NF06L fan switch

230VAC heater line: external SSR module only, not on this PCB.
```

## Prototype fabrication and bring-up gates

The checked-in RevA.2 design is released for **prototype PCB fabrication and the documented partial top-side SMD assembly scope**. KiCad 9.0.8 reports 0 ERC violations, 0 DRC violations, 0 unconnected items and 0 schematic-parity problems. Before payment and first power-up:

1. Use only the newly generated `production/partial-smd-pcba/` package; prior uploads and carts are stale.
2. Inspect the manufacturer's Gerber, drill and placement previews, especially U1/U4/U5/U6/J5, TVS/diode polarity and switch rotation.
3. Re-confirm live supplier mapping for R15/R16 and stop if any MPN package differs from the documented footprint.
4. Hand-solder J1-J4, J6, D1, Q1 and C4 as listed; leave C5 DNP until thermocouple noise/bias testing justifies it.
5. Verify the ESC's input-voltage range and 3.3V PWM compatibility before connecting J6; never connect an ESC/BEC output to the PCB's 24V pin.
6. Validate the 24V/2.5A fan stage thermally on the first assembled prototype under the real enclosure airflow and ambient conditions.
7. Perform first bring-up with a current-limited 24V bench supply before connecting the real fan, ESC, SSR or certified enclosure PSU.
8. Keep an external 24V fuse/current limit, the fused IEC inlet, PE/strain relief, certified 24V PSU, external SSR/heatsink and independent thermal cut-off outside this low-voltage PCB.

## RevB candidates

- Add reverse-polarity ideal-diode/P-MOSFET input protection if final wiring risk justifies the extra footprint/reroute.
- Add current/thermal sensing for fan/heater diagnostics.
- Consider a production-specific compact board after prototype thermal and EMC measurements.
