#include <Arduino.h>
#include <cmath>

#include "controller_core.h"

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
constexpr uint8_t kBatteryAdc = 1;
constexpr uint8_t kLeftTempAdc = 2;
constexpr uint8_t kRightTempAdc = 3;
}  // namespace pins

namespace {
constexpr uint32_t kPwmHz = 20000;
constexpr uint8_t kPwmBits = 10;
constexpr uint32_t kPwmMax = (1U << kPwmBits) - 1U;
constexpr uint32_t kControlPeriodUs = 5000;   // 200 Hz.
constexpr uint32_t kRemoteTimeoutMs = 100;
constexpr float kBatteryDividerRatio = 5.55556F;  // 82k high / 18k low.

Config groundSafeConfig() {
  Config config;
  config.require_motion_feedback = true;
  return config;
}

Controller controller(groundSafeConfig());
Command command;
uint32_t last_command_ms = 0;
uint32_t last_control_us = 0;
uint32_t last_report_ms = 0;
bool pwm_ready = false;

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

// Bench protocol over USB serial: "V <linear_mps> <yaw_radps>" at >= 10 Hz.
// "R" requests fault reset; physical E-stop and all sensors must already be safe.
void readBenchCommand() {
  if (!Serial.available()) return;
  const char type = static_cast<char>(Serial.read());
  if (type == 'V') {
    command.linear_mps = Serial.parseFloat();
    command.yaw_radps = Serial.parseFloat();
    last_command_ms = millis();
  } else if (type == 'R') {
    Sensors sensors;
    sensors.remote_ok = true;
    sensors.emergency_stop = digitalRead(pins::kEmergencyStop) != LOW;
    sensors.battery_v = readBatteryV();
    sensors.motor_temp_c = max(readNtcC(pins::kLeftTempAdc), readNtcC(pins::kRightTempAdc));
    sensors.chassis_tilt_deg = 0.0F;  // Replace with fresh IMU value before ground test.
    sensors.imu_fresh = false;
    sensors.encoders_fresh = false;
    Serial.println(controller.resetFault(sensors) ? "RESET_OK" : "RESET_REJECTED");
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
  pwm_ready = ledcAttach(pins::kLeftPwm, kPwmHz, kPwmBits) &&
              ledcAttach(pins::kRightPwm, kPwmHz, kPwmBits);
  stopHardware();
  Serial.println(pwm_ready ? "BB8_SAFE_BOOT PWM_READY" : "BB8_SAFE_BOOT PWM_FAILED");
  Serial.println("Bench only: keep sphere open and wheels lifted; send V 0 0 at >=10Hz.");
}

void loop() {
  readBenchCommand();
  const uint32_t now_us = micros();
  if (now_us - last_control_us < kControlPeriodUs) return;
  const float dt_s = (now_us - last_control_us) * 1.0e-6F;
  last_control_us = now_us;

  Sensors sensors;
  sensors.remote_ok = millis() - last_command_ms <= kRemoteTimeoutMs;
  sensors.emergency_stop = digitalRead(pins::kEmergencyStop) != LOW;
  sensors.battery_v = readBatteryV();
  sensors.motor_temp_c = max(readNtcC(pins::kLeftTempAdc), readNtcC(pins::kRightTempAdc));
  sensors.chassis_tilt_deg = 0.0F;
  // These remain false until timestamped IMU and quadrature-encoder adapters land.
  // Ground-safe configuration therefore latches motion_sensor_stale and keeps EN low.
  sensors.imu_fresh = false;
  sensors.encoders_fresh = false;
  sensors.left_wheel_mps = 0.0F;
  sensors.right_wheel_mps = 0.0F;
  sensors.yaw_rate_radps = 0.0F;

  const Output output = controller.update(dt_s, command, sensors);
  applyOutput(output);

  if (millis() - last_report_ms >= 200) {
    last_report_ms = millis();
    Serial.printf("enabled=%d fault=%s batt=%.2f temp=%.1f left=%.3f right=%.3f\n",
                  output.enabled, bb8::faultName(output.fault), sensors.battery_v,
                  sensors.motor_temp_c, output.left_normalized, output.right_normalized);
  }
}
