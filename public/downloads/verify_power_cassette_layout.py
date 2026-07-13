#!/usr/bin/env python3
"""Verify the Stage-18 analytical power-cassette packaging contract."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LAYOUT = ROOT / "engineering" / "stage18_power_cassette_layout.json"
DEFAULT_BASELINE = ROOT / "engineering" / "stage18_layout_baseline.json"
DEFAULT_RESULTS = ROOT / "engineering" / "stage18_power_cassette_results.json"


def aabb(centre, dimensions):
    minimum = [centre[index] - dimensions[index] / 2.0 for index in range(3)]
    maximum = [centre[index] + dimensions[index] / 2.0 for index in range(3)]
    return minimum, maximum


def maximum_corner_radius(minimum, maximum):
    return max(
        math.sqrt(x * x + y * y + z * z)
        for x in (minimum[0], maximum[0])
        for y in (minimum[1], maximum[1])
        for z in (minimum[2], maximum[2])
    )


def axis_separation(first, second):
    first_min, first_max = first
    second_min, second_max = second
    return max(
        first_min[0] - second_max[0], second_min[0] - first_max[0],
        first_min[1] - second_max[1], second_min[1] - first_max[1],
        first_min[2] - second_max[2], second_min[2] - first_max[2],
    )


def verify(layout, baseline):
    checks = []

    def check(identifier, passed, actual, requirement):
        checks.append({
            "id": identifier,
            "passed": bool(passed),
            "actual": actual,
            "requirement": requirement,
        })

    check("stage", layout.get("stage") == 18, layout.get("stage"), 18)
    check("baseline_stage", baseline.get("engineering_stage") == 15,
          baseline.get("engineering_stage"), 15)
    check("baseline_internal_count", baseline.get("internal_object_count", 0) >= 150,
          baseline.get("internal_object_count"), ">=150")

    components = layout.get("components", [])
    check("candidate_count", len(components) == 8, len(components), 8)
    ids = [component.get("id") for component in components]
    check("candidate_ids_unique", len(ids) == len(set(ids)), ids, "all unique")

    bms = layout.get("bms_candidate", {})
    check("bms_is_4s", bms.get("series_cells") == 4, bms.get("series_cells"), 4)
    check("bms_two_temperature_channels", bms.get("temperature_sensor_channels", 0) >= 2,
          bms.get("temperature_sensor_channels"), ">=2")
    check("bms_external_contactor_control", bms.get("contactor_control_outputs") is True,
          bms.get("contactor_control_outputs"), True)
    check("bms_charge_disable", bms.get("charge_disable_output") is True,
          bms.get("charge_disable_output"), True)
    check("bms_shunt_range", bms.get("external_shunt_range_a", 0) >= 30.0,
          bms.get("external_shunt_range_a"), ">=30 A")

    by_id = {component["id"]: component for component in components}
    driver = by_id.get("DRV01", {})
    check("mdd20a_board_footprint",
          driver.get("board_dimensions_mm") == [1.6, 88.9, 78.74],
          driver.get("board_dimensions_mm"), [1.6, 88.9, 78.74])
    check("mdd20a_mount_spacing",
          driver.get("mount_hole_spacing_mm") == [83.82, 73.66],
          driver.get("mount_hole_spacing_mm"), [83.82, 73.66])
    check("mdd20a_height_explicitly_unfrozen", "HEIGHT" in str(driver.get("status", "")),
          driver.get("status"), "height remains a measurement gate")

    radius = float(layout["body_inner_radius_assumption_mm"])
    default_shell_clearance = float(layout["minimum_shell_clearance_mm"])
    boxes = {}
    shell_clearances = {}
    for component in components:
        box = aabb(component["centre_mm"], component["dimensions_mm"])
        boxes[component["id"]] = box
        clearance = radius - maximum_corner_radius(*box)
        shell_clearances[component["id"]] = round(clearance, 3)
        required = max(default_shell_clearance, float(component.get("minimum_shell_clearance_mm", 0)))
        check(f"shell_clearance_{component['id']}", clearance >= required,
              round(clearance, 3), f">={required:.1f} mm")

    pair_requirement = float(layout["minimum_candidate_pair_clearance_mm"])
    pair_clearances = {}
    for index, first in enumerate(components):
        for second in components[index + 1:]:
            key = f"{first['id']}__{second['id']}"
            separation = axis_separation(boxes[first["id"]], boxes[second["id"]])
            pair_clearances[key] = round(separation, 3)
            check(f"candidate_pair_{key}", separation >= pair_requirement,
                  round(separation, 3), f">={pair_requirement:.1f} mm")

    baseline_by_name = {item["name"]: item for item in baseline.get("all_internal_aabbs", [])}
    protected_requirement = float(layout["minimum_protected_hardware_clearance_mm"])
    protected_clearances = {}
    for protected_name in layout.get("protected_internal_objects", []):
        protected = baseline_by_name.get(protected_name)
        check(f"protected_exists_{protected_name}", protected is not None,
              protected_name if protected else None, "present in Blender baseline")
        if protected is None:
            continue
        protected_box = (protected["parent_minimum_mm"], protected["parent_maximum_mm"])
        for component in components:
            key = f"{component['id']}__{protected_name}"
            separation = axis_separation(boxes[component["id"]], protected_box)
            protected_clearances[key] = round(separation, 3)
            check(f"protected_clearance_{key}", separation >= protected_requirement,
                  round(separation, 3), f">={protected_requirement:.1f} mm")

    freeze_gates = layout.get("freeze_gates", {})
    unresolved = sorted(key for key, value in freeze_gates.items() if value is not True)
    check("freeze_gates_remain_explicit", len(unresolved) >= 10, len(unresolved), ">=10 unresolved")

    analytical_pass = all(item["passed"] for item in checks)
    overall = (
        "HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED"
        if analytical_pass and unresolved
        else "FAIL_ANALYTICAL_PACKAGING"
    )
    return {
        "stage": 18,
        "overall": overall,
        "analytical_packaging_passed": analytical_pass,
        "physical_fit_tested": False,
        "powered_tested": False,
        "shell_clearances_mm": shell_clearances,
        "minimum_shell_clearance_mm": min(shell_clearances.values()) if shell_clearances else None,
        "candidate_pair_clearances_mm": pair_clearances,
        "minimum_candidate_pair_clearance_mm": min(pair_clearances.values()) if pair_clearances else None,
        "protected_clearances_mm": protected_clearances,
        "minimum_protected_hardware_clearance_mm": min(protected_clearances.values()) if protected_clearances else None,
        "unresolved_freeze_gates": unresolved,
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", type=Path, default=DEFAULT_LAYOUT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    result = verify(layout, baseline)
    args.results.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['overall']} analytical={result['analytical_packaging_passed']} "
        f"shell_min={result['minimum_shell_clearance_mm']:.3f}mm "
        f"candidate_min={result['minimum_candidate_pair_clearance_mm']:.3f}mm "
        f"protected_min={result['minimum_protected_hardware_clearance_mm']:.3f}mm "
        f"unresolved={len(result['unresolved_freeze_gates'])}"
    )
    print("RESULTS", args.results)
    if args.expect_overall and result["overall"] != args.expect_overall:
        raise SystemExit(f"expected {args.expect_overall}, got {result['overall']}")
    if result["overall"] == "FAIL_ANALYTICAL_PACKAGING":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
