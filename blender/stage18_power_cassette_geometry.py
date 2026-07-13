"""Stage-18 modular drive-power cassette candidate geometry."""

from __future__ import annotations

import json
from math import pi
from pathlib import Path

import bpy


STAGE_TAG = "power_cassette_geometry_stage"


def _material(name):
    material = bpy.data.materials.get(name)
    if material is None:
        raise RuntimeError(f"Required material is missing: {name}")
    return material


def _candidate_material(name, rgba):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
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


def _cylinder(name, radius, depth, location, material, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
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
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    return bpy.context.object


def remove_existing_stage18_geometry():
    for obj in list(bpy.data.objects):
        if obj.get(STAGE_TAG) == 18:
            bpy.data.objects.remove(obj, do_unlink=True)


def add_stage18_power_cassette(move_internal, parent=None):
    """Instantiate catalogue envelopes and explicit unresolved keepouts.

    This is an analytical packaging model. MDD20A height, the MIDI holder,
    the gate PCB and all purchased-sample interfaces remain measurement gates.
    """
    root = Path(bpy.data.filepath).resolve().parents[2]
    layout = json.loads(
        (root / "engineering" / "stage18_power_cassette_layout.json").read_text(encoding="utf-8"))
    components = {item["id"]: item for item in layout["components"]}

    blue = _material("BB8 lens blue")
    dark = _material("BB8 graphite")
    orange = _material("BB8 burnt orange")
    silver = _material("BB8 silver")
    green = _candidate_material("BB8 stage18 BMS green", (0.02, 0.24, 0.08, 1.0))
    red = _candidate_material("BB8 stage18 safety red", (0.62, 0.015, 0.008, 1.0))
    violet = _candidate_material("BB8 stage18 assumption violet", (0.22, 0.04, 0.34, 0.35))

    created = []

    def register(obj, component_id=None, physical=True):
        move_internal(obj)
        obj[STAGE_TAG] = 18
        obj["physical_test_status"] = "NOT_RUN"
        obj["stage18_analytical_packaging_only"] = True
        if component_id:
            obj["candidate_component_id"] = component_id
            obj["candidate_status"] = components[component_id]["status"]
        if not physical:
            obj["engineering_annotation"] = True
        if parent is not None:
            obj.parent = parent
        created.append(obj)
        return obj

    legacy_gate = bpy.data.objects.get("Internal ALERT to driver EN hardware gate")
    if legacy_gate is not None:
        legacy_gate["engineering_annotation"] = True
        legacy_gate["legacy_stage13_gate"] = True
        legacy_gate.hide_render = True

    # REC Active BMS 4S: official 44 x 111 x 135 mm enclosed envelope,
    # rotated vertically at the left side of the chassis.
    bms = components["BMS01"]
    bms_body = register(_cube(
        bms["name"], tuple(value / 1000 for value in bms["dimensions_mm"]),
        tuple(value / 1000 for value in bms["centre_mm"]), green, 0.004), "BMS01")
    bms_body["official_enclosed_dimensions_mm"] = "44 x 111 x 135"
    bms_body["series_cells"] = 4
    bms_body["temperature_sensor_channels"] = 2
    bms_body["active_balance_current_a"] = 2.0
    bms_body["external_shunt_required"] = True
    bms_body["external_contactor_control"] = True
    bms_body["exact_order_code_and_chemistry"] = "NOT_FROZEN"
    bms_connector = register(_cube(
        "Internal REC BMS AMPSEAL connector envelope", (0.008, 0.0595, 0.0235),
        (-0.127, 0.0, -0.035), dark, 0.002), "BMS01")
    # This is a component-level candidate interface, not one of the four
    # shell-separation service connectors already modelled in the harness.
    bms_connector["candidate_connector_contract"] = (
        "official AMPSEAL family; harness and mating part not released"
    )
    bms_connector["disconnect_before_service"] = True
    for side, y in (("F", -0.049), ("R", 0.049)):
        rail = register(_cube(
            f"Internal REC BMS mounting rail {side}", (0.006, 0.012, 0.105),
            (-0.165, y, -0.010), silver, 0.001), "BMS01")
        rail["mount_contract"] = "removable rail; final slot geometry requires purchased sample"

    # MDD20A board uses the official footprint and hole spacing. The violet
    # 25 mm-thick box is deliberately an assumed height/connector keepout.
    driver = components["DRV01"]
    driver_centre = tuple(value / 1000 for value in driver["centre_mm"])
    keepout = register(_cube(
        driver["name"], tuple(value / 1000 for value in driver["dimensions_mm"]),
        driver_centre, violet, 0.002), "DRV01", physical=False)
    keepout["height_keepout_assumption_mm"] = 25.0
    keepout["official_height_available"] = False
    board = register(_cube(
        "Internal MDD20A official footprint board", (0.0016, 0.0889, 0.07874),
        driver_centre, blue, 0.001), "DRV01")
    board["official_board_dimensions_mm"] = "88.90 x 78.74; nominal PCB thickness shown as modelling convention"
    board["mount_hole_spacing_mm"] = "83.82 x 73.66"
    board["mount_hole_diameter_mm"] = 3.0
    board["independent_enable_input"] = False
    board["pwm_low_behavior"] = "BRAKE_NOT_DEENERGISED"
    for index, (dy, dz) in enumerate(((-0.04191, -0.03683), (-0.04191, 0.03683),
                                      (0.04191, -0.03683), (0.04191, 0.03683)), 1):
        standoff = register(_cylinder(
            f"Internal MDD20A M3 standoff {index}", 0.0015, 0.012,
            (0.128, dy, -0.040 + dz), silver, (0.0, pi / 2.0, 0.0)), "DRV01")
        standoff["official_hole_pattern"] = True
    for side, y in (("power", -0.034), ("motor", 0.034)):
        terminal = register(_cube(
            f"Internal MDD20A {side} terminal keepout", (0.010, 0.016, 0.030),
            (0.136, y, -0.040), orange, 0.001), "DRV01", physical=False)
        terminal["connector_sweep_measurement_required"] = True

    # SW60 catalogue envelope, provisional replaceable fuse holder and the
    # future independent gate PCB keepout.
    contactor = components["CON01"]
    contactor_body = register(_cube(
        contactor["name"], tuple(value / 1000 for value in contactor["dimensions_mm"]),
        tuple(value / 1000 for value in contactor["centre_mm"]), dark, 0.004), "CON01")
    contactor_body["official_envelope_mm"] = "81 x 37 x 28.1"
    contactor_body["normally_open"] = True
    contactor_body["auxiliary_contact_required"] = True
    contactor_body["plain_diode_suppression_rejected"] = True
    contactor_body["dropout_measurement_contract_ms"] = "<=20"

    fuse = components["FUS01"]
    fuse_keepout = register(_cube(
        fuse["name"], tuple(value / 1000 for value in fuse["dimensions_mm"]),
        tuple(value / 1000 for value in fuse["centre_mm"]), violet, 0.002), "FUS01", physical=False)
    fuse_keepout["holder_envelope_status"] = "PROVISIONAL"
    fuse_body = register(_cube(
        "Internal 30A MIDI fuse body candidate", (0.041, 0.016, 0.005),
        (0.145, 0.105, -0.070), orange, 0.001), "FUS01")
    fuse_body["provisional_rating_a"] = 30.0
    fuse_body["i2t_and_harness_thermal_status"] = "NOT_RUN"

    gate = components["GAT01"]
    gate_keepout = register(_cube(
        gate["name"], tuple(value / 1000 for value in gate["dimensions_mm"]),
        tuple(value / 1000 for value in gate["centre_mm"]), violet, 0.002), "GAT01", physical=False)
    gate_board = register(_cube(
        "Internal dual-channel MDD20A hardware gate PCB placeholder", (0.050, 0.035, 0.003),
        (0.085, -0.110, -0.060), red, 0.001), "GAT01")
    gate_board["mcu_independent_disable_required"] = True
    gate_board["two_independent_channels_required"] = True
    gate_board["released_pcb"] = False

    shunt = components["SHN01"]
    shunt_body = register(_cube(
        shunt["name"], tuple(value / 1000 for value in shunt["dimensions_mm"]),
        tuple(value / 1000 for value in shunt["centre_mm"]), silver, 0.002), "SHN01")
    shunt_body["low_side_pack_current_measurement"] = True
    shunt_body["exact_resistance_and_part"] = "NOT_FROZEN"
    shunt_body["kelvin_connection_required"] = True

    for component_id, material in (("REL01", red), ("EST01", red)):
        item = components[component_id]
        module = register(_cube(
            item["name"], tuple(value / 1000 for value in item["dimensions_mm"]),
            tuple(value / 1000 for value in item["centre_mm"]), material, 0.002), component_id)
        module["safety_part_status"] = "NOT_FROZEN"
        module["manual_reset_required"] = component_id == "REL01"

    service_disconnect = register(_cube(
        "Internal externally reachable service disconnect", (0.032, 0.020, 0.018),
        (0.178, 0.030, -0.060), orange, 0.002))
    service_disconnect["drive_power_contract"] = "manual battery isolation reachable at equator service joint"
    tether = register(_cube(
        "Internal tether E-stop NC jack", (0.020, 0.016, 0.016),
        (0.210, 0.000, -0.035), red, 0.002))
    tether["drive_power_contract"] = "wired tether mandatory for first wheel-off and floor tests"

    for index, x in enumerate((-0.030, 0.030), 1):
        sensor = register(_cylinder(
            f"Internal REC BMS pack temperature sensor {index}", 0.004, 0.003,
            (x, 0.041, -0.078), green, (pi / 2.0, 0.0, 0.0)))
        sensor["temperature_channel"] = index
        sensor["physical_bond_and_calibration_status"] = "NOT_RUN"

    power_paths = {
        "battery positive to service disconnect": [(0.055, 0.005, -0.078), (0.125, 0.030, -0.065), (0.162, 0.030, -0.060)],
        "service disconnect to MIDI fuse": [(0.194, 0.030, -0.060), (0.190, 0.080, -0.075), (0.165, 0.105, -0.070)],
        "MIDI fuse to SW60": [(0.125, 0.105, -0.070), (0.106, 0.110, -0.070)],
        "SW60 to MDD20A": [(0.025, 0.110, -0.070), (0.030, 0.070, -0.060), (0.123, 0.030, -0.045)],
        "MDD20A motor output L": [(0.136, -0.034, -0.055), (0.080, -0.060, -0.085), (-0.040, 0.015, -0.094)],
        "MDD20A motor output R": [(0.136, 0.034, -0.055), (0.100, 0.050, -0.085), (0.040, 0.015, -0.094)],
        "battery negative to REC shunt": [(-0.055, 0.005, -0.078), (-0.060, 0.060, -0.075), (-0.065, 0.088, -0.070)],
    }
    for label, points in power_paths.items():
        cable = register(_tube_mesh(f"Internal stage18 power {label}", points, 0.0025, orange))
        cable["stage18_power_wire"] = label
        cable["minimum_bend_radius_mm"] = 30.0
        cable["conductor_and_terminal_thermal_status"] = "NOT_RUN"

    signal_paths = {
        "BMS contactor command": [(-0.123, 0.030, -0.030), (-0.030, 0.080, -0.045), (0.020, 0.070, -0.045), (0.065, 0.098, -0.070)],
        "BMS shunt Kelvin": [(-0.123, 0.020, -0.040), (-0.090, 0.080, -0.060), (-0.065, 0.100, -0.065)],
        "E-stop channel A": [(-0.030, 0.105, -0.045), (0.000, 0.090, -0.045), (0.020, 0.070, -0.045)],
        "E-stop channel B": [(-0.030, 0.110, -0.050), (0.000, 0.100, -0.050), (0.020, 0.075, -0.050)],
        "relay to dual gate A": [(0.020, 0.070, -0.045), (0.050, 0.000, -0.050), (0.085, -0.100, -0.060)],
        "relay to dual gate B": [(0.020, 0.075, -0.050), (0.060, -0.010, -0.055), (0.090, -0.100, -0.065)],
        "dual gate to MDD20A": [(0.085, -0.092, -0.060), (0.120, -0.060, -0.050), (0.136, -0.044, -0.040)],
        "temperature sensors to BMS": [(0.000, 0.041, -0.078), (-0.070, 0.040, -0.060), (-0.123, 0.030, -0.040)],
    }
    for label, points in signal_paths.items():
        cable = register(_tube_mesh(f"Internal stage18 signal {label}", points, 0.0009, dark))
        cable["stage18_safety_signal"] = label
        cable["minimum_bend_radius_mm"] = 10.0
        cable["physical_test_status"] = "NOT_RUN"

    return created
