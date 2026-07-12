#pragma once

#include <cstdint>

namespace bb8 {

inline constexpr std::int8_t quadratureDelta(std::uint8_t previous, std::uint8_t current) {
  switch (((previous & 0x03U) << 2U) | (current & 0x03U)) {
    case 0x01:
    case 0x07:
    case 0x0E:
    case 0x08:
      return 1;
    case 0x02:
    case 0x0B:
    case 0x0D:
    case 0x04:
      return -1;
    default:
      return 0;
  }
}

float countsToWheelSpeedMps(
    std::int32_t count_delta,
    float counts_per_wheel_revolution,
    float wheel_diameter_m,
    float dt_s);
float mpu6050GyroRawToRadps(std::int16_t raw, float bias_raw);
float accelerometerTiltDeg(std::int16_t ax, std::int16_t ay, std::int16_t az);
bool accelerationNormPlausible(
    std::int16_t ax,
    std::int16_t ay,
    std::int16_t az,
    float lsb_per_g = 8192.0F);
bool encoderResponseFresh(
    float expected_mps,
    float demand_threshold_mps,
    std::uint32_t last_edge_us,
    std::uint32_t now_us,
    std::uint32_t response_timeout_us,
    std::uint32_t& demand_start_us);

}  // namespace bb8
