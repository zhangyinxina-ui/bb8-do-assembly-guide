#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CONFIG="$ROOT/engineering/arduino-cli-do.yaml"
ARCHIVE="$ROOT/third_party/do_public_resources/D-O_AIO32_v2.1.zip"
WORK_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/bb8-do-aio32-compile.XXXXXX")
SKETCH="$WORK_ROOT/D-O_AIO32_v2.1"
BUILD="$WORK_ROOT/build"

mkdir -p "$SKETCH" "$BUILD"
unzip -q "$ARCHIVE" -d "$SKETCH"

arduino-cli compile \
  --config-file "$CONFIG" \
  --fqbn 'esp32:esp32:adafruit_feather_esp32s3_tft:CDCOnBoot=cdc,PSRAM=disabled,FlashSize=4M,PartitionScheme=default' \
  --build-path "$BUILD" \
  "$SKETCH"

echo "PASS D-O AIO32 v2.1 ESP32-S3 compile"
echo "Evidence build retained at: $WORK_ROOT"
