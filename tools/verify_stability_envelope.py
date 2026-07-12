#!/usr/bin/env python3
"""Stage-15 uphill, traction, turning and resultant-lean design screening."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "engineering" / "stability_envelope_input.json"
MASS_RESULTS = ROOT / "engineering" / "mass_properties_results.json"
RESULTS = ROOT / "engineering" / "stability_envelope_results.json"
CSV = ROOT / "engineering" / "stability_envelope_sweep.csv"
REPORT = ROOT / "docs" / "BB8_阶段15_驱动电源与动态稳定性.md"
REPORT_EN = ROOT / "docs" / "BB8_stage15_drive_power_dynamic_stability.md"

p = json.loads(INPUT.read_text(encoding="utf-8"))
mass_results = json.loads(MASS_RESULTS.read_text(encoding="utf-8"))
mass = float(mass_results["nominal"]["total_mass_kg"])
com_offset = -float(mass_results["nominal"]["com_m"][2])
g = 9.80665
effective_mass = mass + 2.0 * p["shell_rotating_mass_kg"] / 3.0


def evaluate(slope_deg: float, accel: float, speed: float, radius: float) -> dict[str, float | bool]:
    slope = math.radians(slope_deg)
    yaw_rate = speed / radius if radius > 0 else 0.0
    lateral_accel = speed * yaw_rate
    uphill_gravity = mass * g * math.sin(slope)
    rolling_force = p["rolling_resistance_coefficient"] * mass * g * math.cos(slope)
    required_force = effective_mass * accel + uphill_gravity + rolling_force
    torque_each = required_force * p["drive_wheel_radius_m"] / (p["motor_count"] * p["drive_efficiency"])
    torque_sf = p["motor_continuous_torque_nm"] / torque_each if torque_each > 0 else math.inf
    traction_capacity = (p["motor_count"] * p["wheel_shell_friction_coefficient"] *
                         p["normal_preload_per_wheel_n"])
    traction_sf = traction_capacity / required_force if required_force > 0 else math.inf
    longitudinal_apparent = accel + g * math.sin(slope)
    vertical_apparent = g * math.cos(slope)
    lean_deg = math.degrees(math.atan2(math.hypot(longitudinal_apparent, lateral_accel), vertical_apparent))
    inner_speed = speed - yaw_rate * p["drive_track_m"] / 2.0
    outer_speed = speed + yaw_rate * p["drive_track_m"] / 2.0
    head_vertical = p["head_mass_kg"] * g * p["vertical_shock_g"]
    head_lateral = p["head_mass_kg"] * (g * p["lateral_shock_g"] + lateral_accel)
    head_load = math.hypot(head_vertical, head_lateral)
    head_sf = p["magnetic_retention_n"] / head_load
    checks = {
        "continuous_torque": torque_sf >= p["required_design_safety_factor"],
        "wheel_shell_traction": traction_sf >= p["required_design_safety_factor"],
        "resultant_lean": lean_deg <= p["maximum_resultant_lean_deg"],
        "wheel_speed": max(abs(inner_speed), abs(outer_speed)) <= p["maximum_wheel_surface_speed_mps"],
        "magnetic_head_combined_shock": head_sf >= p["required_design_safety_factor"],
    }
    return {
        "slope_deg": slope_deg,
        "longitudinal_accel_mps2": accel,
        "speed_mps": speed,
        "turn_radius_m": radius,
        "yaw_rate_radps": yaw_rate,
        "lateral_accel_mps2": lateral_accel,
        "required_uphill_force_n": required_force,
        "motor_torque_each_nm": torque_each,
        "continuous_torque_safety_factor": torque_sf,
        "traction_safety_factor": traction_sf,
        "resultant_lean_deg": lean_deg,
        "inner_wheel_speed_mps": inner_speed,
        "outer_wheel_speed_mps": outer_speed,
        "head_combined_load_n": head_load,
        "magnetic_retention_safety_factor": head_sf,
        "pass": all(checks.values()),
        **{f"check_{key}": value for key, value in checks.items()},
    }


design = evaluate(p["design_slope_deg"], p["design_longitudinal_accel_mps2"],
                  p["design_speed_mps"], p["design_turn_radius_m"])
rows = [
    evaluate(slope_index / 2.0, accel_index / 10.0,
             p["design_speed_mps"], p["design_turn_radius_m"])
    for slope_index in range(0, 17)
    for accel_index in range(0, 8)
]
with CSV.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


def maximum_grade(accel: float) -> float:
    accepted = [index / 100.0 for index in range(0, 1501)
                if evaluate(index / 100.0, accel, p["design_speed_mps"], p["design_turn_radius_m"])["pass"]]
    return max(accepted) if accepted else 0.0


max_grade_zero_accel = maximum_grade(0.0)
max_grade_design_accel = maximum_grade(p["design_longitudinal_accel_mps2"])
result = {
    "status": "PASS_ANALYTICAL_ONLY" if design["pass"] else "HOLD",
    "evidence_boundary": "assumption-driven; physical drive, slope, thermal, traction and E-stop tests remain NOT_RUN",
    "nominal_mass_kg": mass,
    "nominal_com_offset_below_center_m": com_offset,
    "effective_translational_mass_kg": effective_mass,
    "design_point": design,
    "maximum_grade_zero_accel_deg_at_2x_torque_margin": max_grade_zero_accel,
    "maximum_grade_at_design_accel_deg_at_2x_torque_margin": max_grade_design_accel,
    "unpowered_slope_hold": p["unpowered_slope_hold"],
    "physical_test_status": p["physical_test_status"],
}
RESULTS.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

checks = [(key.removeprefix("check_"), value) for key, value in design.items() if key.startswith("check_")]
zh = [
    "# BB-8 阶段 15：驱动电源与动态稳定性", "",
    f"> 结论：**{result['status']}**。阶段15设计点在当前假设下通过，但电机、驱动器、保险丝、接触器、急停、轮壳摩擦与封壳热试验仍全部为`NOT_RUN`。", "",
    "## 新增的实体结构合同", "",
    "- Blender新增左右两块52 × 34 × 16 mm通用电机驱动安装包络、双散热器和8枚M3支柱。驱动器型号未冻结。",
    "- 主电源路径显式建模为：电池正极 → 外部可达维护断电 → 主保险丝 → 常开主接触器 → 左右驱动器 → 电机。",
    "- 急停路径显式建模为双通道常闭输入、安全继电器、接触器反馈、手动复位与左右驱动EN；初次试验必须使用有线系留急停，不能只依赖无线。",
    "- 保险丝电流、接触器直流分断能力、驱动器连续/峰值电流和再生吸收能力均保持`TBD`，必须由真实失速电流与热试验冻结。", "",
    "## 3°上坡 + 转弯设计点", "",
    f"- 名义质量 {mass:.3f} kg；含球壳转动惯量的等效平动质量 {effective_mass:.3f} kg。",
    f"- 坡度 {p['design_slope_deg']:.1f}°、纵向加速度 {p['design_longitudinal_accel_mps2']:.2f} m/s²、速度 {p['design_speed_mps']:.2f} m/s、转弯半径 {p['design_turn_radius_m']:.2f} m。",
    f"- 需求上坡推进力 {design['required_uphill_force_n']:.2f} N；每台电机需求 {design['motor_torque_each_nm']:.3f} N·m；连续扭矩裕量 {design['continuous_torque_safety_factor']:.2f}×。",
    f"- 轮壳附着裕量 {design['traction_safety_factor']:.2f}×；合成稳态倾角 {design['resultant_lean_deg']:.2f}°，低于 {p['maximum_resultant_lean_deg']:.1f}°合同。",
    f"- 左右轮表面速度 {design['inner_wheel_speed_mps']:.3f}/{design['outer_wheel_speed_mps']:.3f} m/s；磁头2.5g垂向+1g横向冲击合载荷裕量 {design['magnetic_retention_safety_factor']:.2f}×。",
    f"- 在2×连续扭矩裕量下，0加速度最大解析坡度约 {max_grade_zero_accel:.2f}°；保持0.20 m/s²加速时约 {max_grade_design_accel:.2f}°。", "",
    "## 判定", "",
]
zh.extend(f"- {'PASS' if value else 'HOLD'} — {name}" for name, value in checks)
zh += ["", "## 必须保留的限制", "",
       "- 球形机器人无机械驻车制动时，断电后不能在坡道保持位置；当前`unpowered_slope_hold=NOT_PROVIDED`。",
       "- 3°是解析设计点，不是实物认证。首轮地面试验仍从水平地面、0.1 m/s、有线急停和软围栏开始。",
       "- 真实采购前必须实测电机失速电流、驱动器封壳温升、轮壳摩擦、接触器分断和急停停止距离。", ""]
REPORT.write_text("\n".join(zh), encoding="utf-8")

en = [
    "# BB-8 Stage 15: Drive Power and Dynamic Stability", "",
    f"> Result: **{result['status']}**. The stage-15 design point passes the current assumptions, but motor, driver, fuse, contactor, E-stop, wheel/shell traction and sealed-shell thermal tests all remain `NOT_RUN`.", "",
    "## New physical contracts", "",
    "- Blender now contains two 52 × 34 × 16 mm generic motor-driver installation envelopes, two heatsinks and eight M3 standoffs. No driver product is frozen.",
    "- The explicit main-power path is battery positive → externally reachable service disconnect → main fuse → normally-open main contactor → left/right drivers → motors.",
    "- The E-stop path has two normally-closed channels, a monitored safety relay, contactor feedback, manual reset and both driver-enable branches. First tests require a wired tether; wireless alone is not accepted.",
    "- Fuse current, DC contactor breaking capacity, continuous/peak driver current and regenerative-energy handling stay `TBD` until measured stall-current and thermal tests are available.", "",
    "## 3° uphill turning design point", "",
    f"- Nominal mass {mass:.3f} kg; effective translational mass including shell rotation {effective_mass:.3f} kg.",
    f"- Grade {p['design_slope_deg']:.1f}°, longitudinal acceleration {p['design_longitudinal_accel_mps2']:.2f} m/s², speed {p['design_speed_mps']:.2f} m/s and turn radius {p['design_turn_radius_m']:.2f} m.",
    f"- Required uphill force {design['required_uphill_force_n']:.2f} N; required torque {design['motor_torque_each_nm']:.3f} N·m per motor; continuous-torque margin {design['continuous_torque_safety_factor']:.2f}×.",
    f"- Wheel/shell traction margin {design['traction_safety_factor']:.2f}×; resultant steady lean {design['resultant_lean_deg']:.2f}° versus a {p['maximum_resultant_lean_deg']:.1f}° contract.",
    f"- Inner/outer wheel surface speeds {design['inner_wheel_speed_mps']:.3f}/{design['outer_wheel_speed_mps']:.3f} m/s; 2.5g vertical plus 1g lateral head-shock retention margin {design['magnetic_retention_safety_factor']:.2f}×.",
    f"- At a 2× continuous-torque margin, the analytical grade ceiling is about {max_grade_zero_accel:.2f}° at zero acceleration and {max_grade_design_accel:.2f}° while accelerating at 0.20 m/s².", "",
    "## Checks", "",
]
en.extend(f"- {'PASS' if value else 'HOLD'} — {name}" for name, value in checks)
en += ["", "## Constraints that remain", "",
       "- Without a mechanical parking brake, a spherical robot cannot hold position on a slope after power removal; `unpowered_slope_hold=NOT_PROVIDED`.",
       "- Three degrees is an analytical design point, not physical certification. Floor tests still begin level at 0.1 m/s with a wired E-stop and soft barriers.",
       "- Before purchasing the final electronics, measure motor stall current, sealed-shell driver temperature, wheel/shell friction, contactor interruption and emergency stopping distance.", ""]
REPORT_EN.write_text("\n".join(en), encoding="utf-8")

print(f"{result['status']} force={design['required_uphill_force_n']:.2f}N "
      f"torque={design['motor_torque_each_nm']:.3f}Nm torque_sf={design['continuous_torque_safety_factor']:.2f} "
      f"lean={design['resultant_lean_deg']:.2f}deg grade_limits={max_grade_zero_accel:.2f}/{max_grade_design_accel:.2f}deg")
print("RESULTS", RESULTS)
print("SWEEP", CSV)
print("REPORT", REPORT)
print("REPORT_EN", REPORT_EN)
if not design["pass"]:
    raise SystemExit(1)
