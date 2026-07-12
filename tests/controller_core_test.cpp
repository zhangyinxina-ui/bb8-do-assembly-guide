#include "../firmware/controller_core.h"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace bb8;

static Sensors safeSensors() {
  return {.remote_ok = true, .emergency_stop = false, .battery_v = 16.0F,
          .motor_temp_c = 30.0F, .chassis_tilt_deg = 0.0F,
          .imu_fresh = true, .encoders_fresh = true};
}

int main() {
  Controller controller;
  auto sensors = safeSensors();

  // Acceleration is limited to 0.2 m/s after one second.
  Output out = controller.update(1.0F, {.linear_mps = 0.5F}, sensors);
  assert(out.enabled && out.fault == Fault::None);
  assert(std::abs(out.limited_linear_mps - 0.2F) < 1e-5F);
  assert(std::abs(out.left_normalized - 0.4F) < 1e-5F);
  assert(std::abs(out.right_normalized - 0.4F) < 1e-5F);

  // Positive yaw produces a faster right wheel and remains bounded.
  out = controller.update(1.0F, {.linear_mps = 0.3F, .yaw_radps = 1.0F}, sensors);
  assert(out.right_normalized > out.left_normalized);
  assert(std::abs(out.right_normalized) <= 1.0F);
  assert(std::abs(out.left_normalized) <= 1.0F);

  // Loaded battery voltage smoothly derates output before hard undervoltage.
  Controller derating_controller;
  auto low_battery = safeSensors();
  low_battery.battery_v = 13.75F;
  out = derating_controller.update(10.0F, {.linear_mps = 0.5F}, low_battery);
  assert(out.enabled && out.power_limit > 0.35F && out.power_limit < 1.0F);
  assert(std::abs(out.left_normalized) <= out.power_limit + 1e-5F);
  assert(std::abs(out.right_normalized) <= out.power_limit + 1e-5F);

  // A 12 V motor on a fully charged 4S bus is voltage-normalized to 71.4% PWM.
  Controller voltage_cap_controller;
  auto full_4s = safeSensors();
  full_4s.battery_v = 16.8F;
  out = voltage_cap_controller.update(10.0F, {.linear_mps = 0.5F}, full_4s);
  assert(std::abs(out.power_limit - (12.0F / 16.8F)) < 1e-5F);

  // Remote loss immediately zeros both outputs and latches.
  sensors.remote_ok = false;
  out = controller.update(0.01F, {.linear_mps = 0.3F}, sensors);
  assert(!out.enabled && out.fault == Fault::RemoteLost);
  assert(out.left_normalized == 0.0F && out.right_normalized == 0.0F);
  sensors.remote_ok = true;
  out = controller.update(0.01F, {}, sensors);
  assert(out.fault == Fault::RemoteLost);
  assert(controller.resetFault(sensors));

  // Every high-risk sensor path stops and latches independently.
  sensors.emergency_stop = true;
  assert(controller.update(0.01F, {}, sensors).fault == Fault::EmergencyStop);
  sensors.emergency_stop = false;
  assert(controller.resetFault(sensors));
  sensors.battery_v = 12.0F;
  assert(controller.update(0.01F, {}, sensors).fault == Fault::UnderVoltage);
  sensors.battery_v = 16.0F;
  assert(controller.resetFault(sensors));
  sensors.motor_temp_c = 80.0F;
  assert(controller.update(0.01F, {}, sensors).fault == Fault::OverTemperature);
  sensors.motor_temp_c = 30.0F;
  assert(controller.resetFault(sensors));
  sensors.chassis_tilt_deg = 31.0F;
  assert(controller.update(0.01F, {}, sensors).fault == Fault::ExcessiveTilt);

  // Ground mode requires fresh, mutually consistent IMU and encoder feedback.
  Config closed_loop_config;
  closed_loop_config.require_motion_feedback = true;
  Controller closed_loop(closed_loop_config);
  sensors = safeSensors();
  sensors.imu_fresh = false;
  assert(closed_loop.update(0.005F, {}, sensors).fault == Fault::MotionSensorStale);
  sensors.imu_fresh = true;
  assert(closed_loop.resetFault(sensors));
  sensors.left_wheel_mps = -0.20F;
  sensors.right_wheel_mps = 0.20F;
  sensors.yaw_rate_radps = 0.0F;
  assert(closed_loop.update(0.005F, {}, sensors).fault == Fault::MotionSensorDisagreement);

  sensors = safeSensors();
  assert(closed_loop.resetFault(sensors));
  out = closed_loop.update(1.0F, {.linear_mps = 0.3F}, sensors);
  assert(out.enabled && out.left_target_mps > 0.0F && out.right_target_mps > 0.0F);
  assert(out.left_normalized > out.left_target_mps / closed_loop_config.max_wheel_speed_mps);

  std::cout << "PASS controller_core: closed-loop wheel/IMU feedback, derating, saturation, and 7 fail-safe paths\n";
  return 0;
}
