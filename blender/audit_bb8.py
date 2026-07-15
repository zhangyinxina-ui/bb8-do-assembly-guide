import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

scene = bpy.context.scene
engineering_stage = int(scene.get("engineering_stage", 0))
expected = {"body_diameter_mm": 508, "head_diameter_mm": 295, "untopped_height_mm": 670}
errors = []
for key, value in expected.items():
    actual = scene.get(key)
    if actual != value:
        errors.append(f"{key}: expected {value}, got {actual}")

internals = [o for o in bpy.data.objects if o.get("bb8_internal")]
required_internal = {
    "Internal aluminium chassis", "Internal 4S battery ballast",
    "Internal drive wheel L", "Internal drive wheel R",
    "Internal geared motor L", "Internal geared motor R",
    "Internal motor face mount L", "Internal motor face mount R",
    "Internal 8 mm key hub L", "Internal 8 mm key hub R",
    "Internal equator gasket envelope",
    "Internal magnet array riser", "Head internal magnetic carrier",
    "Head underside roller 1", "Head underside roller 2", "Head underside roller 3",
    "Internal magnetic mast", "Internal top magnet carrier", "Internal IMU controller",
    "Internal INA226 current monitor L", "Internal INA226 current monitor R",
    "Internal 2mOhm Kelvin shunt L", "Internal 2mOhm Kelvin shunt R",
    "Internal ALERT to driver EN hardware gate", "Internal hardware driver enable line",
    "Internal sealed low ballast cassette", "Internal ballast central hanger",
    "Internal ballast retention strap F", "Internal ballast retention strap R",
    "Engineering nominal COM marker", "Engineering legacy 110mm COM marker",
    "Internal REC Active BMS 4S candidate",
    "Internal MDD20A official footprint board",
    "Internal SW60 main contactor candidate",
    "Internal 30A MIDI fuse body candidate",
    "Internal dual-channel MDD20A hardware gate PCB placeholder",
    "Internal stage19 dual-permissive gate PCB",
    "Internal stage19 gate J1 logic power XH",
    "Internal stage19 gate J2 MCU and ALERT input XH",
    "Internal stage19 gate J3 MDD20A logic output XH",
    "Internal stage19 gate J4 SAFE_A energise-to-run input XH",
    "Internal stage19 gate J5 SAFE_B energise-to-run input XH",
    "Internal stage19 gate U1 VO617A-4", "Internal stage19 gate U2 VO617A-4",
    "Internal stage19 gate U3 SN74LVC2G08", "Internal stage19 gate U4 SN74LVC2G08",
    "Internal stage19 gate U5 SN74LVC2G08",
    "Internal REC BMS external shunt keepout",
    "Internal dual-channel E-stop receiver", "Internal E-stop safety relay",
    "Internal externally reachable service disconnect", "Internal tether E-stop NC jack",
}
missing = required_internal - {o.name for o in internals}
if missing:
    errors.append(f"missing internal objects: {sorted(missing)}")
if len(internals) < 182:
    errors.append(f"stage-19 internal assembly requires at least 182 objects, got {len(internals)}")

if engineering_stage != 19:
    errors.append(f"engineering_stage expected 19, got {engineering_stage}")
if scene.get("drive_track_mm") != 310:
    errors.append(f"drive_track_mm expected 310, got {scene.get('drive_track_mm')}")

# Stage 8 exterior topology gate. Builders Club V3.1 defines six directional
# P-panels, eight octant T-panels and R1/R2/R3 ring distribution 3/2/1.
panel_insets = [o for o in bpy.data.objects if o.name.endswith("curved white field")]
panel_ids = {o.get("panel_id") for o in panel_insets}
if panel_ids != {"P1", "P2", "P3", "P4", "P5", "P6"}:
    errors.append(f"exterior P-panel IDs incomplete: {sorted(str(v) for v in panel_ids)}")
if any(abs(float(o.get("panel_half_angle_deg", 0)) - 35.0) > 0.01 for o in panel_insets):
    errors.append("one or more curved body panels lack the 35 degree half-angle contract")
ring_objects = [o for o in bpy.data.objects if o.name.endswith("orange spherical ring")]
ring_counts = {ring_type: sum(o.get("ring_type") == ring_type for o in ring_objects)
               for ring_type in ("R1", "R2", "R3")}
if ring_counts != {"R1": 3, "R2": 2, "R3": 1}:
    errors.append(f"ring distribution expected R1/R2/R3=3/2/1, got {ring_counts}")
expected_panel_rings = {"P1": "R3", "P2": "R2", "P3": "R2", "P4": "R1", "P5": "R1", "P6": "R1"}
actual_panel_rings = {o.get("panel_id"): o.get("ring_type") for o in ring_objects}
if actual_panel_rings != expected_panel_rings:
    errors.append(f"panel-to-ring mapping mismatch: {actual_panel_rings}")
for panel_id in expected_panel_rings:
    spokes = [o for o in bpy.data.objects if o.get("panel_id") == panel_id and " radial rail " in o.name]
    if len(spokes) != 4:
        errors.append(f"{panel_id} expected four traced orange spokes, got {len(spokes)}")
    inset = next((o for o in panel_insets if o.get("panel_id") == panel_id), None)
    if inset is None or not inset.get("pattern_variant"):
        errors.append(f"{panel_id} lacks a distinct traced pattern variant")
triangle_outlines = [o for o in bpy.data.objects if o.name.endswith("spherical outline")]
triangle_ids = {o.get("triangle_id") for o in triangle_outlines}
if triangle_ids != {"T1a", "T1b", "T2", "T3", "T4", "T5", "T6", "T7"}:
    errors.append(f"exterior T-panel IDs incomplete: {sorted(str(v) for v in triangle_ids)}")
expected_lights = {
    "P1": ["blue"] * 4,
    "P2": ["blue", "red"],
    "P3": ["blue"],
    "P4": ["blue", "red"],
    "P5": ["blue"],
    "P6": ["blue", "red", "red", "red", "red", "yellow"],
}
for panel_id, expected_colors in expected_lights.items():
    actual_colors = sorted(
        o.get("indicator_color") for o in bpy.data.objects
        if o.get("panel_id") == panel_id and o.get("indicator_color")
    )
    if actual_colors != sorted(expected_colors):
        errors.append(f"{panel_id} lights expected {sorted(expected_colors)}, got {actual_colors}")
if bpy.data.objects.get("Head PSI status light") is None:
    errors.append("missing head PSI status light")

# Stage 9.3 head silhouette and face-detail gate. Community photographic
# measurement gives a 295 x 197 mm outline; overlapping it 35 mm into the ball
# silhouette reconciles that outline with the official 0.67 m overall height.
head_shell = [bpy.data.objects.get(name) for name in (
    "Head lower cone - 223 to 295 mm", "Head dome - 295 mm", "Head crown service cap"
)]
if not all(head_shell):
    errors.append("missing stage-9.3 head shell objects")
else:
    shell_vertices = [obj.matrix_world @ Vector(corner) for obj in head_shell for corner in obj.bound_box]
    shell_top_mm = max(v.z for v in shell_vertices) * 1000
    shell_bottom_mm = min(v.z for v in shell_vertices) * 1000
    total_height_mm = shell_top_mm + 254.0
    if abs(total_height_mm - 670.0) > 1.0:
        errors.append(f"untopped geometric height {total_height_mm:.2f} mm, expected 670 mm")
    if abs(shell_bottom_mm - 219.0) > 1.0:
        errors.append(f"head shell bottom {shell_bottom_mm:.2f} mm, expected 219 mm")
if len([o for o in bpy.data.objects if o.name.startswith("Head lower orange belt panel")]) != 11:
    errors.append("stage-9.3 head requires 11 shallow lower orange belt panels")
if len([o for o in bpy.data.objects if o.name.startswith("Head graphite crown panel")]) != 5:
    errors.append("stage-9.3 head requires 5 graphite crown panels")
if any(o.name.startswith("Head orange panel") for o in bpy.data.objects):
    errors.append("obsolete circular head orange panels still present")

# The two 125.2 mm IG42E envelopes must not overlap at the ball centre.
motors = [bpy.data.objects.get(f"Internal geared motor {side}") for side in ("L", "R")]
if all(motors):
    bounds = []
    for motor in motors:
        world_corners = [motor.matrix_world @ Vector(corner) for corner in motor.bound_box]
        bounds.append((min(v.x for v in world_corners), max(v.x for v in world_corners)))
    centre_gap_mm = (bounds[1][0] - bounds[0][1]) * 1000
    if centre_gap_mm < 15.0:
        errors.append(f"motor centre service gap {centre_gap_mm:.2f} mm, expected >= 15 mm")

# Verify the official four-hole pattern was actually instantiated, not just
# written into metadata. The IG-42C drawing specifies four M4 holes on PCD 35.
for side in ("L", "R"):
    motor = bpy.data.objects.get(f"Internal geared motor {side}")
    mount = bpy.data.objects.get(f"Internal motor face mount {side}")
    bolts = [bpy.data.objects.get(f"Internal motor M4 bolt {side}{i}") for i in range(1, 5)]
    if motor is None or mount is None or not all(bolts):
        continue
    for bolt in bolts:
        radial_mm = ((bolt.location.y - motor.location.y) ** 2 +
                     (bolt.location.z - motor.location.z) ** 2) ** 0.5 * 1000
        if abs(radial_mm - 17.5) > 0.1:
            errors.append(f"{bolt.name} PCD radius {radial_mm:.2f} mm, expected 17.5 mm")
    if float(mount.get("tool_clearance_mm", 0)) < 55.0:
        errors.append(f"{mount.name} lacks 55 mm service-tool clearance contract")

# Stage 6 service joint and harness gates.
latches = [o for o in internals if o.name.startswith("Internal equator latch envelope")]
if len(latches) != 8:
    errors.append(f"equator joint requires 8 latch envelopes, got {len(latches)}")
if any(float(o.get("target_clamp_force_n", 0)) < 80.0 for o in latches):
    errors.append("one or more equator latches lack the 80 N clamp-force contract")

harnesses = [o for o in internals if o.get("harness_type")]
connectors = [o for o in internals if o.get("connector_contract")]
if len(harnesses) != 12:
    errors.append(f"expected 12 explicit harness segments, got {len(harnesses)}")
if len(connectors) != 4:
    errors.append(f"expected 4 service connectors, got {len(connectors)}")
for cable in harnesses:
    minimum = 30.0 if cable.get("harness_type") == "power" else 20.0
    if float(cable.get("minimum_bend_radius_mm", 0)) < minimum:
        errors.append(f"{cable.name} bend-radius contract below {minimum:.0f} mm")
    # Conservative wheel avoidance: every cable vertex must remain at least
    # 10 mm beyond a 48 mm bounding sphere around either powered wheel.
    for wheel in (bpy.data.objects.get("Internal drive wheel L"),
                  bpy.data.objects.get("Internal drive wheel R")):
        clearance_mm = min(((cable.matrix_world @ v.co) - wheel.location).length
                           for v in cable.data.vertices) * 1000 - 48.0
        if clearance_mm < 10.0:
            errors.append(f"{cable.name} wheel clearance {clearance_mm:.2f} mm, expected >= 10 mm")
for connector in connectors:
    if connector.get("disconnect_before_service") is not True:
        errors.append(f"{connector.name} lacks disconnect-before-service contract")

# Stage 13 power-safety installation gate. These are physical envelopes and
# wiring contracts; the test-status gate deliberately remains NOT_RUN until a
# real shunt, driver, motor and thermal bench are measured.
current_monitors = [o for o in internals if o.get("current_monitor") == "INA226"]
if len(current_monitors) != 2:
    errors.append(f"power safety requires 2 INA226 monitor envelopes, got {len(current_monitors)}")
elif {int(o.get("i2c_address", -1)) for o in current_monitors} != {0x40, 0x41}:
    errors.append("INA226 address contract must be exactly 0x40 and 0x41")
for monitor in current_monitors:
    if abs(float(monitor.get("shunt_ohm", 0)) - 0.002) > 1e-9:
        errors.append(f"{monitor.name} shunt contract is not 2 mOhm")
    if monitor.get("kelvin_connection_required") is not True:
        errors.append(f"{monitor.name} lacks four-wire Kelvin requirement")
    if monitor.get("physical_test_status") != "NOT_RUN":
        errors.append(f"{monitor.name} must remain NOT_RUN before hardware validation")

shunts = [o for o in internals if o.get("kelvin_4_wire") is True]
if len(shunts) != 2:
    errors.append(f"power safety requires 2 explicit Kelvin shunts, got {len(shunts)}")
for shunt in shunts:
    if abs(float(shunt.get("shunt_ohm", 0)) - 0.002) > 1e-9:
        errors.append(f"{shunt.name} resistance is not 2 mOhm")
    if shunt.get("pulse_rating_requires_validation") is not True:
        errors.append(f"{shunt.name} lacks pulse-rating validation gate")

gate = bpy.data.objects.get("Internal ALERT to driver EN hardware gate")
if gate is not None:
    if gate.get("alert_to_driver_enable_hardware_gate") is not True:
        errors.append("ALERT gate lacks hardware gate contract")
    if gate.get("mcu_independent_disable_required") is not True:
        errors.append("ALERT gate is not explicitly independent from MCU execution")
    if gate.get("physical_test_status") != "NOT_RUN":
        errors.append("ALERT gate must remain NOT_RUN before hardware validation")

wire_counts = {}
power_safety_wires = [o for o in internals if o.get("power_safety_wire")]
for wire in power_safety_wires:
    wire_type = wire.get("power_safety_wire")
    wire_counts[wire_type] = wire_counts.get(wire_type, 0) + 1
expected_wire_counts = {
    "high_side_input": 2,
    "motor_branch_output": 2,
    "kelvin_sense": 4,
    "alert_wire_or": 2,
    "driver_enable": 1,
}
if wire_counts != expected_wire_counts:
    errors.append(f"power-safety wiring expected {expected_wire_counts}, got {wire_counts}")
for wire in power_safety_wires:
    if float(wire.get("minimum_bend_radius_mm", 0)) <= 0:
        errors.append(f"{wire.name} lacks a positive bend-radius contract")

standoffs = [o for o in internals if "M2.5 standoff" in o.name]
if len(standoffs) != 6:
    errors.append(f"power-safety electronics requires 6 removable standoffs, got {len(standoffs)}")

tray = bpy.data.objects.get("Internal electronics tray")
mounted_boards = current_monitors + ([gate] if gate is not None else [])
if tray is not None:
    tray_center = tray.matrix_world.translation
    tray_min_x = tray_center.x - tray.dimensions.x / 2
    tray_max_x = tray_center.x + tray.dimensions.x / 2
    tray_min_y = tray_center.y - tray.dimensions.y / 2
    tray_max_y = tray_center.y + tray.dimensions.y / 2
    for board in mounted_boards:
        board_center = board.matrix_world.translation
        if (board_center.x - board.dimensions.x / 2 < tray_min_x or
                board_center.x + board.dimensions.x / 2 > tray_max_x or
                board_center.y - board.dimensions.y / 2 < tray_min_y or
                board_center.y + board.dimensions.y / 2 > tray_max_y):
            errors.append(f"{board.name} exceeds electronics-tray footprint")
        local_gap_mm = ((board.location.z - board.dimensions.z / 2) -
                        (tray.location.z + tray.dimensions.z / 2)) * 1000
        if abs(local_gap_mm - 3.0) > 0.2:
            errors.append(f"{board.name} chassis-local standoff gap is not 3 mm")

if scene.get("power_safety_physical_test_status") != "NOT_RUN":
    errors.append("scene power-safety physical status must remain NOT_RUN")
if scene.get("power_safety_model_object_count") != 22:
    errors.append(f"power-safety model object count expected 22, got {scene.get('power_safety_model_object_count')}")

# Stage 14 replaces the old unverified 110 mm COM assumption with a mass ledger,
# exhaustive min/max corner evaluation and a removable sealed low ballast pack.
stage14_objects = [o for o in internals if o.get("mass_properties_geometry_stage") == 14]
stage14_annotations = [o for o in stage14_objects if o.get("engineering_annotation") is True]
if len(stage14_objects) != 10:
    errors.append(f"stage-14 mass geometry expected 10 objects, got {len(stage14_objects)}")
if len(stage14_annotations) != 2:
    errors.append(f"stage-14 mass geometry expected 2 engineering annotations, got {len(stage14_annotations)}")
if scene.get("mass_model_object_count") != 10:
    errors.append(f"mass model object count expected 10, got {scene.get('mass_model_object_count')}")
if scene.get("mass_model_status") != "PASS_WITH_MASS_AND_ACCELERATION_DERATING":
    errors.append(f"mass model status is not PASS, got {scene.get('mass_model_status')}")
if scene.get("mass_physical_test_status") != "NOT_RUN":
    errors.append("mass physical test status must remain NOT_RUN")

cassette = bpy.data.objects.get("Internal sealed low ballast cassette")
if cassette is not None:
    actual_mm = tuple(round(v * 1000, 1) for v in cassette.dimensions)
    if actual_mm != (120.0, 70.0, 24.0):
        errors.append(f"ballast cassette dimensions expected 120x70x24 mm, got {actual_mm}")
    if abs(float(cassette.get("mass_nominal_kg", 0)) - 1.50) > 1e-9:
        errors.append("ballast cassette nominal mass expected 1.50 kg")
    if cassette.get("physical_test_status") != "NOT_RUN":
        errors.append("ballast cassette must remain NOT_RUN before weighing")
if len([o for o in stage14_objects if o.name.startswith("Internal ballast M5 captive bolt")]) != 4:
    errors.append("stage-14 ballast cassette requires four captive M5 bolts")
if len([o for o in stage14_objects if o.name.startswith("Internal ballast retention strap")]) != 2:
    errors.append("stage-14 ballast cassette requires two retention straps")

root = Path(bpy.data.filepath).parents[2]
mass_results_path = root / "engineering" / "mass_properties_results.json"
if not mass_results_path.exists():
    errors.append(f"missing stage-14 mass results: {mass_results_path}")
else:
    mass_results = json.loads(mass_results_path.read_text(encoding="utf-8"))
    nominal = mass_results["nominal"]
    if abs(float(scene.get("mass_total_nominal_kg", 0)) - nominal["total_mass_kg"]) > 1e-9:
        errors.append("scene nominal mass differs from the verified stage-14 results")
    if abs(float(scene.get("mass_com_worst_z_m", 0)) - mass_results["highest_com"]["com_m"][2]) > 1e-9:
        errors.append("scene worst-case COM differs from the verified stage-14 results")
    marker = bpy.data.objects.get("Engineering nominal COM marker")
    if marker is not None and (marker.location - Vector(nominal["com_m"])).length > 1e-6:
        errors.append("nominal COM marker differs from the verified stage-14 result")

# Stage 18 replaces the two generic stage-15 driver boxes with one official
# MDD20A footprint, a vertically mounted REC Active BMS 4S catalogue envelope,
# an SW60 envelope, an external shunt and explicit unresolved keepouts.
stage15_objects = [o for o in internals if o.get("drive_power_geometry_stage") == 15]
if stage15_objects:
    errors.append(f"stage-18 master still contains {len(stage15_objects)} obsolete stage-15 objects")

stage18_objects = [o for o in internals if o.get("power_cassette_geometry_stage") == 18]
if len(stage18_objects) != 39:
    errors.append(f"stage-18 power cassette expected 39 objects, got {len(stage18_objects)}")
if scene.get("power_cassette_model_object_count") != 39:
    errors.append(f"stage-18 scene object count expected 39, got {scene.get('power_cassette_model_object_count')}")
if scene.get("power_cassette_packaging_status") != "PASS_ANALYTICAL_ONLY":
    errors.append("stage-18 cassette packaging status must remain analytical-only PASS")
if scene.get("power_cassette_physical_fit_status") != "NOT_RUN":
    errors.append("stage-18 physical fit status must remain NOT_RUN")
if scene.get("power_cassette_powered_test_status") != "NOT_RUN":
    errors.append("stage-18 powered status must remain NOT_RUN")

component_ids = {o.get("candidate_component_id") for o in stage18_objects if o.get("candidate_component_id")}
expected_component_ids = {"BMS01", "DRV01", "CON01", "FUS01", "GAT01", "SHN01", "REL01", "EST01"}
if component_ids != expected_component_ids:
    errors.append(f"stage-18 component IDs expected {sorted(expected_component_ids)}, got {sorted(component_ids)}")

bms = bpy.data.objects.get("Internal REC Active BMS 4S candidate")
bms_connector = bpy.data.objects.get("Internal REC BMS AMPSEAL connector envelope")
driver = bpy.data.objects.get("Internal MDD20A official footprint board")
driver_keepout = bpy.data.objects.get("Internal MDD20A dual motor driver keepout")
contactor = bpy.data.objects.get("Internal SW60 main contactor candidate")
fuse = bpy.data.objects.get("Internal 30A MIDI fuse body candidate")
gate_board = bpy.data.objects.get("Internal dual-channel MDD20A hardware gate PCB placeholder")
pack_shunt = bpy.data.objects.get("Internal REC BMS external shunt keepout")
estop_receiver = bpy.data.objects.get("Internal dual-channel E-stop receiver")
estop_relay = bpy.data.objects.get("Internal E-stop safety relay")
tether_jack = bpy.data.objects.get("Internal tether E-stop NC jack")
if not all((bms, bms_connector, driver, driver_keepout, contactor, fuse, gate_board, pack_shunt,
            estop_receiver, estop_relay, tether_jack)):
    errors.append("stage-18 BMS/driver/fuse/contactor/gate/shunt/E-stop hardware is incomplete")
else:
    if tuple(round(value * 1000, 2) for value in bms.dimensions) != (44.0, 111.0, 135.0):
        errors.append(f"REC Active BMS envelope mismatch: {tuple(bms.dimensions)}")
    if bms.get("series_cells") != 4 or bms.get("temperature_sensor_channels") != 2:
        errors.append("REC Active BMS must retain the official 4S/two-temperature-channel contract")
    if not bms_connector.get("candidate_connector_contract"):
        errors.append("REC Active BMS AMPSEAL candidate interface contract is missing")
    if bms_connector.get("disconnect_before_service") is not True:
        errors.append("REC Active BMS AMPSEAL interface lacks disconnect-before-service contract")
    if tuple(round(value * 1000, 2) for value in driver.dimensions) != (1.6, 88.9, 78.74):
        errors.append(f"MDD20A official footprint mismatch: {tuple(driver.dimensions)}")
    if driver.get("independent_enable_input") is not False or driver.get("pwm_low_behavior") != "BRAKE_NOT_DEENERGISED":
        errors.append("MDD20A interface must not be represented as an independent hard enable")
    if driver_keepout.get("height_keepout_assumption_mm") != 25.0 or driver_keepout.get("official_height_available") is not False:
        errors.append("MDD20A 25 mm height keepout must remain an explicit assumption")
    if contactor.get("normally_open") is not True or contactor.get("plain_diode_suppression_rejected") is not True:
        errors.append("SW60 must remain normally-open and reject plain-diode suppression")
    if gate_board.get("released_pcb") is not False or gate_board.get("mcu_independent_disable_required") is not True:
        errors.append("dual-channel gate must remain an unreleased MCU-independent PCB contract")
    if gate_board.get("stage19_superseded_keepout") is not True or gate_board.hide_render is not True:
        errors.append("stage-18 gate placeholder must remain a hidden superseded keepout")
    if pack_shunt.get("kelvin_connection_required") is not True:
        errors.append("REC BMS pack shunt lacks the Kelvin interface contract")

if len([o for o in stage18_objects if o.name.startswith("Internal MDD20A M3 standoff")]) != 4:
    errors.append("MDD20A official footprint requires four mounting standoffs")
if len([o for o in stage18_objects if o.name.startswith("Internal REC BMS pack temperature sensor")]) != 2:
    errors.append("REC Active BMS model requires two pack temperature sensors")

power_path_types = [o.get("stage18_power_wire") for o in stage18_objects if o.get("stage18_power_wire")]
signal_path_types = [o.get("stage18_safety_signal") for o in stage18_objects if o.get("stage18_safety_signal")]
if len(power_path_types) != 7 or len(set(power_path_types)) != 7:
    errors.append(f"stage-18 high-current path expected 7 unique segments, got {power_path_types}")
if len(signal_path_types) != 8 or len(set(signal_path_types)) != 8:
    errors.append(f"stage-18 signal path expected 8 unique segments, got {signal_path_types}")
if any(float(o.get("minimum_bend_radius_mm", 0)) <= 0 for o in stage18_objects
       if o.get("stage18_power_wire") or o.get("stage18_safety_signal")):
    errors.append("one or more stage-18 wires lack a positive bend-radius contract")
if any(o.get("physical_test_status") != "NOT_RUN" for o in stage18_objects):
    errors.append("all stage-18 objects must remain NOT_RUN before purchased-sample validation")

chassis_rig = bpy.data.objects.get("RIG 20 - Gravity stabilised chassis")
if chassis_rig is None or any(o.parent != chassis_rig for o in stage18_objects):
    errors.append("all stage-18 power-cassette objects must inherit the chassis rig")
legacy_power_block = bpy.data.objects.get("Internal fuse and contactor")
if legacy_power_block is None or legacy_power_block.get("mass_accounting_only") is not True:
    errors.append("stage-14 grouped fuse/contactor mass representative was not preserved")

# Stage 19 replaces the empty GAT01 visual placeholder with component envelopes
# that match the published 50 x 35 x 1.6 mm pre-CAD contract. These objects are
# still analytical-only: there is no copper, routed PCB, Gerber or bench proof.
stage19_objects = [o for o in internals if o.get("dual_permissive_gate_geometry_stage") == 19]
if len(stage19_objects) != 23:
    errors.append(f"stage-19 dual-permissive gate expected 23 objects, got {len(stage19_objects)}")
if scene.get("stage19_gate_model_object_count") != 23:
    errors.append(
        f"stage-19 scene object count expected 23, got {scene.get('stage19_gate_model_object_count')}")
if scene.get("stage19_gate_design_status") != "PASS_ANALYTICAL_ONLY":
    errors.append("stage-19 gate design status must remain analytical-only PASS")
if scene.get("stage19_gate_physical_test_status") != "NOT_RUN":
    errors.append("stage-19 gate physical status must remain NOT_RUN")
if scene.get("stage19_gate_safety_certification") != "NONE":
    errors.append("stage-19 gate must not claim safety certification")
if scene.get("stage19_gate_manufacturing_release") != "NOT_RELEASED_NO_KICAD_GERBER":
    errors.append("stage-19 gate must not claim a manufacturing release")
if scene.get("stage19_gate_fabrication_export") is not False:
    errors.append("stage-19 pre-CAD geometry must be excluded from fabrication exports")
if scene.get("stage19_gate_truth_table_rows") != 64:
    errors.append("stage-19 gate must retain the exhaustive 64-row truth-table contract")
if any(o.get("physical_test_status") != "NOT_RUN" for o in stage19_objects):
    errors.append("all stage-19 gate objects must remain NOT_RUN before bench validation")
if any(o.get("stage19_pre_cad_reference_only") is not True for o in stage19_objects):
    errors.append("one or more stage-19 objects lack the pre-CAD reference boundary")
if any(o.get("non_fabrication_reference") is not True for o in stage19_objects):
    errors.append("one or more stage-19 objects could leak into fabrication STL/CSV exports")
if any(o.get("manufacturing_release") != "NOT_RELEASED_NO_KICAD_GERBER"
       for o in stage19_objects):
    errors.append("one or more stage-19 objects incorrectly claim manufacturing release")
if chassis_rig is None or any(o.parent != chassis_rig for o in stage19_objects):
    errors.append("all stage-19 gate objects must inherit the chassis rig")

stage19_references = {o.get("component_reference") for o in stage19_objects}
expected_stage19_references = {
    "PCB1", "H1", "H2", "H3", "H4", "J1", "J2", "J3", "J4", "J5",
    "U1", "U2", "U3", "U4", "U5", "R1", "R2",
    "TP1", "TP2", "TP3", "TP4", "TP5", "TP6",
}
if stage19_references != expected_stage19_references:
    errors.append(
        f"stage-19 component references mismatch: {sorted(str(v) for v in stage19_references)}")

stage19_board = bpy.data.objects.get("Internal stage19 dual-permissive gate PCB")
if stage19_board is None:
    errors.append("missing Stage-19 detailed dual-permissive gate PCB")
else:
    board_dimensions_mm = tuple(round(value * 1000, 2) for value in stage19_board.dimensions)
    if board_dimensions_mm != (50.0, 35.0, 1.6):
        errors.append(f"stage-19 gate board dimensions mismatch: {board_dimensions_mm}")
    if stage19_board.get("two_independent_energise_to_run_inputs") is not True:
        errors.append("stage-19 gate board lacks two independent energise-to-run inputs")
    if stage19_board.get("direct_dual_ina226_alert_gate") is not True:
        errors.append("stage-19 gate board lacks the direct dual-INA226 ALERT_N contract")
    if stage19_board.get("safety_certification") != "NONE":
        errors.append("stage-19 board must explicitly retain safety certification NONE")

if len([o for o in stage19_objects if o.name.startswith(
        "Internal stage19 gate M3 insulated standoff")]) != 4:
    errors.append("stage-19 gate requires four M3 insulated standoff envelopes")
if len([o for o in stage19_objects if " XH" in o.name]) != 5:
    errors.append("stage-19 gate requires five JST XH connector envelopes")
if len([o for o in stage19_objects if "VO617A-4" in o.name]) != 2:
    errors.append("stage-19 gate requires two VO617A-4 optocoupler envelopes")
if len([o for o in stage19_objects if "SN74LVC2G08" in o.name]) != 3:
    errors.append("stage-19 gate requires three SN74LVC2G08 package envelopes")
if len([o for o in stage19_objects if "2k input resistor" in o.name]) != 2:
    errors.append("stage-19 gate requires two 2.00 kOhm input resistor envelopes")

test_points = [o for o in stage19_objects if o.get("test_net")]
expected_test_nets = {"SAFE_A_OK", "SAFE_B_OK", "ALERT_N", "PWM_L_OUT", "PWM_R_OUT", "GND"}
if len(test_points) != 6 or {o.get("test_net") for o in test_points} != expected_test_nets:
    errors.append("stage-19 gate requires six unique safety and PWM test points")

connectors = [o for o in stage19_objects if o.get("connector_series")]
if connectors and stage19_board is not None:
    assembled_height_mm = max(
        (o.location.z + o.dimensions.z / 2) -
        (stage19_board.location.z - stage19_board.dimensions.z / 2)
        for o in connectors
    ) * 1000
    if abs(assembled_height_mm - 11.4) > 0.2:
        errors.append(
            f"stage-19 connector assembled height {assembled_height_mm:.2f} mm, expected 11.4 mm")
    installed_min_z = min(o.location.z - o.dimensions.z / 2 for o in stage19_objects)
    installed_max_z = max(o.location.z + o.dimensions.z / 2 for o in stage19_objects)
    installed_height_mm = (installed_max_z - installed_min_z) * 1000
    if abs(installed_height_mm - 14.4) > 0.2:
        errors.append(
            f"stage-19 installed height {installed_height_mm:.2f} mm, expected 14.4 mm")
    keepout = bpy.data.objects.get("Internal dual-channel MDD20A hardware gate keepout")
    if keepout is None:
        errors.append("stage-19 gate cannot be checked without the Stage-18 GAT01 keepout")
    else:
        keepout_min_z = keepout.location.z - keepout.dimensions.z / 2
        keepout_max_z = keepout.location.z + keepout.dimensions.z / 2
        if installed_min_z < keepout_min_z - 0.0002 or installed_max_z > keepout_max_z + 0.0002:
            errors.append("stage-19 installed board exceeds the Stage-18 15 mm vertical keepout")
        for axis in range(2):
            installed_min = min(o.location[axis] - o.dimensions[axis] / 2 for o in stage19_objects)
            installed_max = max(o.location[axis] + o.dimensions[axis] / 2 for o in stage19_objects)
            keepout_min = keepout.location[axis] - keepout.dimensions[axis] / 2
            keepout_max = keepout.location[axis] + keepout.dimensions[axis] / 2
            if installed_min < keepout_min - 0.0002 or installed_max > keepout_max + 0.0002:
                errors.append(f"stage-19 installed board exceeds the Stage-18 keepout on axis {axis}")

# Stage 7 opposed magnet arrays and head follower rollers.
lower_magnets = [o for o in internals if o.name.startswith("Internal chassis magnet")]
upper_magnets = [o for o in internals if o.name.startswith("Head internal follower magnet")]
if len(lower_magnets) != 6 or len(upper_magnets) != 6:
    errors.append(f"magnet array expected 6+6, got {len(lower_magnets)}+{len(upper_magnets)}")
else:
    lower_top = max(o.location.z + o.dimensions.z / 2 for o in lower_magnets)
    upper_bottom = min(o.location.z - o.dimensions.z / 2 for o in upper_magnets)
    magnet_gap_mm = (upper_bottom - lower_top) * 1000
    if abs(magnet_gap_mm - 8.0) > 0.2:
        errors.append(f"magnet face gap {magnet_gap_mm:.2f} mm, expected 8 mm")
    if any(float(o.get("measured_pull_force_required_n", 0)) < 40.0 for o in upper_magnets):
        errors.append("one or more follower magnets lack the 40 N assembled pull-force gate")

head_rollers = [o for o in internals if o.get("outer_shell_contact_radius_mm") is not None]
if len(head_rollers) != 3:
    errors.append(f"head follower requires 3 rollers, got {len(head_rollers)}")
for roller in head_rollers:
    center_radius_mm = roller.matrix_world.translation.length * 1000
    element_radius_mm = max(roller.dimensions) * 500
    shell_touch_mm = center_radius_mm - element_radius_mm
    if abs(shell_touch_mm - 254.0) > 1.0:
        errors.append(f"{roller.name} outer shell contact {shell_touch_mm:.2f} mm, expected 254 mm")

# All chassis-side internal mesh vertices must remain inside, or on, the nominal shell.
for obj in internals:
    if obj.type != 'MESH':
        continue
    if obj.get("outer_shell_contact_radius_mm") is not None or obj.name.startswith("Head "):
        continue
    max_radius_mm = max((obj.matrix_world @ v.co).length for v in obj.data.vertices) * 1000
    if max_radius_mm > 255.5:
        errors.append(f"{obj.name} exceeds shell envelope at {max_radius_mm:.2f} mm")

# Contact geometry gate: use the actual transformed mesh support, not
# centre-radius + max-dimension/2. The old shortcut treats a 96 x 26 mm powered
# cylinder as a 96 mm sphere and overstates its reach by about 5.07 mm. Stage 21
# deliberately makes the legacy powered wheels fail until a crowned,
# tangent-axis preload cassette is applied and saved with explicit approval.
for obj in internals:
    contact_radius_mm = obj.get("inner_shell_contact_radius_mm")
    if contact_radius_mm is None:
        continue
    if obj.type != 'MESH' or not obj.data.vertices:
        errors.append(f"{obj.name} contact geometry has no auditable mesh vertices")
        continue
    shell_reach_mm = max((obj.matrix_world @ vertex.co).length
                         for vertex in obj.data.vertices) * 1000
    if abs(shell_reach_mm - 254.0) > 1.0:
        errors.append(f"{obj.name} shell contact {shell_reach_mm:.2f} mm, expected 254 mm")

for name in ("front.png", "side.png", "back.png", "mechanism.png",
             "internal_front.png", "internal_side.png", "internal_top.png"):
    path = root / "blender" / "output" / name
    if not path.exists() or path.stat().st_size < 100_000:
        errors.append(f"missing or undersized render: {path}")

# The dimension sheet must be rebuilt from the same current front/side/back
# renders and the website copy must be byte-identical. This catches a stale
# composite that can otherwise survive a successful Blender regeneration.
view_paths = [root / "blender" / "output" / name for name in ("front.png", "side.png", "back.png")]
sheet_path = root / "blender" / "output" / "BB8_three_view_dimension_sheet.png"
public_sheet_path = root / "public" / "model" / "BB8_three_view_dimension_sheet.png"
if not sheet_path.exists() or sheet_path.stat().st_size < 100_000:
    errors.append(f"missing or undersized dimension sheet: {sheet_path}")
elif any(sheet_path.stat().st_mtime < path.stat().st_mtime for path in view_paths):
    errors.append("dimension sheet is older than one or more orthographic source renders")
if not public_sheet_path.exists():
    errors.append(f"missing website dimension sheet: {public_sheet_path}")
elif sheet_path.exists():
    source_hash = hashlib.sha256(sheet_path.read_bytes()).digest()
    public_hash = hashlib.sha256(public_sheet_path.read_bytes()).digest()
    if source_hash != public_hash:
        errors.append("website dimension sheet differs from the Blender output")

annotations = [o for o in internals if o.get("engineering_annotation") is True]
if len(annotations) != 9:
    errors.append(f"stage-19 expects 9 non-fabrication engineering annotations, got {len(annotations)}")
pre_cad_references = [o for o in internals if o.get("non_fabrication_reference") is True]
if len(pre_cad_references) != 23 or {o.name for o in pre_cad_references} != {
        o.name for o in stage19_objects}:
    errors.append(
        f"stage-19 expects exactly 23 non-fabrication pre-CAD references, got {len(pre_cad_references)}")
fabrication_objects = [
    o for o in internals
    if not o.get("engineering_annotation") and not o.get("non_fabrication_reference")
]
if len(fabrication_objects) != 150:
    errors.append(f"stage-19 expects the fabrication set to remain 150 objects, got {len(fabrication_objects)}")

if errors:
    print("FAIL", " | ".join(errors))
    raise SystemExit(1)


def file_evidence(relative_path):
    path = root / relative_path
    if not path.is_file():
        return {"path": relative_path, "present": False}
    return {
        "path": relative_path,
        "present": True,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


manifest_path = root / "engineering" / "internal_assembly_manifest.csv"
manifest_rows = max(
    len(manifest_path.read_text(encoding="utf-8").splitlines()) - 1,
    0,
)
reopen_evidence = {
    "audited_at": "2026-07-13",
    "blender_version": bpy.app.version_string,
    "master": file_evidence("blender/output/BB8_1to1_screen_referenced.blend"),
    "result": "PASS_REOPEN_AUDIT_ONLY",
    "engineering_stage": int(scene["engineering_stage"]),
    "object_counts": {
        "total": len(bpy.data.objects),
        "internal": len(internals),
        "fabrication": len(fabrication_objects),
        "engineering_annotations": len(annotations),
        "pre_cad_references": len(pre_cad_references),
        "stage19_gate": len(stage19_objects),
        "internal_manifest_rows": manifest_rows,
    },
    "dimensions_mm": {
        "body_diameter": int(scene["body_diameter_mm"]),
        "head_diameter": int(scene["head_diameter_mm"]),
        "untopped_height": int(scene["untopped_height_mm"]),
    },
    "stage19_boundary": {
        "design_status": scene["stage19_gate_design_status"],
        "physical_test_status": scene["stage19_gate_physical_test_status"],
        "safety_certification": scene["stage19_gate_safety_certification"],
        "manufacturing_release": scene["stage19_gate_manufacturing_release"],
        "fabrication_export": bool(scene["stage19_gate_fabrication_export"]),
        "truth_table_rows": int(scene["stage19_gate_truth_table_rows"]),
    },
    "renders": [
        file_evidence(f"blender/output/{name}")
        for name in (
            "mechanism.png",
            "internal_front.png",
            "internal_side.png",
            "internal_top.png",
            "BB8_internal_three_view.png",
        )
    ],
    "exports": [
        file_evidence(relative_path)
        for relative_path in (
            "engineering/internal_assembly_manifest.csv",
            "blender/exports/BB8_body_visual_reference_mm.stl",
            "blender/exports/BB8_head_visual_reference_mm.stl",
            "blender/exports/BB8_internal_mechanism_mm.stl",
            "blender/exports/BB8_1to1_kinematic.glb",
        )
    ],
    "release_boundary": (
        "The Blender master is reopenable and the analytical geometry/export boundary passes. "
        "Physical commissioning remains 0/19; there is no PCB CAD, Gerber, assembled gate board, "
        "bench waveform or safety certification."
    ),
}
encoded_reopen_evidence = json.dumps(reopen_evidence, ensure_ascii=False, indent=2) + "\n"
for output_path in (
        root / "engineering" / "stage19_blender_reopen_audit.json",
        root / "public" / "downloads" / "stage19_blender_reopen_audit.json"):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(encoded_reopen_evidence, encoding="utf-8")

print(f"PASS reopenable_blend engineering_stage={scene['engineering_stage']} objects={len(bpy.data.objects)} internal={len(internals)} fabrication={len(fabrication_objects)} "
      f"pre_cad_reference={len(pre_cad_references)} annotations={len(annotations)} stage19_gate={len(stage19_objects)} panels=6 triangles=8 rings=3/2/1 body={scene['body_diameter_mm']}mm "
      f"head={scene['head_diameter_mm']}mm height={scene['untopped_height_mm']}mm")
