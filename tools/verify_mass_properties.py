#!/usr/bin/env python3
"""Recompute stage-14 mass/COM/inertia results from the exported model input."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

from mass_properties_model import summarize

INPUT = ROOT / "engineering" / "mass_properties_input.json"
RESULTS = ROOT / "engineering" / "mass_properties_results.json"
CSV = ROOT / "engineering" / "mass_properties_scenarios.csv"
REPORT = ROOT / "docs" / "BB8_阶段14_质量质心与惯量验证.md"
REPORT_EN = ROOT / "docs" / "BB8_stage14_mass_cg_inertia_validation.md"

model_input = json.loads(INPUT.read_text(encoding="utf-8"))
results = summarize(model_input)
RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

scenario_rows = []
for name in ("nominal", "minimum_mass", "maximum_mass", "lowest_com", "highest_com"):
    item = results[name]
    scenario_rows.append({
        "scenario": name,
        "total_mass_kg": item["total_mass_kg"],
        "com_x_mm": item["com_m"][0] * 1000,
        "com_y_mm": item["com_m"][1] * 1000,
        "com_z_mm": item["com_m"][2] * 1000,
        "inertia_x_kg_m2": item["inertia_com_kg_m2"][0],
        "inertia_y_kg_m2": item["inertia_com_kg_m2"][1],
        "inertia_z_kg_m2": item["inertia_com_kg_m2"][2],
    })
with CSV.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=scenario_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(scenario_rows)

nominal = results["nominal"]
high = results["highest_com"]
low = results["lowest_com"]
checks = results["checks"]
lines = [
    "# BB-8 阶段 14：质量、质心与惯量验证", "",
    f"> 结论：**{results['status']}**。新增低位密封配重后，当前假设范围内最不利质心仍在球心下方；所有质量仍须分部称重替换。", "",
    "## 模型驱动结果", "",
    f"- 名义总质量：**{nominal['total_mass_kg']:.3f} kg**；输入范围 {results['minimum_mass']['total_mass_kg']:.3f}–{results['maximum_mass']['total_mass_kg']:.3f} kg。",
    f"- 名义质心：x={nominal['com_m'][0]*1000:.1f} mm，y={nominal['com_m'][1]*1000:.1f} mm，z={nominal['com_m'][2]*1000:.1f} mm。",
    f"- 角点穷举质心范围：z={low['com_m'][2]*1000:.1f} 至 {high['com_m'][2]*1000:.1f} mm；最不利下置量 {results['worst_case_com_offset_below_center_m']*1000:.1f} mm。",
    f"- 质心三轴惯量：Ixx={nominal['inertia_com_kg_m2'][0]:.4f}、Iyy={nominal['inertia_com_kg_m2'][1]:.4f}、Izz={nominal['inertia_com_kg_m2'][2]:.4f} kg·m²。",
    f"- 10°回复力矩 {results['restoring_torque_10deg_nm']:.2f} N·m；俯仰小摆周期 {results['pitch_natural_period_s']:.2f} s。", "",
    "## 配重与驱动约束", "",
    "- Blender 新增120 × 70 × 24 mm密封钢配重盒，名义1.50 kg，中央挂板、双束带和4枚M5防松紧固件。",
    f"- 在0.6 N·m连续扭矩、2×裕量和当前质量下，最大设计加速度为 **{results['max_accel_for_2x_continuous_torque_mps2']:.3f} m/s²**；控制目标冻结为0.70 m/s²。",
    f"- 0.70 m/s²等效稳态倾角为 {results['target_equilibrium_lean_deg']:.2f}°；原动画±4°只是示意，不是控制限位。",
    f"- 若仍强求未经证明的球心下110 mm，还需在z=-220 mm附近额外增加约 **{results['additional_ballast_for_legacy_110mm_kg']:.2f} kg**，会进一步降低加速度裕量，因此取消110 mm作为当前设计事实。", "",
    "## 判定", "",
]
for key, value in checks.items():
    lines.append(f"- {'PASS' if value else 'HOLD'} — {key}")
lines += ["", "## 证据边界", "",
          "17个质量组全部标记为`NOT_RUN`或供应商冲突/设计假设。制造前必须逐件称重，并通过悬挂法或四点秤实测整机质心；实测结果须重新生成本报告，不能只接受当前名义值。", ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")

english_lines = [
    "# BB-8 Stage 14: Mass, Centre of Mass and Inertia Validation", "",
    f"> Result: **{results['status']}**. With the sealed low ballast cassette, even the worst enumerated mass corner keeps the centre of mass below the sphere centre. Every assumed mass must still be replaced by a measured value.", "",
    "## Model-driven results", "",
    f"- Nominal total mass: **{nominal['total_mass_kg']:.3f} kg**; input range {results['minimum_mass']['total_mass_kg']:.3f}–{results['maximum_mass']['total_mass_kg']:.3f} kg.",
    f"- Nominal CoM: x={nominal['com_m'][0]*1000:.1f} mm, y={nominal['com_m'][1]*1000:.1f} mm, z={nominal['com_m'][2]*1000:.1f} mm.",
    f"- Exhaustive corner range: z={low['com_m'][2]*1000:.1f} to {high['com_m'][2]*1000:.1f} mm; worst-case offset below centre {results['worst_case_com_offset_below_center_m']*1000:.1f} mm.",
    f"- CoM inertias: Ixx={nominal['inertia_com_kg_m2'][0]:.4f}, Iyy={nominal['inertia_com_kg_m2'][1]:.4f}, Izz={nominal['inertia_com_kg_m2'][2]:.4f} kg·m².",
    f"- Restoring torque at 10°: {results['restoring_torque_10deg_nm']:.2f} N·m; small-angle pitch period: {results['pitch_natural_period_s']:.2f} s.", "",
    "## Ballast and drive constraints", "",
    "- Blender now contains a 120 × 70 × 24 mm sealed steel ballast cassette, nominally 1.50 kg, with a centre hanger, two retention straps and four captive M5 fasteners.",
    f"- With 0.6 N·m continuous torque, a 2× margin and the nominal mass, the acceleration ceiling is **{results['max_accel_for_2x_continuous_torque_mps2']:.3f} m/s²**; the controller target is frozen at 0.70 m/s².",
    f"- The equivalent steady lean at 0.70 m/s² is {results['target_equilibrium_lean_deg']:.2f}°. The ±4° animation is illustrative, not a control limit.",
    f"- Reaching the old unverified 110 mm offset would need about **{results['additional_ballast_for_legacy_110mm_kg']:.2f} kg** more at z=-220 mm and would reduce acceleration headroom, so 110 mm is no longer presented as a design fact.", "",
    "## Checks", "",
]
for key, value in checks.items():
    english_lines.append(f"- {'PASS' if value else 'HOLD'} — {key}")
english_lines += ["", "## Evidence boundary", "",
                  "All 17 mass groups remain `NOT_RUN`, supplier-conflicted, or design assumptions. Before fabrication approval, weigh every component and measure whole-system CoM by suspension or four-scale testing, then regenerate this report from those measurements.", ""]
REPORT_EN.write_text("\n".join(english_lines), encoding="utf-8")

print(f"{results['status']} mass={nominal['total_mass_kg']:.3f}kg com_z={nominal['com_m'][2]*1000:.1f}mm "
      f"worst_z={high['com_m'][2]*1000:.1f}mm max_accel={results['max_accel_for_2x_continuous_torque_mps2']:.3f}m/s2")
print("RESULTS", RESULTS)
print("SCENARIOS", CSV)
print("REPORT", REPORT)
print("REPORT_EN", REPORT_EN)
if not all(checks.values()):
    raise SystemExit(1)
