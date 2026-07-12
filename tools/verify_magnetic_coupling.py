#!/usr/bin/env python3
"""Freeze BB-8 head-coupling geometry and derive the physical acceptance gate.

This intentionally does not estimate neodymium pull force from catalog surface
ratings. Force across a curved shell and an 8 mm assembled gap must be measured.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "engineering" / "magnetic_coupling.json"
REPORT = ROOT / "docs" / "BB8_磁性头部耦合验证.md"

p = json.loads(INPUT.read_text(encoding="utf-8"))
vertical_n = p["head_mass_kg"] * p["gravity_mps2"] * p["vertical_shock_g"]
lateral_n = p["head_mass_kg"] * p["gravity_mps2"] * p["lateral_shock_g"]
combined_n = math.hypot(vertical_n, lateral_n)
gate_n = combined_n * p["required_safety_factor"]
design_gate_n = p["design_measured_pull_force_gate_n"]

assert p["chassis_magnet_count"] == p["head_magnet_count"] == 6
assert p["head_roller_count"] == 3
assert p["face_gap_mm"] <= 8.0
assert design_gate_n >= gate_n

lines = [
    "# BB-8 磁性头部耦合验证（阶段 7）",
    "",
    "> 结论：几何与实测验收门槛已冻结；磁体牌号和实际保持力尚未实测，因此不能声明磁耦合已经通过实物验证。",
    "",
    "## Blender 几何合同",
    "",
    f"- 内车侧/头部侧各 {p['chassis_magnet_count']} 个 Ø{p['magnet_envelope_diameter_mm']:.0f} × {p['magnet_envelope_thickness_mm']:.0f} mm 磁体包络。",
    f"- 两阵列磁体面对面设计气隙 {p['face_gap_mm']:.1f} mm，包含球壳、涂层、结构间隙和滚轮压缩误差。",
    f"- 头底 {p['head_roller_count']} 只 Ø{p['head_roller_diameter_mm']:.0f} mm 非染色滚轮，三点接触508 mm球壳外表面。",
    "- 阵列极性仅定义为交替且装配前逐对确认吸引；未冻结磁体等级、镀层和胶粘剂。",
    "",
    "## 载荷与测力门槛",
    "",
    f"- 头部质量假设 {p['head_mass_kg']:.2f} kg。",
    f"- {p['vertical_shock_g']:.1f}g垂向载荷 {vertical_n:.2f} N；{p['lateral_shock_g']:.1f}g横向载荷 {lateral_n:.2f} N。",
    f"- 合成载荷 {combined_n:.2f} N；按 {p['required_safety_factor']:.1f}×安全系数，最低实测保持力 {gate_n:.2f} N。",
    f"- 工程验收值上调为 {design_gate_n:.1f} N；必须在实际球壳、实际8 mm总气隙和最不利姿态下测得。",
    "",
    "## 必做实物试验",
    "",
    "1. 使用非磁拉力计夹具，在顶置、侧置和45°姿态缓慢拉脱，各做5次。",
    "2. 每个姿态的最低值必须不小于40 N；记录壳厚、气隙、温度和磁体批次。",
    "3. 以泡沫假头完成2.5g等效冲击，再检查滚轮、胶层、磁体封装和头部脱落。",
    "4. 磁体必须完全机械封装；胶粘剂不得作为唯一防飞出措施。",
    "5. 夹具、拆卸工具和操作区域必须标明强磁夹伤及植入式医疗器械风险。",
]
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"PASS GEOMETRY / MEASUREMENT REQUIRED combined={combined_n:.2f}N "
      f"minimum={gate_n:.2f}N acceptance={design_gate_n:.1f}N gap={p['face_gap_mm']:.1f}mm")
print("REPORT", REPORT)
