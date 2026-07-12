#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUTPUT=$(arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  --config-file "$ROOT/.arduino/arduino-cli.yaml" \
  --build-path "$ROOT/build/esp32_bb8_stage11" \
  "$ROOT/firmware/esp32_bb8" 2>&1)
printf '%s\n' "$OUTPUT"

PROGRAM_BYTES=$(printf '%s\n' "$OUTPUT" | sed -n 's/^Sketch uses \([0-9][0-9]*\) bytes.*/\1/p')
GLOBAL_BYTES=$(printf '%s\n' "$OUTPUT" | sed -n 's/^Global variables use \([0-9][0-9]*\) bytes.*/\1/p')
if [ -z "$PROGRAM_BYTES" ] || [ -z "$GLOBAL_BYTES" ]; then
  echo "FAIL unable to parse Arduino CLI size report" >&2
  exit 1
fi

node - "$ROOT/engineering/bb8_firmware_compile.json" "$PROGRAM_BYTES" "$GLOBAL_BYTES" <<'NODE'
const { readFileSync } = require("node:fs");
const [manifestPath, programText, globalText] = process.argv.slice(2);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const program = Number(programText);
const globals = Number(globalText);
if (manifest.program_bytes !== program || manifest.global_bytes !== globals) {
  throw new Error(
    `compile manifest mismatch: expected ${manifest.program_bytes}/${manifest.global_bytes}, got ${program}/${globals}`,
  );
}
console.log(`PASS bb8_firmware_compile program=${program} global=${globals}`);
NODE
