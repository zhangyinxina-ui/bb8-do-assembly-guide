#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CONFIG="$ROOT/engineering/arduino-cli-do.yaml"
SOURCE="$ROOT/third_party/D-O-Printed-Droid/D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino"
LICENSE_README="$ROOT/third_party/D-O-Printed-Droid/D-O_ibus_v3.4/README.md"
STAGE="$ROOT/engineering/do-firmware-stage/D_O_printed_droid_rc_ibus_v3.4.3"
BUILD="$ROOT/engineering/do-firmware-build"

rm -rf "$STAGE" "$BUILD"
mkdir -p "$STAGE" "$BUILD"
cp "$SOURCE" "$STAGE/D_O_printed_droid_rc_ibus_v3.4.3.ino"
cp "$LICENSE_README" "$STAGE/README.md"

arduino-cli compile \
  --config-file "$CONFIG" \
  --fqbn arduino:avr:mega \
  --build-path "$BUILD" \
  "$STAGE"

echo "PASS D-O v3.4.3 Arduino Mega 2560 compile"
