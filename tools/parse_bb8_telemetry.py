#!/usr/bin/env python3
"""Convert ESP32 BB-8 key=value serial telemetry into CSV plus a summary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


FIELDS = [
    "t_ms", "enabled", "fault", "cmdV", "cmdW", "batt", "temp", "estop",
    "remote", "imu", "enc", "tilt", "yaw", "vL", "vR", "iL", "iR",
    "power", "hwtrip", "pwmL", "pwmR",
]
INTEGER_FIELDS = {"t_ms", "enabled", "estop", "remote", "imu", "enc", "power", "hwtrip"}
FLOAT_FIELDS = set(FIELDS) - INTEGER_FIELDS - {"fault"}
TOKEN = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=(?P<value>[^\s]+)")


def parse_telemetry_line(line: str) -> dict[str, Any] | None:
    pairs = {match.group("key"): match.group("value") for match in TOKEN.finditer(line)}
    if "enabled" not in pairs:
        return None
    missing = [field for field in FIELDS if field not in pairs]
    if missing:
        raise ValueError(f"telemetry line missing keys: {', '.join(missing)}")
    parsed: dict[str, Any] = {}
    for field in FIELDS:
        raw = pairs[field]
        if field == "fault":
            parsed[field] = raw
        elif field in INTEGER_FIELDS:
            parsed[field] = int(raw)
        else:
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError(f"{field} must be finite")
            parsed[field] = value
    return parsed


def parse_lines(lines: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    last_t_ms = -1
    for line_number, line in enumerate(lines, start=1):
        try:
            row = parse_telemetry_line(line)
        except ValueError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc
        if row is None:
            continue
        if row["t_ms"] <= last_t_ms:
            raise ValueError(f"line {line_number}: t_ms must increase strictly")
        last_t_ms = row["t_ms"]
        rows.append(row)
    if not rows:
        raise ValueError("no telemetry rows found")
    return rows


def summarise(rows: list[dict[str, Any]], source_sha256: str) -> dict[str, Any]:
    faults = Counter(row["fault"] for row in rows)
    return {
        "schema_version": 1,
        "source_sha256": source_sha256,
        "rows": len(rows),
        "duration_s": round((rows[-1]["t_ms"] - rows[0]["t_ms"]) / 1000.0, 6),
        "enabled_samples": sum(row["enabled"] for row in rows),
        "fault_counts": dict(sorted(faults.items())),
        "minimum_battery_v": min(row["batt"] for row in rows),
        "maximum_temperature_c": max(row["temp"] for row in rows),
        "maximum_abs_tilt_deg": max(abs(row["tilt"]) for row in rows),
        "maximum_abs_left_current_a": max(abs(row["iL"]) for row in rows),
        "maximum_abs_right_current_a": max(abs(row["iR"]) for row in rows),
        "maximum_abs_left_speed_mps": max(abs(row["vL"]) for row in rows),
        "maximum_abs_right_speed_mps": max(abs(row["vR"]) for row in rows),
        "estop_unsafe_samples": sum(1 for row in rows if row["estop"] == 0),
        "remote_stale_samples": sum(1 for row in rows if row["remote"] == 0),
        "hardware_trip_samples": sum(1 for row in rows if row["hwtrip"] != 0),
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    try:
        with args.input.open("r", encoding="utf-8", errors="strict") as handle:
            rows = parse_lines(handle)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR telemetry: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = summarise(rows, file_sha256(args.input))
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"PASS telemetry rows={summary['rows']} duration={summary['duration_s']:.3f}s "
        f"faults={summary['fault_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
