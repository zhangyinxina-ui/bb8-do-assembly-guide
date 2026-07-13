"""Export a read-only Stage-18 internal packaging baseline from the open master."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


MASTER = Path(bpy.data.filepath).resolve()
ROOT = MASTER.parents[2]
OUTPUT = ROOT / "engineering" / "stage18_layout_baseline.json"
EXPECTED_MASTER = ROOT / "blender" / "output" / "BB8_1to1_screen_referenced.blend"


def world_aabb(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) for index in range(3)]
    maximum = [max(point[index] for point in corners) for index in range(3)]
    return {
        "minimum_mm": [round(value * 1000.0, 3) for value in minimum],
        "maximum_mm": [round(value * 1000.0, 3) for value in maximum],
        "dimensions_mm": [round((maximum[index] - minimum[index]) * 1000.0, 3) for index in range(3)],
        "centre_mm": [round((maximum[index] + minimum[index]) * 500.0, 3) for index in range(3)],
    }


def parent_space_aabb(obj):
    corners = [obj.matrix_local @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) for index in range(3)]
    maximum = [max(point[index] for point in corners) for index in range(3)]
    return {
        "parent_minimum_mm": [round(value * 1000.0, 3) for value in minimum],
        "parent_maximum_mm": [round(value * 1000.0, 3) for value in maximum],
        "parent_dimensions_mm": [round((maximum[index] - minimum[index]) * 1000.0, 3) for index in range(3)],
        "parent_centre_mm": [round((maximum[index] + minimum[index]) * 500.0, 3) for index in range(3)],
    }


if MASTER != EXPECTED_MASTER.resolve():
    raise RuntimeError(f"Open master mismatch: {bpy.data.filepath}")

internal = [obj for obj in bpy.data.objects if obj.get("bb8_internal") and obj.type in {"MESH", "CURVE"}]
key_names = {
    "Internal aluminium chassis",
    "Internal 4S battery ballast",
    "Internal sealed low ballast cassette",
    "Internal geared motor L",
    "Internal geared motor R",
    "Internal drive wheel L",
    "Internal drive wheel R",
    "Internal motor driver L",
    "Internal motor driver R",
    "Internal main fuse holder",
    "Internal main contactor",
    "Internal E-stop safety relay",
    "Internal ALERT to driver EN hardware gate",
    "Internal IMU controller",
}

payload = {
    "stage": 18,
    "source_blend": str(MASTER.relative_to(ROOT)),
    "source_saved_state": not bpy.data.is_dirty,
    "engineering_stage": bpy.context.scene.get("engineering_stage"),
    "body_inner_radius_assumption_mm": 254.0,
    "internal_object_count": len(internal),
    "key_objects": {},
    "all_internal_aabbs": [],
}

for obj in sorted(internal, key=lambda item: item.name):
    item = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "engineering_annotation": bool(obj.get("engineering_annotation")),
        **world_aabb(obj),
        **parent_space_aabb(obj),
    }
    payload["all_internal_aabbs"].append(item)
    if obj.name in key_names:
        payload["key_objects"][obj.name] = item

missing = sorted(key_names - set(payload["key_objects"]))
payload["missing_key_objects"] = missing
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("STAGE18_LAYOUT_BASELINE", OUTPUT)
print("STAGE18_LAYOUT_INTERNALS", len(internal))
print("STAGE18_LAYOUT_MISSING", missing)
