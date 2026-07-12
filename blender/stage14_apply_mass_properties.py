"""Apply stage-14 ballast, mass metadata and COM annotations to the master blend."""

import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from stage14_mass_geometry import add_stage14_mass_geometry, remove_existing_stage14_geometry, write_mass_input

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "blender" / "output" / "BB8_1to1_screen_referenced.blend"
CHECKPOINT = ROOT / "blender" / "checkpoints" / "BB8_stage14_mass_cg_ballast.blend"
MASS_INPUT = ROOT / "engineering" / "mass_properties_input.json"
OUTPUT = ROOT / "blender" / "output"

if Path(bpy.data.filepath).resolve() != MASTER.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER))

internal = bpy.data.collections.get("Internal replica mechanism - schematic")
chassis_rig = bpy.data.objects.get("RIG 20 - Gravity stabilised chassis")
if internal is None or chassis_rig is None:
    raise RuntimeError("Stage-14 requires the internal collection and chassis rig")


def move_internal(obj):
    if obj.name not in internal.objects:
        internal.objects.link(obj)
    obj["bb8_internal"] = True
    obj.hide_render = True
    return obj


remove_existing_stage14_geometry()
created, model_input, results = add_stage14_mass_geometry(move_internal, parent=chassis_rig)
write_mass_input(MASS_INPUT, model_input)

scene = bpy.context.scene
scene["engineering_stage"] = 14
scene["mass_model_object_count"] = len(created)

internal_names = {obj.name for obj in internal.objects}
external = [obj for obj in scene.objects if obj.name not in internal_names and obj.type not in {"CAMERA", "LIGHT"}]
external_state = {obj.name: obj.hide_render for obj in external}
internal_state = {obj.name: obj.hide_render for obj in internal.objects}
for obj in external:
    obj.hide_render = True
for obj in internal.objects:
    obj.hide_render = False
for name, resolution in {"mechanism": (1100, 900), "internal_front": (900, 900),
                         "internal_side": (900, 900), "internal_top": (900, 900)}.items():
    scene.camera = bpy.data.objects[name + " orthographic camera"]
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
for obj in external:
    obj.hide_render = external_state[obj.name]
for obj in internal.objects:
    obj.hide_render = internal_state[obj.name]
scene.render.resolution_x, scene.render.resolution_y = 900, 1100

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(CHECKPOINT))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
print("STAGE14_OUTPUT", MASTER)
print("STAGE14_CHECKPOINT", CHECKPOINT)
print("STAGE14_CREATED", len(created))
print("STAGE14_STATUS", results["status"])
