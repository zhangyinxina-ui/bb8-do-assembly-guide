#pragma once

namespace bb8 {

struct PowerProtectionInputs {
  bool sensors_fresh{false};
  bool hardware_trip{true};
  float left_current_a{0.0F};
  float right_current_a{0.0F};
  float left_target_mps{0.0F};
  float right_target_mps{0.0F};
  float left_measured_mps{0.0F};
  float right_measured_mps{0.0F};
};

struct PowerProtectionStatus {
  bool configured{false};
  bool sensors_fresh{false};
  bool hardware_trip{true};
  bool over_current{false};
  bool stalled{false};
  float left_stall_s{0.0F};
  float right_stall_s{0.0F};
};

class PowerSafetyMonitor {
 public:
  bool configure(float instantaneous_trip_a, float stall_current_a, float stall_timeout_s);
  void clearConfiguration();
  PowerProtectionStatus update(float dt_s, const PowerProtectionInputs& inputs);
  bool configured() const { return configured_; }
  float instantaneousTripA() const { return instantaneous_trip_a_; }

 private:
  static bool finiteInRange(float value, float low, float high);
  static bool stallCondition(float current_a, float target_mps, float measured_mps,
                             float stall_current_a);

  bool configured_{false};
  float instantaneous_trip_a_{0.0F};
  float stall_current_a_{0.0F};
  float stall_timeout_s_{0.0F};
  float left_stall_s_{0.0F};
  float right_stall_s_{0.0F};
};

}  // namespace bb8
