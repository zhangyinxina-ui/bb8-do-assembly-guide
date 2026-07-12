#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
REPO="$ROOT/third_party/D-O-Printed-Droid"
REMOTE="https://github.com/PrintedDroid/D-O-Printed-Droid.git"

mkdir -p "$ROOT/third_party"

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

echo "Fetched public D-O references without checking out paid CAD."
echo "Repository remains on its current commit; inspect origin/main before updating."
