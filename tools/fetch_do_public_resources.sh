#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REPO="$ROOT/third_party/D-O-Printed-Droid"
REMOTE="https://github.com/PrintedDroid/D-O-Printed-Droid.git"
PUBLIC="$ROOT/third_party/do_public_resources"

mkdir -p "$ROOT/third_party" "$PUBLIC"

fetch_public() {
  filename=$1
  url=$2
  curl -L --fail --retry 5 --retry-all-errors \
    -o "$PUBLIC/$filename" \
    "$url"
}

if [ -d "$REPO/.git" ]; then
  actual=$(git -C "$REPO" remote get-url origin)
  if [ "$actual" != "$REMOTE" ]; then
    echo "FAIL unexpected origin: $actual" >&2
    exit 1
  fi
  git -C "$REPO" fetch --prune origin
else
  git clone --filter=blob:none "$REMOTE" "$REPO"
fi

curl -L --fail --retry 5 --retry-all-errors \
  -o "$ROOT/third_party/DO-Instructions-Pt1.1.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2022/07/DO-Instructions-Pt1.1.pdf"
curl -L --fail --retry 5 --retry-all-errors \
  -o "$ROOT/third_party/DOV2-Wiring-diagram-notes.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2022/07/DOV2-Wiring-diagram-notes.pdf"
curl -L --fail --retry 5 --retry-all-errors \
  -o "$ROOT/third_party/DO-Stand-60mm.stl" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/DO-Stand-60mm.stl"

# Complete public attachment set exposed by the Printed Droid control-board page
# on 2026-07-13. These stay under the gitignored third_party directory because
# public download availability does not by itself grant redistribution rights.
fetch_public "D-O_AIO32_v2_User_Handbook_v2.1.1.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2_User_Handbook_v2.1.1.pdf"
fetch_public "D-O_AIO32_v2_User_Handbook_v2.1.1_DE.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2_User_Handbook_v2.1.1_DE.pdf"
fetch_public "D-O_AIO32_v2.1.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2.1.zip"
fetch_public "D-O_Control__Power_Board_System_Documentation_v2.2.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Control__Power_Board_System_Documentation_v2.2.pdf"
fetch_public "D-O_Control__Power_Board_System_Documentation_v2.2_DE.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Control__Power_Board_System_Documentation_v2.2_DE.pdf"
fetch_public "D-O_ibus_v3.4.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_ibus_v3.4.zip"
fetch_public "D-O_ibus_v2.1.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_ibus_v2.1.zip"
fetch_public "D-O-AIO-1.4-v1.3.pdf" \
  "https://www.printed-droid.com/wp-content/uploads/2020/11/D-O-AIO-1.4-v1.3.pdf"
fetch_public "dov2_printed_droid_rc_ibus_v1.1.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/dov2_printed_droid_rc_ibus_v1.1.zip"
fetch_public "D_O_Nano_Sketch_v2.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D_O_Nano_Sketch_v2.zip"
fetch_public "D-O_Nano_Sketch.zip" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Nano_Sketch.zip"
fetch_public "DO-Stand-60mm.stl" \
  "https://www.printed-droid.com/wp-content/uploads/2020/09/DO-Stand-60mm.stl"

echo "Fetched the 12 public control-page attachments plus legacy assembly references without checking out paid CAD."
echo "Repository remains on its current commit; inspect origin/main before updating."
