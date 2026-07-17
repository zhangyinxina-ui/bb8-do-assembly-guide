# Stage 22 drivetrain interface

This package corrects the Stage-21 non-catalogue `5M-280-15` belt candidate and closes the analytical bearing, shaft, key and rail-interface load path. It is **reference CAD only**, not a fabrication release.

The selected reference architecture uses:

- Gates `5MGT-300-15`, product `92706002`, 300 mm pitch length, 60 teeth and 15 mm width;
- equal candidate 24-tooth 5MGT pulleys at 90 mm centre distance;
- two candidate 6001 sealed bearings per cassette, 38 mm bearing-centre span;
- a 12 mm keyed shaft with candidate 4 × 4 × 20 mm DIN 6885 key engagement;
- two 6 mm reamed dowels, four M6 clamps and a hard stop per cassette;
- a removable outboard pulley and guard for safe belt installation.

## Build the reference outputs

Run:

```sh
tools/build_stage22_drivetrain_interface_cad.sh
```

The dependency-light builder creates two nominal DXF profiles, a keyed-shaft envelope STL, an assembly-envelope STL, an engineering review PNG and a SHA-256 manifest in `outputs/`. The editable OpenSCAD source is supplied alongside them.

## Assembly order

1. Machine the shaft, keyway, hubs, bearing seats, retainers and rail bracket only after supplier fit tables, material certificates and GD&T are frozen.
2. Press or slide the selected bearings using the supplier-prescribed ring support; retain the outboard bearing and preserve at least 0.3 mm axial float at the inboard bearing.
3. Install the wheel hub between the bearing supports, then fit the keyed shaft and positive axial retainers.
4. Locate the cassette with both 6 mm dowels and the hard stop before tightening the four M6 clamps.
5. Fit the motor pulley, wheel pulley and belt as one serviceable stack by removing the outboard pulley and guard; never force the belt over two flanges.
6. Set belt tension from Gates DesignFlex or a supplier calculation, then record the measurement method and cold/hot values.
7. Perform the 7.2 Nm keyed-joint torque proof, raised-wheel spin/e-stop test, shell clash/service audit and the complete nineteen-item physical commissioning gate.

## Release boundary

The analytical screen passes, but supplier power rating and installation tension, bearing clearance and fits, shaft/hub drawings, materials, dowel ream and GD&T, guard fasteners and service access, Blender clash, tire/shell wear, yaw calibration, thermal/endurance and physical commissioning remain on HOLD. The user's current Blender master is intentionally not changed or saved by Stage 22.
