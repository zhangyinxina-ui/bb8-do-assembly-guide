#!/usr/bin/env python3
"""Numerical audit for the BB-8 rolling-cycle rig; no third-party packages."""

import csv
import math
from pathlib import Path

BODY_R = 0.254
WHEEL_R = 0.048
DURATION = 4.0
FPS = 30
OUT = Path(__file__).resolve().parents[1] / "blender" / "output" / "kinematics.csv"


def sample(t: float) -> dict[str, float]:
    fraction = t / DURATION
    body_theta = 2 * math.pi * fraction
    distance = BODY_R * body_theta
    wheel_theta = distance / WHEEL_R
    return {
        "time_s": t,
        "distance_m": distance,
        "body_angle_deg": math.degrees(body_theta),
        "wheel_angle_deg": math.degrees(wheel_theta),
        "head_pitch_target_deg": 0.0,
    }


rows = [sample(frame / FPS) for frame in range(int(DURATION * FPS) + 1)]
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

end = rows[-1]
expected_distance = 2 * math.pi * BODY_R
assert abs(end["distance_m"] - expected_distance) < 1e-9
assert abs(end["body_angle_deg"] - 360.0) < 1e-9
assert abs(end["wheel_angle_deg"] / 360.0 - expected_distance / (2 * math.pi * WHEEL_R)) < 1e-9
print(f"PASS distance={end['distance_m']:.6f}m body=360deg wheel_turns={end['wheel_angle_deg']/360:.6f}")
print(f"CSV {OUT}")
