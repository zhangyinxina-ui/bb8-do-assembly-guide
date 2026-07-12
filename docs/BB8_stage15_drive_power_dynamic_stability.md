# BB-8 Stage 15: Drive Power and Dynamic Stability

> Result: **PASS_ANALYTICAL_ONLY**. The stage-15 design point passes the current assumptions, but motor, driver, fuse, contactor, E-stop, wheel/shell traction and sealed-shell thermal tests all remain `NOT_RUN`.

## New physical contracts

- Blender now contains two 52 × 34 × 16 mm generic motor-driver installation envelopes, two heatsinks and eight M3 standoffs. No driver product is frozen.
- The explicit main-power path is battery positive → externally reachable service disconnect → main fuse → normally-open main contactor → left/right drivers → motors.
- The E-stop path has two normally-closed channels, a monitored safety relay, contactor feedback, manual reset and both driver-enable branches. First tests require a wired tether; wireless alone is not accepted.
- Fuse current, DC contactor breaking capacity, continuous/peak driver current and regenerative-energy handling stay `TBD` until measured stall-current and thermal tests are available.

## 3° uphill turning design point

- Nominal mass 8.463 kg; effective translational mass including shell rotation 9.263 kg.
- Grade 3.0°, longitudinal acceleration 0.20 m/s², speed 0.30 m/s and turn radius 0.80 m.
- Required uphill force 8.68 N; required torque 0.289 N·m per motor; continuous-torque margin 2.07×.
- Wheel/shell traction margin 12.90×; resultant steady lean 4.22° versus a 12.0° contract.
- Inner/outer wheel surface speeds 0.242/0.358 m/s; 2.5g vertical plus 1g lateral head-shock retention margin 2.33×.
- At a 2× continuous-torque margin, the analytical grade ceiling is about 4.50° at zero acceleration and 3.21° while accelerating at 0.20 m/s².

## Checks

- PASS — continuous_torque
- PASS — wheel_shell_traction
- PASS — resultant_lean
- PASS — wheel_speed
- PASS — magnetic_head_combined_shock

## Constraints that remain

- Without a mechanical parking brake, a spherical robot cannot hold position on a slope after power removal; `unpowered_slope_hold=NOT_PROVIDED`.
- Three degrees is an analytical design point, not physical certification. Floor tests still begin level at 0.1 m/s with a wired E-stop and soft barriers.
- Before purchasing the final electronics, measure motor stall current, sealed-shell driver temperature, wheel/shell friction, contactor interruption and emergency stopping distance.
