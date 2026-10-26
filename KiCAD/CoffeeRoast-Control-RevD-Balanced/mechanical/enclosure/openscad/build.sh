#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SCAD="$ROOT/CoffeeRoast_RevD_enclosure.scad"
OUT="$ROOT/generated"
mkdir -p "$OUT"

openscad --hardwarnings -D 'part="tray"' -o "$OUT/tray.stl" "$SCAD"
openscad --hardwarnings -D 'part="tray"' -o "$OUT/tray.3mf" "$SCAD"
openscad --hardwarnings -D 'part="lid_print"' -o "$OUT/lid_print.stl" "$SCAD"
openscad --hardwarnings -D 'part="lid_print"' -o "$OUT/lid_print.3mf" "$SCAD"
openscad --hardwarnings -D 'part="lid"' -o "$OUT/lid_design.stl" "$SCAD"
openscad --hardwarnings -D 'part="board_proxy"' -o "$OUT/board_proxy.stl" "$SCAD"

# As-delivered JLCPCB Y15 geometry with both 5 mm V-scored process rails still
# attached. These fit-check/transport artifacts are not the recommended
# operating enclosure because the rails obstruct the edge connectors.
openscad --hardwarnings -D 'board_variant="production_rails_attached"' -D 'part="tray"' \
  -o "$OUT/tray_rails_attached.stl" "$SCAD"
openscad --hardwarnings -D 'board_variant="production_rails_attached"' -D 'part="tray"' \
  -o "$OUT/tray_rails_attached.3mf" "$SCAD"
openscad --hardwarnings -D 'board_variant="production_rails_attached"' -D 'part="lid_print"' \
  -o "$OUT/lid_rails_attached_print.stl" "$SCAD"
openscad --hardwarnings -D 'board_variant="production_rails_attached"' -D 'part="lid_print"' \
  -o "$OUT/lid_rails_attached_print.3mf" "$SCAD"
openscad --hardwarnings -D 'board_variant="production_rails_attached"' -D 'part="board_proxy"' \
  -o "$OUT/board_proxy_rails_attached.stl" "$SCAD"

# Render via a temporary X server; this works on headless build hosts.
unset DISPLAY
xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,55,0,25,420 \
  -D 'part="closed"' -o "$OUT/preview_closed.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,55,0,25,500 \
  -D 'part="exploded"' -o "$OUT/preview_exploded.png" "$SCAD"

xvfb-run -a -s '-screen 0 1800x1200x24' \
  openscad --render --autocenter --viewall --projection=p \
  --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
  --camera=0,0,0,55,0,25,440 \
  -D 'board_variant="production_rails_attached"' -D 'part="closed"' \
  -o "$OUT/preview_closed_rails_attached.png" "$SCAD"

python3 "$ROOT/verify_openscad.py"
