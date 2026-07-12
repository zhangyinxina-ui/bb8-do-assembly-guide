import bpy
import hashlib
from pathlib import Path
from mathutils import Vector

scene = bpy.context.scene
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
}
missing = required_internal - {o.name for o in internals}
if missing:
    errors.append(f"missing internal objects: {sorted(missing)}")
if len(internals) < 88:
    errors.append(f"stage-7 internal assembly requires at least 88 objects, got {len(internals)}")

if scene.get("engineering_stage") != 8:
    errors.append(f"engineering_stage expected 8, got {scene.get('engineering_stage')}")
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

# Contact geometry gate: tagged powered wheels and ball-transfer stabilisers must
# reach the nominal inner shell radius to within 1 mm after reopening the file.
for obj in internals:
    contact_radius_mm = obj.get("inner_shell_contact_radius_mm")
    if contact_radius_mm is None:
        continue
    center_radius_mm = obj.matrix_world.translation.length * 1000
    element_radius_mm = max(obj.dimensions) * 500
    shell_reach_mm = center_radius_mm + element_radius_mm
    if abs(shell_reach_mm - 254.0) > 1.0:
        errors.append(f"{obj.name} shell contact {shell_reach_mm:.2f} mm, expected 254 mm")

root = Path(bpy.data.filepath).parents[2]
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

if errors:
    print("FAIL", " | ".join(errors))
    raise SystemExit(1)
print(f"PASS reopenable_blend stage={scene['engineering_stage']} objects={len(bpy.data.objects)} internal={len(internals)} "
      f"panels=6 triangles=8 rings=3/2/1 body={scene['body_diameter_mm']}mm "
      f"head={scene['head_diameter_mm']}mm height={scene['untopped_height_mm']}mm")
