#include "../firmware/power_safety.h"

#include <cassert>
#include <iostream>

int main() {
  bb8::PowerSafetyMonitor monitor;
  assert(!monitor.configure(0.5F, 0.3F, 0.2F));
  assert(!monitor.configure(10.0F, 11.0F, 0.2F));
  assert(!monitor.configure(10.0F, 6.0F, 0.05F));
  assert(monitor.configure(10.0F, 6.0F, 0.30F));

  bb8::PowerProtectionInputs inputs{
      .sensors_fresh = true,
      .hardware_trip = false,
      .left_current_a = 3.0F,
      .right_current_a = 3.2F,
      .left_target_mps = 0.25F,
      .right_target_mps = 0.25F,
      .left_measured_mps = 0.24F,
      .right_measured_mps = 0.24F,
  };
  auto status = monitor.update(0.005F, inputs);
  assert(status.configured && status.sensors_fresh && !status.hardware_trip);
  assert(!status.over_current && !status.stalled);

  inputs.left_current_a = 10.5F;
  status = monitor.update(0.005F, inputs);
  assert(status.over_current);

  inputs.left_current_a = 6.5F;
  inputs.left_measured_mps = 0.0F;
  for (int i = 0; i < 59; ++i) {
    status = monitor.update(0.005F, inputs);
    assert(!status.stalled);
  }
  status = monitor.update(0.005F, inputs);
  assert(status.stalled && status.left_stall_s + 1.0e-6F >= 0.30F);

  inputs.left_measured_mps = 0.20F;
  status = monitor.update(0.005F, inputs);
  assert(!status.stalled && status.left_stall_s == 0.0F);

  inputs.hardware_trip = true;
  status = monitor.update(0.005F, inputs);
  assert(status.hardware_trip && status.left_stall_s == 0.0F);
  inputs.hardware_trip = false;
  inputs.sensors_fresh = false;
  status = monitor.update(0.005F, inputs);
  assert(!status.sensors_fresh && !status.over_current && !status.stalled);

  std::cout << "PASS power_safety: explicit configuration, immediate trips, stale refusal, and timed stall\n";
  return 0;
}
