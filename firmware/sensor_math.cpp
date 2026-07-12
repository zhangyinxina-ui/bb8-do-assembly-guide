#include "sensor_math.h"

#include <cmath>

namespace bb8 {
namespace {
constexpr float kPi = 3.14159265358979323846F;
}

float countsToWheelSpeedMps(
    std::int32_t count_delta,
    float counts_per_wheel_revolution,
    float wheel_diameter_m,
    float dt_s) {
  if (counts_per_wheel_revolution <= 0.0F || wheel_diameter_m <= 0.0F || dt_s <= 0.0F) {
    return 0.0F;
  }
  const float revolutions = static_cast<float>(count_delta) / counts_per_wheel_revolution;
  return revolutions * kPi * wheel_diameter_m / dt_s;
}

float mpu6050GyroRawToRadps(std::int16_t raw, float bias_raw) {
  constexpr float raw_per_degree_per_second = 65.5F;  // MPU6050 FS_SEL=1, ±500 °/s.
  return ((static_cast<float>(raw) - bias_raw) / raw_per_degree_per_second) * kPi / 180.0F;
}

float accelerometerTiltDeg(std::int16_t ax, std::int16_t ay, std::int16_t az) {
  const float horizontal = std::hypot(static_cast<float>(ax), static_cast<float>(ay));
  return std::atan2(horizontal, std::abs(static_cast<float>(az))) * 180.0F / kPi;
}

bool accelerationNormPlausible(
    std::int16_t ax,
    std::int16_t ay,
    std::int16_t az,
    float lsb_per_g) {
  if (lsb_per_g <= 0.0F) return false;
  const float norm_g = std::sqrt(
      static_cast<float>(ax) * ax + static_cast<float>(ay) * ay +
      static_cast<float>(az) * az) / lsb_per_g;
  return norm_g >= 0.75F && norm_g <= 1.25F;
}

bool encoderResponseFresh(
    float expected_mps,
    float demand_threshold_mps,
    std::uint32_t last_edge_us,
    std::uint32_t now_us,
    std::uint32_t response_timeout_us,
    std::uint32_t& demand_start_us) {
  if (std::abs(expected_mps) < demand_threshold_mps) {
    demand_start_us = 0;
    return true;
  }
  if (demand_start_us == 0) demand_start_us = now_us;
  const bool startup_grace = now_us - demand_start_us < response_timeout_us;
  const bool edge_after_demand = last_edge_us - demand_start_us < 0x80000000U;
  const bool recent_edge = now_us - last_edge_us < response_timeout_us;
  return startup_grace || (edge_after_demand && recent_edge);
}

}  // namespace bb8
