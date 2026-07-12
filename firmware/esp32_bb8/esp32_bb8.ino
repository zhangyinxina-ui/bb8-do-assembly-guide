#include <Arduino.h>
#include <Wire.h>
#include <cmath>

#include "controller_core.h"
#include "sensor_math.h"

using bb8::Command;
using bb8::Config;
using bb8::Controller;
using bb8::Output;
using bb8::Sensors;

namespace pins {
constexpr uint8_t kLeftPwm = 4;
constexpr uint8_t kLeftDir = 5;
constexpr uint8_t kRightPwm = 6;
constexpr uint8_t kRightDir = 7;
constexpr uint8_t kDriverEnable = 8;
constexpr uint8_t kEmergencyStop = 9;  // NC loop to GND; open means STOP.
constexpr uint8_t kLeftEncoderA = 10;
constexpr uint8_t kLeftEncoderB = 11;
constexpr uint8_t kRightEncoderA = 12;
constexpr uint8_t kRightEncoderB = 13;
constexpr uint8_t kImuSda = 17;
constexpr uint8_t kImuScl = 18;
constexpr uint8_t kBatteryAdc = 1;
constexpr uint8_t kLeftTempAdc = 2;
constexpr uint8_t kRightTempAdc = 3;
}  // namespace pins

namespace {
constexpr uint32_t kPwmHz = 20000;
constexpr uint8_t kPwmBits = 10;
constexpr uint32_t kPwmMax = (1U << kPwmBits) - 1U;
constexpr uint32_t kControlPeriodUs = 5000;  // 200 Hz.
constexpr uint32_t kRemoteTimeoutMs = 100;
constexpr uint32_t kImuTimeoutMs = 30;
constexpr uint32_t kEncoderResponseTimeoutUs = 750000;
constexpr uint16_t kImuCalibrationSamples = 400;  // Two stationary seconds at 200 Hz.
constexpr float kBatteryDividerRatio = 5.55556F;  // 82k high / 18k low.
constexpr float kWheelDiameterM = 0.096F;
constexpr float kEncoderDemandThresholdMps = 0.05F;
constexpr float kSpeedFilterAlpha = 0.20F;

struct EncoderState {
  uint8_t pin_a;
  uint8_t pin_b;
  volatile int32_t count{0};
  volatile uint8_t state{0};
  volatile uint32_t last_edge_us{0};
};

struct EncoderSnapshot {
  int32_t count;
  uint32_t last_edge_us;
};

struct ImuRaw {
  int16_t ax;
  int16_t ay;
  int16_t az;
  int16_t gz;
};

Config groundSafeConfig() {
  Config config;
  config.require_motion_feedback = true;
  return config;
}

Controller controller(groundSafeConfig());
Command command;
Sensors latest_sensors;
Output latest_output;
EncoderState left_encoder{pins::kLeftEncoderA, pins::kLeftEncoderB};
EncoderState right_encoder{pins::kRightEncoderA, pins::kRightEncoderB};
portMUX_TYPE encoder_mux = portMUX_INITIALIZER_UNLOCKED;
int32_t previous_left_count = 0;
int32_t previous_right_count = 0;
uint32_t left_demand_start_us = 0;
uint32_t right_demand_start_us = 0;
float encoder_counts_per_wheel_revolution = 0.0F;
int8_t left_encoder_direction = 1;
int8_t right_encoder_direction = 1;
float left_speed_filtered_mps = 0.0F;
float right_speed_filtered_mps = 0.0F;

uint8_t imu_address = 0;
uint32_t last_imu_ms = 0;
uint16_t imu_calibration_count = 0;
float gyro_z_bias_accumulator = 0.0F;
float gyro_z_bias_raw = 0.0F;
bool imu_calibrated = false;

uint32_t last_command_ms = 0;
uint32_t last_control_us = 0;
uint32_t last_report_ms = 0;
bool pwm_ready = false;

void ARDUINO_ISR_ATTR encoderIsr(void* argument) {
  auto* encoder = static_cast<EncoderState*>(argument);
  const uint8_t current =
      (static_cast<uint8_t>(digitalRead(encoder->pin_a)) << 1U) |
      static_cast<uint8_t>(digitalRead(encoder->pin_b));
  portENTER_CRITICAL_ISR(&encoder_mux);
  encoder->count += bb8::quadratureDelta(encoder->state, current);
  encoder->state = current;
  encoder->last_edge_us = micros();
  portEXIT_CRITICAL_ISR(&encoder_mux);
}

void setupEncoder(EncoderState& encoder) {
  pinMode(encoder.pin_a, INPUT_PULLUP);
  pinMode(encoder.pin_b, INPUT_PULLUP);
  encoder.state =
      (static_cast<uint8_t>(digitalRead(encoder.pin_a)) << 1U) |
      static_cast<uint8_t>(digitalRead(encoder.pin_b));
  encoder.last_edge_us = micros();
  attachInterruptArg(encoder.pin_a, encoderIsr, &encoder, CHANGE);
  attachInterruptArg(encoder.pin_b, encoderIsr, &encoder, CHANGE);
}

EncoderSnapshot snapshotEncoder(const EncoderState& encoder) {
  portENTER_CRITICAL(&encoder_mux);
  const EncoderSnapshot snapshot{encoder.count, encoder.last_edge_us};
  portEXIT_CRITICAL(&encoder_mux);
  return snapshot;
}

bool writeMpuRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(imu_address);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission(true) == 0;
}

bool readMpuRegister(uint8_t address, uint8_t reg, uint8_t& value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(static_cast<uint16_t>(address), static_cast<uint8_t>(1), true) != 1) {
    return false;
  }
  value = static_cast<uint8_t>(Wire.read());
  return true;
}

bool setupMpu6050() {
  if (!Wire.begin(pins::kImuSda, pins::kImuScl, 400000U)) return false;
  Wire.setTimeOut(10);
  for (const uint8_t candidate : {uint8_t{0x68}, uint8_t{0x69}}) {
    uint8_t who_am_i = 0;
    if (readMpuRegister(candidate, 0x75, who_am_i) &&
        (who_am_i == 0x68 || who_am_i == 0x69)) {
      imu_address = candidate;
      break;
    }
  }
  if (imu_address == 0) return false;
  return writeMpuRegister(0x6B, 0x01) &&  // Wake, X-gyro PLL clock.
         writeMpuRegister(0x1A, 0x03) &&  // 42/44 Hz DLPF.
         writeMpuRegister(0x1B, 0x08) &&  // Gyro ±500 degrees/s.
         writeMpuRegister(0x1C, 0x08);    // Accelerometer ±4 g.
}

int16_t decodeSigned16(uint8_t high, uint8_t low) {
  return static_cast<int16_t>((static_cast<uint16_t>(high) << 8U) | low);
}

bool readMpu6050(ImuRaw& sample) {
  if (imu_address == 0) return false;
  Wire.beginTransmission(imu_address);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(static_cast<uint16_t>(imu_address), static_cast<uint8_t>(14), true) != 14) {
    return false;
  }
  uint8_t bytes[14];
  for (uint8_t& byte : bytes) byte = static_cast<uint8_t>(Wire.read());
  sample.ax = decodeSigned16(bytes[0], bytes[1]);
  sample.ay = decodeSigned16(bytes[2], bytes[3]);
  sample.az = decodeSigned16(bytes[4], bytes[5]);
  sample.gz = decodeSigned16(bytes[12], bytes[13]);
  return true;
}

void updateImu(Sensors& sensors) {
  ImuRaw sample{};
  const bool read_ok = readMpu6050(sample);
  const bool acceleration_ok = read_ok &&
      bb8::accelerationNormPlausible(sample.ax, sample.ay, sample.az);
  if (read_ok) last_imu_ms = millis();

  if (!imu_calibrated && acceleration_ok && std::abs(sample.gz) < 1000) {
    gyro_z_bias_accumulator += sample.gz;
    ++imu_calibration_count;
    if (imu_calibration_count >= kImuCalibrationSamples) {
      gyro_z_bias_raw = gyro_z_bias_accumulator / imu_calibration_count;
      imu_calibrated = true;
      Serial.printf("IMU_READY address=0x%02x gyro_z_bias_raw=%.2f\n", imu_address, gyro_z_bias_raw);
    }
  }

  sensors.imu_fresh = imu_calibrated && acceleration_ok &&
                      millis() - last_imu_ms <= kImuTimeoutMs;
  if (read_ok) {
    sensors.chassis_tilt_deg = bb8::accelerometerTiltDeg(sample.ax, sample.ay, sample.az);
    sensors.yaw_rate_radps = bb8::mpu6050GyroRawToRadps(sample.gz, gyro_z_bias_raw);
  }
}

float readBatteryV() {
  return analogReadMilliVolts(pins::kBatteryAdc) * 0.001F * kBatteryDividerRatio;
}

float readNtcC(uint8_t pin) {
  constexpr float kSeriesOhm = 10000.0F;
  constexpr float kNominalOhm = 10000.0F;
  constexpr float kNominalK = 298.15F;
  constexpr float kBeta = 3950.0F;
  const float mv = static_cast<float>(analogReadMilliVolts(pin));
  if (mv < 100.0F || mv > 3200.0F) return 125.0F;  // Open/short => over-temp fault.
  const float ntc = kSeriesOhm * mv / (3300.0F - mv);
  const float inv_k = (1.0F / kNominalK) + std::log(ntc / kNominalOhm) / kBeta;
  return (1.0F / inv_k) - 273.15F;
}

void stopHardware() {
  digitalWrite(pins::kDriverEnable, LOW);
  if (pwm_ready) {
    ledcWrite(pins::kLeftPwm, 0);
    ledcWrite(pins::kRightPwm, 0);
  }
}

void writeMotor(uint8_t pwm_pin, uint8_t dir_pin, float normalized) {
  normalized = constrain(normalized, -1.0F, 1.0F);
  digitalWrite(dir_pin, normalized >= 0.0F ? HIGH : LOW);
  ledcWrite(pwm_pin, static_cast<uint32_t>(std::abs(normalized) * kPwmMax));
}

void applyOutput(const Output& output) {
  if (!pwm_ready || !output.enabled) {
    stopHardware();
    return;
  }
  writeMotor(pins::kLeftPwm, pins::kLeftDir, output.left_normalized);
  writeMotor(pins::kRightPwm, pins::kRightDir, output.right_normalized);
  digitalWrite(pins::kDriverEnable, HIGH);
}

// Bench protocol over USB serial:
//   E <counts_per_wheel_rev> <left_sign> <right_sign>  (mandatory after boot)
//   V <linear_mps> <yaw_radps>                         (send at >=10 Hz)
//   R                                                  (reset only when all sensors are safe)
// Unknown CPR stays at zero and forces encoders_fresh=false, keeping EN disabled.
void readBenchCommand() {
  if (!Serial.available()) return;
  const char type = static_cast<char>(Serial.read());
  if (type == 'V') {
    command.linear_mps = Serial.parseFloat();
    command.yaw_radps = Serial.parseFloat();
    last_command_ms = millis();
  } else if (type == 'E') {
    const float counts = Serial.parseFloat();
    const float left_sign = Serial.parseFloat();
    const float right_sign = Serial.parseFloat();
    if (counts >= 100.0F && (left_sign == 1.0F || left_sign == -1.0F) &&
        (right_sign == 1.0F || right_sign == -1.0F)) {
      encoder_counts_per_wheel_revolution = counts;
      left_encoder_direction = left_sign > 0.0F ? 1 : -1;
      right_encoder_direction = right_sign > 0.0F ? 1 : -1;
      left_demand_start_us = right_demand_start_us = 0;
      Serial.printf("ENCODER_CONFIG_OK cpr=%.1f left=%d right=%d\n", counts,
                    left_encoder_direction, right_encoder_direction);
    } else {
      encoder_counts_per_wheel_revolution = 0.0F;
      Serial.println("ENCODER_CONFIG_REJECTED");
    }
  } else if (type == 'R') {
    Serial.println(controller.resetFault(latest_sensors) ? "RESET_OK" : "RESET_REJECTED");
  }
  while (Serial.available() && Serial.read() != '\n') {}
}
}  // namespace

void setup() {
  pinMode(pins::kDriverEnable, OUTPUT);
  pinMode(pins::kLeftDir, OUTPUT);
  pinMode(pins::kRightDir, OUTPUT);
  pinMode(pins::kEmergencyStop, INPUT_PULLUP);
  stopHardware();
  analogReadResolution(12);
  Serial.begin(115200);
  setupEncoder(left_encoder);
  setupEncoder(right_encoder);
  const bool imu_found = setupMpu6050();
  pwm_ready = ledcAttach(pins::kLeftPwm, kPwmHz, kPwmBits) &&
              ledcAttach(pins::kRightPwm, kPwmHz, kPwmBits);
  stopHardware();
  Serial.printf("BB8_SAFE_BOOT pwm=%d imu=%d encoder_cpr=UNCONFIGURED\n", pwm_ready, imu_found);
  Serial.println("Keep sphere open and wheels lifted; keep still for IMU calibration, then send E, V 0 0, R.");
}

void loop() {
  readBenchCommand();
  const uint32_t now_us = micros();
  if (now_us - last_control_us < kControlPeriodUs) return;
  const float dt_s = (now_us - last_control_us) * 1.0e-6F;
  last_control_us = now_us;

  const EncoderSnapshot left_snapshot = snapshotEncoder(left_encoder);
  const EncoderSnapshot right_snapshot = snapshotEncoder(right_encoder);
  const int32_t left_delta = left_snapshot.count - previous_left_count;
  const int32_t right_delta = right_snapshot.count - previous_right_count;
  previous_left_count = left_snapshot.count;
  previous_right_count = right_snapshot.count;
  const float left_raw_mps = bb8::countsToWheelSpeedMps(
      left_delta * left_encoder_direction,
      encoder_counts_per_wheel_revolution,
      kWheelDiameterM,
      dt_s);
  const float right_raw_mps = bb8::countsToWheelSpeedMps(
      right_delta * right_encoder_direction,
      encoder_counts_per_wheel_revolution,
      kWheelDiameterM,
      dt_s);
  left_speed_filtered_mps += kSpeedFilterAlpha * (left_raw_mps - left_speed_filtered_mps);
  right_speed_filtered_mps += kSpeedFilterAlpha * (right_raw_mps - right_speed_filtered_mps);

  const float expected_left_mps = command.linear_mps - command.yaw_radps * 0.31F * 0.5F;
  const float expected_right_mps = command.linear_mps + command.yaw_radps * 0.31F * 0.5F;
  const bool left_encoder_fresh = bb8::encoderResponseFresh(
      expected_left_mps,
      kEncoderDemandThresholdMps,
      left_snapshot.last_edge_us,
      now_us,
      kEncoderResponseTimeoutUs,
      left_demand_start_us);
  const bool right_encoder_fresh = bb8::encoderResponseFresh(
      expected_right_mps,
      kEncoderDemandThresholdMps,
      right_snapshot.last_edge_us,
      now_us,
      kEncoderResponseTimeoutUs,
      right_demand_start_us);

  Sensors sensors;
  sensors.remote_ok = millis() - last_command_ms <= kRemoteTimeoutMs;
  sensors.emergency_stop = digitalRead(pins::kEmergencyStop) != LOW;
  sensors.battery_v = readBatteryV();
  sensors.motor_temp_c = max(readNtcC(pins::kLeftTempAdc), readNtcC(pins::kRightTempAdc));
  sensors.encoders_fresh = encoder_counts_per_wheel_revolution >= 100.0F &&
                           left_encoder_fresh && right_encoder_fresh;
  sensors.left_wheel_mps = left_speed_filtered_mps;
  sensors.right_wheel_mps = right_speed_filtered_mps;
  updateImu(sensors);
  latest_sensors = sensors;

  latest_output = controller.update(dt_s, command, sensors);
  applyOutput(latest_output);

  if (millis() - last_report_ms >= 200) {
    last_report_ms = millis();
    Serial.printf(
        "enabled=%d fault=%s batt=%.2f temp=%.1f imu=%d enc=%d tilt=%.1f yaw=%.3f "
        "vL=%.3f vR=%.3f pwmL=%.3f pwmR=%.3f\n",
        latest_output.enabled,
        bb8::faultName(latest_output.fault),
        sensors.battery_v,
        sensors.motor_temp_c,
        sensors.imu_fresh,
        sensors.encoders_fresh,
        sensors.chassis_tilt_deg,
        sensors.yaw_rate_radps,
        sensors.left_wheel_mps,
        sensors.right_wheel_mps,
        latest_output.left_normalized,
        latest_output.right_normalized);
  }
}
