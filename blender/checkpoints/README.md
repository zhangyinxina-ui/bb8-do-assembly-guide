# BB-8 Blender 中间工程

- `BB8_stage01_before_internal_export_fix.blend`：外观面板升级后、内部机构导出回归修复前。
- `BB8_stage02_panel_detail_internal_preserved.blend`：保留 9 个内部机构对象、可关闭 Blender 后重新打开并导出的检查点。
- `BB8_stage03_buildable_internal_assembly.blend`：25 个内部机构对象，加入电机座、四随动轮、桅杆三角支撑、电池固定与电子托盘。
- `BB8_stage04_IG42_contact_geometry.blend`：27个内部对象，按IG42E-24K候选包络重建电机/轴，并让驱动轮及稳定球外缘真实到达508 mm球壳内表面。
- `BB8_stage05_verified_IG42_mount.blend`：45个内部对象；采用125.2 mm电机总包络、310 mm轮距、PCD35电机面板、键毂和紧固件包络，并通过不重叠/球壳内包络审计。
- `BB8_stage06_serviceable_shell_harness.blend`：70个内部对象；加入494 mm赤道密封圈、8个锁扣、12段动力/编码器线束和4个维护连接器，并验证轮子避让与弯曲半径合同。
- `BB8_stage07_magnetic_head_follower.blend`：88个内部对象；加入6+6磁体阵列、8 mm磁隙和3只24 mm头底滚轮，冻结40 N装机拉力验收线。
- `BB8_stage08_unsaved_gui_20260712_183729.blend`：阶段 9.2 结束时 Blender GUI 中带星号的旧内存态；在打开阶段 9.3 新主工程前无损另存，SHA-256 为 `feae71f106221d76f751a086764a18efb1d146b19a03292d65c5384a449a375f`。
- `BB8_stage13_power_safety_hardware.blend`：阶段13首次落盘；板件在帧1冻结世界坐标，已由v2取代，仅作为失败修正证据保留。
- `BB8_stage13_power_safety_hardware_v2.blend`：板件已正确继承内车俯仰；线束对象原点仍在世界零点，已由v3取代。
- `BB8_stage13_power_safety_hardware_v3.blend`：110个内部对象的最终阶段13检查点；双INA226、双2 mΩ Kelvin分流器、6个M2.5支柱、ALERT→EN硬件门和11条保护线均通过重开审计，SHA-256 为 `244acfb60c706770e6bd03c08c76cb9eb8e049152bcd78e71a8b00bc60fa28e7`。
- `BB8_stage14_mass_cg_ballast.blend`：阶段14质量/质心检查点；新增密封1.50 kg低位配重盒及固定结构、17组质量元数据和2个质心标记。后台重开审计为324个总对象、120个内部对象（118制造+2标记），SHA-256 为 `cadd81c99ee3cea6933704de68c6c07e6935c053d063afd77061d3fb11fc1a87`。
- `BB8_stage15_drive_power_estop.blend`：阶段15驱动电源与硬件急停检查点；新增左右通用驱动器、双散热器、8个M3支柱、主保险丝、常开接触器、双通道常闭急停、安全继电器、维护断电、系留急停插口和12条显式电源/安全线。后台重开审计为354个总对象、150个内部对象（147制造+3工程标记），SHA-256 为 `a53d02ab2ffabf14fb747033de267d623f8a41cfb5c5e5d7c5c019c6768f9435`。

主工程始终位于 `blender/output/BB8_1to1_screen_referenced.blend`。检查点只追加、不覆盖，便于继续设计和对比回退。
