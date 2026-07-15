# D-O 合法自组资源索引

## 先说结论

截至 2026-07-15，仍未找到一个同时包含完整机械、控制源码、电气设计、明确再分发条款和真机验证证据的 D-O 整机开源包。已经找到免费与付费模型候选，但它们必须按“可动开发版、静态模型、关节展示模型”分开使用。当前可执行路线是：

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
| Denton V1 / Thingiverse | 分组件 STL、3D PDF、可动机构思路 | 免费；页面标 CC BY 4.0 | WIP；页面仍写头部缺失、STEP 待后续；基于 Baddeley 私下提供的 CAD，衍生几何再许可权需复核；文件包尚未下载审计 |
| WF3D / Printables | 约 300 mm、32 个文件的分色模型 | 免费；CC BY-NC-SA 4.0 | 静态展示模型，不含驱动、平衡或控制设计 |
| CalebTimoteo / Printables | 11 个文件的家居摆件 remix | 免费；CC BY-NC 4.0 | WIP 静态模型，不含驱动系统 |
| JRIZZ / Cults | Fusion 360 F3Z、STL、机器人端与遥控端 Arduino 草图 | 付费；CULTS Private Use | 页面称可动但仍在开发；未购买、未验包、未做真机验证；数字文件不得公开再分发 |
| Gambody Assembly + Action | 116 个 STL、1:1/缩比版本、关节与发动机/电池空间 | 付费；Personal use | 是可关节展示/改装基础，不包含控制源码、平衡控制或完整电气包 |
| MakerWorld 23859 | 搜索发现的 D-O 条目 | 页面受 Cloudflare 阻断 | 文件、作者、许可与用途均未核验，不列为可用开源资源 |

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
- Denton V1 Thingiverse：https://www.thingiverse.com/thing:4189546
- WF3D 30 cm 静态模型：https://www.printables.com/model/147063-star-wars-d-o-droid
- Printables 家居摆件 WIP：https://www.printables.com/model/1269542-d-o-droid-star-wars-home-decor
- JRIZZ Cults 可动开发版：https://cults3d.com/en/3d-model/gadget/d-o-droid-star-wars-droid
- Gambody Assembly + Action：https://www.gambody.com/premium/d-o-droid
- MakerWorld 待核验条目：https://makerworld.com/en/models/23859-star-wars-d-o-droid

## 本地已固定版本

- 仓库：`third_party/D-O-Printed-Droid`
- 提交：`e90aacdbe26a62fd4f0229d5504a3f2f3c409055`（2026-06-08）
- 推荐固件：`D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino`
- 2026-07-15 复核上游 `main` 仍为固定提交 `e90aacdbe26a62fd4f0229d5504a3f2f3c409055`
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

## 公开模型候选的正确用法

1. **Denton V1 是免费可动候选，不是已完成整机包。** Thingiverse 页面级元数据标注 CC BY 4.0，并写明有分组件 STL 与 3D PDF；同一页面也明确标注 WIP、头部尚未完成、STEP 以后再加。页面还说明模型基于 Michael Baddeley 私下发给作者的 CAD，因此在实际采用或再发布衍生文件前，要同时核对压缩包内容和衍生授权来源。
2. **JRIZZ / Cults 是目前最接近“机械 + Arduino”的整合候选，但它是付费私用开发版。** 页面列出 Fusion 360 主装配、机器人端/遥控端两个 Arduino 草图、打印件和硬件架构；页面也说设计仍在开发。购买属于外部付费且接受私用条款的动作，必须等用户明确确认；购买前本项目不会获取、镜像或宣称已验证。
3. **两个 Printables 条目是静态模型。** WF3D 版本约 300 mm、32 个文件，许可为 CC BY-NC-SA 4.0；家居摆件版本为 11 文件 WIP remix，许可为 CC BY-NC 4.0。它们可以帮助外形、分色和打印，但不能替代可平衡、可驱动的机械结构。
4. **Gambody 是付费关节展示/改装底座。** 页面列出 116 个 STL、518 mm 高的“life-size”版本、可动头部和可替换的发动机/电池假件，但没有控制源码、电气设计或平衡算法，不能按完整机器人包验收。
5. **MakerWorld 只保留为待核验线索。** 2026-07-15 审计时页面被 Cloudflare 阻断，未取得足够证据确认许可证、作者、文件或用途。

上述六条候选已经写入 `engineering/do_resource_manifest.json` 的 `external_model_candidates`。清单只记录原始链接和页面证据，不镜像任何第三方数字模型。

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

- 合法免费、完整且已验包的可动 D-O STL/Fusion 机械包
- Matt Denton 改版 CAD 和控制程序
- Printed Droid GitHub 当前没有机械模型；Denton V1 免费候选仍是 WIP，JRIZZ 与 Baddeley 路线仍需分别接受 Cults/Patreon 的付费条款
- Printed Droid 控制板 KiCad/Gerber 源文件
- AIO32 手册所称共享 GitHub 硬件 KiCad 的实际公开位置；固定仓库唯一 `main` 分支和公开 ZIP 都没有这些文件
- 电影 D-O 的官方尺寸、公差和声音授权

## 新增源码与版本阻断门

固定的 v3.4.3 草图一边把舵机连接到 Mega D0/D1，一边启用 `Serial.begin(9600)`。官方 Mega 映射表显示 D0/D1 就是 RX0/TX0。项目现在提供固定哈希转换器，将四路舵机移到 D22–D25，并已在 Mega 2560 编译通过；`DO-SRC-001` 因此前进为 `UPSTREAM_CONFLICT_VARIANT_COMPILED_HOLD_PHYSICAL_CONTINUITY`。这不是实物通过：D22–D25 导通、USB/Serial0 和四路舵机脉宽仍必须上台架。

Printed Droid 控制板页面内嵌的是 v2.1 接线表（D2/D3/D4/D5），而当前 v3.4.3 源码和 GitHub README 是 D0/D1/D5/D6。项目已发布只含本项目生成信息的 [安全变体线束合同](../engineering/do_safe_pin_variant_wiring.csv) 和 [编译证据](../engineering/do_safe_pin_variant_compile.json)，状态为 `DO-SRC-002 / VARIANT_WIRING_GENERATED_HOLD_PHYSICAL_CONTINUITY`。不得把旧网页表、未改原版和 D22–D25 变体混接；上电前仍要逐网导通。

同一页面的 `D-O_ibus_v3.4.zip` 内部仍是 v3.4.0。项目新增 `DO-SRC-003 / USE_PINNED_GITHUB_V3_4_3`：附件保留为历史证据，不作为当前烧录输入。AIO32 已证明可编译，但仍保持实验分支和包级许可/HW-CAD 双 HOLD，不与 Mega v3.4.3 基线混为一条路线。
