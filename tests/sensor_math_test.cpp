#include "../firmware/sensor_math.h"

#include <cassert>
#include <cmath>
#include <iostream>

int main() {
  using bb8::quadratureDelta;

  const unsigned forward[] = {0, 1, 3, 2, 0};
  const unsigned reverse[] = {0, 2, 3, 1, 0};
  int forward_sum = 0;
  int reverse_sum = 0;
  for (int i = 1; i < 5; ++i) {
    forward_sum += quadratureDelta(forward[i - 1], forward[i]);
    reverse_sum += quadratureDelta(reverse[i - 1], reverse[i]);
  }
  assert(forward_sum == 4);
  assert(reverse_sum == -4);
  assert(quadratureDelta(0, 3) == 0);  // Two-bit jump is rejected as invalid.

  const float speed = bb8::countsToWheelSpeedMps(264, 1056.0F, 0.096F, 0.25F);
  assert(std::abs(speed - 0.3015929F) < 1.0e-5F);
  assert(bb8::countsToWheelSpeedMps(1, 0.0F, 0.096F, 0.005F) == 0.0F);

  const float one_rad_s_raw = 65.5F * 180.0F / 3.14159265358979323846F;
  assert(std::abs(bb8::mpu6050GyroRawToRadps(
      static_cast<std::int16_t>(std::round(one_rad_s_raw + 120.0F)), 120.0F) - 1.0F) < 0.001F);
  assert(std::abs(bb8::accelerometerTiltDeg(0, 0, 8192)) < 1.0e-5F);
  assert(std::abs(bb8::accelerometerTiltDeg(8192, 0, 8192) - 45.0F) < 1.0e-4F);
  assert(bb8::accelerationNormPlausible(0, 0, 8192));
  assert(!bb8::accelerationNormPlausible(0, 0, 2000));

  std::uint32_t demand_start = 0;
  assert(bb8::encoderResponseFresh(0.20F, 0.05F, 100U, 1000U, 750U, demand_start));
  assert(demand_start == 1000U);  // First demand opens a bounded response grace period.
  assert(!bb8::encoderResponseFresh(0.20F, 0.05F, 100U, 1800U, 750U, demand_start));
  assert(bb8::encoderResponseFresh(0.20F, 0.05F, 1700U, 1800U, 750U, demand_start));
  assert(bb8::encoderResponseFresh(0.0F, 0.05F, 1700U, 2000U, 750U, demand_start));
  assert(demand_start == 0U);

  std::cout << "PASS sensor_math: quadrature, wheel speed, IMU conversion, and encoder response timeout\n";
  return 0;
}
