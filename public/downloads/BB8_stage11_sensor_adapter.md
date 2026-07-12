# BB-8 阶段 11：ESP32 编码器与 MPU6050 适配

> 结论：**源码、桌面单测和 ESP32-S3 编译通过；实体传感器与电机试验尚未执行。** 本阶段把阶段10的闭环输入从固定占位值改为真实接口代码，但不会把“可编译”冒充“真机可运行”。

## 已实现接口

### 双正交编码器

- GPIO 10/11为左A/B，GPIO 12/13为右A/B；四个输入均使用上拉和CHANGE中断。
- 四状态查表拒绝两位同时跳变；桌面测试覆盖正转、反转和无效跳变。
- 控制循环每5 ms原子快照计数，按96 mm轮径换算m/s并做α=0.20低通。
- 每轮转计数和左右方向没有猜测默认值；必须发送：

```text
E <counts_per_wheel_rev> <left_sign> <right_sign>
```

- 有超过0.05 m/s的运动需求后，若750 ms内没有对应编码器边沿，`encoders_fresh=false`并触发锁存停机。

### MPU6050

- GPIO 17/18为SDA/SCL，400 kHz；探测0x68和0x69地址。
- 配置±4 g加速度、±500°/s陀螺和约42 Hz数字低通。
- 上电保持静止，累计400个合理重力范数样本计算Z轴陀螺零偏；标定完成前IMU不新鲜。
- 加速度范数必须在0.75–1.25 g，最后有效帧年龄不得超过30 ms。
- 使用加速度计算底盘倾角，Z轴陀螺计算偏航率；安装合同要求直立时传感器Z轴平行于底盘竖直轴。

## 安全启动顺序

1. 球壳保持打开、驱动轮架空、驱动EN外部下拉、急停回路闭合。
2. 上电后底盘静止约2秒，等待串口输出`IMU_READY`。
3. 用手转一整圈轮子实测四边沿计数和方向，发送`E`命令；错误参数会使闭环方向错误，因此不持久化保存。
4. 连续发送`V 0 0`，确认遥控帧、IMU、编码器、电池、温度和急停全部安全。
5. 发送`R`；仅当所有门槛为真时才允许清除故障。
6. 首次命令不超过0.05 m/s，分别验证左右轮方向、计数符号、急停和失联停车。

## 编译与单测证据

- `tests/sensor_math_test.cpp`：正反正交序列、无效跳变、轮速换算、MPU6050陀螺比例、倾角、重力范数和750 ms响应超时全部通过。
- `tests/controller_core_test.cpp`：7类锁存故障和闭环输出继续通过。
- Arduino-ESP32 3.3.10 / Generic ESP32-S3：程序367791 / 1310720 bytes（28%），全局变量24636 / 327680 bytes（7%）。
- `npm run test:firmware`会重新编译并把实际程序/RAM字节数与`engineering/bb8_firmware_compile.json`比对，防止网站证据与源码漂移。

## 官方接口依据

- Arduino-ESP32 GPIO与`attachInterruptArg`：<https://docs.espressif.com/projects/arduino-esp32/en/latest/api/gpio.html>
- Arduino-ESP32 I²C `begin`、`setTimeOut`、`requestFrom`：<https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html>
- ESP-IDF FreeRTOS临界区和`portMUX_TYPE`：<https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/freertos_idf.html>

## 仍未通过的实体门槛

1. 未验证目标ESP32-S3板的GPIO 10–13、17–18是否与Flash、PSRAM、USB/JTAG或启动绑定位冲突。
2. 未测量编码器最高边沿频率、GPIO中断占用率和丢计数；高频时可能需要迁移到PCNT硬件。
3. 未完成IMU安装方向、静止偏置、温漂、球壳振动和电磁干扰测试。
4. 未实现驱动电流采样、硬限流和堵转检测。
5. 未执行架空轮、开壳低压、封壳围栏、低速地面和热耐久试验。
