#include "../firmware/controller_core.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

namespace {

constexpr float kDt = 0.005F;
constexpr float kPi = 3.14159265358979323846F;

float quantize(float value, float resolution) {
  return std::round(value / resolution) * resolution;
}

struct Plant {
  float left_mps{0.0F};
  float right_mps{0.0F};
  float x_m{0.0F};
  float y_m{0.0F};
  float heading_rad{0.0F};
  float motor_temp_c{25.0F};

  void update(const bb8::Output& output, const bb8::Config& config) {
    constexpr float motor_time_constant_s = 0.18F;
    constexpr float rolling_deadband_mps = 0.012F;
    auto equilibrium = [&](float normalized) {
      const float signed_speed = normalized * config.max_wheel_speed_mps;
      const float magnitude = std::max(0.0F, std::abs(signed_speed) - rolling_deadband_mps);
      return std::copysign(magnitude, signed_speed);
    };

    left_mps += (equilibrium(output.left_normalized) - left_mps) *
                (kDt / motor_time_constant_s);
    right_mps += (equilibrium(output.right_normalized) - right_mps) *
                 (kDt / motor_time_constant_s);
    const float linear = 0.5F * (left_mps + right_mps);
    const float yaw = (right_mps - left_mps) / config.track_m;
    heading_rad += yaw * kDt;
    x_m += linear * std::cos(heading_rad) * kDt;
    y_m += linear * std::sin(heading_rad) * kDt;
    const float heating = 8.0F *
        (output.left_normalized * output.left_normalized +
         output.right_normalized * output.right_normalized);
    motor_temp_c += (heating - (motor_temp_c - 25.0F) / 18.0F) * kDt;
  }
};

bb8::Command commandAt(float time_s) {
  if (time_s < 1.0F) return {};
  if (time_s < 4.5F) return {.linear_mps = 0.30F};
  if (time_s < 7.1F) return {.linear_mps = 0.25F, .yaw_radps = 0.60F};
  if (time_s < 8.5F) return {};
  return {.linear_mps = 0.20F};
}

}  // namespace

int main(int argc, char** argv) {
  const std::string output_path = argc > 1 ? argv[1] : "closed_loop_telemetry.csv";
  bb8::Config config;
  config.require_motion_feedback = true;
  bb8::Controller controller(config);
  Plant plant;
  std::ofstream csv(output_path);
  assert(csv.good());
  csv << "time_s,command_linear_mps,command_yaw_radps,left_target_mps,right_target_mps,"
         "left_measured_mps,right_measured_mps,linear_measured_mps,yaw_imu_radps,"
         "left_pwm,right_pwm,battery_v,motor_temp_c,x_m,y_m,heading_deg,fault\n";
  csv << std::fixed << std::setprecision(6);

  float heading_at_turn_start = 0.0F;
  float heading_after_turn = 0.0F;
  float cruise_error_sum_sq = 0.0F;
  int cruise_samples = 0;
  bool stale_fault_seen = false;
  float speed_at_fault = 0.0F;
  float speed_after_stop = 0.0F;

  for (int step = 0; step <= static_cast<int>(11.0F / kDt); ++step) {
    const float time_s = step * kDt;
    const bb8::Command command = commandAt(time_s);
    const float encoder_left = quantize(plant.left_mps, 0.002F);
    const float encoder_right = quantize(plant.right_mps, 0.002F);
    const float encoder_yaw = (encoder_right - encoder_left) / config.track_m;
    const float battery_v = 14.8F - 0.55F *
        (std::abs(plant.left_mps) + std::abs(plant.right_mps)) /
        config.max_wheel_speed_mps;
    bb8::Sensors sensors{
        .remote_ok = true,
        .emergency_stop = false,
        .battery_v = battery_v,
        .motor_temp_c = plant.motor_temp_c,
        .chassis_tilt_deg = 2.0F * std::sin(2.0F * kPi * time_s),
        .imu_fresh = time_s < 10.0F,
        .encoders_fresh = true,
        .left_wheel_mps = encoder_left,
        .right_wheel_mps = encoder_right,
        .yaw_rate_radps = encoder_yaw * 0.995F,
    };
    const bb8::Output output = controller.update(kDt, command, sensors);
    const float linear = 0.5F * (plant.left_mps + plant.right_mps);

    if (std::abs(time_s - 4.5F) < kDt * 0.5F) heading_at_turn_start = plant.heading_rad;
    if (std::abs(time_s - 8.4F) < kDt * 0.5F) heading_after_turn = plant.heading_rad;
    if (time_s >= 3.0F && time_s < 4.4F) {
      const float error = linear - 0.30F;
      cruise_error_sum_sq += error * error;
      ++cruise_samples;
    }
    if (time_s >= 10.0F && output.fault == bb8::Fault::MotionSensorStale) {
      if (!stale_fault_seen) speed_at_fault = std::abs(linear);
      stale_fault_seen = true;
      assert(output.left_normalized == 0.0F && output.right_normalized == 0.0F);
    }
    if (std::abs(time_s - 10.8F) < kDt * 0.5F) speed_after_stop = std::abs(linear);

    csv << time_s << ',' << command.linear_mps << ',' << command.yaw_radps << ','
        << output.left_target_mps << ',' << output.right_target_mps << ','
        << plant.left_mps << ',' << plant.right_mps << ',' << linear << ','
        << sensors.yaw_rate_radps << ',' << output.left_normalized << ','
        << output.right_normalized << ',' << battery_v << ',' << plant.motor_temp_c << ','
        << plant.x_m << ',' << plant.y_m << ','
        << plant.heading_rad * 180.0F / kPi << ',' << bb8::faultName(output.fault) << '\n';
    plant.update(output, config);
  }

  const float cruise_rms = std::sqrt(cruise_error_sum_sq / cruise_samples);
  const float turn_deg = (heading_after_turn - heading_at_turn_start) * 180.0F / kPi;
  assert(cruise_rms < 0.025F);
  assert(turn_deg > 84.0F && turn_deg < 96.0F);
  assert(stale_fault_seen && speed_at_fault > 0.10F);
  assert(speed_after_stop < 0.005F);
  assert(plant.motor_temp_c < config.maximum_motor_temp_c);

  std::cout << "PASS closed_loop_sim cruise_rms=" << cruise_rms
            << "m/s turn=" << turn_deg << "deg stale_stop_0.8s=" << speed_after_stop
            << "m/s telemetry=" << output_path << '\n';
  return 0;
}
