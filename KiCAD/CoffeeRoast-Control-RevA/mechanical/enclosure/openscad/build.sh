#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SCAD="$ROOT/CoffeeRoast_RevA2_enclosure.scad"
OUT="$ROOT/generated"
mkdir -p "$OUT"

openscad --hardwarnings -D 'part="tray"' -o "$OUT/tray.stl" "$SCAD"
openscad --hardwarnings -D 'part="tray"' -o "$OUT/tray.3mf" "$SCAD"
openscad --hardwarnings -D 'part="lid_print"' -o "$OUT/lid_print.stl" "$SCAD"
openscad --hardwarnings -D 'part="lid_print"' -o "$OUT/lid_print.3mf" "$SCAD"
openscad --hardwarnings -D 'part="lid"' -o "$OUT/lid_design.stl" "$SCAD"
openscad --hardwarnings -D 'part="board_proxy"' -o "$OUT/board_proxy.stl" "$SCAD"

unset DISPLAY
xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,55,0,25,610 \
  -D 'part="closed"' -o "$OUT/preview_closed.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,55,0,25,760 \
  -D 'part="exploded"' -o "$OUT/preview_exploded.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,90,0,0,560 \
  -D 'part="closed"' -o "$OUT/preview_front.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,90,0,90,560 \
  -D 'part="closed"' -o "$OUT/preview_right.png" "$SCAD"

python3 "$ROOT/verify_openscad.py"
