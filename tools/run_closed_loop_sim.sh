#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$ROOT/build"

${CXX:-c++} -std=c++20 -Wall -Wextra -Werror -pedantic \
  "$ROOT/firmware/controller_core.cpp" \
  "$ROOT/tests/closed_loop_sim_test.cpp" \
  -o "$ROOT/build/closed_loop_sim_test"

"$ROOT/build/closed_loop_sim_test" "$ROOT/engineering/closed_loop_telemetry.csv"
cp "$ROOT/engineering/closed_loop_telemetry.csv" \
  "$ROOT/public/downloads/closed_loop_telemetry.csv"
