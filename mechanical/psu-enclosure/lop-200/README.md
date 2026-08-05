# CoffeeRoast enclosure for one Mean Well LOP-200-24

Compact, screw-closed **digital prototype** for exactly one ordered Mean Well
LOP-200-24 open-frame power supply. It is intentionally not the 10-inch rack
model and has no space or mounting pattern for a second PSU.

## Mechanical contract

Primary source: Mean Well `LOP-200-SPEC.pdf`, archived under `../reference/`.

| Item | Value |
|---|---:|
| PSU PCB | 101.6 × 50.8 mm |
| Maximum PSU height | 25.4 mm |
| Mounting pattern | 95.25 × 44.45 mm |
| PSU holes | 4 × Ø3.3 mm |
| Recommended support | M3 fixed conductive pillar, max. Ø6 mm |
| Printed shell | 122.4 × 71.6 × 42.2 mm closed |
| AC/DC cable-gland holes | 2 × Ø16.2 mm |

The PCB rests on **physical 6 mm conductive M3 pillars**, not printed posts.
Four exact through-holes and shallow screw-head recesses are provided in the
base. The left wall is labelled AC and the right wall 24V.

## Generated files

Run:

```bash
cd mechanical/psu-enclosure/lop-200/openscad
./build.sh
```

Outputs in `generated/`:

- `base.stl` / `base.3mf`
- `lid.stl` / `lid.3mf`
- `preview_closed.png`, `preview_open.png`, `preview_glands.png`
- `verification.json` and `manifest.json`

Both print parts are oriented flat on the bed. The lid uses four M3 screws into
heat-set inserts; it is not tool-free and cannot be opened accidentally.

## Required non-printed hardware

- 4 × conductive M3 × 6 mm brass/copper pillars, max. Ø6 mm
- suitable M3 base screws, washers and locking hardware
- 4 × M3 heat-set inserts fitting the 4.2 mm model bores
- 4 × M3 lid screws
- 2 × certified cable glands for 16.2 mm panel holes, selected for the **actual**
  AC and 24 V cable outside diameters
- protective-earth conductor, ring lugs and locking hardware for every
  Mean-Well mounting point marked PE in the manufacturer drawing
- appropriately engineered upstream fuse/switching; no fuse value is guessed
  by this mechanical model

## Electrical-safety boundary

This repository provides mechanical geometry, **not certification**. An
open-frame 230 V supply must not be energized in an unqualified printed shell.
Before use, a qualified person must verify at least:

1. PE bonding and measured continuity to every manufacturer-marked PE point.
2. Correct fuse/switch design, conductor ratings, ferrules/crimps and polarity.
3. Certified cable glands, cable retention and strain relief.
4. Touch-probe protection through every vent and seam.
5. Required creepage/clearance around wiring, metal hardware and the shell.
6. Final-load temperature in the real installation orientation.
7. Physical fit of the delivered LOP-200-24 and JST-VH harnesses.

Use only a filament with documented flame-retardant **UL94 V-0** suitability
for the intended print process. Ordinary PLA/PETG is not released. A printed
part made from nominally V-0 filament is not automatically a certified V-0
finished enclosure.

The lid and base use narrow 2 mm ventilation slots. This reduces direct finger
access but does not replace the required touch-probe assessment. Mean Well
specifies lower convection power than fan-cooled power; do not infer that full
200 W operation is thermally acceptable in this enclosure.

## Design status

`PROTOTYPE_NOT_RELEASED`: digital geometry can pass while electrical and
thermal release gates remain open. Never bypass these gates based on a clean
STL or successful print.
