# D-O 合法自组资源索引

## 先说结论

截至 2026-07-12，未找到“完整、免费、附明确开源许可证”的 D-O 整机 CAD + PCB + 固件包。当前可执行路线是：

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
| Dozuki D-O Assembly | 五章装配指南 | 免费阅读 | 机械打印件仍指向 Patreon |
| Mantis Hacks #1–#6 | 设计演进、电子、轮胎、BOM | 公开视频 | 未找到改版 CAD/程序下载及许可 |
| DO Stand 60mm | 无轮通电测试支架 STL | 公开下载 | 非整机结构件；未附明确再分发许可 |

## 直接链接

- D-O 总页：https://www.printed-droid.com/kb/d-o/
- 28 页装配 PDF：https://www.printed-droid.com/wp-content/uploads/2022/07/DO-Instructions-Pt1.1.pdf
- V2 接线 PDF：https://www.printed-droid.com/wp-content/uploads/2022/07/DOV2-Wiring-diagram-notes.pdf
- Dozuki 装配：https://d-o.dozuki.com/c/D-O_Assembly
- 控制源码：https://github.com/PrintedDroid/D-O-Printed-Droid
- 控制与供电板：https://www.printed-droid.com/kb/d-o-control-and-power-board/
- 60 mm 无轮调试支架：https://www.printed-droid.com/wp-content/uploads/2020/09/DO-Stand-60mm.stl
- Patreon：https://www.patreon.com/mrbaddeley
- D-O V2 公开帖：https://www.patreon.com/posts/d-o-v2-33070756
- Mantis Hacks 播放列表：https://youtube.com/playlist?list=PLTSAQ5KEjPVCldgA1t-KT1lRTKJdAY7er

## 本地已固定版本

- 仓库：`third_party/D-O-Printed-Droid`
- 提交：`e90aacdbe26a62fd4f0229d5504a3f2f3c409055`（2026-06-08）
- 推荐固件：`D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino`
- 完整自动审计：`python3 tools/audit_do_resources.py`
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

## 目前仍缺失

- 合法免费公开的 D-O V2 完整 STL/Fusion 包
- Matt Denton 改版 CAD 和控制程序
- Printed Droid GitHub 当前没有机械模型；完整 D-O V2 机械文件仍需 Patreon 授权
- Printed Droid 控制板 KiCad/Gerber 源文件
- 电影 D-O 的官方尺寸、公差和声音授权
