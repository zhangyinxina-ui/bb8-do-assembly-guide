#!/usr/bin/env python3
"""Verify Stage-21 powered-wheel contact geometry and preload-cassette screening."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "engineering" / "stage21_wheel_preload_contract.json"
DEFAULT_MANIFEST = ROOT / "engineering" / "internal_assembly_manifest.csv"
DEFAULT_RESULTS = ROOT / "engineering" / "stage21_wheel_preload_results.json"
DEFAULT_SWEEP = ROOT / "engineering" / "stage21_wheel_preload_sweep.csv"
DEFAULT_BOM = ROOT / "engineering" / "stage21_wheel_preload_bom.csv"
DEFAULT_REPORT_ZH = ROOT / "docs" / "BB8_阶段21_切向轮轴与预压滑台门.md"
DEFAULT_REPORT_EN = ROOT / "docs" / "BB8_stage21_tangent_wheel_preload_cassette_gate.md"


Vector = tuple[float, float, float]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: Vector) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vector) -> Vector:
    length = norm(a)
    if length <= 0.0:
        raise ValueError("zero-length vector")
    return tuple(value / length for value in a)  # type: ignore[return-value]


def cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def inverse_pitch_x(center: Vector, pitch_deg: float) -> Vector:
    """Undo the Blender chassis X pitch stored in the fabrication manifest."""
    angle = math.radians(-pitch_deg)
    x, y, z = center
    return (
        x,
        y * math.cos(angle) - z * math.sin(angle),
        y * math.sin(angle) + z * math.cos(angle),
    )


def finite_cylinder_support_radius(
    center: Vector, axis: Vector, radius_mm: float, half_width_mm: float
) -> float:
    """Exact farthest radius of a closed finite cylinder from the sphere origin."""
    axis_u = unit(axis)
    parallel = abs(dot(center, axis_u))
    perpendicular = math.sqrt(max(0.0, norm(center) ** 2 - parallel**2))
    return math.hypot(parallel + half_width_mm, perpendicular + radius_mm)


def crowned_support_radius(
    center_radius_mm: float,
    wheel_radius_mm: float,
    half_width_mm: float,
    crown_drop_mm: float,
    samples: int = 4000,
) -> tuple[float, float]:
    """Return maximum support and its axial coordinate for a parabolic crown."""
    best_support = -math.inf
    best_s = 0.0
    for index in range(samples + 1):
        s = -half_width_mm + 2.0 * half_width_mm * index / samples
        radial = wheel_radius_mm - crown_drop_mm * (s / half_width_mm) ** 2
        support = math.hypot(s, center_radius_mm + radial)
        if support > best_support:
            best_support = support
            best_s = s
    return best_support, best_s


def minimum_crown_drop(
    shell_radius_mm: float,
    center_radius_mm: float,
    wheel_radius_mm: float,
    half_width_mm: float,
) -> float:
    edge_radial_limit = math.sqrt(shell_radius_mm**2 - half_width_mm**2)
    return max(0.0, wheel_radius_mm - (edge_radial_limit - center_radius_mm))


def read_manifest(path: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return rows, {row["object"]: row for row in rows}


def verify(contract: dict, rows: list[dict[str, str]], by_name: dict[str, dict[str, str]]) -> dict:
    checks: list[dict] = []

    def check(identifier: str, passed: bool, actual, requirement) -> None:
        checks.append({"id": identifier, "passed": bool(passed), "actual": actual, "requirement": requirement})

    baseline = contract["geometry_baseline"]
    architecture = contract["selected_architecture"]
    wheel = architecture["wheel"]
    slide = architecture["radial_slide"]
    belt = architecture["parallel_belt_drive"]
    cad = architecture["cassette_reference_cad"]
    loads = contract["load_and_calibration_inputs"]
    thresholds = contract["acceptance_thresholds"]

    shell_radius = float(baseline["sphere_inner_radius_mm"])
    wheel_radius = float(wheel["nominal_radius_mm"])
    half_width = float(wheel["axial_half_width_mm"])
    current_axis = unit(tuple(float(value) for value in baseline["current_wheel_axis_unit"]))
    pitch_deg = float(baseline["animation_frame_pitch_deg"])

    check("stage", contract.get("stage") == 21, contract.get("stage"), 21)
    check("manifest_nonempty", len(rows) >= 100, len(rows), ">=100 current fabrication rows")

    wheel_evidence = []
    for object_name in baseline["wheel_objects"]:
        row = by_name.get(object_name)
        check(f"object_exists_{object_name}", row is not None, object_name if row else None, "present")
        if row is None:
            continue
        dimensions = tuple(float(row[f"size_{axis}_mm"]) for axis in "xyz")
        expected = tuple(float(value) for value in baseline["expected_wheel_envelope_mm"])
        dimension_error = max(abs(actual - target) for actual, target in zip(dimensions, expected))
        check(
            f"wheel_envelope_{object_name}",
            dimension_error <= float(baseline["dimension_tolerance_mm"]),
            dimensions,
            expected,
        )
        world_center = tuple(float(row[f"center_{axis}_mm"]) for axis in "xyz")
        neutral_center = inverse_pitch_x(world_center, pitch_deg)
        center_radius = norm(neutral_center)
        exact_support = finite_cylinder_support_radius(neutral_center, current_axis, wheel_radius, half_width)
        legacy_support = center_radius + max(dimensions) / 2.0
        radial_unit = unit(neutral_center)
        axis_to_tangent_error_deg = math.degrees(math.asin(min(1.0, abs(dot(current_axis, radial_unit)))))
        wheel_evidence.append({
            "object": object_name,
            "manifest_world_center_mm": [round(value, 6) for value in world_center],
            "neutral_center_mm": [round(value, 6) for value in neutral_center],
            "neutral_center_radius_mm": round(center_radius, 6),
            "legacy_spherical_support_mm": round(legacy_support, 6),
            "exact_finite_cylinder_support_mm": round(exact_support, 6),
            "exact_shell_gap_mm": round(shell_radius - exact_support, 6),
            "axis_to_shell_tangent_error_deg": round(axis_to_tangent_error_deg, 6),
            "radial_unit": [round(value, 9) for value in radial_unit],
        })

    if len(wheel_evidence) == 2:
        centres = [item["neutral_center_mm"] for item in wheel_evidence]
        symmetry_error = max(
            abs(centres[0][0] + centres[1][0]),
            abs(centres[0][1] - centres[1][1]),
            abs(centres[0][2] - centres[1][2]),
        )
        center_radius_error = max(
            abs(item["neutral_center_radius_mm"] - float(baseline["expected_neutral_wheel_center_radius_mm"]))
            for item in wheel_evidence
        )
        minimum_gap = min(item["exact_shell_gap_mm"] for item in wheel_evidence)
        minimum_tangent_error = min(item["axis_to_shell_tangent_error_deg"] for item in wheel_evidence)
        legacy_overstatement = min(
            item["legacy_spherical_support_mm"] - item["exact_finite_cylinder_support_mm"]
            for item in wheel_evidence
        )
    else:
        symmetry_error = math.inf
        center_radius_error = math.inf
        minimum_gap = -math.inf
        minimum_tangent_error = -math.inf
        legacy_overstatement = -math.inf

    check("wheel_pair_neutral_symmetry", symmetry_error <= 0.15, round(symmetry_error, 6), "<=0.15 mm")
    check("wheel_center_radius", center_radius_error <= 0.15, round(center_radius_error, 6), "<=0.15 mm from 206 mm")
    check(
        "current_exact_shell_gap_detected",
        minimum_gap >= float(thresholds["minimum_detected_current_shell_gap_mm"]),
        round(minimum_gap, 6),
        f">={thresholds['minimum_detected_current_shell_gap_mm']} mm",
    )
    check(
        "current_axis_tangent_error_detected",
        minimum_tangent_error >= float(thresholds["minimum_detected_axis_to_tangent_error_deg"]),
        round(minimum_tangent_error, 6),
        f">={thresholds['minimum_detected_axis_to_tangent_error_deg']} deg",
    )
    check("legacy_spherical_formula_overstatement_detected", legacy_overstatement >= 4.5, round(legacy_overstatement, 6), ">=4.5 mm")

    nominal_center_radius = (
        float(slide["inner_stop_wheel_center_radius_mm"])
        + float(slide["nominal_contact_position_from_inner_stop_mm"])
    )
    right_radial = unit((
        float(baseline["expected_neutral_wheel_center_x_mm"]),
        0.0,
        -math.sqrt(
            nominal_center_radius**2
            - float(baseline["expected_neutral_wheel_center_x_mm"]) ** 2
        ),
    ))
    drive_direction = (0.0, 1.0, 0.0)
    tangent_axis = unit(cross(right_radial, drive_direction))
    tangent_dot = abs(dot(tangent_axis, right_radial))
    generated_drive = unit(cross(tangent_axis, right_radial))
    drive_alignment = dot(generated_drive, drive_direction)
    selected_crown_drop = float(wheel["selected_crown_drop_at_edge_mm"])
    required_crown_drop = minimum_crown_drop(
        shell_radius, nominal_center_radius, wheel_radius, half_width
    )
    crowned_support, support_s = crowned_support_radius(
        nominal_center_radius, wheel_radius, half_width, selected_crown_drop
    )
    crown_edge_support = math.hypot(
        half_width, nominal_center_radius + wheel_radius - selected_crown_drop
    )
    crown_edge_clearance = shell_radius - crown_edge_support

    check(
        "selected_axis_is_shell_tangent",
        tangent_dot <= float(thresholds["maximum_tangent_axis_dot_radial"]),
        tangent_dot,
        f"<={thresholds['maximum_tangent_axis_dot_radial']}",
    )
    check("selected_axis_generates_forward_tread_velocity", drive_alignment >= 0.999999, round(drive_alignment, 9), ">=0.999999")
    check("selected_crown_exceeds_geometric_minimum", selected_crown_drop >= required_crown_drop, round(selected_crown_drop - required_crown_drop, 6), ">=0 mm margin")
    check(
        "nominal_crowned_support_matches_shell",
        abs(crowned_support - shell_radius) <= float(thresholds["maximum_nominal_crowned_support_error_mm"]),
        round(crowned_support, 6),
        f"{shell_radius} +/- {thresholds['maximum_nominal_crowned_support_error_mm']} mm",
    )
    check(
        "crown_edge_clearance",
        crown_edge_clearance >= float(thresholds["minimum_crown_edge_clearance_mm"]),
        round(crown_edge_clearance, 6),
        f">={thresholds['minimum_crown_edge_clearance_mm']} mm",
    )

    travel = float(slide["total_usable_travel_mm"])
    tolerance_budget = float(slide["stage20_tolerance_budget_mm"])
    outward_reserve = float(slide["outward_reserve_from_nominal_mm"])
    slot_centerline_travel = float(slide["slot_overall_length_mm"]) - float(slide["candidate_clearance_width_mm"])
    travel_margin = outward_reserve - tolerance_budget
    check("slide_travel_matches_stops", abs(travel - (float(slide["inward_reserve_from_nominal_mm"]) + outward_reserve)) <= 1e-9, travel, "inward + outward reserve")
    check("slot_supports_full_travel", abs(slot_centerline_travel - travel) <= 1e-9, round(slot_centerline_travel, 6), travel)
    check(
        "outward_travel_covers_tolerance_with_margin",
        travel_margin >= float(thresholds["minimum_outward_travel_beyond_tolerance_budget_mm"]),
        round(travel_margin, 6),
        f">={thresholds['minimum_outward_travel_beyond_tolerance_budget_mm']} mm",
    )

    pulley_pitch_diameter = float(belt["pulley_teeth_motor"]) * float(belt["belt_pitch_mm"]) / math.pi
    calculated_belt_length = 2.0 * float(belt["axis_center_distance_mm"]) + math.pi * pulley_pitch_diameter
    belt_length_error = abs(calculated_belt_length - float(belt["candidate_belt_pitch_length_mm"]))
    belt_ratio = float(belt["pulley_teeth_wheel"]) / float(belt["pulley_teeth_motor"])
    check(
        "equal_pulley_belt_pitch_length",
        belt_length_error <= float(thresholds["maximum_belt_pitch_length_error_mm"]),
        round(calculated_belt_length, 6),
        float(belt["candidate_belt_pitch_length_mm"]),
    )
    check("belt_ratio_is_one_to_one", abs(belt_ratio - float(belt["ratio"])) <= 1e-9, belt_ratio, belt["ratio"])
    check(
        "belt_tooth_count_integer",
        abs(calculated_belt_length / float(belt["belt_pitch_mm"]) - int(belt["candidate_belt_teeth"])) <= 1e-9,
        calculated_belt_length / float(belt["belt_pitch_mm"]),
        int(belt["candidate_belt_teeth"]),
    )

    motor_center_radius = nominal_center_radius - float(belt["axis_center_distance_mm"])
    motor_support = finite_cylinder_support_radius(
        tuple(value * motor_center_radius for value in right_radial),
        tangent_axis,
        float(belt["motor_envelope_diameter_mm"]) / 2.0,
        float(belt["motor_envelope_length_mm"]) / 2.0,
    )
    motor_clearance = shell_radius - motor_support
    check(
        "tangent_motor_envelope_shell_clearance",
        motor_clearance >= float(thresholds["minimum_motor_envelope_shell_clearance_mm"]),
        round(motor_clearance, 6),
        f">={thresholds['minimum_motor_envelope_shell_clearance_mm']} mm",
    )

    plate_base_radius = nominal_center_radius - float(cad["wheel_axis_local_x_mm"])
    plate_outer_radius = plate_base_radius + float(cad["plate_length_mm"]) + outward_reserve
    plate_half_width = float(cad["plate_width_mm"]) / 2.0
    plate_half_axial = float(cad["fixed_plate_center_separation_mm"]) / 2.0 + float(cad["plate_thickness_mm"]) / 2.0
    plate_support = math.sqrt(plate_outer_radius**2 + plate_half_width**2 + plate_half_axial**2)
    plate_clearance = shell_radius - plate_support
    check(
        "reference_plate_box_shell_clearance",
        plate_clearance >= float(thresholds["minimum_reference_plate_shell_clearance_mm"]),
        round(plate_clearance, 6),
        f">={thresholds['minimum_reference_plate_shell_clearance_mm']} mm",
    )

    peak_torque = float(loads["motor_peak_torque_nm_each"])
    wheel_force = peak_torque / float(loads["wheel_radius_m"])
    pulley_pitch_radius_m = pulley_pitch_diameter / 2000.0
    belt_tension_difference = peak_torque / pulley_pitch_radius_m
    shock_factor = float(loads["mechanical_shock_factor"])
    clamp_force_total = (
        wheel_force * shock_factor * float(loads["clamp_slip_safety_factor"])
        / float(loads["minimum_assumed_dry_interface_friction"])
    )
    clamp_force_each = clamp_force_total / int(slide["clamp_bolts_per_cassette"])
    shaft_diameter_m = float(belt["wheel_shaft_candidate_diameter_mm"]) / 1000.0
    shaft_shock_torsional_shear_mpa = 16.0 * peak_torque * shock_factor / (math.pi * shaft_diameter_m**3) / 1e6
    check(
        "minimum_clamp_force_demand_calculated",
        clamp_force_total >= float(thresholds["minimum_clamp_force_demand_n_total"]),
        round(clamp_force_total, 6),
        f">={thresholds['minimum_clamp_force_demand_n_total']} N",
    )

    analytic_contact_track = 2.0 * shell_radius * abs(right_radial[0])
    nominal_wheel_center_track = 2.0 * nominal_center_radius * abs(right_radial[0])
    firmware_track_mm = float(loads["firmware_current_drive_track_m"]) * 1000.0
    track_delta = analytic_contact_track - firmware_track_mm

    unresolved = sorted(key for key, value in contract["freeze_gates"].items() if value is not True)
    analytical_pass = all(item["passed"] for item in checks)
    if not analytical_pass:
        overall = "FAIL_STAGE21_CONTACT_OR_PACKAGING_SCREEN"
    elif unresolved:
        overall = "HOLD_PHYSICAL_CONTACT_BELT_BEARING_AND_CHASSIS_INTEGRATION_REQUIRED"
    else:
        overall = "READY_FOR_INDEPENDENT_DESIGN_REVIEW_NOT_FABRICATION"

    return {
        "stage": 21,
        "overall": overall,
        "analytical_screen_passed": analytical_pass,
        "manufacturing_release": False,
        "physical_test_status": "NOT_RUN",
        "blender_application_status": "NOT_APPLIED_USER_MASTER_PRESERVED",
        "baseline_correction": {
            "historical_contact_audit_superseded": True,
            "reason": baseline["legacy_formula_disposition"],
            "wheels": wheel_evidence,
            "minimum_exact_shell_gap_mm": round(minimum_gap, 6),
            "minimum_axis_to_tangent_error_deg": round(minimum_tangent_error, 6),
            "minimum_legacy_support_overstatement_mm": round(legacy_overstatement, 6),
        },
        "selected_contact_geometry": {
            "architecture": architecture["id"],
            "right_radial_unit": [round(value, 9) for value in right_radial],
            "right_tangent_axis_unit": [round(value, 9) for value in tangent_axis],
            "generated_drive_direction_unit": [round(value, 9) for value in generated_drive],
            "nominal_wheel_center_radius_mm": round(nominal_center_radius, 6),
            "minimum_crown_drop_mm": round(required_crown_drop, 6),
            "selected_crown_drop_mm": round(selected_crown_drop, 6),
            "crown_drop_margin_mm": round(selected_crown_drop - required_crown_drop, 6),
            "nominal_max_support_mm": round(crowned_support, 6),
            "max_support_axial_coordinate_mm": round(support_s, 6),
            "edge_shell_clearance_mm": round(crown_edge_clearance, 6),
        },
        "radial_slide": {
            "usable_travel_mm": round(travel, 6),
            "nominal_position_from_inner_stop_mm": float(slide["nominal_contact_position_from_inner_stop_mm"]),
            "stage20_tolerance_budget_mm": round(tolerance_budget, 6),
            "outward_reserve_mm": round(outward_reserve, 6),
            "margin_beyond_tolerance_budget_mm": round(travel_margin, 6),
            "slot_centerline_travel_mm": round(slot_centerline_travel, 6),
            "jackscrew_mm_per_turn": float(slide["jackscrew_pitch_mm_per_turn"]),
            "quarter_turn_increment_mm": round(float(slide["jackscrew_pitch_mm_per_turn"]) * float(slide["minimum_adjustment_increment_turn"]), 6),
            "target_measured_preload_n_each": float(slide["target_measured_normal_preload_n_each"]),
            "preload_is_analytically_proven": False,
        },
        "parallel_belt_drive": {
            "pulley_pitch_diameter_mm": round(pulley_pitch_diameter, 6),
            "calculated_belt_pitch_length_mm": round(calculated_belt_length, 6),
            "belt_teeth": int(belt["candidate_belt_teeth"]),
            "ratio": round(belt_ratio, 6),
            "motor_center_radius_mm": round(motor_center_radius, 6),
            "motor_envelope_support_mm": round(motor_support, 6),
            "motor_shell_clearance_mm": round(motor_clearance, 6),
            "peak_belt_tension_difference_n": round(belt_tension_difference, 6),
            "shock_factored_belt_tension_difference_n": round(belt_tension_difference * shock_factor, 6),
            "supplier_rating_and_pretension_proven": False,
        },
        "reference_cad_packaging": {
            "conservative_plate_box_support_mm": round(plate_support, 6),
            "plate_shell_clearance_mm": round(plate_clearance, 6),
            "exact_current_chassis_clash_check": "NOT_RUN",
        },
        "load_demands": {
            "peak_wheel_tangential_force_n_each": round(wheel_force, 6),
            "shock_factored_wheel_force_n_each": round(wheel_force * shock_factor, 6),
            "minimum_total_clamp_demand_n_per_cassette": round(clamp_force_total, 6),
            "minimum_clamp_demand_n_per_m6": round(clamp_force_each, 6),
            "wheel_shaft_shock_torsional_shear_demand_mpa": round(shaft_shock_torsional_shear_mpa, 6),
            "strength_pass_claimed": False,
        },
        "kinematic_calibration_gate": {
            "nominal_wheel_center_track_mm": round(nominal_wheel_center_track, 6),
            "analytic_shell_contact_patch_track_mm": round(analytic_contact_track, 6),
            "current_firmware_track_mm": round(firmware_track_mm, 6),
            "analytic_contact_minus_firmware_track_mm": round(track_delta, 6),
            "disposition": loads["track_disposition"],
            "automatic_firmware_change_allowed": False,
        },
        "checks": checks,
        "unresolved_freeze_gates": unresolved,
    }


def sweep_rows(contract: dict, result: dict) -> list[dict]:
    baseline = contract["geometry_baseline"]
    wheel = contract["selected_architecture"]["wheel"]
    slide = contract["selected_architecture"]["radial_slide"]
    shell_radius = float(baseline["sphere_inner_radius_mm"])
    wheel_radius = float(wheel["nominal_radius_mm"])
    half_width = float(wheel["axial_half_width_mm"])
    crown_drop = float(wheel["selected_crown_drop_at_edge_mm"])
    inner_radius = float(slide["inner_stop_wheel_center_radius_mm"])
    pitch = float(slide["jackscrew_pitch_mm_per_turn"])
    radial_x = abs(float(result["selected_contact_geometry"]["right_radial_unit"][0]))
    analytic_contact_track = float(result["kinematic_calibration_gate"]["analytic_shell_contact_patch_track_mm"])
    rows = []
    steps = int(round(float(slide["total_usable_travel_mm"]) * 2.0))
    for index in range(steps + 1):
        position = index * 0.5
        center_radius = inner_radius + position
        support, support_s = crowned_support_radius(center_radius, wheel_radius, half_width, crown_drop)
        interference = support - shell_radius
        if interference < -0.02:
            state = "FREE_CLEARANCE"
        elif abs(interference) <= 0.02:
            state = "NOMINAL_FIRST_CONTACT"
        else:
            state = "FORCE_CONTROL_REQUIRED_DO_NOT_SET_BY_TURNS_ALONE"
        rows.append({
            "position_from_inner_stop_mm": f"{position:.2f}",
            "jackscrew_turns_from_inner_stop": f"{position / pitch:.2f}",
            "wheel_center_radius_mm": f"{center_radius:.3f}",
            "free_crowned_support_mm": f"{support:.3f}",
            "signed_shell_interference_mm": f"{interference:.3f}",
            "support_axial_coordinate_mm": f"{support_s:.3f}",
            "wheel_center_track_mm": f"{2.0 * center_radius * radial_x:.3f}",
            "analytic_shell_contact_track_mm": f"{analytic_contact_track:.3f}",
            "setup_state": state,
        })
    return rows


def bom_rows() -> list[dict[str, str]]:
    return [
        {"item": "S21-001", "qty_robot": "4", "category": "machined plate", "description": "6 mm moving cassette side plate", "candidate_spec": "6061-T6/T651; reference DXF/STL", "status": "HOLD_MATERIAL_FIT_GDT"},
        {"item": "S21-002", "qty_robot": "4", "category": "machined plate", "description": "6 mm fixed radial-slider plate with 4 M6 slots per cassette", "candidate_spec": "6061-T6/T651; 18.6 x 6.6 mm reference slots", "status": "HOLD_MATERIAL_FIT_GDT"},
        {"item": "S21-003", "qty_robot": "2", "category": "wheel", "description": "96 x 26 mm crowned drive wheel", "candidate_spec": "0.75 mm axial crown drop; TPU or cast polyurethane", "status": "HOLD_DUROMETER_BOND_WEAR"},
        {"item": "S21-004", "qty_robot": "2", "category": "shaft", "description": "12 mm wheel shaft with retained hub", "candidate_spec": "material keyway and retention TBD", "status": "HOLD_SHAFT_HUB_FATIGUE"},
        {"item": "S21-005", "qty_robot": "4", "category": "bearing", "description": "sealed wheel-shaft bearing", "candidate_spec": "6001-2RS 12 x 28 x 8 mm candidate", "status": "HOLD_FIT_LIFE_SUPPLIER"},
        {"item": "S21-006", "qty_robot": "2", "category": "belt", "description": "HTD-style synchronous belt", "candidate_spec": "5M-280-15; 56 teeth", "status": "HOLD_RATING_TENSION_GUARD"},
        {"item": "S21-007", "qty_robot": "2", "category": "pulley", "description": "24T motor pulley", "candidate_spec": "5 mm pitch; 15 mm width; 8 mm motor bore", "status": "HOLD_VENDOR_BORE_RETENTION"},
        {"item": "S21-008", "qty_robot": "2", "category": "pulley", "description": "24T wheel pulley", "candidate_spec": "5 mm pitch; 15 mm width; 12 mm wheel bore", "status": "HOLD_VENDOR_BORE_RETENTION"},
        {"item": "S21-009", "qty_robot": "8", "category": "clamp", "description": "M6 cassette clamp bolt with washer and locking feature", "candidate_spec": "grade preload and locking TBD", "status": "HOLD_GRADE_PRELOAD_FRICTION"},
        {"item": "S21-010", "qty_robot": "2", "category": "adjuster", "description": "M6x1 preload jackscrew with jam nut", "candidate_spec": "hard stops required; 12 mm usable travel", "status": "HOLD_THREAD_SUPPORT_FORCE_CALIBRATION"},
        {"item": "S21-011", "qty_robot": "2", "category": "guard", "description": "belt and pinch-point guard", "candidate_spec": "remove only with power isolated", "status": "HOLD_FINAL_ENVELOPE"},
        {"item": "S21-012", "qty_robot": "2", "category": "measurement", "description": "temporary radial force-gauge fixture", "candidate_spec": "60-100 N setup band; 10 N left-right match", "status": "REQUIRED_BEFORE_CONTACT_FREEZE"},
    ]


def write_reports(result: dict, contract: dict, zh_path: Path, en_path: Path) -> None:
    correction = result["baseline_correction"]
    contact = result["selected_contact_geometry"]
    slide = result["radial_slide"]
    belt = result["parallel_belt_drive"]
    loads = result["load_demands"]
    calibration = result["kinematic_calibration_gate"]
    open_count = len(result["unresolved_freeze_gates"])
    zh = [
        "# BB-8 阶段 21：切向轮轴与预压滑台门", "",
        f"> **{result['overall']}**。精确几何和参考包装筛查通过，但未改动当前打开的 Blender 主模型，也没有制造或真机接触证据。", "",
        "## 纠正旧轮—壳接触结论", "",
        f"- 当前 96 × 26 mm 驱动轮是有限宽圆柱。旧审计用“轮心半径 + 48 mm”把它当成球，结果比真实包络高估 **{correction['minimum_legacy_support_overstatement_mm']:.3f} mm**。",
        f"- 逐轴精确圆柱支撑函数给出的最小轮—壳间隙是 **{correction['minimum_exact_shell_gap_mm']:.3f} mm**；旧 Stage-19 接触通过结论对驱动轮作废。",
        f"- 现有轮轴相对球壳切平面偏离 **{correction['minimum_axis_to_tangent_error_deg']:.3f}°**，会把接触推到轮缘并引入擦滑风险。", "",
        "## 选定结构：切向轮轴 + 平行轴同步带", "",
        "- 轮轴改为与球壳局部切平面平行；电机轴与轮轴平行，电机沿径向内移 80 mm，用 1:1 同步带传动，避免 125.2 mm 长电机直接沿切线撞壳。",
        f"- 24T / 24T、5 mm 节距、80 mm 轴距的闭式节线长度是 **{belt['calculated_belt_pitch_length_mm']:.1f} mm / {belt['belt_teeth']} 齿**；候选为 5M-280-15。额定能力、预紧和防护罩仍需供应商与实物验证。",
        f"- 电机包络最外支撑半径 {belt['motor_envelope_support_mm']:.2f} mm，名义球壳余量 {belt['motor_shell_clearance_mm']:.2f} mm；这只是解析包络，不是当前 Blender 车架的完整干涉检查。", "",
        "## 冠形轮与径向调节", "",
        f"- 26 mm 宽轮在 254 mm 内球面上至少需要 **{contact['minimum_crown_drop_mm']:.3f} mm** 边缘降高；参考轮采用 0.750 mm 抛物线冠高，轮缘解析余量 **{contact['edge_shell_clearance_mm']:.3f} mm**。",
        f"- 滑台总行程 **{slide['usable_travel_mm']:.1f} mm**：名义接触点距内限位 3 mm，向内保留 3 mm，向外保留 9 mm；覆盖阶段20的5.5 mm公差预算后仍余 **{slide['margin_beyond_tolerance_budget_mm']:.1f} mm**。",
        f"- M6×1 调节螺杆每圈 1 mm，四分之一圈 0.25 mm。圈数只用于找接触；最终必须用测力夹具把每侧预压调到 60–100 N、目标 80 N，左右差不超过 10 N，再锁紧 4 颗 M6。",
        "- 禁止把 9 mm 外向余量当成轮胎压缩量；一旦接触，后续只按力值调整。", "",
        "## 载荷与控制校准门", "",
        f"- 1.2 N·m 峰值对应每轮 {loads['peak_wheel_tangential_force_n_each']:.1f} N；3×冲击和2×防滑系数、摩擦系数0.15下，滑台最小总夹紧需求为 **{loads['minimum_total_clamp_demand_n_per_cassette']:.0f} N**，四颗M6平均 {loads['minimum_clamp_demand_n_per_m6']:.0f} N/颗。这里只给需求，不给螺栓强度或预紧通过结论。",
        f"- 12 mm 轮轴在3×扭矩下的理想圆轴扭转剪应力需求为 {loads['wheel_shaft_shock_torsional_shear_demand_mpa']:.2f} MPa；键槽、材料、疲劳和轮毂仍未冻结。",
        f"- 轮心距仍是 {calibration['nominal_wheel_center_track_mm']:.1f} mm，但球壳名义接触点横向间距是 **{calibration['analytic_shell_contact_patch_track_mm']:.1f} mm**，比固件当前 310 mm 参数大 {calibration['analytic_contact_minus_firmware_track_mm']:.1f} mm。球内多体转向不能靠这一个解析数直接改固件，必须用实车偏航响应重新辨识。", "",
        "## 自组装顺序", "",
        "1. 先用DXF加工样板并去毛刺，只做空载装配；确认两片侧板、6001轴承、12 mm轴和24T轮侧皮带轮同轴。",
        "2. 安装电机侧24T皮带轮与5M-280-15候选带，手转一周检查跑偏；没有防护罩时不得通电。",
        "3. 两侧滑台退到内限位，装入球壳后逐侧推进到首次接触；用测力夹具而不是圈数设置80 N目标。",
        "4. 锁紧四颗M6后复测预压与皮带跑偏，再做架空低速旋转、急停和温升测试。",
        "5. 最后用低速地面偏航数据重新辨识有效轮距；未经该步骤不得把解析接触距写入控制器。", "",
        f"开放冻结门：{open_count} 项；制造发布为否，19项整机物理调试仍未通过。", "",
        "机器合同、HOLD结果、0.5 mm调节扫描、BOM、OpenSCAD、DXF/STL和验证器均随项目保存。", "",
    ]
    en = [
        "# BB-8 Stage 21: Tangent Wheel and Preload Cassette Gate", "",
        f"> **{result['overall']}**. Exact geometry and reference packaging screens pass, but the open Blender master was not modified and no fabricated contact evidence exists.", "",
        "## Superseding the old wheel-contact result", "",
        f"- The current 96 × 26 mm powered wheel is a finite cylinder. The old centre-radius-plus-48 mm audit treated it as a sphere and overstates its support by **{correction['minimum_legacy_support_overstatement_mm']:.3f} mm**.",
        f"- The exact finite-cylinder support leaves at least **{correction['minimum_exact_shell_gap_mm']:.3f} mm** to the inner shell, so the historical powered-wheel contact pass is superseded.",
        f"- The current axle misses the local shell tangent plane by **{correction['minimum_axis_to_tangent_error_deg']:.3f}°**, driving contact toward the edge and creating scrub risk.", "",
        "## Selected architecture: tangent axle plus parallel synchronous belt", "",
        "- The wheel axle is tangent to the local shell. The parallel motor axis moves 80 mm radially inward and drives 1:1 by belt, avoiding direct tangent packaging of the 125.2 mm motor envelope.",
        f"- Equal 24T, 5 mm-pitch pulleys at 80 mm centre distance calculate to **{belt['calculated_belt_pitch_length_mm']:.1f} mm / {belt['belt_teeth']} teeth**, represented by a 5M-280-15 candidate. Supplier capacity, pretension and guarding remain open.",
        f"- The motor envelope support is {belt['motor_envelope_support_mm']:.2f} mm, leaving {belt['motor_shell_clearance_mm']:.2f} mm nominal shell clearance. This is an envelope screen, not a current-chassis clash pass.", "",
        "## Crown and radial setting", "",
        f"- A 26 mm-wide wheel needs at least **{contact['minimum_crown_drop_mm']:.3f} mm** edge drop in the 254 mm inner sphere. The reference uses a 0.750 mm parabolic crown and leaves **{contact['edge_shell_clearance_mm']:.3f} mm** analytical edge clearance.",
        f"- Total travel is **{slide['usable_travel_mm']:.1f} mm**: 3 mm inward and 9 mm outward from nominal contact. That covers the 5.5 mm Stage-20 stack with **{slide['margin_beyond_tolerance_budget_mm']:.1f} mm** reserve.",
        "- The M6×1 screw gives 1 mm per turn and 0.25 mm per quarter-turn. Turns only find contact; a force fixture must set 60–100 N per side, target 80 N, with no more than 10 N left-right mismatch before four M6 clamps are locked.",
        "- The 9 mm outward reserve is not allowable tire compression. After contact, adjust by measured force only.", "",
        "## Load and control gates", "",
        f"- 1.2 N·m gives {loads['peak_wheel_tangential_force_n_each']:.1f} N at each wheel. With 3× shock, 2× slip factor and μ=0.15, the minimum clamp demand is **{loads['minimum_total_clamp_demand_n_per_cassette']:.0f} N** total or {loads['minimum_clamp_demand_n_per_m6']:.0f} N per M6. This is demand only, not a bolt/preload pass.",
        f"- Ideal 12 mm shaft torsional shear demand is {loads['wheel_shaft_shock_torsional_shear_demand_mpa']:.2f} MPa at 3× torque; keyway, material, hub and fatigue remain open.",
        f"- Wheel-centre track remains {calibration['nominal_wheel_center_track_mm']:.1f} mm, while nominal shell contact-patch spacing is **{calibration['analytic_shell_contact_patch_track_mm']:.1f} mm**, {calibration['analytic_contact_minus_firmware_track_mm']:.1f} mm above the firmware's current 310 mm parameter. Do not copy the analytical value into firmware; identify effective track from physical yaw response.", "",
        "## Assembly sequence", "",
        "1. Machine deburred fit-test plates from the reference DXF; dry-fit side plates, 6001 bearings, 12 mm shaft and wheel pulley.",
        "2. Fit the motor pulley and candidate 5M-280-15 belt, then hand-turn one revolution to inspect tracking. Never power it without the guard.",
        "3. Retract both slides to the inner stops, install in the shell, advance to first contact and use a force fixture—not turns—to set the 80 N target.",
        "4. Lock four M6 clamps, remeasure preload and belt tracking, then run raised-wheel low-speed, E-stop and thermal tests.",
        "5. Identify effective track from low-speed physical yaw data before changing the controller.", "",
        f"Open freeze gates: {open_count}. Manufacturing release is false and all nineteen physical commissioning gates remain incomplete.", "",
        "The machine contract, HOLD result, 0.5 mm adjustment sweep, BOM, OpenSCAD, DXF/STL and verifier are stored with the project.", "",
    ]
    zh_path.write_text("\n".join(zh), encoding="utf-8")
    en_path.write_text("\n".join(en), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--sweep", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--bom", type=Path, default=DEFAULT_BOM)
    parser.add_argument("--report-zh", type=Path, default=DEFAULT_REPORT_ZH)
    parser.add_argument("--report-en", type=Path, default=DEFAULT_REPORT_EN)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    rows, by_name = read_manifest(args.manifest)
    result = verify(contract, rows, by_name)
    args.results.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sweep = sweep_rows(contract, result)
    with args.sweep.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sweep[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sweep)

    bom = bom_rows()
    with args.bom.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=bom[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(bom)

    write_reports(result, contract, args.report_zh, args.report_en)
    print(
        f"{result['overall']} analytical={result['analytical_screen_passed']} "
        f"gap={result['baseline_correction']['minimum_exact_shell_gap_mm']:.3f}mm "
        f"axis_error={result['baseline_correction']['minimum_axis_to_tangent_error_deg']:.3f}deg "
        f"crown={result['selected_contact_geometry']['selected_crown_drop_mm']:.3f}mm "
        f"travel_margin={result['radial_slide']['margin_beyond_tolerance_budget_mm']:.3f}mm "
        f"unresolved={len(result['unresolved_freeze_gates'])}"
    )
    print("RESULTS", args.results)
    print("SWEEP", args.sweep)
    print("BOM", args.bom)
    if args.expect_overall and result["overall"] != args.expect_overall:
        raise SystemExit(f"expected {args.expect_overall}, got {result['overall']}")
    if result["overall"].startswith("FAIL_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
