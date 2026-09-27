#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SCAD="$ROOT/CoffeeRoast_LOP200_single_enclosure.scad"
OUT="$ROOT/generated"
mkdir -p "$OUT"

openscad --hardwarnings -D 'part="base"' -o "$OUT/base.stl" "$SCAD"
openscad --hardwarnings -D 'part="base"' -o "$OUT/base.3mf" "$SCAD"
openscad --hardwarnings -D 'part="lid"' -o "$OUT/lid.stl" "$SCAD"
openscad --hardwarnings -D 'part="lid"' -o "$OUT/lid.3mf" "$SCAD"
openscad --hardwarnings -D 'part="psu_proxy"' -o "$OUT/psu_proxy.stl" "$SCAD"

unset DISPLAY
xvfb-run -a -s '-screen 0 1800x1200x24' \
 openscad --render --autocenter --viewall --projection=p --imgsize=1800,1200 \
 --colorscheme='Tomorrow Night' --camera=0,0,0,55,0,25,460 \
 -D 'part="closed"' -o "$OUT/preview_closed.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
 openscad --render --autocenter --viewall --projection=p --imgsize=1800,1200 \
 --colorscheme='Tomorrow Night' --camera=0,0,0,55,0,25,620 \
 -D 'part="open"' -o "$OUT/preview_open.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
 openscad --render --autocenter --viewall --projection=p --imgsize=1800,1200 \
 --colorscheme='Tomorrow Night' --camera=0,0,0,90,0,90,440 \
 -D 'part="closed"' -o "$OUT/preview_glands.png" "$SCAD"

python3 "$ROOT/verify_openscad.py"
