"""Apply Stage-19 gate detail to the sole verified Blender master."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys

import bpy


MASTER = Path(bpy.data.filepath).resolve()
ROOT = MASTER.parents[2]
EXPECTED_MASTER = ROOT / "blender" / "output" / "BB8_1to1_screen_referenced.blend"
SCRIPT_DIR = ROOT / "blender"
OUTPUT = SCRIPT_DIR / "output"

if MASTER != EXPECTED_MASTER.resolve():
    raise RuntimeError(f"Stage-19 must run in the sole verified master, got {MASTER}")
if bpy.data.is_dirty:
    raise RuntimeError("Stage-19 refuses to overwrite an already-dirty Blender session")
if int(bpy.context.scene.get("engineering_stage", 0)) != 18:
    raise RuntimeError("Stage-19 requires the reopened and audited Stage-18 master")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stage19_dual_permissive_gate_geometry

importlib.reload(stage19_dual_permissive_gate_geometry)

remove_existing_stage19_geometry = (
    stage19_dual_permissive_gate_geometry.remove_existing_stage19_geometry)
add_stage19_dual_permissive_gate = (
    stage19_dual_permissive_gate_geometry.add_stage19_dual_permissive_gate)

internal = bpy.data.collections.get("Internal replica mechanism - schematic")
chassis_rig = bpy.data.objects.get("RIG 20 - Gravity stabilised chassis")
if internal is None or chassis_rig is None:
    raise RuntimeError("Stage-19 requires the internal collection and chassis rig")


def move_internal(obj):
    if obj.name not in internal.objects:
        internal.objects.link(obj)
    obj["bb8_internal"] = True
    obj.hide_render = True
    return obj


remove_existing_stage19_geometry()
created = add_stage19_dual_permissive_gate(move_internal, parent=chassis_rig)

scene = bpy.context.scene
scene["engineering_stage"] = 19
scene["stage19_gate_model_object_count"] = len(created)
scene["stage19_gate_design_status"] = "PASS_ANALYTICAL_ONLY"
scene["stage19_gate_physical_test_status"] = "NOT_RUN"
scene["stage19_gate_safety_certification"] = "NONE"
scene["stage19_gate_manufacturing_release"] = "NOT_RELEASED_NO_KICAD_GERBER"
scene["stage19_gate_fabrication_export"] = False
scene["stage19_gate_logic_equation"] = (
    "PWM_OUT = LOGIC_POWER_OK AND PWM_IN AND SAFE_A_OK AND SAFE_B_OK AND ALERT_N")
scene["stage19_gate_truth_table_rows"] = 64

internal_names = {obj.name for obj in internal.objects}
external = [
    obj for obj in scene.objects
    if obj.name not in internal_names and obj.type not in {"CAMERA", "LIGHT"}
]
external_state = {obj.name: obj.hide_render for obj in external}
internal_state = {obj.name: obj.hide_render for obj in internal.objects}
try:
    for obj in external:
        obj.hide_render = True
    for obj in internal.objects:
        obj.hide_render = bool(obj.get("engineering_annotation")) or bool(
            obj.get("stage19_superseded_keepout"))

    for name, resolution in {
        "mechanism": (1100, 900),
        "internal_front": (900, 900),
        "internal_side": (900, 900),
        "internal_top": (900, 900),
    }.items():
        camera = bpy.data.objects.get(name + " orthographic camera")
        if camera is None:
            raise RuntimeError(f"Missing render camera: {name}")
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.filepath = str(OUTPUT / f"{name}.png")
        bpy.ops.render.render(write_still=True)
finally:
    for obj in external:
        obj.hide_render = external_state[obj.name]
    for obj in internal.objects:
        obj.hide_render = internal_state[obj.name]
    scene.render.resolution_x, scene.render.resolution_y = 900, 1100

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(EXPECTED_MASTER))
print("STAGE19_OUTPUT", EXPECTED_MASTER)
print("STAGE19_CREATED", len(created))
print("STAGE19_CHECKPOINT_CREATED", False)
