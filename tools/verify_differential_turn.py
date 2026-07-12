#!/usr/bin/env python3
import csv
import math
from pathlib import Path

TRACK = 0.31
TURN_RADIUS = 0.80
SPEED = 0.30
YAW_RATE = SPEED / TURN_RADIUS
DURATION = (math.pi / 2) / YAW_RATE
DT = 0.01
OUT = Path(__file__).resolve().parents[1] / "blender" / "output" / "differential_turn.csv"

left = SPEED - YAW_RATE * TRACK / 2
right = SPEED + YAW_RATE * TRACK / 2
x = y = heading = 0.0
rows = []
t = 0.0
while t < DURATION - 1e-12:
    step = min(DT, DURATION - t)
    heading += YAW_RATE * step
    x += SPEED * math.sin(heading) * step
    y += SPEED * math.cos(heading) * step
    t += step
    rows.append({"time_s": t, "x_m": x, "y_m": y, "heading_deg": math.degrees(heading),
                 "left_mps": left, "right_mps": right})

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0], lineterminator="\n")
    w.writeheader(); w.writerows(rows)

assert abs(math.degrees(heading) - 90.0) < 1e-8
assert abs(x - TURN_RADIUS) < 0.002
assert abs(y - TURN_RADIUS) < 0.002
assert right > left > 0
print(f"PASS 90deg arc radius={TURN_RADIUS:.3f}m end=({x:.4f},{y:.4f})m left={left:.4f} right={right:.4f}m/s")
print(f"CSV {OUT}")
