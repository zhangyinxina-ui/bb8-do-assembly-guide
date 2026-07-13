import bpy
import os
from pathlib import Path

# Resolve from the already-open verified master so the exporter is portable
# when invoked from Blender's console or a temporary execution wrapper.
ROOT = str(Path(bpy.data.filepath).resolve().parents[2])
BLEND = os.path.join(ROOT, "blender", "output", "BB8_1to1_screen_referenced.blend")
OUT = os.path.join(ROOT, "blender", "exports")
os.makedirs(OUT, exist_ok=True)
if Path(bpy.data.filepath).resolve() != Path(BLEND).resolve():
    bpy.ops.wm.open_mainfile(filepath=BLEND)


def select_names(predicate, include_empties=False):
    bpy.ops.object.select_all(action='DESELECT')
    selected = []
    for obj in bpy.context.scene.objects:
        if predicate(obj) and (obj.type == 'MESH' or include_empties and obj.type == 'EMPTY'):
            obj.hide_set(False)
            obj.select_set(True)
            selected.append(obj)
    if selected:
        bpy.context.view_layer.objects.active = next((o for o in selected if o.type == 'MESH'), selected[0])
    return selected


def stl(filename, predicate):
    selected = select_names(predicate)
    if not selected:
        raise RuntimeError(f"No objects for {filename}")
    path = os.path.join(OUT, filename)
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000.0)
    print("EXPORTED", path, len(selected))


body_prefixes = ("BB-8 body", "Body panel", "Body orange", "Body accent", "Body triangle")
head_prefixes = ("Head ", "Main photoreceptor", "Photoreceptor", "Holographic", "Long antenna", "Short antenna")
stl("BB8_body_visual_reference_mm.stl", lambda o: o.name.startswith(body_prefixes))
stl("BB8_head_visual_reference_mm.stl",
    lambda o: o.name.startswith(head_prefixes) and not bool(o.get("bb8_internal")))
stl("BB8_internal_mechanism_mm.stl",
    lambda o: bool(o.get("bb8_internal")) and not bool(o.get("engineering_annotation")))

# GLB keeps hierarchy, materials and animation. Exclude render-only floor/lights/cameras.
select_names(lambda o: o.name.startswith(body_prefixes + head_prefixes + ("Internal", "RIG ")), include_empties=True)
glb = os.path.join(OUT, "BB8_1to1_kinematic.glb")
bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format='GLB',
    use_selection=True,
    export_animations=True,
    export_frame_range=True,
)
print("EXPORTED", glb)
