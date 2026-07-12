# BB-8 阶段 12：电流保护与堵转回放

> 结论：**保护逻辑、INA226 寄存器适配、ESP32-S3 编译和确定性故障回放通过；实体分流器、ALERT 硬件链和电机堵转试验尚未执行。**

## 电流测量架构

- 左右电机高侧电源分支各使用一颗 INA226，I²C 地址为 `0x40` / `0x41`。
- 每路使用 2 mΩ Kelvin 四线分流器；Current_LSB 为 1 mA，校准寄存器为 `0x0A00`（2560）。
- 配置寄存器 `0x4127`：分流和母线电压各 1.1 ms，连续转换；固件每 200 ms 回读配置与校准寄存器。
- 两路 ALERT 为开漏输出，并联到 GPIO 14；必须同时经外部晶体管/逻辑门直接拉低驱动 EN，不得只把 GPIO 读值当作“硬件限流”。
- ALERT 使用正向 Shunt Over-Limit，目标是拦截电池向驱动器的堵转大电流；反向回生电流仅由有符号的软件电流值检查，还必须依赖驱动器/BMS的独立硬件保护。
- 电流帧超过 20 ms、任一 INA226 丢失、寄存器复位或限值未配置时，`current_protection_ready=false`，驱动保持失能。

## 上电必填限值

固件不猜测真实堵转电流。每次上电必须在架空、限流电源下根据实测结果发送：

```text
I <瞬时切断_A> <堵转判定_A> <堵转持续_ms>
```

软件只接受 1–30 A 瞬时值、0.5 A 至瞬时值的堵转值、100–3000 ms 持续时间。这是输入有效性边界，不是对所选电机、驱动器、分流器、导线或保险丝的安全认证。

## 11 类锁存故障

阶段 11 的 7 类故障保留，新增：

1. `current_sensor_stale`：双 INA226、配置回读、数据时间或上电限值不完整。
2. `hardware_current_trip`：ALERT 硬件线已拉低。
3. `over_current`：任一路测量电流超过显式瞬时值。
4. `motor_stall`：目标轮速≥0.10 m/s、实测轮速≤0.025 m/s且电流超过堵转值，持续到配置时间。

任一故障在当前 200 Hz 控制帧内返回零 PWM 并拉低 EN；外部 ALERT→EN 链还必须在 MCU 不运行时也能撤销使能。
解除锁存前必须先发送 `V 0 0`；任一非零线速度或角速度命令存在时，`R` 返回 `RESET_REJECTED_NONZERO_COMMAND`，防止清除 ALERT 后自动恢复运动。

## 确定性回放证据

`tests/power_safety_replay_test.cpp` 以 5 ms 周期产生 `engineering/power_safety_replay.csv`：

- 10.5 A 相对 10.0 A 示例瞬时值：同帧标记 `over_current`。
- 6.5 A、0.005 m/s 相对 0.25 m/s 目标：从 0.700 s 开始，在 0.995 s 标记 `motor_stall`。
- 电流帧过期：标记 `current_sensor_stale`。
- ALERT 拉低：同帧标记 `hardware_current_trip`。

上述数值是回放用测试向量，不是已实测的整机限值。

## 编译与实体门槛

- Arduino-ESP32 3.3.10 / Generic ESP32-S3：程序 369971 / 1310720 bytes（28%），全局变量 24676 / 327680 bytes（7%）。
- 尚未证明：2 mΩ 分流器的功率/脉冲额定、Kelvin 布线、ALERT 与 EN 延迟、驱动器硬件限流、真实空载/堵转电流、保险丝配合和热稳态。
- 高能量电池下不得用软件堵转测试替代限流电源、主保险、硬件断电和围栏。

## 官方依据

- TI INA226 数据表：<https://www.ti.com/lit/ds/symlink/ina226.pdf>
- Arduino-ESP32 I²C：<https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html>
