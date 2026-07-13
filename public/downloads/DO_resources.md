# D-O 合法自组资源索引

## 先说结论

截至 2026-07-13，未找到“完整、免费、附明确开源许可证”的 D-O 整机 CAD + PCB + 固件包。当前可执行路线是：

1. 通过 Mr Baddeley Patreon 合法获得 V2 机械文件；
2. 使用 Printed Droid / Dozuki 的免费装配与接线文档；
3. 使用 PrintedDroid v3.4.3 控制源码，并遵守 README 内嵌的个人非商业许可；
4. 将 Mantis Hacks 当作升级设计和 BOM 参考，不宣称获得了 Matt Denton 的 CAD/代码。

## 资源矩阵

| 资源 | 内容 | 可得性 | 许可/边界 |
|---|---|---|---|
| Mr Baddeley D-O V2 | STL / Fusion 机械设计 | Patreon 会员 | 付费不等于开源；按创作者条款个人使用 |
| Printed Droid D-O | BOM、控制板、说明文档 | 公开网页 | 文档页未见统一开放硬件许可 |
| D-O-Printed-Droid GitHub | Arduino C++、v1–v3.4.3 | 源码公开 | 根目录无 LICENSE；v1.1/v2.1/v3.4 README 有自定义个人非商业许可，不属于 OSI 开源 |
| Printed Droid 官网 12 个附件 | Mega/AIO32 固件、英德手册、旧接线页、60 mm 支架 | 公开下载，本机已哈希固定 | 只作本机个人参考；未见覆盖全部附件的统一再分发许可 |
| AIO32 v2.1 ZIP | ESP32-S3 实验固件，22 个源码文件；已在隔离工具链编译通过 | 公开下载 | 无包级 LICENSE；只有部分文件有 Apache 标记；无 KiCad/Gerber，整体不能称为 OSI 开源或开放硬件 |
| Dozuki D-O Assembly | 五章装配指南 | 免费阅读 | 机械打印件仍指向 Patreon |
| Mantis Hacks #1–#5 + 轮胎视频 | 设计演进、电子、轮胎、BOM | 6个公开视频条目 | 六条公开描述未给出 Matt 改版 CAD/程序下载及许可 |
| DO Stand 60mm | 无轮通电测试支架 STL | 公开下载 | 非整机结构件；未附明确再分发许可 |

## 直接链接

- D-O 总页：https://www.printed-droid.com/kb/d-o/
- 28 页装配 PDF：https://www.printed-droid.com/wp-content/uploads/2022/07/DO-Instructions-Pt1.1.pdf
- V2 接线 PDF：https://www.printed-droid.com/wp-content/uploads/2022/07/DOV2-Wiring-diagram-notes.pdf
- Dozuki 装配：https://d-o.dozuki.com/c/D-O_Assembly
- 控制源码：https://github.com/PrintedDroid/D-O-Printed-Droid
- 控制与供电板：https://www.printed-droid.com/kb/d-o-control-and-power-board/
- AIO32 v2.1 固件附件：https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2.1.zip
- AIO32 v2.1.1 英文手册：https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2_User_Handbook_v2.1.1.pdf
- 官网 v3.4 历史附件：https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_ibus_v3.4.zip
- Arduino Mega 2560 Serial0 引脚：https://docs.arduino.cc/language-reference/en/functions/communication/serial/
- 60 mm 无轮调试支架：https://www.printed-droid.com/wp-content/uploads/2020/09/DO-Stand-60mm.stl
- Patreon：https://www.patreon.com/mrbaddeley
- D-O V2 公开帖：https://www.patreon.com/posts/d-o-v2-33070756
- Mantis Hacks 播放列表：https://youtube.com/playlist?list=PLTSAQ5KEjPVCldgA1t-KT1lRTKJdAY7er

## 本地已固定版本

- 仓库：`third_party/D-O-Printed-Droid`
- 提交：`e90aacdbe26a62fd4f0229d5504a3f2f3c409055`（2026-06-08）
- 推荐固件：`D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino`
- 2026-07-13 复核上游 `main` 仍为固定提交 `e90aacdbe26a62fd4f0229d5504a3f2f3c409055`
- 官网控制板页 12 个附件已下载到 Git 忽略目录 `third_party/do_public_resources/`，每个 URL、字节数和 SHA-256 写入机器清单
- 公开 `D-O_ibus_v3.4.zip` 实际是 v3.4.0；当前制作仍使用 GitHub 固定的 v3.4.3
- AIO32 ZIP 已核验为 23 个成员（22 个源码 + README）、0 个 KiCad/Gerber、0 个机械模型、无包级 LICENSE
- AIO32 已用 ESP32 core 3.3.7 实编译通过：Flash 41%、RAM 15%；手册遗漏的 `SensorLib` 0.4.1 是编译器发现的必要依赖，证据在 `engineering/do_aio32_firmware_compile.json`
- 完整自动审计：`python3 tools/audit_do_resources.py`
- Mantis 六条视频描述审计：`engineering/do_mantis_video_audit.json`
- 可复现获取：`tools/fetch_do_public_resources.sh`
- 审计说明：`docs/DO_资源审计与自组入口.md`
- 采购门控 BOM：`engineering/do_self_build_bom.csv`
- 分阶段调试路线：`docs/DO_自组采购与调试路线.md`

## Mantis Hacks 视频中的主要 BOM

- Arduino MKR WiFi 1010、MKR Proto Shield、MKR IMU Shield、MKR Motor Carrier
- Lynxmotion LSS ST1、Power Hub、32T 齿轮、串口线/适配板
- Dynamixel XL-320，后续改用 AX-18A / AX-12A
- Pololu 25D 带编码器减速电机
- 6 V 5000 mAh NiMH
- 25×32×4、8×12×3.5、4×11×4 轴承，8 mm IGUS 轴
- Adafruit 16 MB Sound FX 2×2 W、2 W 喇叭、Spektrum 遥控

播放列表实际由 **5 集编号构建视频 + 1 个 TPU 轮胎打印视频**组成。2026-07-13 对六条公开视频描述逐条读取后，没有发现 GitHub、GitLab、Google Drive、Dropbox 或其他 Matt 改版 CAD/控制程序发布链接；描述主要指向两个 Facebook 群、Mr Baddeley Patreon、Matt 的 Threeding 主页以及零件/联盟购买页。#4 的描述反而明确说明原始 CAD 由 Michael Baddeley 直接发送给 Matt，Matt 在其上修改舵机、驱动和电子方案。这支持“视频是设计与 BOM 证据，不是公开源码包”的边界，但不排除私有群、付费区或未索引来源以后出现文件。

## 目前仍缺失

- 合法免费公开的 D-O V2 完整 STL/Fusion 包
- Matt Denton 改版 CAD 和控制程序
- Printed Droid GitHub 当前没有机械模型；完整 D-O V2 机械文件仍需 Patreon 授权
- Printed Droid 控制板 KiCad/Gerber 源文件
- AIO32 手册所称共享 GitHub 硬件 KiCad 的实际公开位置；固定仓库唯一 `main` 分支和公开 ZIP 都没有这些文件
- 电影 D-O 的官方尺寸、公差和声音授权

## 新增源码与版本阻断门

固定的 v3.4.3 草图一边把舵机连接到 Mega D0/D1，一边启用 `Serial.begin(9600)`。官方 Mega 映射表显示 D0/D1 就是 RX0/TX0。项目因此新增 `DO-SRC-001 / HOLD_BENCH_VERIFICATION`：在完成非 UART 引脚改配或经验证的隔离/复用设计前，不把 D0/D1 舵机接入首轮 USB/Serial0 台架，也不把当前线束表当作可直接制造的最终设计。

Printed Droid 控制板页面内嵌的是 v2.1 接线表（D2/D3/D4/D5），而当前 v3.4.3 源码和 GitHub README 是 D0/D1/D5/D6。项目新增 `DO-SRC-002 / HOLD_VERSIONED_WIRING_REQUIRED`：不得把旧网页表与新固件混接，最终线束图必须绑定源码文件、提交与 SHA-256，并在上电前逐网导通检查。

同一页面的 `D-O_ibus_v3.4.zip` 内部仍是 v3.4.0。项目新增 `DO-SRC-003 / USE_PINNED_GITHUB_V3_4_3`：附件保留为历史证据，不作为当前烧录输入。AIO32 已证明可编译，但仍保持实验分支和包级许可/HW-CAD 双 HOLD，不与 Mega v3.4.3 基线混为一条路线。
