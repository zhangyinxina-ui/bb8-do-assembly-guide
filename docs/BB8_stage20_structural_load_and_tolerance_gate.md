# BB-8 Stage 20: Structural Load and Tolerance Gate

> **HOLD_JOINT_TOLERANCE_MATERIAL_AND_PHYSICAL_VALIDATION_REQUIRED**. Current digital geometry and closed-form screening pass, but manufacturing release remains false; material, joint, tolerance and physical evidence are open.

## Correcting the legacy geometry

- The current Stage-19 fabrication manifest contains a **Ø24 × 340 mm** magnetic-mast envelope.
- Stage 2 still analyses a **Ø12/Ø8 × 300 mm** aluminium tube, so that mechanical result is not current-model evidence.
- Stage 20 does not touch the open Blender session. It screens a Ø24/Ø20 × 340 mm tube candidate while keeping the bore, material lot and joints unfrozen.

## 2.5 g / 1.0 g analytical screening

| Load path | Analytical result | Evidence boundary |
|---|---:|---|
| Ø24/Ø20 mast candidate | 3.273 MPa, 0.154 mm tip deflection, 84.33× yield factor | No joints, welds, holes or strain data |
| Two Ø12/Ø8 brace candidates | 6.191 N each, 974.8× Euler factor | Pinned ends and bore are candidates |
| Two 380 × 18 × 12 mm rails | 22.814 MPa, 0.670 mm deflection, 12.10× yield factor | Simply supported symmetric sharing; joints omitted |
| 120 × 8 × 12 mm crossmember | 8.105 MPa, 0.024 mm deflection | One-quarter total-shock allocation only |
| 4 mm motor plate / 4×M4 PCD35 | 18.25 N resultant per M4 and 1.140 MPa plate-hole bearing demand | Demand only; M4 grade, preload, hole size and edge distance unfrozen |
| Eight nominal latches | 640 N, 3.08× total 2.5 g shock | 80 N per latch is unmeasured |

## Modal, fatigue and tolerance gates

- The unbraced-credit mast estimate is **40.47 Hz**, 9.79× the 248 rpm motor rotational frequency; hammer testing is still required.
- Ideal 6061-T6/T651 base-material fatigue screens are 29.64× for the mast and 4.25× for a rail. Welds, holes, surface condition and the real duty spectrum are excluded.
- The wheel-to-shell stack requires **5.5 mm** radial adjustment. The current digital geometry provides 0.0 mm, leaving a **5.5 mm** shortfall, so contact preload cannot be frozen.

## Material source and release boundary

Kaiser typical 6061-T6/T651 sheet/plate values—68.3 GPa elastic modulus, 276 MPa yield and 97 MPa reversed-stress fatigue endurance at 5×10^8 cycles—are used only for screening: https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1015/Kaiser_Aluminum_6061_Sheet_Coil_and_Plate.pdf. They are not certificates for purchased tube, bar, weld heat-affected zones or machined parts.

Open freeze gates: 15. Material certificates, joint details, fasteners, wheel preload adjustment, shell contact strength, strain/impact/modal/endurance work and all nineteen physical commissioning gates are required before fabrication release can be considered.

Machine result: `engineering/stage20_structural_load_results.json`; envelope sweep: `engineering/stage20_structural_load_sweep.csv`.
