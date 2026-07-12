#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
mkdir -p "$ROOT/build"
c++ -std=c++20 -Wall -Wextra -Werror -pedantic \
  "$ROOT/firmware/power_safety.cpp" \
  "$ROOT/tests/power_safety_replay_test.cpp" \
  -o "$ROOT/build/power_safety_replay_test"
"$ROOT/build/power_safety_replay_test" "$ROOT/engineering/power_safety_replay.csv"
