#pragma once

#include <cstdint>

namespace bb8 {

enum class Fault : std::uint8_t {
  None,
  EmergencyStop,
  RemoteLost,
  MotionSensorStale,
  MotionSensorDisagreement,
  CurrentSensorStale,
  HardwareCurrentTrip,
  OverCurrent,
  MotorStall,
  UnderVoltage,
  OverTemperature,
  ExcessiveTilt,
};

struct Command {
  float linear_mps{0.0F};
  float yaw_radps{0.0F};
};

struct Sensors {
  bool remote_ok{false};
  bool emergency_stop{true};
  float battery_v{0.0F};
  float motor_temp_c{25.0F};
  float chassis_tilt_deg{0.0F};
  bool imu_fresh{false};
  bool encoders_fresh{false};
  float left_wheel_mps{0.0F};
  float right_wheel_mps{0.0F};
  float yaw_rate_radps{0.0F};
  bool current_protection_ready{false};
  bool hardware_current_trip{true};
  bool current_over_limit{false};
  bool motor_stalled{false};
  float left_motor_current_a{0.0F};
  float right_motor_current_a{0.0F};
};

struct Output {
  float left_normalized{0.0F};
  float right_normalized{0.0F};
  float limited_linear_mps{0.0F};
  float limited_yaw_radps{0.0F};
  float left_target_mps{0.0F};
  float right_target_mps{0.0F};
  float power_limit{0.0F};
  bool enabled{false};
  Fault fault{Fault::None};
};

struct Config {
  float track_m{0.31F};
  float max_wheel_speed_mps{0.50F};
  float max_linear_accel_mps2{0.20F};
  float max_yaw_accel_radps2{0.80F};
  float minimum_battery_v{13.2F};
  float battery_derate_start_v{14.3F};
  float minimum_power_limit{0.35F};
  float maximum_motor_voltage_v{12.0F};
  float maximum_motor_temp_c{75.0F};
  float maximum_tilt_deg{30.0F};
  bool require_motion_feedback{false};
  bool require_current_feedback{false};
  float wheel_speed_kp{0.35F};
  float wheel_speed_ki_per_s{0.80F};
  float yaw_rate_kp_m_per_rad{0.08F};
  float maximum_yaw_correction_mps{0.10F};
  float maximum_yaw_sensor_disagreement_radps{0.80F};
};

class Controller {
 public:
  explicit Controller(Config config = {});
  Output update(float dt_s, Command command, Sensors sensors);
  bool resetFault(const Sensors& sensors);
  Fault latchedFault() const { return latched_fault_; }

 private:
  Fault checkFault(const Sensors& sensors) const;
  static float clamp(float value, float low, float high);
  static float slew(float current, float target, float max_delta);

  Config config_;
  Fault latched_fault_{Fault::None};
  float linear_mps_{0.0F};
  float yaw_radps_{0.0F};
  float left_integral_{0.0F};
  float right_integral_{0.0F};
};

const char* faultName(Fault fault);
bool commandIsZeroForReset(const Command& command, float epsilon = 0.001F);

}  // namespace bb8
