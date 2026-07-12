#include "controller_core.h"

#include <algorithm>
#include <cmath>

namespace bb8 {

Controller::Controller(Config config) : config_(config) {}

float Controller::clamp(float value, float low, float high) {
  return std::max(low, std::min(value, high));
}

float Controller::slew(float current, float target, float max_delta) {
  return current + clamp(target - current, -max_delta, max_delta);
}

Fault Controller::checkFault(const Sensors& sensors) const {
  if (sensors.emergency_stop) return Fault::EmergencyStop;
  if (!sensors.remote_ok) return Fault::RemoteLost;
  if (sensors.battery_v < config_.minimum_battery_v) return Fault::UnderVoltage;
  if (sensors.motor_temp_c > config_.maximum_motor_temp_c) return Fault::OverTemperature;
  if (std::abs(sensors.chassis_tilt_deg) > config_.maximum_tilt_deg) return Fault::ExcessiveTilt;
  return Fault::None;
}

Output Controller::update(float dt_s, Command command, Sensors sensors) {
  const Fault current_fault = checkFault(sensors);
  if (current_fault != Fault::None && latched_fault_ == Fault::None) latched_fault_ = current_fault;
  if (latched_fault_ != Fault::None || dt_s <= 0.0F) {
    linear_mps_ = 0.0F;
    yaw_radps_ = 0.0F;
    return {.fault = latched_fault_};
  }

  command.linear_mps = clamp(command.linear_mps, -config_.max_wheel_speed_mps, config_.max_wheel_speed_mps);
  const float max_yaw = 2.0F * config_.max_wheel_speed_mps / config_.track_m;
  command.yaw_radps = clamp(command.yaw_radps, -max_yaw, max_yaw);
  linear_mps_ = slew(linear_mps_, command.linear_mps, config_.max_linear_accel_mps2 * dt_s);
  yaw_radps_ = slew(yaw_radps_, command.yaw_radps, config_.max_yaw_accel_radps2 * dt_s);

  float left = linear_mps_ - yaw_radps_ * config_.track_m * 0.5F;
  float right = linear_mps_ + yaw_radps_ * config_.track_m * 0.5F;
  float power_limit = 1.0F;
  if (sensors.battery_v < config_.battery_derate_start_v) {
    const float span = config_.battery_derate_start_v - config_.minimum_battery_v;
    const float fraction = span > 0.0F
        ? (sensors.battery_v - config_.minimum_battery_v) / span
        : 0.0F;
    power_limit = config_.minimum_power_limit +
                  (1.0F - config_.minimum_power_limit) * clamp(fraction, 0.0F, 1.0F);
  }
  if (sensors.battery_v > 0.0F) {
    power_limit = std::min(power_limit, config_.maximum_motor_voltage_v / sensors.battery_v);
  }
  const float peak = std::max(std::abs(left), std::abs(right));
  const float effective_max_wheel_speed = config_.max_wheel_speed_mps * power_limit;
  if (peak > effective_max_wheel_speed) {
    const float scale = effective_max_wheel_speed / peak;
    left *= scale;
    right *= scale;
  }

  return {
      .left_normalized = left / config_.max_wheel_speed_mps,
      .right_normalized = right / config_.max_wheel_speed_mps,
      .limited_linear_mps = linear_mps_,
      .limited_yaw_radps = yaw_radps_,
      .power_limit = power_limit,
      .enabled = true,
      .fault = Fault::None,
  };
}

bool Controller::resetFault(const Sensors& sensors) {
  if (checkFault(sensors) != Fault::None) return false;
  latched_fault_ = Fault::None;
  linear_mps_ = 0.0F;
  yaw_radps_ = 0.0F;
  return true;
}

const char* faultName(Fault fault) {
  switch (fault) {
    case Fault::None: return "none";
    case Fault::EmergencyStop: return "emergency_stop";
    case Fault::RemoteLost: return "remote_lost";
    case Fault::UnderVoltage: return "under_voltage";
    case Fault::OverTemperature: return "over_temperature";
    case Fault::ExcessiveTilt: return "excessive_tilt";
  }
  return "unknown";
}

}  // namespace bb8
