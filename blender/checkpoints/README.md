# BB-8 Blender 中间工程

- `BB8_stage01_before_internal_export_fix.blend`：外观面板升级后、内部机构导出回归修复前。
- `BB8_stage02_panel_detail_internal_preserved.blend`：保留 9 个内部机构对象、可关闭 Blender 后重新打开并导出的检查点。
- `BB8_stage03_buildable_internal_assembly.blend`：25 个内部机构对象，加入电机座、四随动轮、桅杆三角支撑、电池固定与电子托盘。
- `BB8_stage04_IG42_contact_geometry.blend`：27个内部对象，按IG42E-24K候选包络重建电机/轴，并让驱动轮及稳定球外缘真实到达508 mm球壳内表面。
- `BB8_stage05_verified_IG42_mount.blend`：45个内部对象；采用125.2 mm电机总包络、310 mm轮距、PCD35电机面板、键毂和紧固件包络，并通过不重叠/球壳内包络审计。
- `BB8_stage06_serviceable_shell_harness.blend`：70个内部对象；加入494 mm赤道密封圈、8个锁扣、12段动力/编码器线束和4个维护连接器，并验证轮子避让与弯曲半径合同。
- `BB8_stage07_magnetic_head_follower.blend`：88个内部对象；加入6+6磁体阵列、8 mm磁隙和3只24 mm头底滚轮，冻结40 N装机拉力验收线。
- `BB8_stage08_unsaved_gui_20260712_183729.blend`：阶段 9.2 结束时 Blender GUI 中带星号的旧内存态；在打开阶段 9.3 新主工程前无损另存，SHA-256 为 `feae71f106221d76f751a086764a18efb1d146b19a03292d65c5384a449a375f`。

主工程始终位于 `blender/output/BB8_1to1_screen_referenced.blend`。检查点只追加、不覆盖，便于继续设计和对比回退。
