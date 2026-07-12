"""Stage-14 low ballast geometry, mass metadata and COM annotations."""

from __future__ import annotations

import json
from pathlib import Path

import bpy

from mass_properties_model import default_input, summarize


STAGE_TAG = "mass_properties_geometry_stage"


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


def _sphere(name, radius, location, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def remove_existing_stage14_geometry():
    for obj in list(bpy.data.objects):
        if obj.get(STAGE_TAG) == 14:
            bpy.data.objects.remove(obj, do_unlink=True)


def add_stage14_mass_geometry(move_internal, parent=None):
    silver = _material("BB8 silver")
    orange = _material("BB8 burnt orange")
    yellow = _material("BB8 yellow indicator")
    red = _material("BB8 red indicator")
    created = []

    def register(obj, annotation=False):
        move_internal(obj)
        obj[STAGE_TAG] = 14
        if annotation:
            obj["engineering_annotation"] = True
        if parent is not None:
            obj.parent = parent
        created.append(obj)
        return obj

    cassette = register(_cube("Internal sealed low ballast cassette", (0.120, 0.070, 0.024),
                              (0, 0, -0.205), silver, 0.003))
    cassette["mass_nominal_kg"] = 1.50
    cassette["mass_min_kg"] = 1.35
    cassette["mass_max_kg"] = 1.65
    cassette["material_contract"] = "sealed steel ballast; no loose lead or free-moving weights"
    cassette["removable_before_service"] = True
    cassette["physical_test_status"] = "NOT_RUN"

    hanger = register(_cube("Internal ballast central hanger", (0.008, 0.060, 0.073),
                            (0, 0, -0.1565), silver, 0.002))
    hanger["load_path"] = "centre crossmember to sealed ballast cassette"
    hanger["material_contract"] = "6061-T6 aluminium or verified equivalent"
    for side, y in (("F", -0.026), ("R", 0.026)):
        strap = register(_cube(f"Internal ballast retention strap {side}", (0.132, 0.006, 0.030),
                               (0, y, -0.205), orange, 0.002))
        strap["retention_contract"] = "captive metal strap; secondary locking feature required"
    for index, (x, y) in enumerate(((-0.0015, -0.020), (-0.0015, 0.020),
                                    (0.0015, -0.020), (0.0015, 0.020)), 1):
        bolt = register(_cylinder(f"Internal ballast M5 captive bolt {index}", 0.0025, 0.020,
                                  (x, y, -0.183), silver))
        bolt["fastener"] = "M5 captive; prevailing-torque retention required"

    model_input = default_input()
    results = summarize(model_input)
    nominal_com = tuple(results["nominal"]["com_m"])
    nominal_marker = register(_sphere("Engineering nominal COM marker", 0.010,
                                      nominal_com, yellow), annotation=True)
    nominal_marker["marker_role"] = "stage-14 nominal full-system centre of mass"
    legacy_marker = register(_sphere("Engineering legacy 110mm COM marker", 0.007,
                                     (0, 0, -0.110), red), annotation=True)
    legacy_marker["marker_role"] = "superseded unverified analytical assumption"

    for component in model_input["components"]:
        obj = bpy.data.objects.get(component["object_name"])
        if obj is None:
            raise RuntimeError(f"Mass representative object missing: {component['object_name']}")
        for key in ("mass_min_kg", "mass_nominal_kg", "mass_max_kg", "physical_test_status"):
            obj[key] = component[key]
        obj["mass_represents"] = component["component"]
        obj["mass_source"] = component["source"]

    scene = bpy.context.scene
    scene["mass_model_status"] = results["status"]
    scene["mass_total_nominal_kg"] = results["nominal"]["total_mass_kg"]
    scene["mass_com_nominal_m"] = results["nominal"]["com_m"]
    scene["mass_com_worst_z_m"] = results["highest_com"]["com_m"][2]
    scene["mass_target_accel_mps2"] = model_input["config"]["target_accel_mps2"]
    scene["mass_max_accel_2x_torque_mps2"] = results["max_accel_for_2x_continuous_torque_mps2"]
    scene["mass_physical_test_status"] = "NOT_RUN"
    return created, model_input, results


def write_mass_input(path, model_input):
    Path(path).write_text(json.dumps(model_input, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
