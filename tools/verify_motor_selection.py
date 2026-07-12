#!/usr/bin/env python3
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "engineering" / "motor_candidates.json").read_text(encoding="utf-8"))
req = data["required"]
rows = []
for motor in data["candidates"]:
    speed = math.pi * req["wheel_diameter_mm"] / 1000 * motor["rated_speed_rpm"] / 60
    torque_sf = motor["rated_torque_nm"] / req["continuous_torque_each_nm"]
    rows.append((motor, speed, torque_sf))

preferred, speed, sf = rows[0]
assert speed >= req["target_ground_speed_mps"]
assert sf >= req["minimum_continuous_safety_factor"]
assert preferred["diameter_mm"] < 2 * 55  # fits 110 mm chassis width envelope

report = ROOT / "docs" / "BB8_真实电机候选与接口决策.md"
lines = [
    "# BB-8 真实电机候选与接口决策（阶段 5）", "",
    "> 未执行采购。以下结论来自厂家当前产品页和当前解析载荷，用于冻结下一版机械接口。", "",
    "## 需求", "",
    f"- 96 mm 驱动轮；每电机连续需求 {req['continuous_torque_each_nm']:.3f} N·m；目标地速 {req['target_ground_speed_mps']:.1f} m/s。",
    f"- 连续扭矩最低设计裕量 {req['minimum_continuous_safety_factor']:.1f}×。", "",
    "## 对比", "",
    "| 候选 | 厂家工作点 | 96 mm轮理论速度 | 连续扭矩裕量 | 判断 |", "|---|---:|---:|---:|---|",
]
for motor, ground_speed, torque_sf in rows:
    decision = "进入阶段5可装配接口" if torque_sf >= 2 else "不作为当前连续工况首选"
    lines.append(f"| {motor['name']} | {motor['rated_speed_rpm']} rpm / {motor['rated_torque_nm']:.3f} N·m | {ground_speed:.2f} m/s | {torque_sf:.2f}× | {decision} |")
lines += ["", "## 首选接口：IG42E-24K", "",
          "- 12 V、248 rpm、额定扭矩0.98 N·m、额定电流5.5 A。",
          "- 厂家关联二维图给出：最大外径45 mm、总包络约125.2 mm、8 × 20 mm输出轴、4×M4×6深/PCD35安装孔。",
          "- 图纸重量360 g，但Cytron当前商品页写609 g；结构质量预算继续按609 g保守取值，采购后称重消除冲突。",
          "- 两电机沿310 mm轮距相向安装，中心保留约19.6 mm检修间隙；原150 mm轮距会发生实体重叠，已废弃。",
          "- Cytron 8 mm键毂为26 × 40 mm、3×M5轮端螺纹；M5孔节圆仍标为待实物/专用图纸确认。",
          "- 4S满电16.8 V高于12 V额定值，因此控制器必须按 `12 V / 实时母线电压` 限制PWM；满电最大占空比71.4%。",
          "", "## 重要差异", "",
          "Pololu 4692体积和编码器分辨率更好，但厂家最大效率点扭矩仅约0.186 N·m，低于当前0.286 N·m需求。即使其失速外推值较高，也不应把失速值当连续额定值。", "",
          "## 尚未冻结", "",
          "编码器尾部连接器、线束弯曲半径、键毂3×M5孔节圆及采购批次公差仍需实物卡尺确认。当前M4电机孔位有厂家图纸依据，M5轮毂孔位仍不可直接下单加工。", ""]
report.write_text("\n".join(lines), encoding="utf-8")
print(f"PASS preferred={preferred['name']} speed={speed:.2f}m/s torque_sf={sf:.2f} pwm_full_4s={12/16.8:.3f}")
print("REPORT", report)
