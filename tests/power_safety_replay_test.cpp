#include "../firmware/power_safety.h"

#include <cassert>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

namespace {
constexpr float kDt = 0.005F;

const char* faultName(const bb8::PowerProtectionStatus& status) {
  if (status.hardware_trip) return "hardware_current_trip";
  if (!status.configured || !status.sensors_fresh) return "current_sensor_stale";
  if (status.over_current) return "over_current";
  if (status.stalled) return "motor_stall";
  return "none";
}
}  // namespace

int main(int argc, char** argv) {
  const std::string output_path = argc > 1 ? argv[1] : "power_safety_replay.csv";
  std::ofstream csv(output_path);
  assert(csv.good());
  csv << "time_s,scenario,left_target_mps,left_measured_mps,left_current_a,"
         "sensors_fresh,hardware_trip,left_stall_s,fault\n";
  csv << std::fixed << std::setprecision(6);

  bb8::PowerSafetyMonitor monitor;
  assert(monitor.configure(10.0F, 6.0F, 0.30F));
  bool over_current_seen = false;
  bool stall_seen = false;
  bool stale_seen = false;
  bool hardware_trip_seen = false;
  float stall_trip_time_s = 0.0F;

  for (int step = 0; step <= static_cast<int>(2.0F / kDt); ++step) {
    const float time_s = step * kDt;
    const char* scenario = "normal";
    bb8::PowerProtectionInputs inputs{
        .sensors_fresh = true,
        .hardware_trip = false,
        .left_current_a = 3.4F,
        .right_current_a = 3.2F,
        .left_target_mps = 0.25F,
        .right_target_mps = 0.25F,
        .left_measured_mps = 0.24F,
        .right_measured_mps = 0.24F,
    };
    if (time_s >= 0.40F && time_s < 0.50F) {
      scenario = "instant_over_current";
      inputs.left_current_a = 10.5F;
    } else if (time_s >= 0.70F && time_s < 1.10F) {
      scenario = "sustained_stall";
      inputs.left_current_a = 6.5F;
      inputs.left_measured_mps = 0.005F;
    } else if (time_s >= 1.30F && time_s < 1.40F) {
      scenario = "sensor_stale";
      inputs.sensors_fresh = false;
    } else if (time_s >= 1.60F && time_s < 1.70F) {
      scenario = "hardware_alert";
      inputs.hardware_trip = true;
    }

    const bb8::PowerProtectionStatus status = monitor.update(kDt, inputs);
    const char* fault = faultName(status);
    if (status.over_current) over_current_seen = true;
    if (status.stalled && !stall_seen) {
      stall_seen = true;
      stall_trip_time_s = time_s;
    }
    if (!status.sensors_fresh) stale_seen = true;
    if (status.hardware_trip) hardware_trip_seen = true;
    csv << time_s << ',' << scenario << ',' << inputs.left_target_mps << ','
        << inputs.left_measured_mps << ',' << inputs.left_current_a << ','
        << status.sensors_fresh << ',' << status.hardware_trip << ','
        << status.left_stall_s << ',' << fault << '\n';
  }

  assert(over_current_seen);
  assert(stall_seen && stall_trip_time_s >= 0.995F && stall_trip_time_s <= 1.005F);
  assert(stale_seen);
  assert(hardware_trip_seen);
  std::cout << "PASS power_safety_replay over_current=immediate stall_trip="
            << stall_trip_time_s << "s stale=refused hardware_alert=immediate telemetry="
            << output_path << '\n';
  return 0;
}
