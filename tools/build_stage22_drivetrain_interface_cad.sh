#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec python3 "$ROOT/tools/build_stage22_drivetrain_interface_cad.py"
