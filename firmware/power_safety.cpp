#include "power_safety.h"

#include <algorithm>
#include <cmath>

namespace bb8 {
namespace {
constexpr float kMinimumInstantaneousTripA = 1.0F;
constexpr float kMaximumInstantaneousTripA = 30.0F;
constexpr float kMinimumStallTimeoutS = 0.10F;
constexpr float kMaximumStallTimeoutS = 3.0F;
constexpr float kMinimumStallTargetMps = 0.10F;
constexpr float kMaximumStallSpeedMps = 0.025F;
}  // namespace

bool PowerSafetyMonitor::finiteInRange(float value, float low, float high) {
  return std::isfinite(value) && value >= low && value <= high;
}

bool PowerSafetyMonitor::configure(
    float instantaneous_trip_a,
    float stall_current_a,
    float stall_timeout_s) {
  const bool valid = finiteInRange(
                         instantaneous_trip_a,
                         kMinimumInstantaneousTripA,
                         kMaximumInstantaneousTripA) &&
                     finiteInRange(stall_current_a, 0.5F, instantaneous_trip_a) &&
                     finiteInRange(
                         stall_timeout_s,
                         kMinimumStallTimeoutS,
                         kMaximumStallTimeoutS);
  clearConfiguration();
  if (!valid) return false;
  configured_ = true;
  instantaneous_trip_a_ = instantaneous_trip_a;
  stall_current_a_ = stall_current_a;
  stall_timeout_s_ = stall_timeout_s;
  return true;
}

void PowerSafetyMonitor::clearConfiguration() {
  configured_ = false;
  instantaneous_trip_a_ = 0.0F;
  stall_current_a_ = 0.0F;
  stall_timeout_s_ = 0.0F;
  left_stall_s_ = 0.0F;
  right_stall_s_ = 0.0F;
}

bool PowerSafetyMonitor::stallCondition(
    float current_a,
    float target_mps,
    float measured_mps,
    float stall_current_a) {
  return std::abs(current_a) >= stall_current_a &&
         std::abs(target_mps) >= kMinimumStallTargetMps &&
         std::abs(measured_mps) <= kMaximumStallSpeedMps;
}

PowerProtectionStatus PowerSafetyMonitor::update(
    float dt_s,
    const PowerProtectionInputs& inputs) {
  PowerProtectionStatus status;
  status.configured = configured_;
  status.sensors_fresh = inputs.sensors_fresh;
  status.hardware_trip = inputs.hardware_trip;

  if (!configured_ || !inputs.sensors_fresh || inputs.hardware_trip || dt_s <= 0.0F) {
    left_stall_s_ = 0.0F;
    right_stall_s_ = 0.0F;
    return status;
  }

  status.over_current =
      std::abs(inputs.left_current_a) >= instantaneous_trip_a_ ||
      std::abs(inputs.right_current_a) >= instantaneous_trip_a_;

  left_stall_s_ = stallCondition(
                      inputs.left_current_a,
                      inputs.left_target_mps,
                      inputs.left_measured_mps,
                      stall_current_a_)
                      ? left_stall_s_ + dt_s
                      : 0.0F;
  right_stall_s_ = stallCondition(
                       inputs.right_current_a,
                       inputs.right_target_mps,
                       inputs.right_measured_mps,
                       stall_current_a_)
                       ? right_stall_s_ + dt_s
                       : 0.0F;
  status.left_stall_s = left_stall_s_;
  status.right_stall_s = right_stall_s_;
  constexpr float kTimerComparisonEpsilonS = 1.0e-6F;
  status.stalled = left_stall_s_ + kTimerComparisonEpsilonS >= stall_timeout_s_ ||
                   right_stall_s_ + kTimerComparisonEpsilonS >= stall_timeout_s_;
  return status;
}

}  // namespace bb8
