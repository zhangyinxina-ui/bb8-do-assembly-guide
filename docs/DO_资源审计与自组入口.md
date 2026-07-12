# D-O 资源审计与自组入口

## 已落地的本地资源

- Printed Droid 控制仓库：`third_party/D-O-Printed-Droid`
- 固定提交：`e90aacdbe26a62fd4f0229d5504a3f2f3c409055`
- 当前推荐固件：`D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino`
- 目标控制器：Arduino Mega 2560
- 装配 PDF：`third_party/DO-Instructions-Pt1.1.pdf`
- 接线 PDF：`third_party/DOV2-Wiring-diagram-notes.pdf`
- 无轮调试支架：`third_party/DO-Stand-60mm.stl`（非整机结构件，许可未明确，不对外再打包）
- 机器可读清单：`engineering/do_resource_manifest.json`
- 固件编译证据：`engineering/do_firmware_compile.json`
- 24 项采购门控 BOM：`engineering/do_self_build_bom.csv`
- D01–D16 自组路线：`docs/DO_自组采购与调试路线.md`

运行 `python3 tools/audit_do_resources.py` 可重新核验提交、固件、许可证位置、机械文件缺口和 PDF 哈希。运行 `tools/fetch_do_public_resources.sh` 可重新获取公开资料；脚本不会购买、抓取或绕过 Patreon 付费资源，也不会自动切换仓库提交。

## 固件编译门

`tools/compile_do_firmware.sh` 已在项目隔离的 Arduino 环境中，以 `arduino:avr:mega` 编译 v3.4.3 成功。工具链为 Arduino CLI 1.5.1、AVR core 1.8.8、IBusBM 1.1.4、DFRobotDFPlayerMini 1.0.6、Servo 1.3.0。结果为 Flash 43,198 / 253,952 B（17%），全局 RAM 1,516 / 8,192 B（18%）。这证明源码可编译，不等于真机平衡、接线或安全验收通过。

## 许可证结论

仓库根目录没有统一 `LICENSE` 文件，但 v1.1、v2.1、v3.4 三个版本 README 内都包含相同的自定义 `NON-COMMERCIAL LICENSE`：允许个人非商业使用、复制、修改和分发，同时要求保留声明、署名，并禁止商业用途。

所以准确说法是“公开源码，受自定义个人非商业许可约束”，不是“完全无许可”，也不是 OSI 定义的开源软件。旧版 Mega 与 Nano 目录没有同样清楚的内嵌条款，优先使用 v3.4.3，并随衍生副本保留 v3.4 README。

## 能直接开始的部分

1. 按 Printed Droid 装配 PDF 和 Dozuki 五章指南理解机械装配顺序。
2. 按接线 PDF 准备 Arduino Mega 2560、Cytron MDD10A、MPU6050、遥控接收机、舵机和 DFPlayer Mini。
3. 安装 `IBusBM` 与 `DFRobotDFPlayerMini`；`Servo`、`EEPROM`、`SoftwareSerial`、`Wire` 和 `avr/wdt` 由 AVR 工具链提供。
4. 先在无负载台架上检查急停、方向、限幅和失控保护，再连接执行器。

公开说明存在必须先解决的硬件冲突：仓库根 README 写一块 Cytron MDD10A 双路驱动，v3.4 README 写两块 MD10C。驱动电机、减速比、四个舵机负载和真实峰值电流也未冻结。因此采购表把这些项标为 HOLD，而不是把来源中的示例值冒充最终选型。

## 尚不能凭公开资源完成的部分

- 该 GitHub 仓库中机械 CAD/STL/STEP/Fusion 文件数量为 **0**。
- Printed Droid 控制板页面另有一个公开下载的 60 mm 无轮调试支架 STL，但没有明确再分发许可，也不能替代整机机械模型。
- Mr Baddeley D-O V2 STL/Fusion 属 Patreon 付费资源；购买和接受其使用条款需要用户明确确认。
- 未找到 Matt Denton / Mantis Hacks 改版 CAD 与控制程序的官方公开下载许可证。
- Printed Droid 控制与供电板仓库中没有可验证的 KiCad/Gerber 源文件。

因此，本阶段已经把合法可用的控制与装配资料拉到本地并可重复审计，但“完整可打印 D-O 机械包”仍处于付费授权门后，不能宣称已完成整机开源包。
