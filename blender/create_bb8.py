import bpy
import math
import os
import sys
from mathutils import Matrix, Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from power_safety_geometry import add_power_safety_hardware
from stage14_mass_geometry import add_stage14_mass_geometry, write_mass_input
from stage15_drive_power_geometry import add_stage15_drive_power_hardware

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "blender", "output")
os.makedirs(OUT, exist_ok=True)

# 1:1 screen-referenced replica dimensions (metres in Blender).
BODY_D = 0.508
BODY_R = BODY_D / 2
HEAD_D = 0.295
HEAD_R = HEAD_D / 2
HEAD_VISIBLE_H = 0.197
OFFICIAL_HEIGHT = 0.670
# The 197 mm photographic head outline overlaps the 508 mm ball by about
# 35 mm. This places the untopped silhouette at the official 0.67 m height
# while preserving the independently measured 295 mm maximum head diameter.
HEAD_Z0 = -BODY_R + OFFICIAL_HEIGHT - HEAD_VISIBLE_H


def mat(name, color, metallic=0.0, rough=0.35):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    return m


def add_weathering(material, base_color, dirt_color, scale=18.0, bump_strength=0.08):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (*dirt_color, 1)
    ramp.color_ramp.elements[1].position = 0.48
    ramp.color_ramp.elements[1].color = (*base_color, 1)
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.0015
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material["finish_accuracy"] = "procedural visual weathering; not color-card certified"
    return material


WHITE = add_weathering(mat("BB8 warm white", (0.687, 0.651, 0.571), 0.03, 0.38),
                       (0.687, 0.651, 0.571), (0.18, 0.14, 0.09), 23.0, 0.022)
ORANGE = add_weathering(mat("BB8 burnt orange", (0.578, 0.102, 0.009), 0.01, 0.44),
                        (0.578, 0.102, 0.009), (0.12, 0.025, 0.006), 28.0, 0.020)
DARK = mat("BB8 graphite", (0.009, 0.016, 0.019), 0.35, 0.42)
SILVER = mat("BB8 silver", (0.175, 0.215, 0.215), 0.72, 0.34)
BLUE = mat("BB8 lens blue", (0.003, 0.018, 0.025), 0.08, 0.08)
LENS_BLACK = mat("BB8 optical glass", (0.002, 0.006, 0.008), 0.05, 0.055)
EMISSIVE_BLUE = mat("BB8 blue indicator", (0.015, 0.20, 0.60), 0.25, 0.10)
EMISSIVE_RED = mat("BB8 red indicator", (0.62, 0.012, 0.008), 0.20, 0.12)
EMISSIVE_YELLOW = mat("BB8 yellow indicator", (0.85, 0.42, 0.015), 0.20, 0.12)


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def uv_sphere(name, radius, loc=(0, 0, 0), material=WHITE, segments=128, rings=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def cylinder(name, radius, depth, loc, material, rot=(0, 0, 0), vertices=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def cylinder_between(name, start, end, radius, material, vertices=32):
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = cylinder(name, radius, direction.length, (a + b) * 0.5, material, vertices=vertices)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    return obj


def cube(name, scale, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Rounded edges", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    return obj


def torus(name, major, minor, loc, rot, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=128,
                                    minor_segments=24, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def lathe(name, profile, material):
    verts, faces = [], []
    seg = 192
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for r, z in profile:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    n = len(profile)
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(n - 1):
            faces.append((i*n+k, j*n+k, j*n+k+1, i*n+k+1))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def orient_to_normal(obj, normal):
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(normal))


def tangent_bar(name, center, normal, radial, length, width, material):
    """Rounded rectangular applique aligned to a sphere tangent plane."""
    n = Vector(normal).normalized()
    x = Vector(radial).normalized()
    y = n.cross(x).normalized()
    obj = cube(name, (length / 2, width / 2, 0.0024), center, material, width / 2)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Matrix((x, y, n)).transposed().to_quaternion()
    return obj


def curve_tube(name, points, radius, material, cyclic=False, resolution=2):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def panel_basis(normal):
    n = Vector(normal).normalized()
    helper = Vector((0, 0, 1)) if abs(n.z) < .9 else Vector((0, 1, 0))
    u = n.cross(helper).normalized()
    v = n.cross(u).normalized()
    return n, u, v


def spherical_direction(normal, azimuth, polar):
    n, u, v = panel_basis(normal)
    tangent = u * math.cos(azimuth) + v * math.sin(azimuth)
    return (n * math.cos(polar) + tangent * math.sin(polar)).normalized()


def spherical_cap(name, normal, half_angle, radius, material, rings=12, segments=96):
    n, u, v = panel_basis(normal)
    verts = [tuple(n * radius)]
    for ring_index in range(1, rings + 1):
        polar = half_angle * ring_index / rings
        for i in range(segments):
            azimuth = 2 * math.pi * i / segments
            direction = n * math.cos(polar) + (u * math.cos(azimuth) + v * math.sin(azimuth)) * math.sin(polar)
            verts.append(tuple(direction * radius))
    faces = []
    for i in range(segments):
        faces.append((0, 1 + i, 1 + (i + 1) % segments))
    for ring_index in range(1, rings):
        start = 1 + (ring_index - 1) * segments
        next_start = start + segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((start + i, next_start + i, next_start + j, start + j))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def spherical_radial_rail(name, normal, azimuth, polar_start, polar_end, material):
    points = [
        spherical_direction(normal, azimuth, polar) * (BODY_R + 0.0045)
        for polar in (polar_start + (polar_end - polar_start) * i / 16 for i in range(17))
    ]
    return curve_tube(name, points, 0.0055, material)


def spherical_arc_rail(name, normal, polar, azimuth_start, azimuth_end, material, thickness=0.007):
    if azimuth_end < azimuth_start:
        azimuth_end += 2 * math.pi
    points = [
        spherical_direction(normal, azimuth_start + (azimuth_end - azimuth_start) * i / 32, polar)
        * (BODY_R + 0.0048)
        for i in range(33)
    ]
    return curve_tube(name, points, thickness, material)


def surface_panel(normal, name, panel_id, ring_type, layout):
    n = Vector(normal).normalized()
    loc = n * (BODY_R + 0.004)
    half_angle = math.radians(35.0)
    # Builders Club V3.1 defines six directional circular panels covering about
    # 70 degrees of the sphere.  Use a curved cap and curved ring/rails instead
    # of flat tangent discs; this keeps all three orthographic views consistent.
    # The screen prop's six large circular fields are predominantly white;
    # silver is reserved for smaller mechanical details, not the whole disc.
    inset = spherical_cap(name + " curved white field", n, half_angle, BODY_R + 0.0010, WHITE)
    ring_points = [
        spherical_direction(n, 2 * math.pi * i / 192, math.radians(31.8)) * (BODY_R + 0.0052)
        for i in range(192)
    ]
    ring = curve_tube(name + " orange spherical ring", ring_points, 0.0085, ORANGE, cyclic=True)
    hub = cylinder(name + " graphite centre hub", 0.025, 0.0060, loc, DARK, vertices=64)
    orient_to_normal(hub, n)
    for obj in (inset, ring, hub):
        obj["panel_id"] = panel_id
        obj["ring_type"] = ring_type
        obj["panel_half_angle_deg"] = 35.0
        obj["reference"] = "BB-8 Builders Club V3.1 Panel Orientation Guide Rev 1.06"
    for i, angle_deg in enumerate(layout["spokes"]):
        a = math.radians(angle_deg)
        rail = spherical_radial_rail(f"{name} radial rail {i+1}", n, a,
                                     math.radians(10.0), math.radians(27.0), ORANGE)
        rail["panel_id"] = panel_id
        rail["pattern_variant"] = panel_id
        direction = spherical_direction(n, a, math.radians(27.0))
        p = direction * (BODY_R + 0.0065)
        port = cylinder(f"{name} utility port {i+1}", 0.0065, 0.005, p, DARK, vertices=32)
        orient_to_normal(port, direction)
        port["panel_id"] = panel_id
    for idx, (start_deg, end_deg, polar_deg) in enumerate(layout.get("dark_arcs", ())):
        feature = spherical_arc_rail(
            f"{name} traced graphite arc {idx+1}", n, math.radians(polar_deg),
            math.radians(start_deg), math.radians(end_deg), DARK, 0.010
        )
        feature["panel_id"] = panel_id
        feature["accuracy"] = "visual trace from V3.1 guide; dimensions approximate"
    for idx, (angle_deg, start_deg, end_deg) in enumerate(layout.get("dark_ribs", ())):
        feature = spherical_radial_rail(
            f"{name} traced graphite rib {idx+1}", n, math.radians(angle_deg),
            math.radians(start_deg), math.radians(end_deg), DARK
        )
        feature["panel_id"] = panel_id
        feature["accuracy"] = "visual trace from V3.1 guide; dimensions approximate"
    light_materials = {"blue": EMISSIVE_BLUE, "red": EMISSIVE_RED, "yellow": EMISSIVE_YELLOW}
    lights = []
    for idx, (color, azimuth_deg, polar_deg) in enumerate(layout["lights"]):
        lights.append(color)
        direction = spherical_direction(n, math.radians(azimuth_deg), math.radians(polar_deg))
        lamp = cylinder(f"{name} {color} indicator {idx+1}", 0.0052, 0.006,
                        direction * (BODY_R + 0.0075), light_materials[color], vertices=32)
        orient_to_normal(lamp, direction)
        lamp["panel_id"] = panel_id
        lamp["indicator_color"] = color
    inset["light_layout"] = ",".join(lights)
    inset["pattern_variant"] = layout["variant"]
    inset["accuracy"] = "V3.1 topology and visual-trace pattern; no official millimetre CAD"


def triangular_corner_panel(signs, triangle_id):
    center = Vector(signs).normalized()
    # The eight octant gaps between the six circular panels are distinct
    # printable corner pieces in the V3.1 orientation guide. A rounded spherical
    # triangular outline preserves that topology without claiming unavailable
    # Lucasfilm surface CAD.
    axes = [Vector((signs[0], 0, 0)), Vector((0, signs[1], 0)), Vector((0, 0, signs[2]))]
    vertices = []
    for axis in axes:
        direction = (center * 0.57 + axis.normalized() * 0.43).normalized()
        vertices.append(direction * (BODY_R + 0.0042))
    points = []
    for edge in range(3):
        a, b = vertices[edge], vertices[(edge + 1) % 3]
        for i in range(18):
            direction = (a.normalized() * (17 - i) + b.normalized() * i).normalized()
            points.append(direction * (BODY_R + 0.0042))
    outline = curve_tube(f"Body triangle {triangle_id} spherical outline", points, 0.0038, WHITE, cyclic=True)
    outline["triangle_id"] = triangle_id
    outline["corner_signs"] = str(tuple(signs))
    outline["reference"] = "BB-8 Builders Club V3.1 Panel Orientation Guide Rev 1.06"
    marker = cylinder(f"Body triangle {triangle_id} graphite detail", 0.007, 0.004,
                      center * (BODY_R + 0.005), DARK, vertices=36)
    orient_to_normal(marker, center)
    marker["triangle_id"] = triangle_id
    return outline


# Reset scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

body = uv_sphere("BB-8 body shell - 508 mm", BODY_R)
body["diameter_mm"] = 508
equator_seam = torus("Body equator removable-shell seam", BODY_R + .0005, .0015,
                     (0,0,0), (0,0,0), DARK)
equator_seam["joint_type"] = "two-shell equator service joint; seam is visual until shell CAD is frozen"
panel_specs = (
    ("P1", "Front", (0,-1,0), "R3", {
        "variant": "partial centre annulus + left wedge + right blue light arc",
        "spokes": (45,135,225,315),
        "dark_arcs": ((210,315,21),(20,105,24)),
        "dark_ribs": (),
        "lights": (("blue",42,20),("blue",55,20),("blue",68,20),("blue",81,20)),
    }),
    ("P2", "Right", (1,0,0), "R2", {
        "variant": "large left polygon wedge + lower two-colour module + four vents",
        "spokes": (45,135,225,315),
        "dark_arcs": ((200,350,22),(75,130,18)),
        "dark_ribs": ((82,14,22),(96,14,22),(110,14,22),(124,14,22)),
        "lights": (("blue",180,17),("red",180,24)),
    }),
    ("P3", "Bottom", (0,0,-1), "R2", {
        "variant": "offset keyhole channel + left wedge + segmented right blade",
        "spokes": (0,90,180,270),
        "dark_arcs": ((190,300,22),(60,88,24),(92,120,24),(124,150,24)),
        "dark_ribs": ((105,10,24),),
        "lights": (("blue",245,20),),
    }),
    ("P4", "Top", (0,0,1), "R1", {
        "variant": "three central rails + upper arc + lower bent arm",
        "spokes": (0,90,180,270),
        "dark_arcs": ((205,300,20),(20,155,23)),
        "dark_ribs": ((80,8,24),(90,8,25),(100,8,23)),
        "lights": (("blue",345,15),("red",15,15)),
    }),
    ("P5", "Left", (-1,0,0), "R1", {
        "variant": "eccentric crescent + top/right/lower wedges",
        "spokes": (45,135,225,315),
        "dark_arcs": ((330,30,18),(15,130,24),(190,275,22)),
        "dark_ribs": ((250,13,20),(265,13,20)),
        "lights": (("blue",72,20),),
    }),
    ("P6", "Back", (0,1,0), "R1", {
        "variant": "three vertical ribs + asymmetric left/right lamp bays",
        "spokes": (45,135,225,315),
        "dark_arcs": ((205,285,22),(75,155,22)),
        "dark_ribs": ((350,8,25),(0,8,26),(10,8,25)),
        "lights": (("red",235,17),("red",250,20),("yellow",265,23),
                   ("red",125,17),("blue",110,20),("red",95,23)),
    }),
)
for panel_id, label, normal, ring_type, layout in panel_specs:
    surface_panel(normal, f"Body panel {panel_id} {label}", panel_id, ring_type, layout)

triangle_specs = (
    ((-1,-1, 1), "T1a"), ((1,-1, 1), "T1b"),
    ((-1, 1, 1), "T2"),  ((1, 1, 1), "T3"),
    ((-1,-1,-1), "T4"), ((1,-1,-1), "T5"),
    ((-1, 1,-1), "T6"), ((1, 1,-1), "T7"),
)
for signs, triangle_id in triangle_specs:
    triangular_corner_panel(signs, triangle_id)

# Additional orange/graphite utility ports populate otherwise empty shell zones.
for idx, normal in enumerate(((.70,-.70,.16),(-.70,-.70,.16),(.64,-.64,-.46),(-.64,-.64,-.46),
                              (.70,.70,.16),(-.70,.70,.16),(.64,.64,-.46),(-.64,.64,-.46))):
    n = Vector(normal).normalized()
    plate = cylinder(f"Body orange accent {idx+1}", 0.020, 0.004, n*(BODY_R+0.001), ORANGE, vertices=48)
    orient_to_normal(plate, n)
    inset = cylinder(f"Body accent inset {idx+1}", 0.010, 0.005, n*(BODY_R+0.003), DARK, vertices=40)
    orient_to_normal(inset, n)

# Head: 20 mm lower cone, 31 mm full-diameter base band and a 146 mm
# elliptical half-dome. The proportions follow community photographic
# measurement; only the overall 0.67 m height is an official published value.
skirt = lathe("Head lower cone - 223 to 295 mm", [
    (0.1115, HEAD_Z0),
    (0.1240, HEAD_Z0+0.008),
    (0.1400, HEAD_Z0+0.016),
    (HEAD_R, HEAD_Z0+0.020),
    (HEAD_R, HEAD_Z0+0.051),
], WHITE)
profile = []
center_z = HEAD_Z0 + 0.051
for i in range(33):
    theta = (math.pi/2) * i / 32
    profile.append((HEAD_R*math.cos(theta), center_z + 0.146*math.sin(theta)))
dome = lathe("Head dome - 295 mm", profile, WHITE)
dome["max_diameter_mm"] = 295
dome["photographic_outline_height_mm"] = 197

def head_dome_patch(name, azimuth_deg, z_rel, length, width, material, offset=0.0018):
    """Shallow rectangular patch tangent to the elliptical head dome."""
    dz = z_rel - 0.051
    horizontal = HEAD_R * math.sqrt(max(0.0, 1.0 - (dz / 0.146) ** 2))
    angle = math.radians(azimuth_deg)
    x, y = horizontal * math.cos(angle), horizontal * math.sin(angle)
    normal = Vector((x / HEAD_R**2, y / HEAD_R**2, dz / 0.146**2)).normalized()
    tangent = Vector((-math.sin(angle), math.cos(angle), 0))
    patch = tangent_bar(name, Vector((x,y,HEAD_Z0+z_rel)) + normal*offset,
                        normal, tangent, length, width, material)
    patch["head_panel_basis"] = "screen-traced shallow dome plate; non-official"
    return patch

# Film-visible lower double graphite stripes and segmented orange belt. The
# plates are intentionally asymmetric and shallow, replacing the incorrect
# four circular orange buttons used in the earlier visual draft.
torus("Head lower graphite stripe 1", 0.1435, 0.0017, (0,0,HEAD_Z0+0.021), (0,0,0), DARK)
torus("Head lower graphite stripe 2", 0.1460, 0.0016, (0,0,HEAD_Z0+0.029), (0,0,0), DARK)
for idx, angle_deg in enumerate((-165,-132,-101,-70,-38,-7,25,58,91,124,157), 1):
    angle = math.radians(angle_deg)
    n = Vector((math.cos(angle), math.sin(angle), 0))
    tangent = Vector((-math.sin(angle), math.cos(angle), 0))
    length = 0.028 if idx in (2, 5, 8, 11) else 0.038
    panel = tangent_bar(
        f"Head lower orange belt panel {idx}",
        n*0.1482 + Vector((0,0,HEAD_Z0+0.044)),
        n, tangent, length, 0.013, ORANGE,
    )
    panel["head_panel_basis"] = "screen-traced shallow belt plate; non-official"

# Upper orange trace and segmented graphite crown plates.
torus("Head upper orange trace", 0.101, 0.0028, (0,0,HEAD_Z0+0.158), (0,0,0), ORANGE)
for idx, angle_deg in enumerate((-146,-118,-90,-62,-34), 1):
    angle = math.radians(angle_deg)
    r = 0.086
    x, y = r*math.cos(angle), r*math.sin(angle)
    n = Vector((x / HEAD_R**2, y / HEAD_R**2, 0.120 / 0.146**2)).normalized()
    tangent = Vector((-math.sin(angle), math.cos(angle), 0))
    plate = tangent_bar(
        f"Head graphite crown panel {idx}",
        Vector((x,y,HEAD_Z0+0.171)) + n*0.0018, n, tangent, 0.032, 0.024, DARK,
    )
    plate["head_panel_basis"] = "screen-traced crown segmentation; non-official"
cylinder("Head crown service cap", 0.024, 0.0025, (0,0,HEAD_Z0+0.1958), DARK, vertices=72)

# Minimum side/rear visual density for orthographic matching. These are
# parameterised trace patches, not a claim of official panel count or CAD.
rear_patch_specs = (
    ("Head rear orange maintenance plate A", 65, 0.103, 0.040, 0.018, ORANGE),
    ("Head rear graphite service plate", 90, 0.128, 0.036, 0.020, DARK),
    ("Head rear orange maintenance plate B", 118, 0.088, 0.046, 0.017, ORANGE),
    ("Head right silver dome plate", 5, 0.105, 0.037, 0.019, SILVER),
    ("Head left orange dome plate", 176, 0.112, 0.035, 0.018, ORANGE),
)
for patch_spec in rear_patch_specs:
    head_dome_patch(*patch_spec)
for idx, (angle_deg, z_rel) in enumerate(((52,0.076),(82,0.083),(112,0.075),(142,0.092)), 1):
    head_dome_patch(f"Head rear graphite seam {idx}", angle_deg, z_rel,
                    0.030, 0.0025, DARK, 0.0020)

# Main photoreceptor and smaller holographic projector face toward -Y (front camera view).
eye_z = HEAD_Z0 + 0.121
eye_x = -0.040
eye = cylinder("Main photoreceptor", 0.035, 0.011, (eye_x,-0.125,eye_z), DARK,
               rot=(math.pi/2,0,0), vertices=96)
lens = uv_sphere("Main photoreceptor lens", 0.028, (eye_x,-0.133,eye_z), LENS_BLACK, 96, 48)
lens.scale = (1.0, 0.34, 1.0)
bpy.context.view_layer.objects.active = lens
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
eye_ring = torus("Photoreceptor silver bezel", 0.033, 0.0028, (eye_x,-0.135,eye_z),
                 (math.pi/2,0,0), SILVER)
glint = uv_sphere("Main photoreceptor blue glint", 0.0035, (eye_x-0.008,-0.144,eye_z+0.008), BLUE, 32, 16)
small_x, small_z = 0.056, HEAD_Z0+0.086
small_eye = cylinder("Holographic projector", 0.022, 0.011, (small_x,-0.136,small_z), SILVER,
                     rot=(math.pi/2,0,0), vertices=64)
torus("Holographic projector bezel", 0.019, 0.0025, (small_x,-0.143,small_z),
      (math.pi/2,0,0), DARK)
small_lens = uv_sphere("Holographic lens", 0.014, (small_x,-0.144,small_z), LENS_BLACK, 64, 32)
small_lens.scale = (1.0, 0.36, 1.0)
bpy.context.view_layer.objects.active = small_lens
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
psi_frame = cube("Head PSI silver frame", (0.013,0.0025,0.007),
                 (-0.098,-0.146,HEAD_Z0+0.052), SILVER, 0.002)
psi = cube("Head PSI status light", (0.008,0.0028,0.0035),
           (-0.098,-0.149,HEAD_Z0+0.052), EMISSIVE_BLUE, 0.001)
psi["screen_reference"] = "lower belt rectangular status aperture"

# Parameterised antennae; lengths remain editable pending authoritative blueprint data.
long_length = 0.112
short_length = 0.066
cylinder("Long antenna stepped base", 0.0055, 0.014, (-0.026,0.008,HEAD_Z0+0.204), SILVER, vertices=32)
cylinder("Short antenna stepped base", 0.0070, 0.012, (0.034,0.030,HEAD_Z0+0.203), SILVER, vertices=32)
ant1 = cylinder("Long antenna - provisional", 0.0019, long_length,
                (-0.026,0.008,HEAD_Z0+0.211+long_length/2), SILVER, vertices=32)
ant2 = cylinder("Short antenna - provisional", 0.0035, short_length,
                (0.034,0.030,HEAD_Z0+0.209+short_length/2), DARK, vertices=32)
ant1["provisional_length_mm"] = 112
ant2["provisional_length_mm"] = 66
ant1["antenna_type"] = "tall thin whip with tapered base; estimated from screen reference"
ant2["antenna_type"] = "short thick rubber-duck; estimated from screen reference"

# Schematic, buildable internal drive system in a separate collection.
internal = bpy.data.collections.new("Internal replica mechanism - schematic")
bpy.context.scene.collection.children.link(internal)

def move_internal(obj):
    # Keep a root-scene link as well as the organisational collection. Blender
    # 5.1 can otherwise drop objects that are parented outside a hidden-only
    # collection when the background file is saved/reopened for export.
    if obj.name not in internal.objects:
        internal.objects.link(obj)
    obj["bb8_internal"] = True
    obj.hide_render = True
    return obj

frame = move_internal(cube("Internal aluminium chassis", (.190,.009,.006), (0,-.048,-.120), SILVER, .003))
frame["rail_size_mm"] = "380 x 18 x 12"
frame["stage"] = 5
frame_right = move_internal(cube("Internal aluminium chassis rail R", (.190,.009,.006),
                                 (0,.048,-.120), SILVER, .003))
frame_right["rail_size_mm"] = "380 x 18 x 12"
crossmember = move_internal(cube("Internal chassis centre crossmember", (.004,.060,.006),
                                 (0,0,-.120), SILVER, .002))
crossmember["bar_size_mm"] = "8 x 120 x 12"
battery = move_internal(cube("Internal 4S battery ballast", (.060,.037,.028), (0,.005,-.078), DARK, .005))
battery["recommended_mass_kg"] = 1.2
for y in (-.022, .032):
    strap = move_internal(cube(f"Internal battery strap {'front' if y < 0 else 'rear'}",
                               (.066,.004,.032), (0,y,-.077), ORANGE, .002))
# Wheel centres are placed on R_body - R_wheel, so the 96 mm crowned tread
# actually intersects the inner 508 mm shell instead of floating in free space.
wheel_center_x = .155
wheel_center_y = 0.0
wheel_center_z = -math.sqrt((BODY_R - .048) ** 2 - wheel_center_x ** 2 - wheel_center_y ** 2)
motor_total_length = .1252
motor_front_x = wheel_center_x - .020
motor_center_x = motor_front_x - motor_total_length / 2
for side in (-1,1):
    motor_y = wheel_center_y
    label = 'L' if side < 0 else 'R'
    wheel = cylinder(f"Internal drive wheel {'L' if side<0 else 'R'}", .048, .026,
                     (side*wheel_center_x,motor_y,wheel_center_z), DARK, rot=(0,math.pi/2,0), vertices=64)
    move_internal(wheel)
    wheel["inner_shell_contact_radius_mm"] = round((BODY_R - .048) * 1000, 3)
    motor = cylinder(f"Internal geared motor {label}", .0225, motor_total_length,
                     (side*motor_center_x,motor_y,wheel_center_z), SILVER,
                     rot=(0,math.pi/2,0), vertices=64)
    move_internal(motor)
    motor["candidate"] = "Sha Yang Ye / Cytron IG42E-24K"
    motor["rated_voltage_v"] = 12.0
    motor["rated_speed_rpm"] = 248
    motor["rated_torque_nm"] = 0.98
    motor["verified_envelope_mm"] = "45 x 45 x 125.2"
    motor["mount_pattern"] = "4 x M4 x 6 deep on PCD 35 mm"
    shaft = cylinder(f"Internal motor shaft {label}", .004, .020,
                     (side*(wheel_center_x-.010),motor_y,wheel_center_z), SILVER,
                     rot=(0,math.pi/2,0), vertices=32)
    move_internal(shaft)
    mount = move_internal(cube(f"Internal motor face mount {label}", (.002,.026,.026),
                               (side*(motor_front_x-.002),motor_y,wheel_center_z), SILVER, .003))
    mount["material"] = "4 mm 6061-T6 aluminium; printed prototype is fit-check only"
    mount["verified_mount_pattern"] = "4 x M4 clearance on PCD 35 mm"
    mount["tool_clearance_mm"] = 55.0
    for bolt_index, angle_deg in enumerate((45,135,225,315), 1):
        angle = math.radians(angle_deg)
        y = motor_y + .0175 * math.cos(angle)
        z = wheel_center_z + .0175 * math.sin(angle)
        bolt = cylinder(f"Internal motor M4 bolt {label}{bolt_index}", .002, .010,
                        (side*(motor_front_x-.001),y,z), DARK,
                        rot=(0,math.pi/2,0), vertices=24)
        move_internal(bolt)
        bolt["fastener"] = "M4 socket-head; thread engagement 6 mm maximum"
        bolt["pcd_mm"] = 35.0
    hub = cylinder(f"Internal 8 mm key hub {label}", .013, .040,
                   (side*(wheel_center_x-.007),motor_y,wheel_center_z), ORANGE,
                   rot=(0,math.pi/2,0), vertices=48)
    move_internal(hub)
    hub["vendor_envelope_mm"] = "26 diameter x 40"
    hub["shaft_bore_mm"] = 8.0
    hub["wheel_threads"] = "3 x M5; PCD provisional pending hub drawing/sample"
    hub["anti_loosen"] = "medium-strength removable threadlocker after bench fit"
    for bolt_index, angle_deg in enumerate((90,210,330), 1):
        angle = math.radians(angle_deg)
        y = motor_y + .009 * math.cos(angle)
        z = wheel_center_z + .009 * math.sin(angle)
        bolt = cylinder(f"Internal wheel M5 bolt {label}{bolt_index}", .0025, .032,
                        (side*wheel_center_x,y,z), DARK,
                        rot=(0,math.pi/2,0), vertices=24)
        move_internal(bolt)
        bolt["fastener"] = "M5 wheel-to-hub; radial position provisional"
mast = move_internal(cylinder("Internal magnetic mast", .012, .340, (0,0,.050), SILVER, vertices=48))
magnet = move_internal(cylinder("Internal top magnet carrier", .056, .018, (0,0,.225), DARK, vertices=64))
magnet["carrier_role"] = "chassis-side magnetic follower support"
magnet_riser = move_internal(cylinder("Internal magnet array riser", .045, .010,
                                      (0,0,.239), SILVER, vertices=64))
for index in range(6):
    angle = 2 * math.pi * index / 6
    x, y = .035 * math.cos(angle), .035 * math.sin(angle)
    lower = move_internal(cylinder(f"Internal chassis magnet {index+1}", .010, .006,
                                   (x,y,.247), DARK, vertices=48))
    lower["magnet_envelope_mm"] = "20 diameter x 6; grade and coating not frozen"
    lower["polarity_contract"] = "alternating array; verify attraction before bonding"

head_carrier = move_internal(cylinder("Head internal magnetic carrier", .055, .006,
                                      (0,0,.267), SILVER, vertices=64))
head_carrier["removal_tool"] = "non-magnetic two-hand carrier tool required"
for index in range(6):
    angle = 2 * math.pi * index / 6
    x, y = .035 * math.cos(angle), .035 * math.sin(angle)
    upper = move_internal(cylinder(f"Head internal follower magnet {index+1}", .010, .006,
                                   (x,y,.261), DARK, vertices=48))
    upper["magnet_envelope_mm"] = "20 diameter x 6; grade and coating not frozen"
    upper["design_air_gap_mm"] = 8.0
    upper["measured_pull_force_required_n"] = 40.0

head_roller_ring = move_internal(torus("Head underside roller carrier ring", .094, .004,
                                      (0,0,.268), (0,0,0), SILVER))
head_roller_ring["carrier_role"] = "three-point follower support"
contact_xy = .090
contact_z = math.sqrt(BODY_R ** 2 - contact_xy ** 2)
roller_center_scale = (BODY_R + .012) / BODY_R
for index, angle_deg in enumerate((90,210,330), 1):
    angle = math.radians(angle_deg)
    x = contact_xy * math.cos(angle) * roller_center_scale
    y = contact_xy * math.sin(angle) * roller_center_scale
    z = contact_z * roller_center_scale
    roller = move_internal(uv_sphere(f"Head underside roller {index}", .012,
                                    (x,y,z), DARK, segments=48, rings=24))
    roller["outer_shell_contact_radius_mm"] = 266.0
    roller["roller_diameter_mm"] = 24.0
    roller["replaceable_non_marking_tread"] = True
imu = move_internal(cube("Internal IMU controller", (.028,.020,.006), (0,-.045,-.100), BLUE, .002))

# Triangulated mast braces transfer head shock into the chassis instead of the
# mast root alone. Four small rollers constrain chassis yaw/pitch without being
# counted as powered wheels.
for side in (-1, 1):
    brace = cylinder_between(f"Internal mast brace {'L' if side<0 else 'R'}",
                             (side*.165,0,-.108), (0,0,.145), .006, SILVER, 32)
    move_internal(brace)
for x in (-.090, .090):
    for y in (-.075, .075):
        roller_z = math.sqrt((BODY_R - .018) ** 2 - x ** 2 - y ** 2)
        roller = uv_sphere(f"Internal stabiliser roller {'L' if x<0 else 'R'} {'F' if y<0 else 'B'}",
                           .018, (x,y,roller_z), DARK, segments=48, rings=24)
        move_internal(roller)
        roller["inner_shell_contact_radius_mm"] = round((BODY_R - .018) * 1000, 3)
        arm = cylinder_between(f"Internal roller arm {x:+.3f} {y:+.3f}",
                               (x*1.25,y*.70,-.108), (x,y,roller_z), .0045, SILVER, 28)
        move_internal(arm)

electronics = move_internal(cube("Internal electronics tray", (.052,.040,.006), (0,.010,-.098), BLUE, .003))
electronics["envelope_mm"] = "104 x 80 x 12"
fuse = move_internal(cube("Internal fuse and contactor", (.022,.014,.012), (0.105,.020,-.095), ORANGE, .003))

# Stage 13: physical installation envelopes for the dual INA226 current chain,
# 2 mOhm four-wire shunts and MCU-independent ALERT-to-driver-EN gate.
add_power_safety_hardware(internal, move_internal)
stage14_created, stage14_mass_input, stage14_mass_results = add_stage14_mass_geometry(move_internal)
write_mass_input(os.path.join(ROOT, "engineering", "mass_properties_input.json"), stage14_mass_input)
stage15_created = add_stage15_drive_power_hardware(move_internal)

# Stage 6 serviceability: a removable equator joint and explicit harness routes.
# The gasket/latches are clearance envelopes, not supplier-specific final parts.
gasket = torus("Internal equator gasket envelope", .247, .0025, (0,0,0), (0,0,0), DARK)
move_internal(gasket)
gasket["gasket_section_mm"] = "5 mm circular envelope; final profile depends on shell laminate"
gasket["joint_diameter_mm"] = 494.0
for index in range(8):
    angle = 2 * math.pi * index / 8
    loc = (.238 * math.cos(angle), .238 * math.sin(angle), 0)
    latch = cube(f"Internal equator latch envelope {index+1}", (.008,.004,.006), loc, ORANGE, .001)
    latch.rotation_euler.z = angle
    move_internal(latch)
    latch["service_joint"] = "tool-releasable captive latch; supplier not frozen"
    latch["target_clamp_force_n"] = 80.0

for side in (-1, 1):
    label = 'L' if side < 0 else 'R'
    routes = {
        "power": [
            (side*.010, side*.018, wheel_center_z),
            (side*.028, side*.030, -.112),
            (side*.070, side*.030, -.100),
            (side*.042, .016, -.094),
        ],
        "encoder": [
            (side*.010, side*.010, wheel_center_z + .010),
            (side*.025, side*.040, -.105),
            (side*.060, side*.040, -.090),
            (side*.032, .004, -.086),
        ],
    }
    for harness_type, points in routes.items():
        radius = .0025 if harness_type == "power" else .0016
        material = ORANGE if harness_type == "power" else BLUE
        for segment_index, (start, end) in enumerate(zip(points, points[1:]), 1):
            cable = cylinder_between(
                f"Internal {harness_type} harness {label}{segment_index}",
                start, end, radius, material, 20)
            move_internal(cable)
            cable["harness_type"] = harness_type
            cable["minimum_bend_radius_mm"] = 30.0 if harness_type == "power" else 20.0
            cable["abrasion_sleeve"] = "required at chassis and shell-adjacent edges"
        connector = move_internal(cube(
            f"Internal {harness_type} connector {label}",
            (.008,.005,.004), points[-1], material, .001))
        connector["connector_contract"] = (
            "Molex 3.96 mm 2-pin power" if harness_type == "power"
            else "JST-PH 2.0 mm 4-pin encoder")
        connector["disconnect_before_service"] = True
internal.hide_render = False

# Kinematic hierarchy. The ball rolls, while gravity keeps the chassis and head
# approximately world-upright. This is a deliberately inspectable animation rig,
# not a claim about the undisclosed movie prop mechanism.
def empty(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = .08
    return obj

def parent_keep_world(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world

travel_rig = empty("RIG 00 - World travel")
body_rig = empty("RIG 10 - Rolling ball")
chassis_rig = empty("RIG 20 - Gravity stabilised chassis")
head_rig = empty("RIG 30 - Magnetically coupled head")
body_rig.parent = travel_rig
chassis_rig.parent = travel_rig
head_rig.parent = travel_rig

body_names = [o for o in bpy.context.scene.objects
              if o.name.startswith("BB-8 body") or o.name.startswith("Body panel") or o.name.startswith("Body orange") or o.name.startswith("Body accent")]
for obj in body_names:
    parent_keep_world(obj, body_rig)
for obj in list(internal.objects):
    parent_keep_world(obj, chassis_rig)
head_prefixes = ("Head ", "Main photoreceptor", "Photoreceptor", "Holographic", "Long antenna", "Short antenna")
for obj in bpy.context.scene.objects:
    if obj.name.startswith(head_prefixes):
        parent_keep_world(obj, head_rig)

# One exact body circumference over 120 frames.
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 30
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
travel_distance = 2 * math.pi * BODY_R
travel_rig.location = (0, 0, 0)
travel_rig.keyframe_insert(data_path="location", frame=1)
travel_rig.location = (0, travel_distance, 0)
travel_rig.keyframe_insert(data_path="location", frame=120)
body_rig.rotation_euler = (0, 0, 0)
body_rig.keyframe_insert(data_path="rotation_euler", frame=1)
body_rig.rotation_euler.x = 2 * math.pi
body_rig.keyframe_insert(data_path="rotation_euler", frame=120)

# Internal wheel rotation derived from surface velocity ratio. A small chassis
# pitch response visualises acceleration/deceleration without rotating with shell.
wheel_r = .048
wheel_turns = travel_distance / (2 * math.pi * wheel_r)
for obj in internal.objects:
    if obj.name.startswith("Internal drive wheel"):
        obj.rotation_mode = 'XYZ'
        obj.keyframe_insert(data_path="rotation_euler", frame=1)
        obj.rotation_euler.rotate_axis('Z', -2 * math.pi * wheel_turns)
        obj.keyframe_insert(data_path="rotation_euler", frame=120)
chassis_rig.rotation_euler.x = math.radians(-4)
chassis_rig.keyframe_insert(data_path="rotation_euler", frame=1)
chassis_rig.rotation_euler.x = 0
chassis_rig.keyframe_insert(data_path="rotation_euler", frame=20)
chassis_rig.keyframe_insert(data_path="rotation_euler", frame=100)
chassis_rig.rotation_euler.x = math.radians(4)
chassis_rig.keyframe_insert(data_path="rotation_euler", frame=120)

travel_rig["distance_per_cycle_mm"] = round(travel_distance * 1000, 3)
body_rig["roll_angle_per_cycle_deg"] = 360.0
chassis_rig["drive_wheel_diameter_mm"] = 96.0
chassis_rig["drive_wheel_turns_per_cycle"] = wheel_turns
head_rig["stabilisation"] = "world-upright magnetic follower; schematic control target"
scene["kinematic_relation"] = "s = R_body * theta_body; wheel turns = s / (2*pi*R_wheel)"

scene.frame_set(1)

# Ground plane.
bpy.ops.mesh.primitive_plane_add(size=3, location=(0,0,-BODY_R))
ground = bpy.context.object
ground.name = "Ground"
ground.data.materials.append(mat("Ground matte", (0.028,0.032,0.035), 0, .55))

# Text metadata stored with the scene.
scene["replica_basis"] = "Screen-referenced fan replica; not official Lucasfilm CAD"
scene["body_diameter_mm"] = 508
scene["head_diameter_mm"] = 295
scene["untopped_height_mm"] = 670
scene["head_outline_height_mm"] = 197
scene["head_overlap_into_ball_silhouette_mm"] = 35
scene["engineering_stage"] = 15
scene["exterior_topology_stage"] = "V3.1-oriented six curved P-panels and eight T-panels"
scene["body_panel_half_angle_deg"] = 35.0
scene["body_ring_distribution"] = "R1 x3, R2 x2, R3 x1"
scene["drive_track_mm"] = 310
scene["motor_mount_source"] = "Sha Yang Ye IG-42C: 4 x M4 x 6 deep, PCD 35 mm"
scene["motor_envelope_source"] = "Cytron IG42E-24K: 45 x 45 x 125.2 mm"
scene["service_joint"] = "494 mm equator gasket envelope with 8 captive-latch envelopes"
scene["magnetic_follower"] = "6+6 magnet envelopes, 8 mm face gap, 3-point 24 mm head rollers"
scene["power_safety_hardware"] = "dual INA226 + dual 2 mOhm Kelvin shunts + ALERT wire-OR to independent driver EN gate"
scene["power_safety_physical_test_status"] = "NOT_RUN"
scene["power_safety_model_object_count"] = 22
scene["mass_model_object_count"] = len(stage14_created)
scene["drive_power_hardware"] = "dual generic driver envelopes + fuse + NO contactor + dual-channel NC E-stop + tether jack"
scene["drive_power_model_object_count"] = len(stage15_created)
scene["drive_power_candidate_status"] = "NOT_FROZEN"
scene["drive_power_physical_test_status"] = "NOT_RUN"
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.color = (0.012, 0.016, 0.022)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -0.35

# Lighting.
bpy.ops.object.light_add(type='AREA', location=(1.5,-1.7,2.1))
bpy.context.object.data.energy = 1100; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=1.3
bpy.ops.object.light_add(type='AREA', location=(-1.4,-0.2,1.1))
bpy.context.object.data.energy = 700; bpy.context.object.data.size=1.0
bpy.ops.object.light_add(type='AREA', location=(0,1.3,1.7))
bpy.context.object.data.energy = 900; bpy.context.object.data.size=0.8

def render_view(name, camera_loc, target=(0,0,0.16), ortho_scale=0.92):
    bpy.ops.object.camera_add(location=camera_loc)
    cam = bpy.context.object
    cam.name = name + " orthographic camera"
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho_scale
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return cam

render_view("front", (0,-3,0.18))
render_view("side", (3,0,0.18))
render_view("back", (0,3,0.18))

# Render a separate transparent-shell mechanism reference.
internal_names = {o.name for o in internal.objects}
external_objects = [o for o in scene.objects if o.name not in internal_names and o.type not in {'CAMERA','LIGHT'}]
for o in external_objects:
    o.hide_render = True
for o in internal.objects:
    o.hide_render = False
scene.render.filepath = os.path.join(OUT, "mechanism.png")
scene.render.resolution_x = 1100
scene.render.resolution_y = 900
render_view("mechanism", (1.4,-2.2,.55), target=(0,0,-.02), ortho_scale=.62)
scene.render.resolution_x = 900
scene.render.resolution_y = 900
render_view("internal_front", (0,-2.2,.10), target=(0,0,.02), ortho_scale=.62)
render_view("internal_side", (2.2,0,.10), target=(0,0,.02), ortho_scale=.62)
render_view("internal_top", (0,0,2.2), target=(0,0,.02), ortho_scale=.62)
for o in external_objects:
    o.hide_render = False
for o in internal.objects:
    o.hide_render = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1100

# Rolling-cycle preview. Camera follows translational travel while shell rotation,
# wheel rotation and chassis/head stabilisation remain visible in the scene data.
scene.frame_set(1)
bpy.ops.object.camera_add(location=(0,-2.4,.18))
anim_cam = bpy.context.object
anim_cam.name = "Kinematic preview camera"
anim_cam.rotation_euler = (math.radians(90), 0, 0)
direction = Vector((0,0,.14)) - anim_cam.location
anim_cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
anim_cam.data.type = 'ORTHO'
anim_cam.data.ortho_scale = .92
parent_keep_world(anim_cam, travel_rig)
scene.camera = anim_cam
scene.render.resolution_x = 640
scene.render.resolution_y = 760
scene.render.image_settings.file_format = 'PNG'
anim_frames = os.path.join(OUT, "kinematic_frames")
os.makedirs(anim_frames, exist_ok=True)
scene.render.filepath = os.path.join(anim_frames, "roll_")
scene.frame_step = 2
if os.environ.get("BB8_SKIP_ANIMATION") != "1":
    bpy.ops.render.render(animation=True)
scene.frame_step = 1
scene.frame_set(1)

blend_path = os.path.join(OUT, "BB8_1to1_screen_referenced.blend")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("BB8_OUTPUT", blend_path)
