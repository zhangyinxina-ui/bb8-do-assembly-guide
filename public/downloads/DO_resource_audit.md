# D-O 资源审计与自组入口

## 已落地的本地资源

- Printed Droid 控制仓库：`third_party/D-O-Printed-Droid`
- 固定提交：`e90aacdbe26a62fd4f0229d5504a3f2f3c409055`
- 当前推荐固件：`D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino`
- 目标控制器：Arduino Mega 2560
- 装配 PDF：`third_party/DO-Instructions-Pt1.1.pdf`
- 接线 PDF：`third_party/DOV2-Wiring-diagram-notes.pdf`
- 无轮调试支架：`third_party/DO-Stand-60mm.stl`（非整机结构件，许可未明确，不对外再打包）
- 官方控制板页面的 12 个公开附件：`third_party/do_public_resources/`（本机核验副本，Git 忽略）
- AIO32 v2.1 公开附件：23 个成员，其中 22 个源码文件和 1 个 README；未发现 KiCad/Gerber 或包级 LICENSE
- 机器可读清单：`engineering/do_resource_manifest.json`
- Mantis 六条视频描述审计：`engineering/do_mantis_video_audit.json`
- 固件编译证据：`engineering/do_firmware_compile.json`
- AIO32 编译证据：`engineering/do_aio32_firmware_compile.json`
- 26 项采购门控 BOM：`engineering/do_self_build_bom.csv`
- D01–D16 自组路线：`docs/DO_自组采购与调试路线.md`

运行 `python3 tools/audit_do_resources.py` 可重新核验提交、固件、许可证位置、机械文件缺口、12 个官网附件及其 SHA-256。运行 `python3 tools/audit_do_mantis_videos.py` 只读取六条公开视频元数据与描述链接，不下载视频。运行 `tools/fetch_do_public_resources.sh` 可重新获取公开资料；脚本不会购买、抓取或绕过 Patreon 付费资源，也不会自动切换仓库提交。官网附件只保存在 Git 忽略目录：公开可下载不等于允许本仓库再分发。

## 固件编译门

`tools/compile_do_firmware.sh` 已在项目隔离的 Arduino 环境中，以 `arduino:avr:mega` 编译 v3.4.3 成功。工具链为 Arduino CLI 1.5.1、AVR core 1.8.8、IBusBM 1.1.4、DFRobotDFPlayerMini 1.0.6、Servo 1.3.0。结果为 Flash 43,198 / 253,952 B（17%），全局 RAM 1,516 / 8,192 B（18%）。这证明源码可编译，不等于真机平衡、接线或安全验收通过。

`tools/compile_do_aio32_firmware.sh` 也已从官网原始 ZIP 的固定 SHA-256 重建临时草图，并以 `esp32:esp32@3.3.7`、Adafruit Feather ESP32-S3 TFT 目标编译成功：Flash 549,831 / 1,310,720 B（41%），全局 RAM 49,652 / 327,680 B（15%）。首次编译暴露手册依赖表遗漏 `SensorLib`（缺少 `SensorQMI8658.hpp`）；补装官方 Library Manager 的 SensorLib 0.4.1 后通过。此结果只解除“源码能否编译”的疑问，不解除包级 LICENSE、KiCad/Gerber、实物接线、运动与安全 HOLD。

## 许可证结论

仓库根目录没有统一 `LICENSE` 文件，但 v1.1、v2.1、v3.4 三个版本 README 内都包含相同的自定义 `NON-COMMERCIAL LICENSE`：允许个人非商业使用、复制、修改和分发，同时要求保留声明、署名，并禁止商业用途。

所以准确说法是“公开源码，受自定义个人非商业许可约束”，不是“完全无许可”，也不是 OSI 定义的开源软件。旧版 Mega 与 Nano 目录没有同样清楚的内嵌条款，优先使用 v3.4.3，并随衍生副本保留 v3.4 README。

## 能直接开始的部分

1. 按 Printed Droid 装配 PDF 和 Dozuki 五章指南理解机械装配顺序。
2. 按接线 PDF 准备 Arduino Mega 2560、Cytron MDD10A、MPU6050、遥控接收机、舵机和 DFPlayer Mini。
3. 安装 `IBusBM` 与 `DFRobotDFPlayerMini`；`Servo`、`EEPROM`、`SoftwareSerial`、`Wire` 和 `avr/wdt` 由 AVR 工具链提供。
4. 先在无负载台架上检查急停、方向、限幅和失控保护，再连接执行器。

公开说明存在必须先解决的硬件冲突：仓库根 README 写一块 Cytron MDD10A 双路驱动，v3.4 README 写两块 MD10C。驱动电机、减速比、四个舵机负载和真实峰值电流也未冻结。因此采购表把这些项标为 HOLD，而不是把来源中的示例值冒充最终选型。

源码还存在第二个硬件冲突门。v3.4.3 把 `MAINBAR_SERVO_PIN` 和 `HEAD1_SERVO_PIN` 分别固定为 D0、D1，并实际调用四路 `Servo.attach()`；同一草图又执行 `Serial.begin(9600)`，把 USB 配置菜单放在 Serial0。Arduino Mega 2560 官方映射中 D0 是 RX0、D1 是 TX0，因此这两路舵机与上传/配置串口复用了同一对物理引脚。当前状态是 `HOLD_BENCH_VERIFICATION`：首轮 USB 烧录与配置时不得连接 D0/D1 舵机信号；最终必须改到非 UART 引脚，或给出经台架验证的隔离/复用电路，并用示波器或逻辑分析仪同时证明舵机脉宽和串口收发完整。

官网还存在两个版本化入口冲突。控制板页面内嵌的 **v2.1** 接线表把四个舵机写成 D2/D3/D4/D5，而固定的 **v3.4.3** 源码与当前 GitHub README 使用 D0/D1/D5/D6；页面名为 `D-O_ibus_v3.4.zip` 的附件内部版本头仍是 **3.4.0**，不是固定仓库中的 3.4.3。项目因此新增 `DO-SRC-002 / HOLD_VERSIONED_WIRING_REQUIRED` 和 `DO-SRC-003 / USE_PINNED_GITHUB_V3_4_3`：线束必须由实际编译源码常量生成，并把文件名、提交、SHA-256 与接线图绑定；网页 ZIP 只作历史参考。

AIO32 v2.1 是另一条实验性 ESP32-S3 控制路线，不是当前 Mega 基线的无条件替代。其公开 ZIP 有 22 个源码文件，部分文件出现 Apache 2.0 标记，但压缩包没有统一 LICENSE；随附手册声称源码和硬件 KiCad 在共享 GitHub 仓库，而 2026-07-13 固定的唯一 `main` 分支及该 ZIP 中都没有 AIO32 KiCad/Gerber。故整体许可与硬件可制造性保持 `HOLD_PACKAGE_LICENSE_AND_HARDWARE_CAD_NOT_FOUND`，不能因为个别文件头或手册一句话就把整包称为开放硬件。

## 尚不能凭公开资源完成的部分

- 该 GitHub 仓库中机械 CAD/STL/STEP/Fusion 文件数量为 **0**。
- Printed Droid 控制板页面另有一个公开下载的 60 mm 无轮调试支架 STL，但没有明确再分发许可，也不能替代整机机械模型。
- Mr Baddeley D-O V2 STL/Fusion 属 Patreon 付费资源；购买和接受其使用条款需要用户明确确认。
- Mantis 播放列表实际为5集编号构建视频加1个轮胎打印视频；六条公开描述没有 Matt 改版 CAD/控制程序的直接下载链接或许可证。#4 说明基础 CAD 由 Michael Baddeley 直接发给 Matt，而不是在视频描述中公开发布。
- Printed Droid 控制与供电板仓库及核验过的 AIO32 公开附件中都没有可验证的 KiCad/Gerber 源文件；这与 AIO32 手册的仓库声明不一致，需等待上游发布位置澄清。

官方 Mega 2560 串口引脚参考：https://docs.arduino.cc/language-reference/en/functions/communication/serial/

因此，本阶段已经把合法可用的控制与装配资料拉到本地并可重复审计，但“完整可打印 D-O 机械包”仍处于付费授权门后，不能宣称已完成整机开源包。
