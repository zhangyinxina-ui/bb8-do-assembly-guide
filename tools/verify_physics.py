#!/usr/bin/env python3
"""Parametric first-principles checks for the BB-8 replica concept.

This is a design-screening model, not physical certification. Inputs are kept
outside the code so measured hardware values can replace assumptions later.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "engineering" / "physics_inputs.json"
OUT_CSV = ROOT / "engineering" / "physics_sweep.csv"
OUT_MD = ROOT / "docs" / "BB8_机械动力学物理验证.md"

p = json.loads(INPUT.read_text(encoding="utf-8"))
g = 9.80665
R = p["body_radius_m"]
rw = p["drive_wheel_radius_m"]
m = p["total_mass_kg"]
ms = p["shell_rotating_mass_kg"]
eta = p["drive_efficiency"]
n = p["motor_count"]


def evaluate(accel: float) -> dict[str, float]:
    # Thin spherical shell I=2/3*mR^2; rolling adds I/R^2=2/3*m_shell.
    effective_mass = m + (2.0 / 3.0) * ms
    rolling_force = p["rolling_resistance_coefficient"] * m * g
    required_force = effective_mass * accel + rolling_force
    motor_torque = required_force * rw / (n * eta)
    traction_capacity = n * p["wheel_shell_friction_coefficient"] * p["normal_preload_per_wheel_n"]
    lean_deg = math.degrees(math.atan2(accel, g))
    return {
        "accel_mps2": accel,
        "required_force_n": required_force,
        "motor_torque_each_nm": motor_torque,
        "traction_margin": traction_capacity / required_force,
        "pendulum_lean_deg": lean_deg,
    }


rows = [evaluate(i / 10) for i in range(0, 21)]
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    w.writeheader(); w.writerows(rows)

design = evaluate(p["target_accel_mps2"])
sf = p["required_design_safety_factor"]
torque_sf = p["motor_continuous_torque_nm"] / design["motor_torque_each_nm"]
peak_sf = p["motor_peak_torque_nm"] / design["motor_torque_each_nm"]
traction_sf = design["traction_margin"]
power_total = design["required_force_n"] * p["target_speed_mps"] / eta
head_dynamic_load = p["head_mass_kg"] * g * p["vertical_shock_g"]
magnetic_sf = p["magnetic_retention_n"] / head_dynamic_load
static_righting_torque_10deg = m * g * p["com_offset_below_center_m"] * math.sin(math.radians(10))

checks = {
    "continuous_motor_torque": torque_sf >= sf,
    "peak_motor_torque": peak_sf >= sf,
    "wheel_shell_traction": traction_sf >= sf,
    "magnetic_head_retention": magnetic_sf >= sf,
}

status = "PASS" if all(checks.values()) else "FAIL"
lines = [
    "# BB-8 机械、动力学与物理学验证（阶段 1：解析模型）",
    "",
    f"> 结果：**{status}（仅针对当前假设参数）**。这不是实物认证；所有输入都必须由称重、测力、编码器和电流数据替换后重跑。",
    "",
    "## 可追溯输入",
    "",
    f"输入文件：`engineering/physics_inputs.json`。状态：{p['status']}。",
    "",
    "## 设计点结果",
    "",
    f"- 总质量 {m:.2f} kg，目标速度 {p['target_speed_mps']:.2f} m/s，目标加速度 {p['target_accel_mps2']:.2f} m/s²。",
    f"- 含球壳转动惯量后的等效质量 {m + 2*ms/3:.2f} kg；总推进力 {design['required_force_n']:.2f} N。",
    f"- 每台电机轮端需求 {design['motor_torque_each_nm']:.3f} N·m；0.6 N·m 连续额定裕量 {torque_sf:.2f}×，1.2 N·m 峰值裕量 {peak_sf:.2f}×。",
    f"- 轮/壳最大静摩擦力 {n*p['wheel_shell_friction_coefficient']*p['normal_preload_per_wheel_n']:.1f} N；附着裕量 {traction_sf:.2f}×。",
    f"- 设计点机械/电气输入功率估算 {power_total:.1f} W（未含控制器、待机和冲击峰值）。",
    f"- 等效摆体稳态倾角 {design['pendulum_lean_deg']:.2f}°；阶段14质量账本给出的名义重心下置 {p['com_offset_below_center_m']*1000:.1f} mm，10°回复力矩 {static_righting_torque_10deg:.2f} N·m。",
    f"- 头部按 {p['vertical_shock_g']:.1f}g 冲击载荷 {head_dynamic_load:.1f} N；40 N 磁保持裕量 {magnetic_sf:.2f}×。",
    "",
    "## 判定",
    "",
]
for key, ok in checks.items():
    lines.append(f"- {'PASS' if ok else 'FAIL'} — {key}")
lines += [
    "",
    "## 模型覆盖范围与缺口",
    "",
    "已覆盖：纯滚动运动学、球壳转动惯量、滚阻、双轮扭矩、轮壳附着、摆体倾角/回复力矩、头部垂向冲击磁保持。",
    "",
    "尚未证明：壳体接触有限元、结构疲劳、齿轮热平衡、电池瞬态压降、真实地面滑移、侧向转弯耦合、磁头六自由度稳定性。上述项目必须通过实物参数、台架试验和必要的 FEA/多体动力学继续验证。",
    "",
    "## 下一阶段实测门槛",
    "",
    "1. 对阶段14的17个质量组逐件称重并测量整机重心；替换当前8.463 kg与56.2 mm模型值。",
    "2. 用拉力计测轮壳静摩擦和弹簧预紧；更新 μ 与每轮法向力。",
    "3. 用扭矩/电流曲线替换 0.6/1.2 N·m 假设，并完成 10 分钟热稳态试验。",
    "4. 用测力计测磁头脱离力；至少在全姿态达到目标冲击载荷的 2×。",
    "5. 轮子架空后再低速落地，记录编码器、IMU、电流、温度和急停响应。",
]
OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"{status} force={design['required_force_n']:.2f}N torque_each={design['motor_torque_each_nm']:.3f}Nm "
      f"torque_sf={torque_sf:.2f} traction_sf={traction_sf:.2f} magnetic_sf={magnetic_sf:.2f}")
print("REPORT", OUT_MD)
print("SWEEP", OUT_CSV)
if not all(checks.values()):
    raise SystemExit(1)
