#!/usr/bin/env python3
"""Verify Stage-20 current-geometry structural screening without claiming hardware proof."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "engineering" / "stage20_structural_load_contract.json"
DEFAULT_MANIFEST = ROOT / "engineering" / "internal_assembly_manifest.csv"
DEFAULT_AUDIT = ROOT / "engineering" / "stage19_blender_reopen_audit.json"
DEFAULT_LEGACY = ROOT / "engineering" / "physics_inputs.json"
DEFAULT_RESULTS = ROOT / "engineering" / "stage20_structural_load_results.json"
DEFAULT_SWEEP = ROOT / "engineering" / "stage20_structural_load_sweep.csv"
DEFAULT_REPORT_ZH = ROOT / "docs" / "BB8_阶段20_结构载荷与公差门.md"
DEFAULT_REPORT_EN = ROOT / "docs" / "BB8_stage20_structural_load_and_tolerance_gate.md"


def tube_properties(outer_m: float, inner_m: float) -> tuple[float, float]:
    area = math.pi * (outer_m**2 - inner_m**2) / 4.0
    inertia = math.pi * (outer_m**4 - inner_m**4) / 64.0
    return area, inertia


def rectangular_inertia(width_m: float, depth_m: float) -> float:
    return width_m * depth_m**3 / 12.0


def read_manifest(path: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return rows, {row["object"]: row for row in rows}


def verify(contract: dict, rows: list[dict[str, str]], by_name: dict[str, dict[str, str]], audit: dict, legacy: dict) -> dict:
    checks: list[dict] = []

    def check(identifier: str, passed: bool, actual, requirement) -> None:
        checks.append({"id": identifier, "passed": bool(passed), "actual": actual, "requirement": requirement})

    baseline = contract["geometry_baseline"]
    check("stage", contract.get("stage") == 20, contract.get("stage"), 20)
    check("manifest_row_count", len(rows) == baseline["expected_manifest_rows"], len(rows), baseline["expected_manifest_rows"])
    check("reopen_audit_passed", audit.get("result") == "PASS_REOPEN_AUDIT_ONLY", audit.get("result"), "PASS_REOPEN_AUDIT_ONLY")
    check("master_hash_matches", audit.get("master", {}).get("sha256") == baseline["master_blend_sha256"], audit.get("master", {}).get("sha256"), baseline["master_blend_sha256"])

    geometry_matches = {}
    tolerance = float(baseline["dimension_tolerance_mm"])
    for name, expected in baseline["expected_objects"].items():
        row = by_name.get(name)
        check(f"object_exists_{name}", row is not None, name if row else None, "present in fabrication manifest")
        if row is None:
            geometry_matches[name] = None
            continue
        actual = [float(row[f"size_{axis}_mm"]) for axis in "xyz"]
        passed = all(abs(value - target) <= tolerance for value, target in zip(actual, expected))
        geometry_matches[name] = actual
        check(f"dimensions_{name}", passed, actual, expected)

    legacy_outer_mm = float(legacy["mast_outer_diameter_m"]) * 1000.0
    legacy_inner_mm = float(legacy["mast_inner_diameter_m"]) * 1000.0
    legacy_length_mm = float(legacy["mast_length_m"]) * 1000.0
    current_mast = geometry_matches.get("Internal magnetic mast")
    legacy_mismatch = bool(current_mast) and (
        abs(current_mast[0] - legacy_outer_mm) > tolerance
        or abs(current_mast[2] - legacy_length_mm) > tolerance
    )
    check("legacy_stage2_mast_mismatch_detected", legacy_mismatch,
          {"current_envelope_mm": current_mast, "legacy_od_id_length_mm": [legacy_outer_mm, legacy_inner_mm, legacy_length_mm]},
          "current Stage-19 mast envelope must not be represented as the legacy Stage-2 12/8 x 300 mm tube")

    loads = contract["load_cases"]
    material = contract["candidate_material"]
    sections = contract["candidate_sections"]
    thresholds = contract["acceptance_thresholds"]
    g = float(loads["gravity_mps2"])
    total_mass = float(loads["nominal_total_mass_kg"])
    head_mass = float(loads["nominal_head_mass_kg"])
    shock_g = float(loads["vertical_service_shock_g"])
    lateral_accel = g * float(loads["lateral_service_shock_g"]) + float(loads["design_speed_mps"]) * float(loads["design_yaw_rate_radps"])
    head_lateral_force = head_mass * lateral_accel
    total_vertical_shock = total_mass * g * shock_g
    E = float(material["elastic_modulus_gpa"]) * 1e9
    density = float(material["density_kg_m3"])
    yield_pa = float(material["yield_strength_mpa_typical"]) * 1e6
    fatigue_pa = float(material["reversed_fatigue_endurance_mpa_typical_at_5e8_cycles"]) * 1e6

    mast = sections["mast"]
    mast_do = float(mast["outer_diameter_mm"]) / 1000.0
    mast_di = float(mast["inner_diameter_mm"]) / 1000.0
    mast_length = float(mast["length_mm"]) / 1000.0
    mast_area, mast_inertia = tube_properties(mast_do, mast_di)
    mast_moment = head_lateral_force * mast_length
    mast_stress = mast_moment * mast_do / 2.0 / mast_inertia
    mast_tip_deflection = head_lateral_force * mast_length**3 / (3.0 * E * mast_inertia)
    mast_mass = mast_area * mast_length * density
    mast_modal_effective_mass = head_mass + 0.236 * mast_mass
    mast_frequency = math.sqrt(3.0 * E * mast_inertia / (mast_modal_effective_mass * mast_length**3)) / (2.0 * math.pi)
    motor_rotation_frequency = float(loads["motor_rated_speed_rpm"]) / 60.0
    mast_frequency_ratio = mast_frequency / motor_rotation_frequency
    mast_yield_sf = yield_pa / mast_stress
    mast_fatigue_sf = fatigue_pa / mast_stress

    brace = sections["mast_brace"]
    brace_do = float(brace["outer_diameter_mm"]) / 1000.0
    brace_di = float(brace["inner_diameter_mm"]) / 1000.0
    brace_length = float(brace["length_mm"]) / 1000.0
    brace_horizontal = float(brace["horizontal_projection_mm"]) / 1000.0
    brace_area, brace_inertia = tube_properties(brace_do, brace_di)
    brace_force = head_lateral_force / (2.0 * brace_horizontal / brace_length)
    brace_stress = brace_force / brace_area
    brace_euler = math.pi**2 * E * brace_inertia / (float(brace["end_condition_factor"]) * brace_length) ** 2
    brace_buckling_sf = brace_euler / brace_force

    rail = sections["chassis_rail"]
    rail_length = float(rail["length_mm"]) / 1000.0
    rail_width = float(rail["width_mm"]) / 1000.0
    rail_depth = float(rail["vertical_depth_mm"]) / 1000.0
    rail_force = total_vertical_shock / int(rail["parallel_rails"])
    rail_inertia = rectangular_inertia(rail_width, rail_depth)
    rail_moment = rail_force * rail_length / 4.0
    rail_stress = rail_moment * rail_depth / 2.0 / rail_inertia
    rail_deflection = rail_force * rail_length**3 / (48.0 * E * rail_inertia)
    rail_yield_sf = yield_pa / rail_stress
    rail_fatigue_sf = fatigue_pa / rail_stress

    cross = sections["crossmember"]
    cross_length = float(cross["length_mm"]) / 1000.0
    cross_width = float(cross["width_mm"]) / 1000.0
    cross_depth = float(cross["vertical_depth_mm"]) / 1000.0
    cross_force = total_vertical_shock * float(cross["load_share_of_total"])
    cross_inertia = rectangular_inertia(cross_width, cross_depth)
    cross_moment = cross_force * cross_length / 4.0
    cross_stress = cross_moment * cross_depth / 2.0 / cross_inertia
    cross_deflection = cross_force * cross_length**3 / (48.0 * E * cross_inertia)
    cross_yield_sf = yield_pa / cross_stress

    plate = sections["motor_face_plate"]
    wheel_force = float(loads["motor_peak_torque_nm_each"]) / float(loads["drive_wheel_radius_m"])
    plate_thickness = float(plate["thickness_mm"]) / 1000.0
    m4_count = int(plate["m4_bolt_count"])
    m4_diameter = float(plate["m4_nominal_diameter_mm"]) / 1000.0
    m4_pcd_radius = float(plate["m4_bolt_circle_diameter_mm"]) / 2000.0
    m4_torque_force_each = float(loads["motor_peak_torque_nm_each"]) / (m4_count * m4_pcd_radius)
    m4_direct_force_each = wheel_force / m4_count
    m4_resultant_force_each = math.hypot(m4_torque_force_each, m4_direct_force_each)
    m4_plate_bearing_stress = m4_resultant_force_each / (plate_thickness * m4_diameter)

    hub = sections["wheel_hub"]
    m5_count = int(hub["m5_bolt_count"])
    m5_diameter = float(hub["m5_nominal_diameter_mm"]) / 1000.0
    m5_nominal_direct_shear_stress = (wheel_force / m5_count) / (math.pi * m5_diameter**2 / 4.0)

    latches = sections["equator_latches"]
    latch_total_clamp = int(latches["count"]) * float(latches["target_clamp_force_n_each"])
    latch_to_shock_ratio = latch_total_clamp / total_vertical_shock

    tolerance_budget = contract["tolerance_budget"]
    required_adjustment = sum(float(tolerance_budget[key]) for key in (
        "shell_inner_radius_allowance_mm", "wheel_radius_allowance_mm",
        "wheel_centre_location_allowance_mm", "wear_and_preload_allowance_mm"))
    provided_adjustment = float(tolerance_budget["provided_radial_adjustment_range_mm"])
    adjustment_gap = required_adjustment - provided_adjustment

    check("mast_static_yield_screen", mast_yield_sf >= thresholds["minimum_static_yield_safety_factor"], round(mast_yield_sf, 3), f">={thresholds['minimum_static_yield_safety_factor']}")
    check("mast_tip_deflection_screen", mast_tip_deflection * 1000.0 <= thresholds["maximum_mast_tip_deflection_mm"], round(mast_tip_deflection * 1000.0, 4), f"<={thresholds['maximum_mast_tip_deflection_mm']} mm")
    check("mast_ideal_material_fatigue_screen", mast_fatigue_sf >= thresholds["minimum_ideal_material_fatigue_screen_factor"], round(mast_fatigue_sf, 3), f">={thresholds['minimum_ideal_material_fatigue_screen_factor']}")
    check("mast_modal_separation_screen", mast_frequency_ratio >= thresholds["minimum_mast_frequency_to_motor_rotation_ratio"], round(mast_frequency_ratio, 3), f">={thresholds['minimum_mast_frequency_to_motor_rotation_ratio']} x motor rotation")
    check("brace_euler_buckling_screen", brace_buckling_sf >= thresholds["minimum_brace_euler_buckling_factor"], round(brace_buckling_sf, 3), f">={thresholds['minimum_brace_euler_buckling_factor']}")
    check("rail_static_yield_screen", rail_yield_sf >= thresholds["minimum_static_yield_safety_factor"], round(rail_yield_sf, 3), f">={thresholds['minimum_static_yield_safety_factor']}")
    check("rail_deflection_screen", rail_deflection * 1000.0 <= thresholds["maximum_rail_deflection_mm"], round(rail_deflection * 1000.0, 4), f"<={thresholds['maximum_rail_deflection_mm']} mm")
    check("rail_ideal_material_fatigue_screen", rail_fatigue_sf >= thresholds["minimum_ideal_material_fatigue_screen_factor"], round(rail_fatigue_sf, 3), f">={thresholds['minimum_ideal_material_fatigue_screen_factor']}")
    check("crossmember_static_yield_screen", cross_yield_sf >= thresholds["minimum_static_yield_safety_factor"], round(cross_yield_sf, 3), f">={thresholds['minimum_static_yield_safety_factor']}")
    check("crossmember_deflection_screen", cross_deflection * 1000.0 <= thresholds["maximum_crossmember_deflection_mm"], round(cross_deflection * 1000.0, 4), f"<={thresholds['maximum_crossmember_deflection_mm']} mm")
    check("nominal_latch_clamp_screen", latch_to_shock_ratio >= thresholds["minimum_nominal_latch_clamp_to_vertical_shock_ratio"], round(latch_to_shock_ratio, 3), f">={thresholds['minimum_nominal_latch_clamp_to_vertical_shock_ratio']}")
    check("fastener_demand_calculations_finite", all(math.isfinite(value) and value > 0 for value in (m4_plate_bearing_stress, m5_nominal_direct_shear_stress)), {"m4_plate_bearing_mpa": round(m4_plate_bearing_stress / 1e6, 4), "m5_nominal_direct_shear_mpa": round(m5_nominal_direct_shear_stress / 1e6, 4)}, "positive finite demand only; not a fastener strength pass")
    check("tolerance_budget_explicit", required_adjustment > 0.0, round(required_adjustment, 3), ">0 mm")

    unresolved = sorted(key for key, value in contract["freeze_gates"].items() if value is not True)
    analytical_pass = all(item["passed"] for item in checks)
    overall = "HOLD_JOINT_TOLERANCE_MATERIAL_AND_PHYSICAL_VALIDATION_REQUIRED" if analytical_pass and unresolved else "FAIL_ANALYTICAL_STRUCTURE"
    return {
        "stage": 20,
        "overall": overall,
        "analytical_screen_passed": analytical_pass,
        "manufacturing_release": False,
        "physical_test_status": "NOT_RUN",
        "legacy_stage2_mast_analysis_current": False,
        "legacy_mismatch": {
            "detected": legacy_mismatch,
            "current_mast_envelope_mm": current_mast,
            "legacy_tube_od_id_length_mm": [legacy_outer_mm, legacy_inner_mm, legacy_length_mm],
            "disposition": baseline["legacy_disposition"]
        },
        "load_summary": {
            "head_lateral_service_force_n": round(head_lateral_force, 6),
            "total_vertical_service_shock_n": round(total_vertical_shock, 6),
            "peak_wheel_tangential_force_each_n": round(wheel_force, 6)
        },
        "mast_candidate": {
            "area_mm2": round(mast_area * 1e6, 6),
            "second_moment_mm4": round(mast_inertia * 1e12, 6),
            "root_moment_nm": round(mast_moment, 6),
            "bending_stress_mpa": round(mast_stress / 1e6, 6),
            "tip_deflection_mm": round(mast_tip_deflection * 1000.0, 6),
            "static_yield_safety_factor": round(mast_yield_sf, 6),
            "ideal_material_fatigue_screen_factor": round(mast_fatigue_sf, 6),
            "first_bending_frequency_hz": round(mast_frequency, 6),
            "tube_mass_kg": round(mast_mass, 6),
            "modal_effective_mass_kg": round(mast_modal_effective_mass, 6),
            "motor_rotation_frequency_hz": round(motor_rotation_frequency, 6),
            "frequency_ratio": round(mast_frequency_ratio, 6)
        },
        "brace_candidate": {
            "area_mm2": round(brace_area * 1e6, 6),
            "axial_force_each_n": round(brace_force, 6),
            "axial_stress_mpa": round(brace_stress / 1e6, 6),
            "euler_critical_load_n": round(brace_euler, 6),
            "buckling_factor": round(brace_buckling_sf, 6)
        },
        "chassis_rail_candidate": {
            "load_each_n": round(rail_force, 6),
            "bending_stress_mpa": round(rail_stress / 1e6, 6),
            "deflection_mm": round(rail_deflection * 1000.0, 6),
            "static_yield_safety_factor": round(rail_yield_sf, 6),
            "ideal_material_fatigue_screen_factor": round(rail_fatigue_sf, 6)
        },
        "crossmember_candidate": {
            "load_n": round(cross_force, 6),
            "bending_stress_mpa": round(cross_stress / 1e6, 6),
            "deflection_mm": round(cross_deflection * 1000.0, 6),
            "static_yield_safety_factor": round(cross_yield_sf, 6)
        },
        "motor_mount_candidate": {
            "m4_torque_force_each_n": round(m4_torque_force_each, 6),
            "m4_direct_traction_force_each_n": round(m4_direct_force_each, 6),
            "m4_resultant_force_each_n": round(m4_resultant_force_each, 6),
            "m4_plate_bearing_demand_mpa": round(m4_plate_bearing_stress / 1e6, 6),
            "m5_nominal_direct_shear_demand_mpa": round(m5_nominal_direct_shear_stress / 1e6, 6),
            "fastener_strength_pass": False
        },
        "equator_latch_candidate": {
            "nominal_total_clamp_n": round(latch_total_clamp, 6),
            "vertical_shock_ratio": round(latch_to_shock_ratio, 6),
            "measured_clamp_force_pass": False
        },
        "tolerance_gate": {
            "required_radial_adjustment_range_mm": round(required_adjustment, 6),
            "provided_radial_adjustment_range_mm": round(provided_adjustment, 6),
            "adjustment_shortfall_mm": round(adjustment_gap, 6),
            "passed": provided_adjustment >= required_adjustment
        },
        "unresolved_freeze_gates": unresolved,
        "checks": checks
    }


def sweep_rows(contract: dict) -> list[dict]:
    loads = contract["load_cases"]
    material = contract["candidate_material"]
    sections = contract["candidate_sections"]
    g = float(loads["gravity_mps2"])
    mass = float(loads["nominal_total_mass_kg"])
    head_mass = float(loads["nominal_head_mass_kg"])
    speed_yaw = float(loads["design_speed_mps"]) * float(loads["design_yaw_rate_radps"])
    E = float(material["elastic_modulus_gpa"]) * 1e9
    yield_pa = float(material["yield_strength_mpa_typical"]) * 1e6
    mast = sections["mast"]
    do = float(mast["outer_diameter_mm"]) / 1000.0
    di = float(mast["inner_diameter_mm"]) / 1000.0
    length = float(mast["length_mm"]) / 1000.0
    _, mast_inertia = tube_properties(do, di)
    rail = sections["chassis_rail"]
    rail_length = float(rail["length_mm"]) / 1000.0
    rail_width = float(rail["width_mm"]) / 1000.0
    rail_depth = float(rail["vertical_depth_mm"]) / 1000.0
    rail_inertia = rectangular_inertia(rail_width, rail_depth)
    result = []
    for shock_g in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        for lateral_g in (0.0, 0.5, 1.0, 1.5):
            lateral_force = head_mass * (lateral_g * g + speed_yaw)
            mast_stress = lateral_force * length * do / 2.0 / mast_inertia
            rail_force = mass * g * shock_g / int(rail["parallel_rails"])
            rail_stress = (rail_force * rail_length / 4.0) * rail_depth / 2.0 / rail_inertia
            rail_deflection = rail_force * rail_length**3 / (48.0 * E * rail_inertia)
            result.append({
                "vertical_shock_g": shock_g,
                "lateral_shock_g": lateral_g,
                "head_lateral_force_n": round(lateral_force, 6),
                "mast_bending_stress_mpa": round(mast_stress / 1e6, 6),
                "mast_yield_safety_factor": round(yield_pa / mast_stress, 6),
                "rail_bending_stress_mpa": round(rail_stress / 1e6, 6),
                "rail_yield_safety_factor": round(yield_pa / rail_stress, 6),
                "rail_deflection_mm": round(rail_deflection * 1000.0, 6)
            })
    return result


def write_reports(result: dict, contract: dict, zh_path: Path, en_path: Path) -> None:
    mast = result["mast_candidate"]
    brace = result["brace_candidate"]
    rail = result["chassis_rail_candidate"]
    cross = result["crossmember_candidate"]
    mount = result["motor_mount_candidate"]
    latch = result["equator_latch_candidate"]
    tolerance = result["tolerance_gate"]
    source = contract["candidate_material"]["source"]
    zh = [
        "# BB-8 阶段 20：结构载荷与公差门", "",
        f"> **{result['overall']}**。当前数字几何与闭式解析筛查通过，但制造发布仍为否；材料、连接、公差和真机证据均未完成。", "",
        "## 首先纠正旧几何", "",
        "- 当前 Stage-19 制造清单中的磁力桅杆包络是 **Ø24 × 340 mm**。",
        "- 阶段 2 仍按 **Ø12/Ø8 × 300 mm** 铝管计算；该机械结论不再代表当前主模型。",
        "- 阶段 20 不改动正在打开的 Blender 文件，而是把 Ø24/Ø20 × 340 mm 定义为待冻结的管材候选；内孔、材料批次和连接仍是开放门。", "",
        "## 2.5 g / 1.0 g 解析筛查", "",
        "| 路径 | 解析结果 | 证据边界 |", "|---|---:|---|",
        f"| Ø24/Ø20 桅杆候选 | {mast['bending_stress_mpa']:.3f} MPa，挠度 {mast['tip_deflection_mm']:.3f} mm，屈服裕量 {mast['static_yield_safety_factor']:.2f}× | 无接头、焊缝、孔位与实测应变 |",
        f"| 两根 Ø12/Ø8 斜撑候选 | 单根 {brace['axial_force_each_n']:.3f} N，Euler 屈曲裕量 {brace['buckling_factor']:.1f}× | 端部铰接和管内径只是候选 |",
        f"| 两根 380 × 18 × 12 mm 纵梁 | {rail['bending_stress_mpa']:.3f} MPa，挠度 {rail['deflection_mm']:.3f} mm，屈服裕量 {rail['static_yield_safety_factor']:.2f}× | 简支、对称分载；连接未建模 |",
        f"| 120 × 8 × 12 mm 横梁 | {cross['bending_stress_mpa']:.3f} MPa，挠度 {cross['deflection_mm']:.3f} mm | 仅分配总冲击的四分之一 |",
        f"| 4 mm 电机面板 / 4×M4 PCD35 | 每颗 M4 合成需求 {mount['m4_resultant_force_each_n']:.2f} N，板孔承压需求 {mount['m4_plate_bearing_demand_mpa']:.3f} MPa | 只算需求；M4 等级、预紧、孔径和边距未冻结 |",
        f"| 8 个锁扣名义夹紧 | {latch['nominal_total_clamp_n']:.0f} N，对 2.5 g 总冲击比 {latch['vertical_shock_ratio']:.2f}× | 80 N/个尚未实测 |", "",
        "## 模态、疲劳与公差", "",
        f"- 无斜撑信用的桅杆一阶弯曲估算为 **{mast['first_bending_frequency_hz']:.2f} Hz**，是 248 rpm 电机转频的 {mast['frequency_ratio']:.2f}×；仍需锤击模态试验。",
        f"- 理想 6061-T6/T651 基材疲劳筛查：桅杆 {mast['ideal_material_fatigue_screen_factor']:.2f}×、纵梁 {rail['ideal_material_fatigue_screen_factor']:.2f}×。这不覆盖焊缝、孔口、表面和真实载荷谱。",
        f"- 轮—壳接触公差预算要求 **{tolerance['required_radial_adjustment_range_mm']:.1f} mm** 径向调节，当前数字几何提供 {tolerance['provided_radial_adjustment_range_mm']:.1f} mm，短缺 **{tolerance['adjustment_shortfall_mm']:.1f} mm**。因此接触预紧不能冻结。", "",
        "## 材料来源与放行边界", "",
        f"Kaiser 6061-T6/T651 典型数据用于解析筛查：68.3 GPa 弹性模量、276 MPa 屈服强度和 97 MPa（5×10^8 次反向应力）疲劳耐久值。来源：{source}。这些是典型板材数据，不是待购管材、棒材、焊接热影响区或加工件的材料证书。", "",
        f"未关闭冻结门：{len(result['unresolved_freeze_gates'])} 项。必须完成管材/板材证书、连接详图、紧固件、轮压调节、壳体接触强度、应变/冲击/模态/耐久和 19 项整机调试后，才可讨论制造放行。", "",
        "机器可读结果：`engineering/stage20_structural_load_results.json`；载荷扫描：`engineering/stage20_structural_load_sweep.csv`。", ""
    ]
    en = [
        "# BB-8 Stage 20: Structural Load and Tolerance Gate", "",
        f"> **{result['overall']}**. Current digital geometry and closed-form screening pass, but manufacturing release remains false; material, joint, tolerance and physical evidence are open.", "",
        "## Correcting the legacy geometry", "",
        "- The current Stage-19 fabrication manifest contains a **Ø24 × 340 mm** magnetic-mast envelope.",
        "- Stage 2 still analyses a **Ø12/Ø8 × 300 mm** aluminium tube, so that mechanical result is not current-model evidence.",
        "- Stage 20 does not touch the open Blender session. It screens a Ø24/Ø20 × 340 mm tube candidate while keeping the bore, material lot and joints unfrozen.", "",
        "## 2.5 g / 1.0 g analytical screening", "",
        "| Load path | Analytical result | Evidence boundary |", "|---|---:|---|",
        f"| Ø24/Ø20 mast candidate | {mast['bending_stress_mpa']:.3f} MPa, {mast['tip_deflection_mm']:.3f} mm tip deflection, {mast['static_yield_safety_factor']:.2f}× yield factor | No joints, welds, holes or strain data |",
        f"| Two Ø12/Ø8 brace candidates | {brace['axial_force_each_n']:.3f} N each, {brace['buckling_factor']:.1f}× Euler factor | Pinned ends and bore are candidates |",
        f"| Two 380 × 18 × 12 mm rails | {rail['bending_stress_mpa']:.3f} MPa, {rail['deflection_mm']:.3f} mm deflection, {rail['static_yield_safety_factor']:.2f}× yield factor | Simply supported symmetric sharing; joints omitted |",
        f"| 120 × 8 × 12 mm crossmember | {cross['bending_stress_mpa']:.3f} MPa, {cross['deflection_mm']:.3f} mm deflection | One-quarter total-shock allocation only |",
        f"| 4 mm motor plate / 4×M4 PCD35 | {mount['m4_resultant_force_each_n']:.2f} N resultant per M4 and {mount['m4_plate_bearing_demand_mpa']:.3f} MPa plate-hole bearing demand | Demand only; M4 grade, preload, hole size and edge distance unfrozen |",
        f"| Eight nominal latches | {latch['nominal_total_clamp_n']:.0f} N, {latch['vertical_shock_ratio']:.2f}× total 2.5 g shock | 80 N per latch is unmeasured |", "",
        "## Modal, fatigue and tolerance gates", "",
        f"- The unbraced-credit mast estimate is **{mast['first_bending_frequency_hz']:.2f} Hz**, {mast['frequency_ratio']:.2f}× the 248 rpm motor rotational frequency; hammer testing is still required.",
        f"- Ideal 6061-T6/T651 base-material fatigue screens are {mast['ideal_material_fatigue_screen_factor']:.2f}× for the mast and {rail['ideal_material_fatigue_screen_factor']:.2f}× for a rail. Welds, holes, surface condition and the real duty spectrum are excluded.",
        f"- The wheel-to-shell stack requires **{tolerance['required_radial_adjustment_range_mm']:.1f} mm** radial adjustment. The current digital geometry provides {tolerance['provided_radial_adjustment_range_mm']:.1f} mm, leaving a **{tolerance['adjustment_shortfall_mm']:.1f} mm** shortfall, so contact preload cannot be frozen.", "",
        "## Material source and release boundary", "",
        f"Kaiser typical 6061-T6/T651 sheet/plate values—68.3 GPa elastic modulus, 276 MPa yield and 97 MPa reversed-stress fatigue endurance at 5×10^8 cycles—are used only for screening: {source}. They are not certificates for purchased tube, bar, weld heat-affected zones or machined parts.", "",
        f"Open freeze gates: {len(result['unresolved_freeze_gates'])}. Material certificates, joint details, fasteners, wheel preload adjustment, shell contact strength, strain/impact/modal/endurance work and all nineteen physical commissioning gates are required before fabrication release can be considered.", "",
        "Machine result: `engineering/stage20_structural_load_results.json`; envelope sweep: `engineering/stage20_structural_load_sweep.csv`.", ""
    ]
    zh_path.write_text("\n".join(zh), encoding="utf-8")
    en_path.write_text("\n".join(en), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--sweep", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--report-zh", type=Path, default=DEFAULT_REPORT_ZH)
    parser.add_argument("--report-en", type=Path, default=DEFAULT_REPORT_EN)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    rows, by_name = read_manifest(args.manifest)
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    legacy = json.loads(args.legacy.read_text(encoding="utf-8"))
    result = verify(contract, rows, by_name, audit, legacy)
    args.results.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sweep = sweep_rows(contract)
    with args.sweep.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sweep[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sweep)
    write_reports(result, contract, args.report_zh, args.report_en)
    print(
        f"{result['overall']} analytical={result['analytical_screen_passed']} "
        f"legacy_mismatch={result['legacy_mismatch']['detected']} "
        f"mast_sf={result['mast_candidate']['static_yield_safety_factor']:.2f} "
        f"rail_sf={result['chassis_rail_candidate']['static_yield_safety_factor']:.2f} "
        f"tolerance_shortfall={result['tolerance_gate']['adjustment_shortfall_mm']:.1f}mm "
        f"unresolved={len(result['unresolved_freeze_gates'])}"
    )
    print("RESULTS", args.results)
    print("SWEEP", args.sweep)
    if args.expect_overall and result["overall"] != args.expect_overall:
        raise SystemExit(f"expected {args.expect_overall}, got {result['overall']}")
    if result["overall"] == "FAIL_ANALYTICAL_STRUCTURE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
