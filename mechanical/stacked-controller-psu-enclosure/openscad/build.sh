#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SCAD="$ROOT/CoffeeRoast_RevA2_LOP200_stacked.scad"
OUT="$ROOT/generated"
mkdir -p "$OUT"

for part in lower_base controller_deck lid_print; do
  openscad --hardwarnings -D "part=\"$part\"" -o "$OUT/$part.stl" "$SCAD"
  openscad --hardwarnings -D "part=\"$part\"" -o "$OUT/$part.3mf" "$SCAD"
done
openscad --hardwarnings -D 'part="lid"' -o "$OUT/lid_design.stl" "$SCAD"
openscad --hardwarnings -D 'part="psu_proxy"' -o "$OUT/psu_proxy.stl" "$SCAD"
openscad --hardwarnings -D 'part="pcb_proxy"' -o "$OUT/pcb_proxy.stl" "$SCAD"

unset DISPLAY
render() {
  local name="$1" part="$2" camera="$3" zoom="$4"
  xvfb-run -a -s '-screen 0 1800x1200x24' \
    openscad --render --autocenter --viewall --projection=p \
    --imgsize=1800,1200 --colorscheme='Tomorrow Night' \
    --camera="$camera,$zoom" -D "part=\"$part\"" \
    -o "$OUT/$name.png" "$SCAD"
}
render preview_closed closed '0,0,0,55,0,25' 650
render preview_exploded exploded '0,0,0,55,0,25' 920
render preview_usb closed '0,0,0,90,0,90' 620
render preview_ac closed '0,0,0,90,0,-90' 620

python3 "$ROOT/verify_openscad.py"
