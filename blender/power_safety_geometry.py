"""Stage-13 physical envelopes for the BB-8 dual-current safety chain."""

import bpy


STAGE_TAG = "power_safety_geometry_stage"


def _material(name):
    material = bpy.data.materials.get(name)
    if material is None:
        raise RuntimeError(f"Required material is missing: {name}")
    return material


def _cube(name, dimensions, location, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Rounded edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def _cylinder(name, radius, depth, location, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def _tube_mesh(name, points, radius, material):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    return bpy.context.object


def _parent_in_design_coordinates(obj, parent):
    # Stage-13 coordinates are authored in the same chassis-local frame as the
    # pre-existing tray. Parenting directly makes the board inherit the -4/+4
    # degree animation pitch instead of freezing its world transform at frame 1.
    obj.parent = parent


def remove_existing_power_safety_geometry():
    for obj in list(bpy.data.objects):
        if obj.get(STAGE_TAG) == 13:
            bpy.data.objects.remove(obj, do_unlink=True)


def add_power_safety_hardware(internal_collection, move_internal, parent=None):
    """Add two INA226 branches, Kelvin shunts and an MCU-independent EN gate.

    Dimensions are conservative module envelopes, not supplier-frozen PCBs. The
    objects intentionally carry electrical acceptance metadata so a reopened
    .blend can be audited instead of relying on labels in a drawing.
    """
    blue = _material("BB8 lens blue")
    dark = _material("BB8 graphite")
    orange = _material("BB8 burnt orange")
    silver = _material("BB8 silver")

    copper = bpy.data.materials.get("BB8 power copper")
    if copper is None:
        copper = bpy.data.materials.new("BB8 power copper")
        copper.diffuse_color = (0.45, 0.12, 0.025, 1.0)
        copper.use_nodes = True
        bsdf = copper.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.45, 0.12, 0.025, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.72
        bsdf.inputs["Roughness"].default_value = 0.28

    created = []

    def register(obj):
        move_internal(obj)
        obj[STAGE_TAG] = 13
        if parent is not None:
            _parent_in_design_coordinates(obj, parent)
        created.append(obj)
        return obj

    board_z = -0.0882
    shunt_z = -0.0859
    board_x = {"L": -0.027, "R": 0.027}
    addresses = {"L": 0x40, "R": 0x41}
    for side in ("L", "R"):
        x = board_x[side]
        board = register(_cube(
            f"Internal INA226 current monitor {side}",
            (0.034, 0.022, 0.0016), (x, 0.002, board_z), blue, 0.0010))
        board["current_monitor"] = "INA226"
        board["i2c_address"] = addresses[side]
        board["high_side_branch"] = side
        board["module_envelope_mm"] = "34 x 22 x 1.6"
        board["shunt_ohm"] = 0.002
        board["current_lsb_a"] = 0.001
        board["calibration_register"] = "0x0A00"
        board["configuration_register"] = "0x4127"
        board["kelvin_connection_required"] = True
        board["physical_test_status"] = "NOT_RUN"

        shunt = register(_cube(
            f"Internal 2mOhm Kelvin shunt {side}",
            (0.012, 0.005, 0.0030), (x, 0.002, shunt_z), copper, 0.0005))
        shunt["shunt_ohm"] = 0.002
        shunt["kelvin_4_wire"] = True
        shunt["high_side_branch"] = side
        shunt["pulse_rating_requires_validation"] = True
        shunt["physical_test_status"] = "NOT_RUN"

        for index, y in enumerate((-0.006, 0.010), 1):
            standoff = register(_cylinder(
                f"Internal INA226 M2.5 standoff {side}{index}",
                0.0015, 0.0030, (x, y, -0.0905), silver))
            standoff["fastener"] = "M2.5 removable electronics standoff"
            standoff["mounting_height_mm"] = 3.0

        kelvin_paths = {
            "+": [(x - 0.004, 0.001, -0.0842), (x - 0.006, -0.005, -0.0866)],
            "-": [(x + 0.004, 0.003, -0.0842), (x + 0.006, -0.005, -0.0866)],
        }
        for polarity, points in kelvin_paths.items():
            sense = register(_tube_mesh(
                f"Internal Kelvin sense {polarity} {side}", points, 0.00055, blue))
            sense["power_safety_wire"] = "kelvin_sense"
            sense["high_side_branch"] = side
            sense["kelvin_polarity"] = polarity
            sense["minimum_bend_radius_mm"] = 5.0

    gate = register(_cube(
        "Internal ALERT to driver EN hardware gate",
        (0.028, 0.014, 0.0016), (0.0, 0.028, board_z), dark, 0.0010))
    gate["alert_to_driver_enable_hardware_gate"] = True
    gate["mcu_independent_disable_required"] = True
    gate["logic_contract"] = "dual INA226 open-drain ALERT wire-OR pulls both driver EN low"
    gate["physical_test_status"] = "NOT_RUN"
    for index, x in enumerate((-0.010, 0.010), 1):
        standoff = register(_cylinder(
            f"Internal ALERT gate M2.5 standoff {index}",
            0.0015, 0.0030, (x, 0.028, -0.0905), silver))
        standoff["fastener"] = "M2.5 removable electronics standoff"
        standoff["mounting_height_mm"] = 3.0

    power_paths = {
        "L input": [(0.083, 0.020, -0.092), (0.060, 0.032, -0.085), (-0.044, 0.018, -0.085), (-0.036, 0.006, -0.0859)],
        "R input": [(0.083, 0.020, -0.092), (0.052, 0.016, -0.085), (0.036, 0.006, -0.0859)],
        "L output": [(-0.018, 0.006, -0.0859), (-0.028, 0.013, -0.088), (-0.042, 0.016, -0.094)],
        "R output": [(0.018, 0.006, -0.0859), (0.028, 0.013, -0.088), (0.042, 0.016, -0.094)],
    }
    for label, points in power_paths.items():
        side, direction = label.split()
        cable = register(_tube_mesh(
            f"Internal monitored power {direction} {side}", points, 0.0022, orange))
        cable["power_safety_wire"] = "high_side_input" if direction == "input" else "motor_branch_output"
        cable["high_side_branch"] = side
        cable["minimum_bend_radius_mm"] = 30.0
        cable["conductor_contract"] = "size by measured continuous/stall current and thermal test"

    for side in ("L", "R"):
        x = board_x[side]
        target_x = -0.006 if side == "L" else 0.006
        alert = register(_tube_mesh(
            f"Internal INA226 ALERT wire {side}",
            [(x, 0.010, -0.0868), (x * 0.55, 0.018, -0.0848), (target_x, 0.022, -0.0868)],
            0.00075, blue))
        alert["power_safety_wire"] = "alert_wire_or"
        alert["high_side_branch"] = side
        alert["active_level"] = "open-drain active-low"
        alert["minimum_bend_radius_mm"] = 10.0

    enable = register(_tube_mesh(
        "Internal hardware driver enable line",
        [(0.0, 0.021, -0.0868), (0.0, -0.018, -0.083), (0.0, -0.030, -0.092)],
        0.0009, dark))
    enable["power_safety_wire"] = "driver_enable"
    enable["mcu_independent_disable_required"] = True
    enable["active_level"] = "fail-safe low disables both drivers"
    enable["minimum_bend_radius_mm"] = 10.0

    return created
