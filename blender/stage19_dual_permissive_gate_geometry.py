"""Stage-19 detailed pre-CAD dual-permissive PWM-gate geometry."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


STAGE_TAG = "dual_permissive_gate_geometry_stage"
BOARD_CENTRE = (0.085, -0.110, -0.0637)


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


def _cylinder(name, radius, depth, location, material):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def remove_existing_stage19_geometry():
    for obj in list(bpy.data.objects):
        if obj.get(STAGE_TAG) == 19:
            bpy.data.objects.remove(obj, do_unlink=True)


def add_stage19_dual_permissive_gate(move_internal, parent=None):
    """Instantiate the Stage-19 component envelopes inside the Stage-18 keepout.

    The result is a mechanical reference model, not routed PCB geometry and not
    a manufacturing release. Electrical truth comes from the JSON contract and
    CSV netlist; footprints, copper, creepage, courtyard and DRC remain open.
    """
    root = Path(bpy.data.filepath).resolve().parents[2]
    contract = json.loads(
        (root / "engineering" / "stage19_dual_permissive_gate_contract.json")
        .read_text(encoding="utf-8"))
    board_contract = contract["board_envelope"]
    if (
        board_contract["length_mm"] != 50.0
        or board_contract["width_mm"] != 35.0
        or board_contract["pcb_thickness_mm"] != 1.6
        or board_contract["mounting_stack_height_mm"] != 3.0
        or board_contract["maximum_installed_height_mm"] != 14.4
        or len(contract["connectors"]) != 5
        or len(contract["test_points"]) != 6
    ):
        raise RuntimeError("Stage-19 Blender geometry contract has changed; review placement first")

    green = _candidate_material("BB8 stage19 gate PCB green", (0.015, 0.30, 0.12, 1.0))
    cream = _candidate_material("BB8 stage19 JST cream", (0.88, 0.86, 0.70, 1.0))
    black = _material("BB8 graphite")
    orange = _material("BB8 burnt orange")
    silver = _material("BB8 silver")
    gold = _candidate_material("BB8 stage19 testpoint gold", (0.72, 0.48, 0.05, 1.0))

    created = []

    def register(obj, reference, role, part=""):
        move_internal(obj)
        obj[STAGE_TAG] = 19
        obj["candidate_component_id"] = "GAT01"
        obj["component_reference"] = reference
        obj["component_role"] = role
        obj["candidate_part"] = part
        obj["physical_test_status"] = "NOT_RUN"
        obj["stage19_pre_cad_reference_only"] = True
        obj["non_fabrication_reference"] = True
        obj["manufacturing_release"] = "NOT_RELEASED_NO_KICAD_GERBER"
        if parent is not None:
            obj.parent = parent
        created.append(obj)
        return obj

    placeholder = bpy.data.objects.get(
        "Internal dual-channel MDD20A hardware gate PCB placeholder")
    if placeholder is None:
        raise RuntimeError("Stage-19 requires the Stage-18 GAT01 keepout placeholder")
    placeholder["stage19_superseded_keepout"] = True
    placeholder["superseded_by"] = "Internal stage19 dual-permissive gate PCB"
    placeholder.hide_render = True

    board = register(_cube(
        "Internal stage19 dual-permissive gate PCB",
        (0.050, 0.035, 0.0016), BOARD_CENTRE, green, 0.0015),
        "PCB1", "component-envelope substrate", "CUSTOM_STAGE19_GATE")
    board["pcb_dimensions_mm"] = "50 x 35 x 1.6"
    board["mount_hole_diameter_mm"] = 3.2
    board["mount_hole_centres_mm"] = "(3,3); (47,3); (3,32); (47,32)"
    board["logic_equation"] = (
        "PWM_OUT = LOGIC_POWER_OK AND PWM_IN AND SAFE_A_OK AND SAFE_B_OK AND ALERT_N")
    board["two_independent_energise_to_run_inputs"] = True
    board["direct_dual_ina226_alert_gate"] = True
    board["safety_certification"] = "NONE"

    x0 = BOARD_CENTRE[0] - 0.025
    y0 = BOARD_CENTRE[1] - 0.0175
    board_top = BOARD_CENTRE[2] + 0.0008

    for index, (x_mm, y_mm) in enumerate(board_contract["mount_hole_centres_mm"], 1):
        register(_cylinder(
            f"Internal stage19 gate M3 insulated standoff {index}", 0.0025, 0.003,
            (x0 + x_mm / 1000, y0 + y_mm / 1000, BOARD_CENTRE[2] - 0.0023),
            silver), f"H{index}", "insulated board mounting", "M3 candidate")

    connector_specs = [
        ("J1", "logic power", "B2B-XH-A", 8.0, 7.0, 7.4),
        ("J2", "MCU and ALERT input", "B6B-XH-A", 25.0, 7.0, 17.4),
        ("J3", "MDD20A logic output", "B5B-XH-A", 39.0, 28.0, 14.9),
        ("J4", "SAFE_A energise-to-run input", "B2B-XH-A", 8.0, 28.0, 7.4),
        ("J5", "SAFE_B energise-to-run input", "B2B-XH-A", 18.0, 28.0, 7.4),
    ]
    for reference, role, part, x_mm, y_mm, width_mm in connector_specs:
        connector = register(_cube(
            f"Internal stage19 gate {reference} {role} XH",
            (width_mm / 1000, 0.00575, 0.0098),
            (x0 + x_mm / 1000, y0 + y_mm / 1000, board_top + 0.0049),
            cream, 0.0005), reference, role, part)
        connector["connector_series"] = "JST XH 2.5 mm top-entry"
        connector["catalogue_mounting_height_mm"] = 9.8

    for reference, role, y_mm in (
        ("U1", "SAFE_A optocoupler", 17.0),
        ("U2", "SAFE_B optocoupler", 22.0),
    ):
        opto = register(_cube(
            f"Internal stage19 gate {reference} VO617A-4",
            (0.00762, 0.0046, 0.0040),
            (x0 + 0.009, y0 + y_mm / 1000, board_top + 0.0020), black, 0.0004),
            reference, role, "Vishay VO617A-4")
        opto["ctr_bin_percent_at_5ma_25c"] = "160-320"

    for reference, role, x_mm in (
        ("U3", "SAFE_A dual PWM AND stage", 25.0),
        ("U4", "SAFE_B dual PWM AND stage", 32.0),
        ("U5", "ALERT_N dual PWM AND stage", 39.0),
    ):
        register(_cube(
            f"Internal stage19 gate {reference} SN74LVC2G08",
            (0.0032, 0.0032, 0.0012),
            (x0 + x_mm / 1000, y0 + 0.017, board_top + 0.0006), black, 0.0002),
            reference, role, "TI SN74LVC2G08DCU")

    for reference, role, y_mm in (
        ("R1", "SAFE_A LED current limit", 16.0),
        ("R2", "SAFE_B LED current limit", 21.0),
    ):
        resistor = register(_cube(
            f"Internal stage19 gate {reference} 2k input resistor",
            (0.0065, 0.0025, 0.0025),
            (x0 + 0.017, y0 + y_mm / 1000, board_top + 0.00125), orange, 0.0003),
            reference, role, "2.00 kOhm 1% 0.5 W")
        resistor["worst_case_power_w"] = 0.12482
        resistor["power_derating_x"] = 4.006

    test_point_positions = [22.0, 26.5, 31.0, 35.5, 40.0, 44.5]
    for item, x_mm in zip(contract["test_points"], test_point_positions):
        test_point = register(_cylinder(
            f"Internal stage19 gate {item['reference']} {item['net']}",
            0.00075, 0.0020,
            (x0 + x_mm / 1000, y0 + 0.023, board_top + 0.0010), gold),
            item["reference"], f"test point for {item['net']}", "1.0 mm loop or pad")
        test_point["test_net"] = item["net"]

    return created
