#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SCAD="$ROOT/hardware/stage21_wheel_preload_adjuster/stage21_wheel_preload_adjuster.scad"
OUT="$ROOT/hardware/stage21_wheel_preload_adjuster/outputs"
OPENSCAD=${OPENSCAD:-/opt/homebrew/bin/openscad}

mkdir -p "$OUT"

if [ ! -x "$OPENSCAD" ]; then
  echo "OpenSCAD is unavailable; using the dependency-light DXF/STL/PNG fallback." >&2
  exec python3 "$ROOT/tools/build_stage21_wheel_preload_cad.py"
fi

"$OPENSCAD" -o "$OUT/stage21_wheel_preload_assembly.stl" -D 'part="assembly"' -D 'travel=3' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_fixed_slider_plate.stl" -D 'part="fixed_plate"' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_moving_side_plate.stl" -D 'part="moving_plate"' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_jackscrew_block.stl" -D 'part="jackscrew_block"' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_crowned_wheel_envelope.stl" -D 'part="crowned_wheel"' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_fixed_slider_plate.dxf" -D 'part="fixed_plate_2d"' "$SCAD"
"$OPENSCAD" -o "$OUT/stage21_moving_side_plate.dxf" -D 'part="moving_plate_2d"' "$SCAD"
"$OPENSCAD" --render --autocenter --viewall --projection=p --imgsize=1600,1000 \
  -o "$OUT/stage21_wheel_preload_global_pair.png" \
  -D 'part="global_pair"' -D 'travel=3' -D 'show_shell=true' "$SCAD"

echo "STAGE21_CAD_OUTPUT $OUT"
