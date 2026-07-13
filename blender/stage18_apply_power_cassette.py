"""Apply the Stage-18 modular drive-power cassette to the verified master."""

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
    raise RuntimeError(f"Stage-18 must run in the verified master, got {MASTER}")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stage15_drive_power_geometry
import stage18_power_cassette_geometry

# Blender keeps imported modules alive across console executions. Reload the
# geometry modules so a corrected generator is always what gets saved.
importlib.reload(stage15_drive_power_geometry)
importlib.reload(stage18_power_cassette_geometry)

remove_existing_stage15_geometry = stage15_drive_power_geometry.remove_existing_stage15_geometry
add_stage18_power_cassette = stage18_power_cassette_geometry.add_stage18_power_cassette
remove_existing_stage18_geometry = stage18_power_cassette_geometry.remove_existing_stage18_geometry


internal = bpy.data.collections.get("Internal replica mechanism - schematic")
chassis_rig = bpy.data.objects.get("RIG 20 - Gravity stabilised chassis")
if internal is None or chassis_rig is None:
    raise RuntimeError("Stage-18 requires the internal collection and chassis rig")


def move_internal(obj):
    if obj.name not in internal.objects:
        internal.objects.link(obj)
    obj["bb8_internal"] = True
    obj.hide_render = True
    return obj


remove_existing_stage15_geometry()
remove_existing_stage18_geometry()
created = add_stage18_power_cassette(move_internal, parent=chassis_rig)

scene = bpy.context.scene
scene["engineering_stage"] = 18
scene["drive_power_hardware"] = (
    "vertical REC Active BMS 4S catalogue envelope + MDD20A official footprint/assumed height keepout "
    "+ SW60 + MIDI service keepout + external shunt + dual-channel gate keepout")
scene["power_cassette_model_object_count"] = len(created)
scene["power_cassette_packaging_status"] = "PASS_ANALYTICAL_ONLY"
scene["power_cassette_physical_fit_status"] = "NOT_RUN"
scene["power_cassette_powered_test_status"] = "NOT_RUN"
scene["power_cassette_bms_candidate"] = "REC Active BMS 4S - NOT_PURCHASE_FROZEN"

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
    obj.hide_render = bool(obj.get("engineering_annotation"))

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

for obj in external:
    obj.hide_render = external_state[obj.name]
for obj in internal.objects:
    obj.hide_render = internal_state[obj.name]
scene.render.resolution_x, scene.render.resolution_y = 900, 1100

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(EXPECTED_MASTER))
print("STAGE18_OUTPUT", EXPECTED_MASTER)
print("STAGE18_CREATED", len(created))
print("STAGE18_CHECKPOINT_CREATED", False)
