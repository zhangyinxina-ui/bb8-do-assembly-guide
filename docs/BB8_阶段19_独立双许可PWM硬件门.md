# BB-8 阶段19：独立双许可 PWM 硬件门原理图/ERC门

> 结论：**64组布尔组合、输入电流、逻辑电平、功耗降额和50 × 35 × 15 mm机械包络的解析检查全部通过；确定性生成的KiCad 10正式原理图现为0项ERC违规，34个器件引用、91条规范引脚连接和21个网络也完成交叉审计。但独立同行复核、PCB/DRC、Gerber、实装板和示波器证据仍缺失，整体状态必须保持 `HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED`。**

## 为什么必须新增这一阶段

阶段17确认MDD20A只有PWM+DIR，没有独立EN，而且PWM低的官方行为是制动，不是电气隔离。阶段18只在电源舱里保留了50 × 35 × 15 mm门板空间，没有发布电路。阶段19把这个空白收敛为可机器审计的正式原理图/ERC参考设计，同时保留安全继电器和常开SW60接触器作为真正的母线去能路径。

## 三条独立许可链

左右两路都执行同一个公式：

`PWM_OUT = LOGIC_POWER_OK ∧ PWM_IN ∧ SAFE_A_OK ∧ SAFE_B_OK ∧ ALERT_N`

| 级 | 器件 | 功能 | 失效目标 |
| --- | --- | --- | --- |
| 输入A/B | 2 × Vishay VO617A-4 | 把12.0–16.8 V“上电才允许运行”回路隔离成3.3 V许可 | 任一路断线或撤电，许可拉低 |
| 许可A | TI SN74LVC2G08 U3 | 左右PWM分别与`SAFE_A_OK`相与 | A路单独可阻断两路PWM |
| 许可B | TI SN74LVC2G08 U4 | U3输出分别与`SAFE_B_OK`相与 | B路单独可阻断两路PWM |
| 电流告警 | TI SN74LVC2G08 U5 | U4输出分别与双INA226开漏`ALERT_N`相与 | 任一硬件ALERT可直接阻断两路PWM |
| 母线去能 | 安全继电器 + 常开接触器 | 与门板并行撤销电机母线 | PWM低不能替代这一层 |

`DIR_L/R`只是直通信号，不属于安全链；因此本设计只允许MDD20A的sign-magnitude模式。

## 厂商数据与解析点

- [TI SN74LVC2G08数据表](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf)：3.0–3.6 V时`VIH ≥ 2.0 V`、`VIL ≤ 0.8 V`；-40–125 °C、3.3 V ±0.3 V时单级传播延迟最大5.3 ns；`Ioff`支持掉电防回灌。
- [Vishay VO617A数据表](https://www.vishay.com/docs/83430/vo617a.pdf)：VO617A-4在`IF=5 mA、VCE=5 V、25 °C`时CTR为160–320%；`IF=5 mA、IC=1 mA`时`VCE(sat)`最大0.4 V。25 µs饱和关断只是典型值，不能当作最坏值。
- [Cytron MDD20A产品页](https://sg.cytron.io/p-20amp-6v-30v-dc-motor-driver-2-channels)：输入兼容1.8/3.3/5/12 V逻辑，PWM最高20 kHz。
- [JST XH官方目录](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)：2.5 mm间距；标准顶部型安装高度9.8 mm，配AWG22时额定3 A。

在12.0 V、采用数据表1.65 V正向压降上界时，2.00 kΩ输入电阻提供5.175 mA，达到CTR的5 mA测试点；在16.8 V和1.0 V压降时为7.900 mA。最坏电阻功耗0.12482 W，0.5 W器件有4.006×降额。光耦发射极输出按0.4 V饱和上界仍为2.9 V，高于LVC的2.0 V高电平门槛；4.7 kΩ下拉负载约0.617 mA，低于数据表1 mA饱和测试电流。

三片LVC级联的数字逻辑传播上界为15.9 ns，但光耦只有典型关断值，因此**20 ms总去能合同仍只能通过示波器实测证明**。

## 机械与制造边界

- PCB预设为50 × 35 × 1.6 mm、四个Ø3.2 mm孔；JST XH最高9.8 mm，PCB加器件高11.4 mm。再计入3.0 mm绝缘安装柱后总安装高14.4 mm，阶段18的15 mm空间实际只余0.6 mm，必须用实物复核。
- OpenSCAD源文件只表达板框、孔和器件包络，不含焊盘、铜箔、阻焊、丝印、爬电距离或线束弯曲半径。本机OpenSCAD 2021.01无头导出未在限定时间内完成，因此本阶段不声称已有STL。
- Blender 中的23个板件/器件包络标为 `non_fabrication_reference`：它们可以进入带属性的GLB和内部三视图用于设计复核，但必须从150件制造清单及内部机构STL排除，不能伪装成可打印零件。
- 这23个参考包络已写入唯一主工程并完成关闭后重开审计。Blender 5.1.2确认386个总对象、182个内部对象、150个制造对象、9个工程标记和23个阶段19参考对象；主文件SHA-256为 `ecd9a8b02db7c0b253c06005aaf16e7a8bf10147f8adec9c8900415e18b38af4`。150行制造清单、内部机构STL、动画GLB和内部正/侧/俯三视图均已重导出。
- 正式`.kicad_sch`已可确定性生成，KiCad 10.0.4报告0项ERC违规；KiCad XML导出与34个器件引用、91条规范引脚连接和21个网络全部一致。但当前仍没有`.kicad_pcb`、DRC、Gerber、钻孔文件或独立原理图同行复核；任何PCB厂家下单都不被本阶段授权。

## 已发布证据

- [机器合同](../engineering/stage19_dual_permissive_gate_contract.json)
- [64行真值表](../engineering/stage19_gate_truth_table.csv)
- [预选BOM](../engineering/stage19_gate_bom.csv)
- [引脚网表](../engineering/stage19_gate_netlist.csv)
- [当前HOLD结果](../engineering/stage19_dual_permissive_gate_results.json)
- [Blender重开审计与导出哈希](../engineering/stage19_blender_reopen_audit.json)
- [验证器](../tools/verify_dual_permissive_gate.py)
- [KiCad正式原理图](../hardware/stage19_dual_permissive_gate/stage19_dual_permissive_gate.kicad_sch)
- [KiCad ERC报告](../engineering/stage19_kicad_erc.json)
- [KiCad连接导出](../engineering/stage19_kicad_netlist.xml)
- [KiCad原理图验证结果](../engineering/stage19_kicad_verification.json)
- [KiCad原理图PDF](../output/pdf/BB8_stage19_dual_permissive_gate_schematic.pdf)
- [KiCad验证器](../tools/verify_stage19_kicad.py)
- [硬件包说明](../hardware/stage19_dual_permissive_gate/README.md)

## 下一道不可跳过的门

1. 对已捕获的KiCad原理图及安全假设做独立同行复核；
2. 布板后检查隔离区、安装孔、丝印极性、测试点、线束出口并通过DRC；
3. 人工检查Gerber/钻孔后才允许制造；
4. 分别在12.0 V与16.8 V测A/B输入电流、输出高低电平和温升；
5. 对A断开、B断开、ALERT拉低、3.3 V掉电、MCU PWM卡高逐项抓示波器波形；
6. 证明两路PWM均在20 ms内拉低，再与安全继电器和接触器组合完成E02；
7. 完成20 kHz、温度、振动、连接器保持力与EMC试验。

实物状态：`NOT_RUN`；安全认证：`NONE`；制造发布：`NOT_RELEASED_NO_PCB_OR_GERBER`。
