#!/usr/bin/env python3
"""Stage-2 BB-8 turning, structural, battery and thermal screening."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = json.loads((ROOT / "engineering" / "physics_inputs.json").read_text(encoding="utf-8"))
CSV = ROOT / "engineering" / "turning_multibody_sweep.csv"
REPORT = ROOT / "docs" / "BB8_多体结构电热验证.md"
g = 9.80665


def turn(v: float, yaw: float) -> dict[str, float]:
    lateral_accel = abs(v * yaw)
    head_lateral = p["head_mass_kg"] * lateral_accel
    total_head_lateral = p["head_mass_kg"] * (lateral_accel + p["head_lateral_shock_g"] * g)
    lateral_capacity = p["magnetic_retention_n"] * p["magnetic_lateral_capacity_fraction"]
    return {
        "speed_mps": v,
        "yaw_rate_radps": yaw,
        "turn_radius_m": v / yaw if yaw else math.inf,
        "lateral_accel_mps2": lateral_accel,
        "head_turn_force_n": head_lateral,
        "head_turn_plus_shock_force_n": total_head_lateral,
        "lateral_retention_margin": lateral_capacity / total_head_lateral,
    }


rows = [turn(v / 10, yaw / 10) for v in range(2, 13, 2) for yaw in range(2, 13, 2)]
with CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    w.writeheader(); w.writerows(rows)

design = turn(p["target_speed_mps"], p["design_yaw_rate_radps"])
vertical = p["head_mass_kg"] * g * p["vertical_shock_g"]
combined = math.hypot(vertical, design["head_turn_plus_shock_force_n"])
combined_sf = p["magnetic_retention_n"] / combined

# Hollow aluminium mast, conservative cantilever with head lateral shock at tip.
do = p["mast_outer_diameter_m"]
di = p["mast_inner_diameter_m"]
I = math.pi * (do**4 - di**4) / 64.0
moment = design["head_turn_plus_shock_force_n"] * p["mast_length_m"]
stress = moment * (do / 2) / I
mast_sf = p["mast_yield_strength_pa"] / stress

# Torque-current and lumped steady thermal estimate at the stage-1 design point.
effective_mass = p["total_mass_kg"] + 2 * p["shell_rotating_mass_kg"] / 3
force = effective_mass * p["target_accel_mps2"] + p["rolling_resistance_coefficient"] * p["total_mass_kg"] * g
torque_each = force * p["drive_wheel_radius_m"] / (p["motor_count"] * p["drive_efficiency"])
current_each = torque_each / p["motor_torque_constant_nm_per_a"]
copper_loss_each = current_each**2 * p["motor_winding_resistance_ohm"]
motor_temp = p["ambient_temperature_c"] + copper_loss_each * p["motor_thermal_resistance_k_per_w"]

design_current = p["motor_count"] * current_each + p["auxiliary_current_a"]
peak_current = p["motor_count"] * p["motor_peak_torque_nm"] / p["motor_torque_constant_nm_per_a"] + p["auxiliary_current_a"]
v_design = p["battery_nominal_open_voltage_v"] - design_current * p["battery_internal_resistance_ohm"]
v_peak = p["battery_nominal_open_voltage_v"] - peak_current * p["battery_internal_resistance_ohm"]
v_peak_low_soc = p["battery_low_open_voltage_v"] - peak_current * p["battery_internal_resistance_ohm"]

hard = {
    "combined_head_retention": combined_sf >= p["required_design_safety_factor"],
    "mast_yield": mast_sf >= p["required_design_safety_factor"],
    "motor_steady_temperature": motor_temp <= p["motor_temperature_limit_c"],
    "battery_design_voltage": v_design >= p["battery_cutoff_loaded_voltage_v"],
    "battery_peak_nominal_soc": v_peak >= p["battery_cutoff_loaded_voltage_v"],
}
constraint = v_peak_low_soc < p["battery_cutoff_loaded_voltage_v"]
status = "PASS WITH DERATING CONSTRAINT" if all(hard.values()) and constraint else "FAIL"

lines = [
    "# BB-8 多体、结构与电热验证（阶段 2）", "",
    f"> **{status}**。解析模型要求：低电量时禁止峰值扭矩；结论仍需实物数据和台架验证。", "",
    "## 转弯与磁头六自由度载荷简化", "",
    f"- 设计点 {p['target_speed_mps']:.1f} m/s、{p['design_yaw_rate_radps']:.1f} rad/s，转弯半径 {design['turn_radius_m']:.2f} m，侧向加速度 {design['lateral_accel_mps2']:.2f} m/s²。",
    f"- 叠加 {p['head_lateral_shock_g']:.1f}g 横向冲击后，头部横向载荷 {design['head_turn_plus_shock_force_n']:.2f} N。",
    f"- 同时考虑 2.5g 垂向冲击，合载荷 {combined:.2f} N；40 N 保持力的合载荷裕量 {combined_sf:.2f}×。",
    f"- 假设横向承载为总保持力的 55%，横向单独裕量 {design['lateral_retention_margin']:.2f}×。", "",
    "## 磁桅杆弯曲", "",
    f"- 300 mm 长、外径 12 mm、内径 8 mm 铝管悬臂；根部弯矩 {moment:.2f} N·m。",
    f"- 最大弯曲应力 {stress/1e6:.1f} MPa；按 276 MPa 屈服强度，静态屈服裕量 {mast_sf:.2f}×。",
    "- 尚未包含焊缝、孔位、接头间隙、疲劳和共振降额。", "",
    "## 电机热估算", "",
    f"- 设计扭矩 {torque_each:.3f} N·m/电机，按 0.12 N·m/A 得 {current_each:.2f} A/电机。",
    f"- 绕组铜耗 {copper_loss_each:.2f} W/电机；集总热阻 7 K/W 时稳态温度约 {motor_temp:.1f} °C，低于 {p['motor_temperature_limit_c']:.0f} °C 假设限值。", "",
    "## 4S 电池压降", "",
    f"- 设计点总电流 {design_current:.2f} A，14.8 V 开路时负载电压 {v_design:.2f} V。",
    f"- 峰值总电流 {peak_current:.1f} A，标称电量负载电压 {v_peak:.2f} V。",
    f"- 若开路电压仅 13.6 V，峰值负载电压降至 **{v_peak_low_soc:.2f} V**，低于 13.2 V 门槛；控制器必须按电池电压降额。", "",
    "## 硬判定", "",
]
for key, value in hard.items():
    lines.append(f"- {'PASS' if value else 'FAIL'} — {key}")
lines += ["", "## 下一步实物替换", "",
          "用实际电机 Kt/电阻/热阻、实测电池内阻、磁保持六方向测力、桅杆材料证书和模态试验替换当前假设。转弯扫描表位于 `engineering/turning_multibody_sweep.csv`。", ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"{status} combined_head_sf={combined_sf:.2f} mast_sf={mast_sf:.2f} motor_temp={motor_temp:.1f}C "
      f"v_peak={v_peak:.2f}V v_peak_low_soc={v_peak_low_soc:.2f}V")
print("REPORT", REPORT); print("SWEEP", CSV)
if not all(hard.values()) or not constraint:
    raise SystemExit(1)
