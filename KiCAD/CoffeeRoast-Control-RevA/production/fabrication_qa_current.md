# CoffeeRoast RevA.1 fabrication QA current

Run timestamp: 2026-07-05T11:41:45+02:00
Workspace: `/home/smicbee/CoffeeRoast`
PCB project: `/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA`

## Verdict

- The production package appears to have been regenerated after the current board/silkscreen patch: the board mtime is `2026-07-05 09:41:55 +0200`, the generated silkscreen Gerbers are `2026-07-05 09:42:11 +0200`, and the ZIP is `2026-07-05 09:42:12 +0200`.
- KiCad error-only DRC is clean: `0 DRC violations`, `0 unconnected pads`, `0 Footprint errors`.
- The generated ZIP passes `unzip -t` and contains the expected fabrication, drill, and assembly handoff files.
- No error-level fabrication blocker was found in this QA pass. Do not use the old JLC cart item if it predates these regenerated Gerbers; re-upload the ZIP and review the manufacturer preview again.

## Git diff / KiCad file status

Command:

```bash
git status --short -- KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt
git diff --stat -- KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt
git diff --name-status -- KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt
```

Status summary:

```text
 M KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/drill/CoffeeRoast-Control-RevA-drl_map.pdf
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/drill/CoffeeRoast-Control-RevA.drl
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/drill/drill_report.txt
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-B_Cu.gbl
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-B_Mask.gbs
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-B_Paste.gbp
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-B_Silkscreen.gbo
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-Edge_Cuts.gm1
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-F_Cu.gtl
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-F_Mask.gts
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-F_Paste.gtp
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-F_Silkscreen.gto
 M KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-job.gbrjob
?? KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/assembly/footprint_check_reva1.json
?? KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/assembly/footprint_max_pcba_review.md
?? KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt
```

Diff stat for the relevant tracked files:

```text
 .../CoffeeRoast-Control-RevA.kicad_pcb             |  253 +-
 ...oast-Control-RevA1_partial_smd_pcba_package.zip |  Bin 81622 -> 73404 bytes
 .../drill/CoffeeRoast-Control-RevA-drl_map.pdf     |  Bin 29071 -> 29071 bytes
 .../drill/CoffeeRoast-Control-RevA.drl             |    4 +-
 .../partial-smd-pcba/drill/drill_report.txt        |    2 +-
 .../gerbers/CoffeeRoast-Control-RevA-B_Cu.gbl      |    4 +-
 .../gerbers/CoffeeRoast-Control-RevA-B_Mask.gbs    |    4 +-
 .../gerbers/CoffeeRoast-Control-RevA-B_Paste.gbp   |    4 +-
 .../CoffeeRoast-Control-RevA-B_Silkscreen.gbo      | 6670 ++++++++++----------
 .../gerbers/CoffeeRoast-Control-RevA-Edge_Cuts.gm1 |    4 +-
 .../gerbers/CoffeeRoast-Control-RevA-F_Cu.gtl      |    4 +-
 .../gerbers/CoffeeRoast-Control-RevA-F_Mask.gts    |    4 +-
 .../gerbers/CoffeeRoast-Control-RevA-F_Paste.gtp   |    4 +-
 .../CoffeeRoast-Control-RevA-F_Silkscreen.gto      | 2528 +-------
 .../gerbers/CoffeeRoast-Control-RevA-job.gbrjob    |    2 +-
 15 files changed, 3626 insertions(+), 5861 deletions(-)
```

KiCad/package file mtimes and sizes:

```text
/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb|293918 bytes|2026-07-05 09:41:55.901525512 +0200
/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-F_Silkscreen.gto|54679 bytes|2026-07-05 09:42:11.880886551 +0200
/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/gerbers/CoffeeRoast-Control-RevA-B_Silkscreen.gbo|85527 bytes|2026-07-05 09:42:11.887886555 +0200
/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip|73404 bytes|2026-07-05 09:42:12.612886992 +0200
```

## KiCad error-only DRC

Command:

```bash
kicad-cli pcb drc --severity-error --format report --output /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb
```

Tool version: KiCad CLI `9.0.8`

Result:

```text
0 Verstöße gefunden
Unverbundene Elemente (0) gefunden
DRC-Bericht wurde gespeichert in /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/render/drc_report_errors_only_current.txt
```

Report excerpt:

```text
** Drc report for CoffeeRoast-Control-RevA.kicad_pcb **
** Created on 2026-07-05T11:41:10+0200 **
** Report includes: Fehler **

** Found 0 DRC violations **

** Found 0 unconnected pads **

** Found 0 Footprint errors **

** End of Report **
```

Additional warning-only check, run to identify upload-preview caveats:

```bash
kicad-cli pcb drc --format report --output /tmp/coffeeroast_drc_full_current.txt /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/CoffeeRoast-Control-RevA.kicad_pcb
```

Result: full DRC reports `69` warning-only violations, all category `silk_over_copper`. These are not error-level fabrication blockers, but they remain preview-review items because they are silkscreen segments over soldermask/copper near component outlines/pads.

## ZIP integrity / contents

ZIP path:

`/home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip`

Size and hash:

```text
73404 bytes
sha256 0a84ccc357dfba282485046a2ab31d095fdcc09adf6131d05556b5a8a583e282
```

Command:

```bash
unzip -t /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip
```

Result:

```text
Archive:  /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip
    testing: README_ORDERING.md       OK
    testing: drill/CoffeeRoast-Control-RevA-drl_map.pdf   OK
    testing: drill/drill_report.txt   OK
    testing: drill/CoffeeRoast-Control-RevA.drl   OK
    testing: assembly/part_mapping_review.csv   OK
    testing: assembly/cpl_smd_partial.csv   OK
    testing: assembly/bom_smd_partial.csv   OK
    testing: assembly/dnp_hand_solder.csv   OK
    testing: gerbers/CoffeeRoast-Control-RevA-F_Paste.gtp   OK
    testing: gerbers/CoffeeRoast-Control-RevA-B_Mask.gbs   OK
    testing: gerbers/CoffeeRoast-Control-RevA-B_Cu.gbl   OK
    testing: gerbers/CoffeeRoast-Control-RevA-F_Silkscreen.gto   OK
    testing: gerbers/CoffeeRoast-Control-RevA-B_Paste.gbp   OK
    testing: gerbers/CoffeeRoast-Control-RevA-B_Silkscreen.gbo   OK
    testing: gerbers/CoffeeRoast-Control-RevA-F_Cu.gtl   OK
    testing: gerbers/CoffeeRoast-Control-RevA-Edge_Cuts.gm1   OK
    testing: gerbers/CoffeeRoast-Control-RevA-F_Mask.gts   OK
    testing: gerbers/CoffeeRoast-Control-RevA-job.gbrjob   OK
No errors detected in compressed data of /home/smicbee/CoffeeRoast/KiCAD/CoffeeRoast-Control-RevA/production/partial-smd-pcba/CoffeeRoast-Control-RevA1_partial_smd_pcba_package.zip.
```

ZIP structure summary:

```text
entries=18
README_ORDERING.md: 1
assembly/: 4
  - bom_smd_partial.csv: 17 data rows
  - cpl_smd_partial.csv: 17 data rows
  - dnp_hand_solder.csv: 100 data rows
  - part_mapping_review.csv: 17 data rows
drill/: 3
gerbers/: 10
```

## Open blockers / gates for JLC upload

No blocker was found by error-only DRC or ZIP integrity checks. Remaining gates before upload/checkout:

1. Treat any previous JLC cart/quote item as stale if it was created before the `09:42:12 +0200` ZIP. Upload the current ZIP above as a fresh fabrication package.
2. In the JLC preview, visually check the remaining full-DRC warning class: `69` warning-only `silk_over_copper` items. They are not error-level blockers, but the silkscreen should still look acceptable in the manufacturer preview.
3. For PCBA, confirm top-side partial assembly only and map/verify the 17 BOM/CPL assembled designators. Orientation/placement must be visually checked for at least U1 ESP32-S3-WROOM, U2 MAX6675, J5 USB-C, Q2 2N7002, and the 0805 R/C parts.
4. Keep DNP/hand-solder parts out of automated assembly for this prototype, especially J1-J4, F1, D1, Q1, U3, U4, C4, SW1, SW2, U5, D2, D3, and C5 unless a later footprint-specific review changes that decision.
5. No checkout/payment was performed in this QA task.
