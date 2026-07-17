#!/usr/bin/env python3
"""Verify the Stage-22 catalog belt, bearing, shaft, key and rail-interface gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "engineering" / "stage22_drivetrain_interface_contract.json"
DEFAULT_STAGE21_CONTRACT = ROOT / "engineering" / "stage21_wheel_preload_contract.json"
DEFAULT_STAGE21_RESULTS = ROOT / "engineering" / "stage21_wheel_preload_results.json"
DEFAULT_RESULTS = ROOT / "engineering" / "stage22_drivetrain_interface_results.json"
DEFAULT_LOAD_CASES = ROOT / "engineering" / "stage22_drivetrain_load_cases.csv"
DEFAULT_BOM = ROOT / "engineering" / "stage22_drivetrain_interface_bom.csv"
DEFAULT_REPORT_ZH = ROOT / "docs" / "BB8_阶段22_标准同步带与轮轴底盘接口门.md"
DEFAULT_REPORT_EN = ROOT / "docs" / "BB8_stage22_catalog_belt_bearing_shaft_interface_gate.md"


def verify(contract: dict, stage21_contract: dict, stage21_results: dict) -> dict:
    checks: list[dict] = []

    def check(identifier: str, passed: bool, actual, requirement) -> None:
        checks.append(
            {
                "id": identifier,
                "passed": bool(passed),
                "actual": actual,
                "requirement": requirement,
            }
        )

    inputs = contract["stage21_inputs"]
    sources = {item["id"]: item for item in contract["official_source_evidence"]}
    architecture = contract["selected_architecture"]
    belt = architecture["belt_drive"]
    bearings = architecture["bearing_stack"]
    shaft = architecture["shaft_and_hubs"]
    interface = architecture["rail_interface"]
    packaging = architecture["packaging"]
    loads = contract["load_inputs"]
    thresholds = contract["acceptance_thresholds"]

    check("stage", contract.get("stage") == 22, contract.get("stage"), 22)
    check(
        "stage21_overall_bound",
        stage21_results.get("overall") == inputs["required_stage21_overall"],
        stage21_results.get("overall"),
        inputs["required_stage21_overall"],
    )
    check(
        "stage21_architecture_bound",
        stage21_contract["selected_architecture"]["id"] == inputs["required_architecture"],
        stage21_contract["selected_architecture"]["id"],
        inputs["required_architecture"],
    )
    check(
        "blender_master_preservation_policy",
        inputs["active_master_policy"] == "USER_MODIFIED_MASTER_PRESERVED_NOT_SAVED_BY_STAGE22",
        inputs["active_master_policy"],
        "USER_MODIFIED_MASTER_PRESERVED_NOT_SAVED_BY_STAGE22",
    )

    gates_belt = sources["GATES_5MGT_300_15"]["facts_used"]
    gates_catalog = sources["GATES_2025_INDUSTRIAL_CATALOG"]["facts_used"]
    gates_manual = sources["GATES_POWERGRIP_GT3_MANUAL"]["facts_used"]
    gates_maintenance = sources["GATES_PREVENTIVE_MAINTENANCE"]["facts_used"]
    skf = sources["SKF_STAINLESS_DGBB_CATALOG"]["facts_used"]

    stock_lengths = [float(value) for value in gates_catalog["5mgt_15mm_stock_pitch_lengths_mm"]]
    historical_length = float(inputs["historical_candidate_pitch_length_mm"])
    selected_length = float(belt["pitch_length_mm"])
    historical_is_stock = historical_length in stock_lengths
    selected_is_stock = selected_length in stock_lengths
    check(
        "stage21_280mm_candidate_not_in_official_stock_list",
        not historical_is_stock and historical_length < float(gates_catalog["minimum_catalog_pitch_length_mm"]),
        {"historical_mm": historical_length, "stock_lengths_mm": stock_lengths},
        "historical length absent and below 300 mm catalog minimum",
    )
    check(
        "selected_belt_is_official_catalog_part",
        selected_is_stock
        and belt["selected_belt_part"] == gates_belt["part_number"]
        and belt["selected_product_number"] == gates_belt["product_number"]
        and selected_length == float(gates_belt["pitch_length_mm"])
        and int(belt["teeth"]) == int(gates_belt["teeth"])
        and float(belt["width_mm"]) == float(gates_belt["width_mm"]),
        {
            "part": belt["selected_belt_part"],
            "product": belt["selected_product_number"],
            "length_mm": selected_length,
            "teeth": belt["teeth"],
            "width_mm": belt["width_mm"],
        },
        gates_belt,
    )

    pitch_mm = float(belt["pitch_mm"])
    motor_teeth = int(belt["pulley_teeth_motor"])
    wheel_teeth = int(belt["pulley_teeth_wheel"])
    pulley_pitch_diameter_mm = motor_teeth * pitch_mm / math.pi
    center_distance_mm = float(belt["nominal_axis_center_distance_mm"])
    calculated_length_mm = 2.0 * center_distance_mm + math.pi * pulley_pitch_diameter_mm
    belt_length_error_mm = abs(calculated_length_mm - selected_length)
    ratio = wheel_teeth / motor_teeth
    calculated_teeth = calculated_length_mm / pitch_mm
    check(
        "equal_pulley_catalog_belt_geometry",
        belt_length_error_mm <= float(thresholds["maximum_belt_pitch_length_error_mm"]),
        round(calculated_length_mm, 6),
        selected_length,
    )
    check(
        "catalog_belt_tooth_count_integer",
        abs(calculated_teeth - int(belt["teeth"])) <= 1e-9,
        calculated_teeth,
        int(belt["teeth"]),
    )
    check("belt_ratio_one_to_one", abs(ratio - float(belt["ratio"])) <= 1e-9, ratio, belt["ratio"])
    check(
        "pulley_teeth_meet_gates_minimum",
        motor_teeth >= int(gates_manual["minimum_recommended_5mgt_pulley_teeth"])
        and wheel_teeth >= int(gates_manual["minimum_recommended_5mgt_pulley_teeth"])
        and motor_teeth == int(gates_manual["candidate_pulley_teeth"]),
        {"motor": motor_teeth, "wheel": wheel_teeth},
        f">={gates_manual['minimum_recommended_5mgt_pulley_teeth']} teeth",
    )
    tension_adjustment_mm = float(belt["motor_mount_tension_adjustment_total_mm"])
    check(
        "motor_mount_has_tensioning_allowance",
        tension_adjustment_mm >= float(thresholds["minimum_motor_tension_adjustment_total_mm"])
        and tension_adjustment_mm >= float(gates_maintenance["5mgt_up_to_500mm_minimum_tensioning_allowance_mm"]),
        tension_adjustment_mm,
        f">={max(float(thresholds['minimum_motor_tension_adjustment_total_mm']), float(gates_maintenance['5mgt_up_to_500mm_minimum_tensioning_allowance_mm']))} mm",
    )
    check(
        "flanged_belt_installation_is_serviceable",
        bool(belt["removable_outboard_pulley_required"])
        and belt["belt_installation_method"].startswith("REMOVE_OUTBOARD_PULLEY"),
        belt["belt_installation_method"],
        "remove pulley instead of forcing belt over two flanges",
    )

    check(
        "bearing_reference_dimensions_match",
        float(bearings["bore_mm"]) == float(skf["bore_mm"])
        and float(bearings["outside_diameter_mm"]) == float(skf["outside_diameter_mm"])
        and float(bearings["width_mm"]) == float(skf["width_mm"]),
        [bearings["bore_mm"], bearings["outside_diameter_mm"], bearings["width_mm"]],
        [skf["bore_mm"], skf["outside_diameter_mm"], skf["width_mm"]],
    )
    check(
        "bearing_rating_floor_matches_official_reference",
        float(bearings["minimum_dynamic_rating_n"]) >= float(skf["dynamic_rating_n"])
        and float(bearings["minimum_static_rating_n"]) >= float(skf["static_rating_n"]),
        [bearings["minimum_dynamic_rating_n"], bearings["minimum_static_rating_n"]],
        [skf["dynamic_rating_n"], skf["static_rating_n"]],
    )

    peak_torque_nm = float(loads["motor_peak_torque_nm_each"])
    shock_factor = float(loads["mechanical_shock_factor"])
    shock_torque_nm = peak_torque_nm * shock_factor
    pulley_pitch_radius_m = pulley_pitch_diameter_mm / 2000.0
    peak_belt_tension_difference_n = peak_torque_nm / pulley_pitch_radius_m
    shock_belt_tension_difference_n = shock_torque_nm / pulley_pitch_radius_m
    pretension_n = float(loads["maximum_assumed_belt_pretension_n_per_span"])
    belt_radial_load_envelope_n = 2.0 * pretension_n + shock_belt_tension_difference_n

    span_m = float(bearings["bearing_center_span_mm"]) / 1000.0
    overhang_m = float(bearings["pulley_overhang_from_outboard_bearing_mm"]) / 1000.0
    outboard_belt_reaction_n = belt_radial_load_envelope_n * (span_m + overhang_m) / span_m
    inboard_belt_reaction_n = belt_radial_load_envelope_n - outboard_belt_reaction_n
    wheel_normal_n = float(loads["maximum_wheel_normal_preload_n"])
    shock_wheel_tangential_n = shock_torque_nm / float(loads["wheel_radius_m"])
    outboard_radial_n = outboard_belt_reaction_n + wheel_normal_n / 2.0
    inboard_radial_n = inboard_belt_reaction_n + wheel_normal_n / 2.0
    outboard_bearing_load_n = math.hypot(outboard_radial_n, shock_wheel_tangential_n / 2.0)
    inboard_bearing_load_n = math.hypot(inboard_radial_n, shock_wheel_tangential_n / 2.0)
    worst_bearing_load_n = max(outboard_bearing_load_n, inboard_bearing_load_n)
    bearing_static_sf = float(bearings["minimum_static_rating_n"]) / worst_bearing_load_n
    l10_revolutions = (
        float(bearings["minimum_dynamic_rating_n"]) / worst_bearing_load_n
    ) ** float(loads["bearing_life_exponent"]) * 1_000_000.0
    analysis_speed_rpm = float(bearings["analysis_speed_rpm"])
    l10_hours = l10_revolutions / (60.0 * analysis_speed_rpm)
    speed_margin = float(bearings["reference_limiting_speed_rpm"]) / analysis_speed_rpm
    check(
        "bearing_static_safety",
        bearing_static_sf >= float(thresholds["minimum_bearing_static_safety_factor"]),
        round(bearing_static_sf, 6),
        f">={thresholds['minimum_bearing_static_safety_factor']}",
    )
    check(
        "bearing_l10_reference_life",
        l10_hours >= float(thresholds["minimum_bearing_l10_hours_at_analysis_speed"]),
        round(l10_hours, 3),
        f">={thresholds['minimum_bearing_l10_hours_at_analysis_speed']} h",
    )
    check(
        "bearing_speed_margin",
        speed_margin >= float(thresholds["minimum_bearing_speed_margin_factor"]),
        round(speed_margin, 6),
        f">={thresholds['minimum_bearing_speed_margin_factor']}",
    )

    shaft_diameter_m = float(shaft["shaft_diameter_mm"]) / 1000.0
    radial_bending_moment_nm = (
        belt_radial_load_envelope_n * overhang_m + wheel_normal_n * span_m / 4.0
    )
    tangential_bending_moment_nm = shock_wheel_tangential_n * span_m / 4.0
    combined_bending_moment_nm = math.hypot(radial_bending_moment_nm, tangential_bending_moment_nm)
    shaft_bending_stress_mpa = (
        32.0 * combined_bending_moment_nm / (math.pi * shaft_diameter_m**3) / 1e6
    )
    shaft_torsional_shear_mpa = (
        16.0 * shock_torque_nm / (math.pi * shaft_diameter_m**3) / 1e6
    )
    ideal_von_mises_mpa = math.sqrt(
        shaft_bending_stress_mpa**2 + 3.0 * shaft_torsional_shear_mpa**2
    )
    keyed_von_mises_mpa = ideal_von_mises_mpa * float(shaft["keyway_combined_stress_factor"])
    shaft_yield_sf = float(shaft["minimum_certified_shaft_yield_mpa"]) / keyed_von_mises_mpa
    shaft_second_moment_m4 = math.pi * shaft_diameter_m**4 / 64.0
    shaft_modulus_pa = float(shaft["shaft_modulus_gpa"]) * 1e9
    stiffness_retention = float(shaft["keyway_stiffness_retention"])
    pulley_deflection_m = (
        belt_radial_load_envelope_n
        * overhang_m**2
        * (span_m + overhang_m)
        / (3.0 * shaft_modulus_pa * shaft_second_moment_m4 * stiffness_retention)
    )
    wheel_deflection_m = (
        wheel_normal_n
        * span_m**3
        / (48.0 * shaft_modulus_pa * shaft_second_moment_m4 * stiffness_retention)
    )
    shaft_deflection_mm = (pulley_deflection_m + wheel_deflection_m) * 1000.0
    check(
        "keyway_factored_shaft_yield_safety",
        shaft_yield_sf >= float(thresholds["minimum_shaft_yield_safety_factor"]),
        round(shaft_yield_sf, 6),
        f">={thresholds['minimum_shaft_yield_safety_factor']}",
    )
    check(
        "shaft_deflection",
        shaft_deflection_mm <= float(thresholds["maximum_keyway_shaft_deflection_mm"]),
        round(shaft_deflection_mm, 6),
        f"<={thresholds['maximum_keyway_shaft_deflection_mm']} mm",
    )

    key_width_m = float(shaft["key_width_mm"]) / 1000.0
    key_height_m = float(shaft["key_height_mm"]) / 1000.0
    key_length_m = float(shaft["minimum_key_engagement_mm"]) / 1000.0
    key_shear_mpa = (
        2.0 * shock_torque_nm / (shaft_diameter_m * key_width_m * key_length_m) / 1e6
    )
    key_bearing_mpa = (
        4.0 * shock_torque_nm / (shaft_diameter_m * key_height_m * key_length_m) / 1e6
    )
    check(
        "parallel_key_shear",
        key_shear_mpa <= float(thresholds["maximum_key_shear_stress_mpa"]),
        round(key_shear_mpa, 6),
        f"<={thresholds['maximum_key_shear_stress_mpa']} MPa",
    )
    check(
        "parallel_key_bearing",
        key_bearing_mpa <= float(thresholds["maximum_key_bearing_stress_mpa"]),
        round(key_bearing_mpa, 6),
        f"<={thresholds['maximum_key_bearing_stress_mpa']} MPa",
    )

    interface_load_n = float(interface["interface_design_load_n_per_cassette"])
    dowel_count = int(interface["dowel_pins_per_cassette"])
    dowel_diameter_m = float(interface["dowel_diameter_mm"]) / 1000.0
    plate_thickness_m = float(interface["fixed_plate_thickness_mm"]) / 1000.0
    edge_distance_m = float(interface["minimum_dowel_edge_distance_mm"]) / 1000.0
    load_per_dowel_n = interface_load_n / dowel_count
    dowel_area_m2 = math.pi * dowel_diameter_m**2 / 4.0
    dowel_shear_mpa = load_per_dowel_n / dowel_area_m2 / 1e6
    plate_bearing_mpa = load_per_dowel_n / (plate_thickness_m * dowel_diameter_m) / 1e6
    tearout_area_m2 = (
        2.0 * (edge_distance_m - dowel_diameter_m / 2.0) * plate_thickness_m
    )
    plate_tearout_mpa = (
        math.inf
        if tearout_area_m2 <= 0.0
        else load_per_dowel_n / tearout_area_m2 / 1e6
    )
    check(
        "dowel_single_shear",
        dowel_shear_mpa <= float(thresholds["maximum_dowel_shear_stress_mpa"]),
        round(dowel_shear_mpa, 6),
        f"<={thresholds['maximum_dowel_shear_stress_mpa']} MPa",
    )
    check(
        "plate_dowel_bearing",
        plate_bearing_mpa <= float(thresholds["maximum_plate_bearing_stress_mpa"]),
        round(plate_bearing_mpa, 6),
        f"<={thresholds['maximum_plate_bearing_stress_mpa']} MPa",
    )
    check(
        "plate_dowel_tearout",
        plate_tearout_mpa <= float(thresholds["maximum_plate_tearout_stress_mpa"])
        and edge_distance_m > dowel_diameter_m / 2.0,
        round(plate_tearout_mpa, 6),
        f"<={thresholds['maximum_plate_tearout_stress_mpa']} MPa",
    )
    check(
        "interface_has_positive_load_path",
        bool(interface["hard_stop_reacts_jackscrew_load"])
        and not bool(interface["friction_credit_in_strength_screen"])
        and dowel_count >= 2,
        {
            "hard_stop": interface["hard_stop_reacts_jackscrew_load"],
            "friction_credit": interface["friction_credit_in_strength_screen"],
            "dowels": dowel_count,
        },
        "hard stop + >=2 dowels, no friction credit",
    )

    shell_radius_mm = float(packaging["sphere_inner_radius_mm"])
    wheel_center_radius_mm = float(packaging["nominal_wheel_center_radius_mm"])
    motor_center_radius_mm = wheel_center_radius_mm - center_distance_mm
    motor_support_mm = math.hypot(
        float(packaging["motor_envelope_length_mm"]) / 2.0,
        motor_center_radius_mm + float(packaging["motor_envelope_diameter_mm"]) / 2.0,
    )
    motor_clearance_mm = shell_radius_mm - motor_support_mm
    plate_base_radius_mm = (
        wheel_center_radius_mm - float(packaging["wheel_axis_local_x_mm"])
    )
    plate_outer_radius_mm = (
        plate_base_radius_mm
        + float(packaging["reference_plate_length_mm"])
        + float(packaging["stage21_outward_reserve_mm"])
    )
    plate_support_mm = math.sqrt(
        plate_outer_radius_mm**2
        + (float(packaging["reference_plate_width_mm"]) / 2.0) ** 2
        + (
            float(packaging["fixed_plate_center_separation_mm"]) / 2.0
            + float(packaging["reference_plate_thickness_mm"]) / 2.0
        )
        ** 2
    )
    plate_clearance_mm = shell_radius_mm - plate_support_mm
    guarded_pulley_support_mm = math.hypot(
        wheel_center_radius_mm
        + float(packaging["pulley_envelope_radius_mm"])
        + float(packaging["guard_radial_allowance_mm"]),
        float(packaging["pulley_center_from_wheel_midplane_mm"])
        + float(packaging["pulley_width_mm"]) / 2.0
        + float(packaging["guard_radial_allowance_mm"]),
    )
    guarded_pulley_clearance_mm = shell_radius_mm - guarded_pulley_support_mm
    check(
        "motor_shell_clearance",
        motor_clearance_mm >= float(thresholds["minimum_motor_shell_clearance_mm"]),
        round(motor_clearance_mm, 6),
        f">={thresholds['minimum_motor_shell_clearance_mm']} mm",
    )
    check(
        "plate_shell_clearance",
        plate_clearance_mm >= float(thresholds["minimum_plate_shell_clearance_mm"]),
        round(plate_clearance_mm, 6),
        f">={thresholds['minimum_plate_shell_clearance_mm']} mm",
    )
    check(
        "guarded_pulley_shell_clearance",
        guarded_pulley_clearance_mm
        >= float(thresholds["minimum_guarded_pulley_shell_clearance_mm"]),
        round(guarded_pulley_clearance_mm, 6),
        f">={thresholds['minimum_guarded_pulley_shell_clearance_mm']} mm",
    )

    unresolved = sorted(
        key for key, value in contract["freeze_gates"].items() if value is not True
    )
    analytical_pass = all(item["passed"] for item in checks)
    if not analytical_pass:
        overall = "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN"
    elif unresolved:
        overall = "HOLD_SUPPLIER_FITS_TENSION_TORQUE_PROOF_AND_PHYSICAL_INTEGRATION_REQUIRED"
    else:
        overall = "READY_FOR_INDEPENDENT_DESIGN_REVIEW_NOT_FABRICATION"

    return {
        "stage": 22,
        "overall": overall,
        "analytical_screen_passed": analytical_pass,
        "manufacturing_release": False,
        "physical_test_status": "NOT_RUN",
        "blender_application_status": inputs["blender_application_status"],
        "catalog_correction": {
            "stage21_candidate": inputs["historical_candidate_belt"],
            "stage21_candidate_in_official_stock_list": historical_is_stock,
            "official_15mm_stock_pitch_lengths_mm": stock_lengths,
            "selected_part": belt["selected_belt_part"],
            "selected_product_number": belt["selected_product_number"],
            "selected_pitch_length_mm": selected_length,
            "selected_teeth": int(belt["teeth"]),
            "selected_width_mm": float(belt["width_mm"]),
            "source_ids": [
                "GATES_5MGT_300_15",
                "GATES_2025_INDUSTRIAL_CATALOG",
                "GATES_POWERGRIP_GT3_MANUAL",
                "GATES_PREVENTIVE_MAINTENANCE",
            ],
        },
        "belt_geometry": {
            "pulley_pitch_diameter_mm": round(pulley_pitch_diameter_mm, 6),
            "nominal_center_distance_mm": round(center_distance_mm, 6),
            "calculated_pitch_length_mm": round(calculated_length_mm, 6),
            "pitch_length_error_mm": round(belt_length_error_mm, 9),
            "calculated_teeth": round(calculated_teeth, 6),
            "ratio": round(ratio, 6),
            "minimum_recommended_pulley_teeth": int(
                gates_manual["minimum_recommended_5mgt_pulley_teeth"]
            ),
            "motor_tension_adjustment_total_mm": tension_adjustment_mm,
            "installation_method": belt["belt_installation_method"],
            "supplier_power_rating_passed": False,
            "installation_tension_passed": False,
        },
        "load_path": {
            "peak_torque_nm": round(peak_torque_nm, 6),
            "shock_torque_nm": round(shock_torque_nm, 6),
            "peak_belt_tension_difference_n": round(peak_belt_tension_difference_n, 6),
            "shock_belt_tension_difference_n": round(shock_belt_tension_difference_n, 6),
            "assumed_pretension_n_per_span": round(pretension_n, 6),
            "belt_radial_load_envelope_n": round(belt_radial_load_envelope_n, 6),
            "shock_wheel_tangential_force_n": round(shock_wheel_tangential_n, 6),
            "maximum_wheel_normal_preload_n": round(wheel_normal_n, 6),
            "outboard_belt_reaction_n": round(outboard_belt_reaction_n, 6),
            "inboard_belt_reaction_n": round(inboard_belt_reaction_n, 6),
        },
        "bearing_screen": {
            "rating_floor_source": "SKF_STAINLESS_DGBB_CATALOG",
            "worst_outboard_equivalent_radial_load_n": round(outboard_bearing_load_n, 6),
            "inboard_equivalent_radial_load_n": round(inboard_bearing_load_n, 6),
            "static_safety_factor": round(bearing_static_sf, 6),
            "l10_revolutions": round(l10_revolutions, 3),
            "l10_hours_at_analysis_speed": round(l10_hours, 3),
            "analysis_speed_rpm": round(analysis_speed_rpm, 3),
            "speed_margin_factor": round(speed_margin, 6),
            "fit_clearance_retention_life_physically_proven": False,
        },
        "shaft_key_screen": {
            "combined_bending_moment_nm": round(combined_bending_moment_nm, 6),
            "bending_stress_mpa": round(shaft_bending_stress_mpa, 6),
            "torsional_shear_mpa": round(shaft_torsional_shear_mpa, 6),
            "ideal_von_mises_mpa": round(ideal_von_mises_mpa, 6),
            "keyway_factored_von_mises_mpa": round(keyed_von_mises_mpa, 6),
            "minimum_certified_yield_mpa": float(
                shaft["minimum_certified_shaft_yield_mpa"]
            ),
            "yield_safety_factor": round(shaft_yield_sf, 6),
            "conservative_shaft_deflection_mm": round(shaft_deflection_mm, 6),
            "key_shear_stress_mpa": round(key_shear_mpa, 6),
            "key_bearing_stress_mpa": round(key_bearing_mpa, 6),
            "physical_torque_proof_nm": float(shaft["physical_torque_proof_nm"]),
            "physical_torque_proof_passed": False,
        },
        "rail_interface_screen": {
            "design_load_n_per_cassette": round(interface_load_n, 6),
            "load_per_dowel_n": round(load_per_dowel_n, 6),
            "dowel_single_shear_mpa": round(dowel_shear_mpa, 6),
            "plate_bearing_mpa": round(plate_bearing_mpa, 6),
            "plate_tearout_mpa": round(plate_tearout_mpa, 6),
            "friction_credit_used": bool(interface["friction_credit_in_strength_screen"]),
            "hard_stop_required": bool(interface["hard_stop_reacts_jackscrew_load"]),
            "physical_fit_and_gdt_passed": False,
        },
        "packaging_screen": {
            "motor_center_radius_mm": round(motor_center_radius_mm, 6),
            "motor_support_mm": round(motor_support_mm, 6),
            "motor_shell_clearance_mm": round(motor_clearance_mm, 6),
            "plate_support_mm": round(plate_support_mm, 6),
            "plate_shell_clearance_mm": round(plate_clearance_mm, 6),
            "guarded_pulley_support_mm": round(guarded_pulley_support_mm, 6),
            "guarded_pulley_shell_clearance_mm": round(
                guarded_pulley_clearance_mm, 6
            ),
            "current_blender_master_clash_check": "NOT_RUN",
        },
        "control_gate": {
            "current_firmware_track_m": float(loads["firmware_current_drive_track_m"]),
            "automatic_firmware_change_allowed": bool(
                loads["automatic_firmware_change_allowed"]
            ),
            "disposition": "HOLD_PHYSICAL_YAW_IDENTIFICATION_AFTER_CASSETTE_INSTALLATION",
        },
        "checks": checks,
        "unresolved_freeze_gates": unresolved,
    }


def load_case_rows(result: dict) -> list[dict[str, str]]:
    load = result["load_path"]
    bearing = result["bearing_screen"]
    shaft = result["shaft_key_screen"]
    interface = result["rail_interface_screen"]
    return [
        {
            "case": "nominal_peak_torque",
            "torque_nm": f"{load['peak_torque_nm']:.3f}",
            "belt_tension_difference_n": f"{load['peak_belt_tension_difference_n']:.3f}",
            "radial_load_envelope_n": "",
            "worst_bearing_load_n": "",
            "shaft_keyway_vm_mpa": "",
            "disposition": "DEMAND_ONLY_SUPPLIER_RATING_OPEN",
        },
        {
            "case": "3x_shock_plus_80n_per_span_pretension",
            "torque_nm": f"{load['shock_torque_nm']:.3f}",
            "belt_tension_difference_n": f"{load['shock_belt_tension_difference_n']:.3f}",
            "radial_load_envelope_n": f"{load['belt_radial_load_envelope_n']:.3f}",
            "worst_bearing_load_n": f"{bearing['worst_outboard_equivalent_radial_load_n']:.3f}",
            "shaft_keyway_vm_mpa": f"{shaft['keyway_factored_von_mises_mpa']:.3f}",
            "disposition": "ANALYTICAL_SCREEN_PASS_PHYSICAL_PROOF_OPEN",
        },
        {
            "case": "rail_interface_positive_load_path",
            "torque_nm": "",
            "belt_tension_difference_n": "",
            "radial_load_envelope_n": f"{interface['design_load_n_per_cassette']:.3f}",
            "worst_bearing_load_n": "",
            "shaft_keyway_vm_mpa": "",
            "disposition": "TWO_DOWELS_PLUS_HARD_STOP_NO_FRICTION_CREDIT",
        },
    ]


def bom_rows() -> list[dict[str, str]]:
    return [
        {"item": "S22-001", "qty_robot": "2", "category": "belt", "description": "Gates Poly Chain GT Carbon belt", "candidate_spec": "5MGT-300-15, product 92706002, 300 mm, 60T, 15 mm", "status": "CATALOG_IDENTIFIED_HOLD_POWER_RATING_TENSION"},
        {"item": "S22-002", "qty_robot": "2", "category": "motor pulley", "description": "24T 5MGT 15 mm pulley", "candidate_spec": "P24-5MGT-15-MPB family, finish-bore to verified 8 mm motor shaft", "status": "HOLD_BORE_KEY_OR_CLAMP_RETENTION"},
        {"item": "S22-003", "qty_robot": "2", "category": "wheel pulley", "description": "24T 5MGT 15 mm removable pulley", "candidate_spec": "P24-5MGT-15-MPB family, 12 mm keyed bore", "status": "HOLD_BORE_KEY_AXIAL_RETENTION"},
        {"item": "S22-004", "qty_robot": "4", "category": "bearing", "description": "sealed 6001 wheel-shaft bearing", "candidate_spec": "12x28x8 mm; C>=4.42 kN, C0>=2.36 kN", "status": "HOLD_SUPPLIER_CLEARANCE_SEAL_FITS"},
        {"item": "S22-005", "qty_robot": "2", "category": "shaft", "description": "12 mm keyed wheel shaft", "candidate_spec": "certified yield >=400 MPa; keyway factored screen", "status": "HOLD_MATERIAL_CERT_DRAWING_FATIGUE"},
        {"item": "S22-006", "qty_robot": "4", "category": "key", "description": "wheel and pulley parallel keys", "candidate_spec": "DIN 6885 candidate 4x4x20 mm minimum engagement", "status": "HOLD_FIT_AND_7P2NM_TORQUE_PROOF"},
        {"item": "S22-007", "qty_robot": "2", "category": "wheel hub", "description": "keyed wheel hub with positive axial retention", "candidate_spec": "20 mm minimum keyed engagement", "status": "HOLD_HUB_DRAWING_AND_TORQUE_PROOF"},
        {"item": "S22-008", "qty_robot": "2", "category": "bearing retainer", "description": "outboard bolted bearing retainer", "candidate_spec": "reference DXF; shoulder and fasteners TBD", "status": "HOLD_FIT_GDT_ENDPLAY"},
        {"item": "S22-009", "qty_robot": "2", "category": "floating housing", "description": "inboard floating-bearing housing", "candidate_spec": ">=0.3 mm axial float, anti-creep validation", "status": "HOLD_PHYSICAL_ENDPLAY_ANTICREEP"},
        {"item": "S22-010", "qty_robot": "4", "category": "dowel", "description": "rail-interface locating dowel", "candidate_spec": "6 mm, two per cassette, reamed fit", "status": "HOLD_MATERIAL_REAM_GDT"},
        {"item": "S22-011", "qty_robot": "8", "category": "clamp", "description": "rail-interface M6 clamp bolt", "candidate_spec": "four per cassette; not credited for shear strength", "status": "HOLD_GRADE_PRELOAD_LOCKING"},
        {"item": "S22-012", "qty_robot": "2", "category": "hard stop", "description": "positive cassette radial hard stop", "candidate_spec": "reacts jackscrew and shock load into rail bridge", "status": "HOLD_RAIL_INTEGRATION"},
        {"item": "S22-013", "qty_robot": "2", "category": "guard", "description": "removable belt and pulley guard", "candidate_spec": "3 mm reference envelope; power-isolated service only", "status": "HOLD_MATERIAL_FASTENERS_ACCESS"},
        {"item": "S22-014", "qty_robot": "2", "category": "test", "description": "keyed-joint torque-proof fixture", "candidate_spec": "7.2 N m proof without slip or permanent set", "status": "REQUIRED_BEFORE_RELEASE"},
    ]


def write_reports(result: dict, contract: dict, zh_path: Path, en_path: Path) -> None:
    correction = result["catalog_correction"]
    belt = result["belt_geometry"]
    load = result["load_path"]
    bearing = result["bearing_screen"]
    shaft = result["shaft_key_screen"]
    interface = result["rail_interface_screen"]
    packaging = result["packaging_screen"]
    sources = {item["id"]: item["url"] for item in contract["official_source_evidence"]}
    open_count = len(result["unresolved_freeze_gates"])
    zh = [
        "# BB-8 阶段 22：标准同步带、双轴承键轴与底盘接口门",
        "",
        f"> **{result['overall']}**。目录几何、轴承寿命、键轴强度、正向定位接口与球壳包络解析筛查通过；制造、Blender写入和真机验证仍未放行。",
        "",
        "## 先纠正阶段21的皮带候选",
        "",
        f"- Gates 2025工业目录的15 mm宽5MGT标准长度从300 mm起；阶段21的 **{correction['stage21_candidate']} / 280 mm / 56齿** 不在该标准库存长度表中。",
        f"- 改用官方产品 **{correction['selected_part']}**（产品号 {correction['selected_product_number']}）：300 mm节线、60齿、15 mm宽。",
        f"- 两只24T、5 mm节距等径带轮的节径为 {belt['pulley_pitch_diameter_mm']:.3f} mm；90 mm轴距精确得到 **{belt['calculated_pitch_length_mm']:.1f} mm** 闭式节线，传动比仍为1:1。",
        f"- 24齿高于Gates对5MGT的18齿最小建议。电机安装位提供 {belt['motor_tension_adjustment_total_mm']:.1f} mm总调节，超过目录的1 mm张紧余量。",
        "- 双法兰条件不允许强行把皮带撬过法兰；规定先拆防护罩和轮侧可拆带轮，带轮与皮带一起装回。额定功率和安装张力仍必须用Gates DesignFlex或供应商计算冻结。",
        "",
        "## 双6001轴承与悬臂带轮载荷",
        "",
        f"- 用SKF W 6001-2RS1的较保守目录值作评级下限：12×28×8 mm，C={contract['selected_architecture']['bearing_stack']['minimum_dynamic_rating_n']/1000:.2f} kN，C0={contract['selected_architecture']['bearing_stack']['minimum_static_rating_n']/1000:.2f} kN，极限转速16000 r/min；未声称已经采购SKF轴承。",
        f"- 轴承中心跨距38 mm，带轮中心比外侧轴承悬出14.5 mm。3×冲击扭矩和每跨80 N预紧上界形成 {load['belt_radial_load_envelope_n']:.1f} N带轮径向包络，最重外侧轴承等效载荷 **{bearing['worst_outboard_equivalent_radial_load_n']:.1f} N**。",
        f"- 静强度安全系数 {bearing['static_safety_factor']:.2f}；即使按1000 r/min解析，L10仍为 **{bearing['l10_hours_at_analysis_speed']:.0f} h**。这不替代游隙、密封、配合、偏心、污染和温升实测。",
        "",
        "## 12 mm键轴、轮毂与正向底盘接口",
        "",
        f"- 12 mm轴在3.6 N·m冲击扭矩、带轮悬臂和100 N轮压下，理想弯扭von Mises为 {shaft['ideal_von_mises_mpa']:.1f} MPa；乘2.5键槽系数后为 **{shaft['keyway_factored_von_mises_mpa']:.1f} MPa**。要求材料证书屈服强度至少400 MPa，解析安全系数 {shaft['yield_safety_factor']:.2f}。",
        f"- 4×4×20 mm平键需求为剪应力 {shaft['key_shear_stress_mpa']:.1f} MPa、挤压应力 {shaft['key_bearing_stress_mpa']:.1f} MPa；最终仍要做7.2 N·m无滑移、无永久变形的实物扭矩证明。",
        f"- 每侧底盘接口用2根6 mm定位销、4颗M6夹紧和一个硬限位；1000 N设计载荷下，定位销单剪 {interface['dowel_single_shear_mpa']:.1f} MPa、6 mm板孔挤压 {interface['plate_bearing_mpa']:.1f} MPa、边缘撕裂 {interface['plate_tearout_mpa']:.1f} MPa。强度筛查不借用摩擦力。",
        "",
        "## 包络与装配限制",
        "",
        f"- 电机轴距增至90 mm后，电机球壳解析余量为 {packaging['motor_shell_clearance_mm']:.1f} mm；板件最小余量 {packaging['plate_shell_clearance_mm']:.1f} mm；含3 mm防护罩余量的带轮最小余量 {packaging['guarded_pulley_shell_clearance_mm']:.1f} mm。",
        "- 这些是局部解析包络，不是当前用户Blender主工程的完整干涉通过结论；本阶段没有保存或覆盖该主文件。",
        "",
        "## 自组装与验证顺序",
        "",
        "1. 先按参考DXF做廉价样板，确认90 mm轴距、24T带轮、300 mm皮带和可拆轮侧带轮的装配顺序。",
        "2. 用选定轴承供应商的配合表冻结12 mm轴和28 mm座孔；一端固定、一端至少0.3 mm浮动，再测端游和外圈爬动。",
        "3. 加工带证书的12 mm键轴与4×4键，先在台架做7.2 N·m扭矩证明，再装轮胎。",
        "4. 用两根定位销和硬限位把每侧1000 N载荷送入车架，M6只负责夹紧；检查防护罩必须在断电后才能拆。",
        "5. 之后才允许进行架空皮带跑偏、急停、温升、球壳接触、低速偏航辨识和19项整机调试。",
        "",
        f"开放冻结门：{open_count}项；制造发布为否，物理试验状态为NOT_RUN。",
        "",
        "## 官方来源",
        "",
        f"- Gates 5MGT-300-15产品页：{sources['GATES_5MGT_300_15']}",
        f"- Gates 2025工业传动目录：{sources['GATES_2025_INDUSTRIAL_CATALOG']}",
        f"- Gates PowerGrip GT3设计手册：{sources['GATES_POWERGRIP_GT3_MANUAL']}",
        f"- Gates预防维护手册：{sources['GATES_PREVENTIVE_MAINTENANCE']}",
        f"- SKF不锈钢深沟球轴承目录：{sources['SKF_STAINLESS_DGBB_CATALOG']}",
        "",
    ]
    en = [
        "# BB-8 Stage 22: Catalog Belt, Dual-Bearing Keyed Shaft and Rail Interface Gate",
        "",
        f"> **{result['overall']}**. Catalog geometry, bearing life, keyed-shaft strength, positive rail load path and shell-envelope screens pass. Fabrication, Blender integration and physical release remain blocked.",
        "",
        "## Correcting the Stage-21 belt candidate",
        "",
        f"- Gates' 2025 industrial catalog starts its standard 15 mm-wide 5MGT list at 300 mm. The Stage-21 **{correction['stage21_candidate']} / 280 mm / 56-tooth** candidate is not in that stock-length table.",
        f"- The replacement is official part **{correction['selected_part']}**, product {correction['selected_product_number']}: 300 mm pitch length, 60 teeth and 15 mm width.",
        f"- Equal 24T, 5 mm-pitch pulleys have {belt['pulley_pitch_diameter_mm']:.3f} mm pitch diameter. A 90 mm center distance gives exactly **{belt['calculated_pitch_length_mm']:.1f} mm** closed pitch length at 1:1.",
        f"- Twenty-four teeth exceed Gates' 18-tooth 5MGT minimum recommendation. The motor mount provides {belt['motor_tension_adjustment_total_mm']:.1f} mm total adjustment, exceeding the catalog's 1 mm tensioning allowance.",
        "- Do not force the belt over two flanges. Remove the guard and outboard wheel pulley, then install the belt together with that pulley. Gates DesignFlex or supplier power and installation-tension calculations remain mandatory.",
        "",
        "## Dual 6001 bearing and overhung-pulley load path",
        "",
        f"- Conservative rating floors come from SKF W 6001-2RS1: 12×28×8 mm, C={contract['selected_architecture']['bearing_stack']['minimum_dynamic_rating_n']/1000:.2f} kN, C0={contract['selected_architecture']['bearing_stack']['minimum_static_rating_n']/1000:.2f} kN and 16000 r/min limiting speed. This does not claim an SKF purchase.",
        f"- Bearing centers are 38 mm apart and the pulley center overhangs the outboard bearing by 14.5 mm. Three-times shock torque plus an 80 N-per-span pretension ceiling creates a {load['belt_radial_load_envelope_n']:.1f} N pulley envelope and **{bearing['worst_outboard_equivalent_radial_load_n']:.1f} N** worst equivalent bearing load.",
        f"- Static safety is {bearing['static_safety_factor']:.2f}; analytical L10 is **{bearing['l10_hours_at_analysis_speed']:.0f} h** even at 1000 r/min. Clearance, seals, fits, misalignment, contamination and temperature still require selected-part evidence.",
        "",
        "## 12 mm keyed shaft, hubs and positive rail interface",
        "",
        f"- Under 3.6 N·m shock torque, pulley overhang and 100 N wheel preload, the ideal bending-torsion von Mises stress is {shaft['ideal_von_mises_mpa']:.1f} MPa. A 2.5 keyway factor raises it to **{shaft['keyway_factored_von_mises_mpa']:.1f} MPa**. Requiring certified yield of at least 400 MPa gives {shaft['yield_safety_factor']:.2f} analytical safety.",
        f"- A 4×4×20 mm key sees {shaft['key_shear_stress_mpa']:.1f} MPa shear and {shaft['key_bearing_stress_mpa']:.1f} MPa bearing stress. A physical 7.2 N·m no-slip, no-permanent-set torque proof remains required.",
        f"- Each cassette uses two 6 mm dowels, four M6 clamps and a hard stop. At 1000 N interface load, dowel shear is {interface['dowel_single_shear_mpa']:.1f} MPa, plate bearing {interface['plate_bearing_mpa']:.1f} MPa and tear-out {interface['plate_tearout_mpa']:.1f} MPa. No interface friction is credited.",
        "",
        "## Packaging and assembly limits",
        "",
        f"- Moving to 90 mm center distance leaves {packaging['motor_shell_clearance_mm']:.1f} mm motor clearance, {packaging['plate_shell_clearance_mm']:.1f} mm plate clearance and {packaging['guarded_pulley_shell_clearance_mm']:.1f} mm guarded-pulley clearance.",
        "- These are local analytical envelopes, not a full current-master clash pass. Stage 22 did not save or overwrite the user's Blender master.",
        "",
        "## Maker assembly and verification sequence",
        "",
        "1. Cut inexpensive fit-test profiles first and confirm 90 mm center distance, 24T pulleys, the 300 mm belt and removable-pulley installation order.",
        "2. Freeze the 12 mm shaft and 28 mm housing fits from the selected bearing supplier; locate one bearing and allow at least 0.3 mm float at the other, then measure endplay and outer-ring creep.",
        "3. Machine the certified 12 mm keyed shaft and 4×4 keys, and pass the 7.2 N·m bench torque proof before installing the tire.",
        "4. Feed each 1000 N cassette load into the chassis through two dowels and a hard stop; M6 fasteners clamp only. Guard removal must require isolated power.",
        "5. Only then run raised-wheel belt tracking, E-stop, thermal, shell-contact, low-speed yaw-identification and nineteen-item commissioning tests.",
        "",
        f"Open freeze gates: {open_count}. Manufacturing release is false and physical status is NOT_RUN.",
        "",
        "## Official sources",
        "",
        f"- Gates 5MGT-300-15 product page: {sources['GATES_5MGT_300_15']}",
        f"- Gates 2025 industrial catalog: {sources['GATES_2025_INDUSTRIAL_CATALOG']}",
        f"- Gates PowerGrip GT3 design manual: {sources['GATES_POWERGRIP_GT3_MANUAL']}",
        f"- Gates preventive-maintenance manual: {sources['GATES_PREVENTIVE_MAINTENANCE']}",
        f"- SKF stainless deep-groove ball-bearing catalog: {sources['SKF_STAINLESS_DGBB_CATALOG']}",
        "",
    ]
    zh_path.write_text("\n".join(zh), encoding="utf-8")
    en_path.write_text("\n".join(en), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--stage21-contract", type=Path, default=DEFAULT_STAGE21_CONTRACT)
    parser.add_argument("--stage21-results", type=Path, default=DEFAULT_STAGE21_RESULTS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--load-cases", type=Path, default=DEFAULT_LOAD_CASES)
    parser.add_argument("--bom", type=Path, default=DEFAULT_BOM)
    parser.add_argument("--report-zh", type=Path, default=DEFAULT_REPORT_ZH)
    parser.add_argument("--report-en", type=Path, default=DEFAULT_REPORT_EN)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    stage21_contract = json.loads(args.stage21_contract.read_text(encoding="utf-8"))
    stage21_results = json.loads(args.stage21_results.read_text(encoding="utf-8"))
    result = verify(contract, stage21_contract, stage21_results)

    args.results.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    load_cases = load_case_rows(result)
    with args.load_cases.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=load_cases[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(load_cases)
    bom = bom_rows()
    with args.bom.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=bom[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(bom)
    write_reports(result, contract, args.report_zh, args.report_en)

    print(
        f"{result['overall']} analytical={result['analytical_screen_passed']} "
        f"belt={result['catalog_correction']['selected_part']} "
        f"bearing={result['bearing_screen']['worst_outboard_equivalent_radial_load_n']:.1f}N "
        f"L10={result['bearing_screen']['l10_hours_at_analysis_speed']:.0f}h "
        f"shaft_sf={result['shaft_key_screen']['yield_safety_factor']:.2f} "
        f"unresolved={len(result['unresolved_freeze_gates'])}"
    )
    print("RESULTS", args.results)
    print("LOAD_CASES", args.load_cases)
    print("BOM", args.bom)
    if args.expect_overall and result["overall"] != args.expect_overall:
        raise SystemExit(f"expected {args.expect_overall}, got {result['overall']}")
    if result["overall"].startswith("FAIL_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
