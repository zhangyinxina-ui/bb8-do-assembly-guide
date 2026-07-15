# BB-8 Stage 21: Tangent Wheel and Preload Cassette Gate

> **HOLD_PHYSICAL_CONTACT_BELT_BEARING_AND_CHASSIS_INTEGRATION_REQUIRED**. Exact geometry and reference packaging screens pass, but the open Blender master was not modified and no fabricated contact evidence exists.

## Superseding the old wheel-contact result

- The current 96 × 26 mm powered wheel is a finite cylinder. The old centre-radius-plus-48 mm audit treated it as a sphere and overstates its support by **5.072 mm**.
- The exact finite-cylinder support leaves at least **5.070 mm** to the inner shell, so the historical powered-wheel contact pass is superseded.
- The current axle misses the local shell tangent plane by **48.800°**, driving contact toward the edge and creating scrub risk.

## Selected architecture: tangent axle plus parallel synchronous belt

- The wheel axle is tangent to the local shell. The parallel motor axis moves 80 mm radially inward and drives 1:1 by belt, avoiding direct tangent packaging of the 125.2 mm motor envelope.
- Equal 24T, 5 mm-pitch pulleys at 80 mm centre distance calculate to **280.0 mm / 56 teeth**, represented by a 5M-280-15 candidate. Supplier capacity, pretension and guarding remain open.
- The motor envelope support is 161.16 mm, leaving 92.84 mm nominal shell clearance. This is an envelope screen, not a current-chassis clash pass.

## Crown and radial setting

- A 26 mm-wide wheel needs at least **0.333 mm** edge drop in the 254 mm inner sphere. The reference uses a 0.750 mm parabolic crown and leaves **0.417 mm** analytical edge clearance.
- Total travel is **12.0 mm**: 3 mm inward and 9 mm outward from nominal contact. That covers the 5.5 mm Stage-20 stack with **3.5 mm** reserve.
- The M6×1 screw gives 1 mm per turn and 0.25 mm per quarter-turn. Turns only find contact; a force fixture must set 60–100 N per side, target 80 N, with no more than 10 N left-right mismatch before four M6 clamps are locked.
- The 9 mm outward reserve is not allowable tire compression. After contact, adjust by measured force only.

## Load and control gates

- 1.2 N·m gives 25.0 N at each wheel. With 3× shock, 2× slip factor and μ=0.15, the minimum clamp demand is **1000 N** total or 250 N per M6. This is demand only, not a bolt/preload pass.
- Ideal 12 mm shaft torsional shear demand is 10.61 MPa at 3× torque; keyway, material, hub and fatigue remain open.
- Wheel-centre track remains 310.0 mm, while nominal shell contact-patch spacing is **382.2 mm**, 72.2 mm above the firmware's current 310 mm parameter. Do not copy the analytical value into firmware; identify effective track from physical yaw response.

## Assembly sequence

1. Machine deburred fit-test plates from the reference DXF; dry-fit side plates, 6001 bearings, 12 mm shaft and wheel pulley.
2. Fit the motor pulley and candidate 5M-280-15 belt, then hand-turn one revolution to inspect tracking. Never power it without the guard.
3. Retract both slides to the inner stops, install in the shell, advance to first contact and use a force fixture—not turns—to set the 80 N target.
4. Lock four M6 clamps, remeasure preload and belt tracking, then run raised-wheel low-speed, E-stop and thermal tests.
5. Identify effective track from low-speed physical yaw data before changing the controller.

Open freeze gates: 13. Manufacturing release is false and all nineteen physical commissioning gates remain incomplete.

The machine contract, HOLD result, 0.5 mm adjustment sweep, BOM, OpenSCAD, DXF/STL and verifier are stored with the project.
