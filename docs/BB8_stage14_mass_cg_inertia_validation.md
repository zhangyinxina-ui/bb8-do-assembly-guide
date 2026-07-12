# BB-8 Stage 14: Mass, Centre of Mass and Inertia Validation

> Result: **PASS_WITH_MASS_AND_ACCELERATION_DERATING**. With the sealed low ballast cassette, even the worst enumerated mass corner keeps the centre of mass below the sphere centre. Every assumed mass must still be replaced by a measured value.

## Model-driven results

- Nominal total mass: **8.463 kg**; input range 6.375–10.628 kg.
- Nominal CoM: x=1.9 mm, y=1.4 mm, z=-56.2 mm.
- Exhaustive corner range: z=-74.5 to -27.7 mm; worst-case offset below centre 27.7 mm.
- CoM inertias: Ixx=0.2386, Iyy=0.2703, Izz=0.1085 kg·m².
- Restoring torque at 10°: 0.81 N·m; small-angle pitch period: 1.51 s.

## Ballast and drive constraints

- Blender now contains a 120 × 70 × 24 mm sealed steel ballast cassette, nominally 1.50 kg, with a centre hanger, two retention straps and four captive M5 fasteners.
- With 0.6 N·m continuous torque, a 2× margin and the nominal mass, the acceleration ceiling is **0.703 m/s²**; the controller target is frozen at 0.70 m/s².
- The equivalent steady lean at 0.70 m/s² is 4.08°. The ±4° animation is illustrative, not a control limit.
- Reaching the old unverified 110 mm offset would need about **4.14 kg** more at z=-220 mm and would reduce acceleration headroom, so 110 mm is no longer presented as a design fact.

## Checks

- PASS — nominal_com_offset
- PASS — worst_case_com_offset
- PASS — continuous_torque_derated_acceleration

## Evidence boundary

All 17 mass groups remain `NOT_RUN`, supplier-conflicted, or design assumptions. Before fabrication approval, weigh every component and measure whole-system CoM by suspension or four-scale testing, then regenerate this report from those measurements.
