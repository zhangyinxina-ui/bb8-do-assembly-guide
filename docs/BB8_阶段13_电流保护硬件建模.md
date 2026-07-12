# BB-8 阶段 13：电流保护硬件建模与重开审计

> 结论：**双 INA226、双 2 mΩ 四线分流器、开漏 ALERT 汇接和独立驱动 EN 门已落实为 Blender 内部安装包络，并通过关闭后重新打开审计；真实板卡接线、脉冲额定、堵转和热试验仍为 `NOT_RUN`。**

## 新增的 22 个内部对象

| 对象组 | 数量 | 建模包络/合同 |
|---|---:|---|
| INA226 电流监测板 | 2 | 34 × 22 × 1.6 mm；地址 `0x40` / `0x41` |
| Kelvin 分流器 | 2 | 12 × 5 × 3 mm；2 mΩ、四线采样 |
| M2.5 可拆支柱 | 6 | 3 mm 安装高度；两监测板各2个，门板2个 |
| ALERT→EN 硬件门板 | 1 | 28 × 14 × 1.6 mm；MCU 停止执行时仍须能拉低双驱动 EN |
| 受监测高侧电源线 | 4 | 左右支路各输入/输出1条；最小弯曲半径30 mm |
| Kelvin 采样线 | 4 | 左右分流器各正/负1条；不可与大电流压降共用测量点 |
| 开漏 ALERT 线 | 2 | 左右 INA226 线与后汇接到硬件门 |
| 独立驱动 EN 线 | 1 | 失效低电平同时关闭两路驱动 |

这些对象安装在现有 104 × 80 × 12 mm 电子托盘上，板底与托盘顶面保持 3 mm 支柱间隙，并继承内车 `-4° → +4°` 俯仰动画。模型对象带有 `physical_test_status=NOT_RUN`，防止把几何布置误写成实物验证。

## 重开审计门

`blender/audit_bb8.py` 现在同时检查：

- 内部对象不少于110件，总对象保持314件；
- 两块 INA226 地址恰为 `0x40` / `0x41`；
- 两个分流器均为2 mΩ、四线连接，并保留脉冲额定实测门；
- 11条保护线的种类和数量固定为输入2、输出2、Kelvin 4、ALERT 2、EN 1；
- 三块电路板都落在电子托盘占地范围内，板底间隙为3 mm；
- 场景级实体试验状态必须保持 `NOT_RUN`；
- 原有508/295/670 mm、6个主面板、8个角区、驱动/磁头/线束和球壳包络门继续通过。

重开结果：

```text
PASS reopenable_blend engineering_stage=13 objects=314 internal=110 panels=6 triangles=8 rings=3/2/1 body=508mm head=295mm height=670mm
```

## 可追溯输出

- 主工程：`blender/output/BB8_1to1_screen_referenced.blend`
  - SHA-256：`5653ae72b029a4c770382bb6525e142e55fed60b0225811d9fb1149bd0434eac`
- 最终检查点：`blender/checkpoints/BB8_stage13_power_safety_hardware_v3.blend`
  - SHA-256：`244acfb60c706770e6bd03c08c76cb9eb8e049152bcd78e71a8b00bc60fa28e7`
- 内部机构 STL：`blender/exports/BB8_internal_mechanism_mm.stl`
  - SHA-256：`4427cc7410c61d39281e6c22748d0ca548c1616383fa8e3295839d79f5b226e4`
- 动画 GLB：`blender/exports/BB8_1to1_kinematic.glb`
  - SHA-256：`1585a883fb4cd93ae3380fb1d2773486e598ddf5707e7d9f7e959b1dcdc73de1`
- 自动装配清单：`engineering/internal_assembly_manifest.csv`，共110行对象记录。

## 下一道实体门

只有拿到真实 INA226 模块、2 mΩ 分流器、驱动器、电机、电池和线束后，才可执行：四线焊点核验、零点/量程标定、ALERT 断 MCU 试验、分流器脉冲温升、保险丝配合、架空堵转和封壳热平衡。未完成这些项目时，不得把本阶段标记为“硬件保护验证通过”。
