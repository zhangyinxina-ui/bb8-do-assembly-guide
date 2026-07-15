# Stage 21 tangent-wheel preload cassette

This directory contains **reference CAD only** for the Stage-21 BB-8 powered-wheel correction. It is not a fabrication release.

The current Blender wheel is a 96 × 26 mm finite cylinder with its axle along global X. Exact support geometry leaves about 5.07 mm to the 254 mm inner shell and the axle misses the local tangent plane by about 48.8°. The reference cassette therefore:

- cants the wheel axle tangent to the local shell;
- moves the IG42 motor 80 mm radially inward on a parallel axis;
- uses candidate equal 24T, 5 mm-pitch pulleys and a 280 mm / 56-tooth belt;
- carries the wheel on two candidate 6001-2RS bearings and a 12 mm shaft;
- gives 12 mm radial travel with an M6×1 jackscrew, hard stops and four M6 clamps;
- uses a 0.75 mm parabolic crown drop across the 26 mm wheel width.

## Build the reference outputs

Run:

```sh
tools/build_stage21_wheel_preload_cad.sh
```

When OpenSCAD is available, the script exports the assembly, fixed/moving plates, jackscrew block, crowned-wheel envelope, two DXF profiles and a review PNG into `outputs/`.

If OpenSCAD is unavailable, the checked-in Python fallback creates exact 2D DXF cut profiles, an exact crowned-wheel STL, reference-envelope STL files and the review PNG without installing anything. In that fallback, the plate STL files are deliberately named `*_envelope.stl`: use the DXF—not the envelope STL—for holes and slots.

## Safety and release boundary

The DXF and STL files are fit references. Do not manufacture a running robot from them until the open gates in `engineering/stage21_wheel_preload_contract.json` are closed. In particular, bearing fits, shaft/hub retention, belt rating and tension, guards, plate material, M6 preload, shell contact strength, tire compound and measured 60–100 N wheel preload are not frozen. The current open Blender master is intentionally not modified by this package.
