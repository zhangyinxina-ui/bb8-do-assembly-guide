"""Apply and render stage-13 power-safety hardware to the current master .blend."""

import os
import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from power_safety_geometry import (
    add_power_safety_hardware,
    remove_existing_power_safety_geometry,
)


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "blender" / "output" / "BB8_1to1_screen_referenced.blend"
CHECKPOINT = ROOT / "blender" / "checkpoints" / "BB8_stage13_power_safety_hardware_v3.blend"
OUTPUT = ROOT / "blender" / "output"

if Path(bpy.data.filepath).resolve() != MASTER.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER))

internal = bpy.data.collections.get("Internal replica mechanism - schematic")
chassis_rig = bpy.data.objects.get("RIG 20 - Gravity stabilised chassis")
if internal is None or chassis_rig is None:
    raise RuntimeError("Stage-13 requires the existing internal collection and chassis rig")


def move_internal(obj):
    if obj.name not in internal.objects:
        internal.objects.link(obj)
    obj["bb8_internal"] = True
    obj.hide_render = True
    return obj


remove_existing_power_safety_geometry()
created = add_power_safety_hardware(internal, move_internal, parent=chassis_rig)

scene = bpy.context.scene
scene["engineering_stage"] = 13
scene["power_safety_hardware"] = "dual INA226 + dual 2 mOhm Kelvin shunts + ALERT wire-OR to independent driver EN gate"
scene["power_safety_physical_test_status"] = "NOT_RUN"
scene["power_safety_model_object_count"] = len(created)

# Refresh the four internal reference renders with the new board and wiring
# geometry while leaving the already calibrated exterior views untouched.
internal_names = {obj.name for obj in internal.objects}
external = [
    obj for obj in scene.objects
    if obj.name not in internal_names and obj.type not in {"CAMERA", "LIGHT"}
]
external_state = {obj.name: obj.hide_render for obj in external}
internal_state = {obj.name: obj.hide_render for obj in internal.objects}
for obj in external:
    obj.hide_render = True
for obj in internal.objects:
    obj.hide_render = False

render_specs = {
    "mechanism": (1100, 900),
    "internal_front": (900, 900),
    "internal_side": (900, 900),
    "internal_top": (900, 900),
}
for name, resolution in render_specs.items():
    camera = bpy.data.objects.get(name + " orthographic camera")
    if camera is None:
        raise RuntimeError(f"Missing render camera: {name}")
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

for obj in external:
    obj.hide_render = external_state[obj.name]
for obj in internal.objects:
    obj.hide_render = internal_state[obj.name]
scene.render.resolution_x = 900
scene.render.resolution_y = 1100

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(CHECKPOINT))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
print("STAGE13_OUTPUT", MASTER)
print("STAGE13_CHECKPOINT", CHECKPOINT)
print("STAGE13_CREATED", len(created))
