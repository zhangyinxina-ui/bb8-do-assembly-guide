"""Stage-15 motor-driver and hard E-stop power-chain geometry."""

from __future__ import annotations

import bpy


STAGE_TAG = "drive_power_geometry_stage"


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
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    return bpy.context.object


def remove_existing_stage15_geometry():
    for obj in list(bpy.data.objects):
        if obj.get(STAGE_TAG) == 15:
            bpy.data.objects.remove(obj, do_unlink=True)


def add_stage15_drive_power_hardware(move_internal, parent=None):
    """Add conservative physical envelopes without freezing a vendor driver.

    The two driver envelopes are deliberately generic. Current, thermal,
    regenerative-energy and fuse ratings remain acceptance gates until the
    selected motor is measured at the actual battery voltage.
    """
    blue = _material("BB8 lens blue")
    dark = _material("BB8 graphite")
    orange = _material("BB8 burnt orange")
    silver = _material("BB8 silver")

    red = bpy.data.materials.get("BB8 stage15 safety red")
    if red is None:
        red = bpy.data.materials.new("BB8 stage15 safety red")
        red.diffuse_color = (0.62, 0.015, 0.008, 1.0)
    green = bpy.data.materials.get("BB8 stage15 safety green")
    if green is None:
        green = bpy.data.materials.new("BB8 stage15 safety green")
        green.diffuse_color = (0.02, 0.28, 0.07, 1.0)

    created = []

    def register(obj):
        move_internal(obj)
        obj[STAGE_TAG] = 15
        if parent is not None:
            obj.parent = parent
        created.append(obj)
        return obj

    # The old single orange block remains only as the stage-14 grouped mass
    # representative. Stage 15 replaces it with explicit fabrication objects.
    grouped = bpy.data.objects.get("Internal fuse and contactor")
    if grouped is not None:
        grouped["engineering_annotation"] = True
        grouped["legacy_grouped_envelope"] = True
        grouped["mass_accounting_only"] = True
        grouped.hide_render = True

    driver_x = {"L": -0.080, "R": 0.080}
    for side in ("L", "R"):
        x = driver_x[side]
        board = register(_cube(
            f"Internal motor driver {side}",
            (0.052, 0.034, 0.006), (x, -0.028, -0.087), blue, 0.0015))
        board["motor_driver_envelope_mm"] = "52 x 34 x 16 including heatsink"
        board["candidate_status"] = "NOT_FROZEN"
        board["battery_full_voltage_v"] = 16.8
        board["continuous_and_peak_current"] = "TBD from measured motor stall, thermal soak and fuse coordination"
        board["enable_contract"] = "fail-safe LOW; hardware gate and E-stop chain both disable output"
        board["regenerative_energy_path_required"] = True
        board["mass_accounting_group"] = "electronics tray controller and current boards"
        board["physical_test_status"] = "NOT_RUN"

        heatsink = register(_cube(
            f"Internal motor driver heatsink {side}",
            (0.044, 0.026, 0.010), (x, -0.028, -0.079), silver, 0.0010))
        heatsink["thermal_contract"] = "size from sealed-shell 10 minute worst-case thermal soak"
        heatsink["air_clearance_above_mm"] = 8.0
        heatsink["mass_accounting_group"] = "electronics tray controller and current boards"
        heatsink["physical_test_status"] = "NOT_RUN"

        for index, (dx, dy) in enumerate(((-0.020, -0.012), (-0.020, 0.012),
                                           (0.020, -0.012), (0.020, 0.012)), 1):
            standoff = register(_cylinder(
                f"Internal motor driver M3 standoff {side}{index}",
                0.0017, 0.006, (x + dx, -0.028 + dy, -0.093), silver))
            standoff["fastener"] = "M3 removable electronics standoff"
            standoff["mounting_height_mm"] = 6.0

    modules = (
        ("Internal main fuse holder", (0.036, 0.016, 0.018), (0.128, 0.025, -0.093), orange,
         "replaceable branch-rated DC fuse next to battery positive"),
        ("Internal main contactor", (0.040, 0.028, 0.024), (0.128, -0.005, -0.093), dark,
         "normally open DC contactor; de-energise-to-safe"),
        ("Internal dual-channel E-stop receiver", (0.042, 0.030, 0.012), (0.080, 0.055, -0.090), red,
         "dual normally-closed channels; safety rating or wired tether required"),
        ("Internal E-stop safety relay", (0.038, 0.028, 0.018), (0.025, 0.055, -0.090), red,
         "monitored dual-channel relay drives contactor coil and driver enable"),
        ("Internal externally reachable service disconnect", (0.032, 0.020, 0.018),
         (0.178, 0.030, -0.060), orange, "manual battery isolation reachable at equator service joint"),
        ("Internal tether E-stop NC jack", (0.020, 0.016, 0.016), (0.210, 0.000, -0.035), green,
         "sealed equator pass-through for first wheel-off and tethered floor tests"),
    )
    for name, dimensions, location, material, contract in modules:
        module = register(_cube(name, dimensions, location, material, 0.0020))
        module["drive_power_contract"] = contract
        module["candidate_status"] = "NOT_FROZEN"
        module["physical_test_status"] = "NOT_RUN"
        module["mass_accounting_group"] = "fuse contactor and main connector"
        if name == "Internal main fuse holder":
            module["fuse_rating"] = "TBD after measured stall current and wire ampacity"
        elif name == "Internal main contactor":
            module["dc_break_rating"] = "TBD at 16.8 V and measured fault current"
            module["normally_open"] = True
        elif name == "Internal dual-channel E-stop receiver":
            module["wireless_alone_not_accepted"] = True
        elif name == "Internal E-stop safety relay":
            module["manual_reset_required"] = True
            module["contactor_feedback_required"] = True

    power_paths = {
        "battery positive to service disconnect": [(0.055, 0.005, -0.078), (0.120, 0.030, -0.068), (0.162, 0.030, -0.060)],
        "service disconnect to fuse": [(0.194, 0.030, -0.060), (0.165, 0.030, -0.075), (0.146, 0.025, -0.090)],
        "fuse to contactor": [(0.128, 0.017, -0.093), (0.128, 0.009, -0.093)],
        "contactor to driver L": [(0.108, -0.005, -0.093), (0.020, -0.052, -0.091), (-0.054, -0.035, -0.087)],
        "contactor to driver R": [(0.108, -0.005, -0.093), (0.100, -0.026, -0.090), (0.106, -0.028, -0.087)],
        "driver output L": [(-0.106, -0.028, -0.087), (-0.078, -0.010, -0.096), (-0.042, 0.016, -0.094)],
        "driver output R": [(0.054, -0.028, -0.087), (0.060, -0.005, -0.096), (0.042, 0.016, -0.094)],
    }
    for label, points in power_paths.items():
        cable = register(_tube_mesh(f"Internal drive power {label}", points, 0.0025, orange))
        cable["drive_power_wire"] = label
        cable["minimum_bend_radius_mm"] = 30.0
        cable["conductor_contract"] = "size from measured continuous/stall current, voltage drop and sealed-shell thermal test"
        cable["physical_test_status"] = "NOT_RUN"

    safety_paths = {
        "estop_channel_A": [(0.210, -0.004, -0.035), (0.150, 0.050, -0.072), (0.090, 0.055, -0.084), (0.044, 0.055, -0.085)],
        "estop_channel_B": [(0.210, 0.004, -0.035), (0.150, 0.060, -0.078), (0.070, 0.062, -0.084), (0.025, 0.064, -0.085)],
        "contactor_feedback": [(0.044, 0.050, -0.090), (0.080, 0.035, -0.084), (0.128, 0.009, -0.084)],
        "driver_enable_L": [(0.000, -0.030, -0.092), (-0.030, -0.045, -0.084), (-0.080, -0.045, -0.084)],
        "driver_enable_R": [(0.000, -0.030, -0.092), (0.030, -0.045, -0.084), (0.080, -0.045, -0.084)],
    }
    for wire_type, points in safety_paths.items():
        cable = register(_tube_mesh(f"Internal {wire_type.replace('_', ' ')}", points, 0.0009, dark))
        cable["drive_safety_wire"] = wire_type
        cable["minimum_bend_radius_mm"] = 10.0
        cable["normally_closed"] = wire_type.startswith("estop_channel")
        cable["physical_test_status"] = "NOT_RUN"

    return created
