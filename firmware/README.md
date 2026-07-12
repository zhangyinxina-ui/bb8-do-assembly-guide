# BB-8 双电机控制核心

## 当前状态

`controller_core.*` 是不依赖 Arduino/ESP32 SDK 的控制核心；`sensor_math.*` 是编码器/IMU换算层；`power_safety.*` 是电流阈值、新鲜度与堵转计时层；`esp32_bb8/` 是已通过 ESP32-S3 编译的硬件适配草案。

已实现：

- `v / ω` 到左右轮速差速混控
- 线速度和角速度斜坡限制
- 编码器左右轮速 PI 闭环与 IMU 偏航率差动修正
- IMU/编码器新鲜度和两类偏航测量一致性检查
- 四边沿正交解码、轮速低通、运动指令后750 ms无脉冲停机
- MPU6050地址探测、±4g/±500°/s配置、400样本静止陀螺零偏标定和30 ms超时
- 双 INA226、2 mΩ Kelvin分流、20 ms新鲜度和200 ms寄存器回读门槛
- 每次上电显式配置瞬时电流/堵转电流/持续时间，默认拒动
- INA226 ALERT、测量过流、电流传感器过期和持续堵转锁存
- 左右输出按最大轮速同比例饱和
- 13.2–14.3 V 之间连续功率降额，避免低电量峰值电流触发压降停机
- 12 V 电机母线归一化：4S 满电 16.8 V 时占空比上限 71.4%，避免电机过压
- 急停、遥控丢失、运动传感器过期/不一致、电流传感器过期、硬件电流告警、过流、堵转、欠压、过温、过度倾斜共11类锁存故障
- 只有当所有传感器恢复安全后才允许手动复位

## 本地验证

```bash
clang++ -std=c++20 -Wall -Wextra -Werror \
  firmware/controller_core.cpp tests/controller_core_test.cpp \
  -o build/controller_core_test
./build/controller_core_test
sh tools/run_closed_loop_sim.sh
sh tools/run_power_safety_replay.sh
npm run test:firmware
```

预期输出：

`PASS controller_core: closed-loop feedback, derating, saturation, and 11 fail-safe paths`

闭环仿真会生成 `engineering/closed_loop_telemetry.csv`，电流故障回放会生成 `engineering/power_safety_replay.csv`。两者都是确定性软件证据，不等于真机地面验证。

阶段16把ESP32每200 ms输出的真机遥测扩展为带单调毫秒时间戳的固定字段：命令速度、使能、故障、电池、温度、急停、遥控、IMU、编码器、轮速、电流、硬件ALERT和PWM。将串口监视器原始文本保存后，可运行：

```bash
python3 tools/parse_bb8_telemetry.py \
  --input evidence/run-001/serial.log \
  --output evidence/run-001/telemetry.csv \
  --summary evidence/run-001/telemetry_summary.json
```

解析器只整理真实记录，不会把软件仿真或示例日志转成物理验收PASS。物理记录还必须按 `engineering/commissioning_test_plan.json` 补齐仪表、照片/视频、测量值和SHA-256，再由阶段16验证器审计。

## ESP32 硬件适配合同

200 Hz 主循环必须执行：

1. 更新 RC 帧并计算最后有效帧年龄；超过 100 ms 将 `remote_ok=false`。
2. 从独立常闭急停回路读取 `emergency_stop`；不得只用软件按钮。
3. 电池电压必须经电阻分压和 ADC 标定；默认 4S 欠压门槛 13.2 V。
4. 电机温度传感器脱落必须视为故障，不能当作低温。
5. IMU 与编码器数据必须带时间戳；任一过期或二者偏航率差异超过门槛都必须锁存停机。
6. 两路高侧电流数据必须带时间戳；INA226校准/配置回读错误、未配置限值或数据超过20 ms都必须停机。
7. 两路开漏 ALERT 必须除了进入 GPIO 14，还通过外部硬件门直接撤销驱动 EN。
8. 调用 `Controller::update(0.005F, command, sensors)`。
9. `enabled=false` 时必须在同一循环内拉低驱动器 EN 硬件引脚，而不只把 PWM 设为零。

## ESP32-S3 编译验证

本项目已用 Arduino CLI 1.5.1 与官方 Arduino-ESP32 3.3.10 对通用 ESP32-S3 目标完成本地编译：

```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  --config-file .arduino/arduino-cli.yaml \
  --build-path build/esp32_bb8 \
  firmware/esp32_bb8
```

阶段 10 编译结果：程序 338051 bytes（25%），全局变量 22492 bytes（6%）。这只证明源码与当前官方工具链兼容，尚未上传开发板，也未进行带电电机试验。

阶段 11 传感器适配编译结果：程序 367791 bytes（28%），全局变量 24636 bytes（7%）。

阶段 12 电流保护适配编译结果：程序 369971 bytes（28%），全局变量 24676 bytes（7%）。

阶段 16 固定字段真机遥测编译结果：程序 370095 bytes（28%），全局变量 24676 bytes（7%）。

台架串口协议：

1. 上电后保持底盘静止约2秒，等待 `IMU_READY`。
2. 依据实测编码器数据发送 `E <每轮转四边沿计数> <左方向±1> <右方向±1>`；默认CPR为0，未配置时电机EN保持关闭。
3. 依据限流电源下的实测发送 `I <瞬时切断_A> <堵转判定_A> <堵转持续_ms>`；限值默认未配置。
4. 以至少10 Hz发送 `V <线速度m/s> <角速度rad/s>`；先发送 `V 0 0`。
5. 全部传感器安全且最新指令严格为 `V 0 0` 后发送 `R` 清除故障锁存；非零命令下复位会被拒绝。超过100 ms未收到速度帧会停机。

CPR、方向和电流限值都不会写入非易失存储，每次上电都必须重新确认。

## 建议硬件映射（ESP32-S3）

| 信号 | 建议引脚 | 要求 |
|---|---:|---|
| 左 PWM / DIR | GPIO 4 / 5 | PWM 至少 20 kHz |
| 右 PWM / DIR | GPIO 6 / 7 | PWM 至少 20 kHz |
| 驱动 EN | GPIO 8 | 外部下拉，MCU 复位时为禁用 |
| 急停返回 | GPIO 9 | 常闭回路，断线即停机 |
| 左编码器 A/B | GPIO 10 / 11 | 屏蔽双绞线 |
| 右编码器 A/B | GPIO 12 / 13 | 屏蔽双绞线 |
| 电流 ALERT | GPIO 14 | 双 INA226 开漏并联；同时硬件门控 EN |
| IMU I²C SDA/SCL | GPIO 17 / 18 | 3.3 V，短线 |
| 电池 ADC | GPIO 1 | 分压+输入保护 |
| 温度 ADC | GPIO 2 / 3 | 左右电机分开采样 |

> 引脚仅是建议映射，必须对照所选 ESP32-S3 开发板原理图排除启动绑定、USB/JTAG 和 Flash/PSRAM 占用引脚。

## 真机前未完成的门槛

- 软件适配已实现并编译，但尚未接入真实MPU6050、编码器和电机验证。只有完成静止标定、显式CPR配置且数据持续新鲜时，`imu_fresh`与`encoders_fresh`才可能为真。
- 当前正交编码器使用GPIO CHANGE中断而不是ESP32 PCNT硬件；必须在目标最高转速下测量中断负载和丢计数，再决定是否迁移到PCNT。
- INA226适配、软件过流/堵转判定和ALERT配置已编译，但实体2 mΩ分流、Kelvin布线、ALERT→EN外部门、驱动器硬限流与急停回路仍未验证。
- 必须在轮子架空时标定方向、比例和电流上限。
- 必须有物理急停、保险丝、独立驱动 EN 和围栏后才可落地。
