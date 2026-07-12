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
  if (config_.require_motion_feedback && (!sensors.imu_fresh || !sensors.encoders_fresh)) {
    return Fault::MotionSensorStale;
  }
  if (config_.require_motion_feedback) {
    const float encoder_yaw =
        (sensors.right_wheel_mps - sensors.left_wheel_mps) / config_.track_m;
    if (std::abs(encoder_yaw - sensors.yaw_rate_radps) >
        config_.maximum_yaw_sensor_disagreement_radps) {
      return Fault::MotionSensorDisagreement;
    }
  }
  if (config_.require_current_feedback) {
    if (sensors.hardware_current_trip) return Fault::HardwareCurrentTrip;
    if (!sensors.current_protection_ready) return Fault::CurrentSensorStale;
    if (sensors.current_over_limit) return Fault::OverCurrent;
    if (sensors.motor_stalled) return Fault::MotorStall;
  }
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
    left_integral_ = 0.0F;
    right_integral_ = 0.0F;
    return {.fault = latched_fault_};
  }

  command.linear_mps = clamp(command.linear_mps, -config_.max_wheel_speed_mps, config_.max_wheel_speed_mps);
  const float max_yaw = 2.0F * config_.max_wheel_speed_mps / config_.track_m;
  command.yaw_radps = clamp(command.yaw_radps, -max_yaw, max_yaw);
  linear_mps_ = slew(linear_mps_, command.linear_mps, config_.max_linear_accel_mps2 * dt_s);
  yaw_radps_ = slew(yaw_radps_, command.yaw_radps, config_.max_yaw_accel_radps2 * dt_s);

  float left_target = linear_mps_ - yaw_radps_ * config_.track_m * 0.5F;
  float right_target = linear_mps_ + yaw_radps_ * config_.track_m * 0.5F;
  if (config_.require_motion_feedback) {
    const float yaw_error = yaw_radps_ - sensors.yaw_rate_radps;
    const float yaw_correction = clamp(
        config_.yaw_rate_kp_m_per_rad * yaw_error,
        -config_.maximum_yaw_correction_mps,
        config_.maximum_yaw_correction_mps);
    left_target -= yaw_correction;
    right_target += yaw_correction;
  }
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
  float left_normalized = left_target / config_.max_wheel_speed_mps;
  float right_normalized = right_target / config_.max_wheel_speed_mps;
  if (config_.require_motion_feedback) {
    const float left_error =
        (left_target - sensors.left_wheel_mps) / config_.max_wheel_speed_mps;
    const float right_error =
        (right_target - sensors.right_wheel_mps) / config_.max_wheel_speed_mps;
    left_integral_ = clamp(
        left_integral_ + config_.wheel_speed_ki_per_s * left_error * dt_s,
        -power_limit,
        power_limit);
    right_integral_ = clamp(
        right_integral_ + config_.wheel_speed_ki_per_s * right_error * dt_s,
        -power_limit,
        power_limit);
    left_normalized += config_.wheel_speed_kp * left_error + left_integral_;
    right_normalized += config_.wheel_speed_kp * right_error + right_integral_;
  }
  const float peak = std::max(std::abs(left_normalized), std::abs(right_normalized));
  if (peak > power_limit) {
    const float scale = power_limit / peak;
    left_normalized *= scale;
    right_normalized *= scale;
  }

  return {
      .left_normalized = left_normalized,
      .right_normalized = right_normalized,
      .limited_linear_mps = linear_mps_,
      .limited_yaw_radps = yaw_radps_,
      .left_target_mps = left_target,
      .right_target_mps = right_target,
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
  left_integral_ = 0.0F;
  right_integral_ = 0.0F;
  return true;
}

const char* faultName(Fault fault) {
  switch (fault) {
    case Fault::None: return "none";
    case Fault::EmergencyStop: return "emergency_stop";
    case Fault::RemoteLost: return "remote_lost";
    case Fault::MotionSensorStale: return "motion_sensor_stale";
    case Fault::MotionSensorDisagreement: return "motion_sensor_disagreement";
    case Fault::CurrentSensorStale: return "current_sensor_stale";
    case Fault::HardwareCurrentTrip: return "hardware_current_trip";
    case Fault::OverCurrent: return "over_current";
    case Fault::MotorStall: return "motor_stall";
    case Fault::UnderVoltage: return "under_voltage";
    case Fault::OverTemperature: return "over_temperature";
    case Fault::ExcessiveTilt: return "excessive_tilt";
  }
  return "unknown";
}

bool commandIsZeroForReset(const Command& command, float epsilon) {
  return epsilon >= 0.0F && std::abs(command.linear_mps) <= epsilon &&
         std::abs(command.yaw_radps) <= epsilon;
}

}  // namespace bb8
