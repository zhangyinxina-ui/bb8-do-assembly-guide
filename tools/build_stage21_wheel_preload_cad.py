#!/usr/bin/env python3
"""Dependency-light Stage-21 CAD fallback: exact DXF profiles and reference STL/PNG."""

from __future__ import annotations

import math
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "stage21_wheel_preload_adjuster" / "outputs"

PLATE_L = 132.0
PLATE_W = 64.0
PLATE_T = 6.0
WHEEL_X = 110.0
MOTOR_X = 30.0
WHEEL_R = 48.0
WHEEL_HALF_WIDTH = 13.0
CROWN_DROP = 0.75
TRAVEL = 3.0
MOVING_Z = 19.0
FIXED_Z = 26.0
PULLEY_R = 20.0
PULLEY_Z = 38.5
SHELL_R = 254.0
NX = 155.0 / 206.0
NZ = -math.sqrt(1.0 - NX * NX)


class Mesh:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []

    def add(self, other: "Mesh") -> None:
        offset = len(self.vertices)
        self.vertices.extend(other.vertices)
        self.faces.extend(tuple(index + offset for index in face) for face in other.faces)

    def transformed(self, matrix, translation=(0.0, 0.0, 0.0)) -> "Mesh":
        result = Mesh()
        for vertex in self.vertices:
            result.vertices.append(tuple(
                sum(matrix[row][col] * vertex[col] for col in range(3)) + translation[row]
                for row in range(3)
            ))
        result.faces = list(self.faces)
        return result


def box(size, center=(0.0, 0.0, 0.0)) -> Mesh:
    sx, sy, sz = (value / 2.0 for value in size)
    cx, cy, cz = center
    mesh = Mesh()
    mesh.vertices = [
        (cx + x * sx, cy + y * sy, cz + z * sz)
        for x, y, z in [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
        ]
    ]
    mesh.faces = [
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    ]
    return mesh


def cylinder(radius: float, length: float, center=(0.0, 0.0, 0.0), segments=64) -> Mesh:
    cx, cy, cz = center
    mesh = Mesh()
    for z in (-length / 2.0, length / 2.0):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            mesh.vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), cz + z))
    bottom_center = len(mesh.vertices)
    mesh.vertices.append((cx, cy, cz - length / 2.0))
    top_center = len(mesh.vertices)
    mesh.vertices.append((cx, cy, cz + length / 2.0))
    for index in range(segments):
        next_index = (index + 1) % segments
        mesh.faces.extend([
            (index, next_index, segments + next_index),
            (index, segments + next_index, segments + index),
            (bottom_center, next_index, index),
            (top_center, segments + index, segments + next_index),
        ])
    return mesh


def crowned_wheel(center=(0.0, 0.0, 0.0), rings=24, segments=96) -> Mesh:
    cx, cy, cz = center
    mesh = Mesh()
    for ring in range(rings + 1):
        s = -WHEEL_HALF_WIDTH + 2.0 * WHEEL_HALF_WIDTH * ring / rings
        radius = WHEEL_R - CROWN_DROP * (s / WHEEL_HALF_WIDTH) ** 2
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            mesh.vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), cz + s))
    for ring in range(rings):
        start = ring * segments
        next_start = (ring + 1) * segments
        for index in range(segments):
            next_index = (index + 1) % segments
            mesh.faces.extend([
                (start + index, start + next_index, next_start + next_index),
                (start + index, next_start + next_index, next_start + index),
            ])
    bottom = len(mesh.vertices)
    top = bottom + 1
    mesh.vertices.extend([(cx, cy, cz - WHEEL_HALF_WIDTH), (cx, cy, cz + WHEEL_HALF_WIDTH)])
    for index in range(segments):
        next_index = (index + 1) % segments
        mesh.faces.append((bottom, next_index, index))
        top_ring = rings * segments
        mesh.faces.append((top, top_ring + index, top_ring + next_index))
    return mesh


def triangle_normal(a, b, c):
    ux, uy, uz = (b[i] - a[i] for i in range(3))
    vx, vy, vz = (c[i] - a[i] for i in range(3))
    nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0.0:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def write_ascii_stl(path: Path, mesh: Mesh, name: str) -> None:
    lines = [f"solid {name}"]
    for face in mesh.faces:
        vertices = [mesh.vertices[index] for index in face]
        normal = triangle_normal(*vertices)
        lines.append(f"  facet normal {normal[0]:.9g} {normal[1]:.9g} {normal[2]:.9g}")
        lines.append("    outer loop")
        for vertex in vertices:
            lines.append(f"      vertex {vertex[0]:.9g} {vertex[1]:.9g} {vertex[2]:.9g}")
        lines.extend(["    endloop", "  endfacet"])
    lines.append(f"endsolid {name}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def dxf_header() -> list[str]:
    return ["0", "SECTION", "2", "HEADER", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]


def dxf_line(lines, x1, y1, x2, y2, layer="CUT"):
    lines.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])


def dxf_arc(lines, cx, cy, radius, start, end, layer="CUT"):
    lines.extend(["0", "ARC", "8", layer, "10", str(cx), "20", str(cy), "40", str(radius), "50", str(start), "51", str(end)])


def dxf_circle(lines, cx, cy, diameter, layer="CUT"):
    lines.extend(["0", "CIRCLE", "8", layer, "10", str(cx), "20", str(cy), "40", str(diameter / 2.0)])


def rounded_plate_outline(lines, length=PLATE_L, width=PLATE_W, radius=5.0):
    x0, x1 = 0.0, length
    y0, y1 = -width / 2.0, width / 2.0
    dxf_line(lines, x0 + radius, y0, x1 - radius, y0)
    dxf_arc(lines, x1 - radius, y0 + radius, radius, 270, 360)
    dxf_line(lines, x1, y0 + radius, x1, y1 - radius)
    dxf_arc(lines, x1 - radius, y1 - radius, radius, 0, 90)
    dxf_line(lines, x1 - radius, y1, x0 + radius, y1)
    dxf_arc(lines, x0 + radius, y1 - radius, radius, 90, 180)
    dxf_line(lines, x0, y1 - radius, x0, y0 + radius)
    dxf_arc(lines, x0 + radius, y0 + radius, radius, 180, 270)


def dxf_slot(lines, cx, cy, length=18.6, width=6.6):
    radius = width / 2.0
    half_straight = (length - width) / 2.0
    dxf_line(lines, cx - half_straight, cy + radius, cx + half_straight, cy + radius)
    dxf_arc(lines, cx + half_straight, cy, radius, 270, 90)
    dxf_line(lines, cx + half_straight, cy - radius, cx - half_straight, cy - radius)
    dxf_arc(lines, cx - half_straight, cy, radius, 90, 270)


def write_fixed_dxf(path: Path) -> None:
    lines = dxf_header()
    rounded_plate_outline(lines)
    for x in (48, 84):
        for y in (-23, 23):
            dxf_slot(lines, x + 3, y)
    for x in (10, 122):
        for y in (-24, 24):
            dxf_circle(lines, x, y, 6.6)
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_moving_dxf(path: Path) -> None:
    lines = dxf_header()
    rounded_plate_outline(lines)
    dxf_circle(lines, WHEEL_X, 0, 28.2)
    dxf_circle(lines, MOTOR_X, 0, 9.0)
    for angle in (45, 135, 225, 315):
        dxf_circle(lines, MOTOR_X + 17.5 * math.cos(math.radians(angle)), 17.5 * math.sin(math.radians(angle)), 4.5)
    for x in (48, 84):
        for y in (-23, 23):
            dxf_circle(lines, x, y, 6.6)
    for x in (12, 120):
        for y in (-24, 24):
            dxf_circle(lines, x, y, 5.2)
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def local_assembly() -> Mesh:
    mesh = Mesh()
    for z in (-FIXED_Z, FIXED_Z):
        mesh.add(box((PLATE_L, PLATE_W, PLATE_T), (PLATE_L / 2.0, 0, z)))
    for z in (-MOVING_Z, MOVING_Z):
        mesh.add(box((PLATE_L, PLATE_W, PLATE_T), (PLATE_L / 2.0, 0, z)))
    mesh.add(crowned_wheel((WHEEL_X, 0, 0)))
    mesh.add(cylinder(22.5, 125.2, (MOTOR_X, 0, 0)))
    mesh.add(cylinder(6.0, 58.0, (WHEEL_X, 0, 0)))
    mesh.add(cylinder(PULLEY_R, 15.0, (WHEEL_X, 0, PULLEY_Z)))
    mesh.add(cylinder(PULLEY_R, 15.0, (MOTOR_X, 0, PULLEY_Z)))
    mesh.add(box((80.0, 4.0, 15.0), ((MOTOR_X + WHEEL_X) / 2.0, PULLEY_R, PULLEY_Z)))
    mesh.add(box((80.0, 4.0, 15.0), ((MOTOR_X + WHEEL_X) / 2.0, -PULLEY_R, PULLEY_Z)))
    mesh.add(box((16.0, 24.0, 18.0), (-8.0, 0, 0)))
    screw = cylinder(3.0, 42.0).transformed(
        ((0, 0, 1), (0, 1, 0), (-1, 0, 0)), (-16.0, 0, 0)
    )
    mesh.add(screw)
    return mesh


def draw_preview(path: Path) -> None:
    fig = plt.figure(figsize=(16, 10), dpi=100)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.15, 0.85])
    ax_global = fig.add_subplot(grid[:, 0])
    ax_local = fig.add_subplot(grid[0, 1])
    ax_gate = fig.add_subplot(grid[1, 1])

    ax_global.add_patch(Circle((0, 0), SHELL_R, fill=False, linewidth=3, color="#171914"))
    for side in (-1, 1):
        n = (side * NX, NZ)
        a = (-NZ, side * NX)
        wheel_center = (206 * n[0], 206 * n[1])
        motor_center = (126 * n[0], 126 * n[1])
        ax_global.add_patch(Circle(wheel_center, WHEEL_R, color="#22241f", alpha=0.95))
        ax_global.add_patch(Circle(motor_center, 22.5, color="#9ca09a", alpha=0.95))
        ax_global.plot([wheel_center[0], motor_center[0]], [wheel_center[1], motor_center[1]], color="#ff4b13", linewidth=8, alpha=0.65)
        scale = 72
        ax_global.arrow(wheel_center[0] - a[0] * scale / 2, wheel_center[1] - a[1] * scale / 2,
                        a[0] * scale, a[1] * scale, width=1.8, head_width=8, color="#ff4b13")
    ax_global.set_title("GLOBAL X-Z PACKAGING\nTangent wheel axes + 80 mm parallel belt offset", loc="left", fontweight="bold")
    ax_global.text(0, 235, "254 mm inner shell", ha="center", fontsize=11)
    ax_global.text(0, -285, "Reference envelope only — current Blender master not modified", ha="center", color="#a52a14", fontsize=10)
    ax_global.set_aspect("equal")
    ax_global.set_xlim(-290, 290)
    ax_global.set_ylim(-305, 285)
    ax_global.axis("off")

    ax_local.add_patch(FancyBboxPatch((0, -PLATE_W/2), PLATE_L, PLATE_W, boxstyle="round,pad=0,rounding_size=5", facecolor="#ece8dc", edgecolor="#171914", linewidth=2))
    ax_local.add_patch(Circle((MOTOR_X, 0), PULLEY_R, color="#ff4b13"))
    ax_local.add_patch(Circle((WHEEL_X, 0), PULLEY_R, color="#ff4b13"))
    ax_local.plot([MOTOR_X, WHEEL_X], [PULLEY_R, PULLEY_R], color="#171914", linewidth=4)
    ax_local.plot([MOTOR_X, WHEEL_X], [-PULLEY_R, -PULLEY_R], color="#171914", linewidth=4)
    ax_local.add_patch(Circle((WHEEL_X, 0), 14.1, fill=False, color="#171914", linewidth=2))
    ax_local.add_patch(Circle((MOTOR_X, 0), 4.5, fill=False, color="#171914", linewidth=2))
    for x in (48, 84):
        for y in (-23, 23):
            ax_local.add_patch(Rectangle((x - 9.3, y - 3.3), 18.6, 6.6, facecolor="#ffffff", edgecolor="#171914"))
    ax_local.annotate("80 mm", xy=(MOTOR_X, 28), xytext=(WHEEL_X, 28), arrowprops=dict(arrowstyle="<->"), ha="center")
    ax_local.set_title("LOCAL CASSETTE / REFERENCE PLATE", loc="left", fontweight="bold")
    ax_local.text(2, -43, "24T / 24T · 5M-280-15 candidate · four 18.6 × 6.6 slots", fontsize=9)
    ax_local.set_aspect("equal")
    ax_local.set_xlim(-20, 145)
    ax_local.set_ylim(-52, 52)
    ax_local.axis("off")

    ax_gate.axis("off")
    ax_gate.set_title("CONTACT + PRELOAD GATES", loc="left", fontweight="bold")
    lines = [
        ("OLD CYLINDER GAP", "5.070 mm", "FAIL DETECTED"),
        ("AXIS TO TANGENT", "48.800°", "FAIL DETECTED"),
        ("CROWN DROP", "0.750 mm", "> 0.333 mm minimum"),
        ("SLIDE TRAVEL", "12.0 mm", "3 in / 9 out"),
        ("PRELOAD TARGET", "80 N each", "MEASURE — not turn-count"),
        ("CONTACT TRACK", "382.233 mm", "PHYSICAL YAW CALIBRATION HOLD"),
    ]
    for index, (label, value, note) in enumerate(lines):
        y = 0.88 - index * 0.145
        ax_gate.text(0.0, y, label, transform=ax_gate.transAxes, fontsize=9, family="monospace", color="#666")
        ax_gate.text(0.39, y, value, transform=ax_gate.transAxes, fontsize=14, fontweight="bold")
        ax_gate.text(0.68, y, note, transform=ax_gate.transAxes, fontsize=8.5, color="#a52a14")
    ax_gate.text(0.0, -0.02, "HOLD: tire · shell coupon · belt · bearings · shaft/hub · M6 preload · Blender clash · physical commissioning", transform=ax_gate.transAxes, fontsize=9, color="#ffffff", bbox=dict(facecolor="#171914", pad=8, edgecolor="none"))

    fig.patch.set_facecolor("#f1ede1")
    for axis in (ax_global, ax_local, ax_gate):
        axis.set_facecolor("#f1ede1")
    fig.suptitle("BB-8 STAGE 21 · TANGENT WHEEL PRELOAD CASSETTE", x=0.04, y=0.98, ha="left", fontsize=20, fontweight="bold")
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_fixed_dxf(OUT / "stage21_fixed_slider_plate.dxf")
    write_moving_dxf(OUT / "stage21_moving_side_plate.dxf")
    write_ascii_stl(OUT / "stage21_fixed_slider_plate_envelope.stl", box((PLATE_L, PLATE_W, PLATE_T), (PLATE_L / 2, 0, 0)), "stage21_fixed_slider_plate_envelope")
    write_ascii_stl(OUT / "stage21_moving_side_plate_envelope.stl", box((PLATE_L, PLATE_W, PLATE_T), (PLATE_L / 2, 0, 0)), "stage21_moving_side_plate_envelope")
    write_ascii_stl(OUT / "stage21_crowned_wheel_envelope.stl", crowned_wheel(), "stage21_crowned_wheel_envelope")
    write_ascii_stl(OUT / "stage21_wheel_preload_assembly_envelope.stl", local_assembly(), "stage21_wheel_preload_assembly_envelope")
    draw_preview(OUT / "stage21_wheel_preload_global_pair.png")
    classifications = {
        "stage21_fixed_slider_plate.dxf": "EXACT_2D_REFERENCE_PROFILE_HOLES_AND_SLOTS_INCLUDED",
        "stage21_moving_side_plate.dxf": "EXACT_2D_REFERENCE_PROFILE_HOLES_INCLUDED",
        "stage21_crowned_wheel_envelope.stl": "EXACT_STAGE21_PARAMETRIC_CROWN_ENVELOPE",
        "stage21_fixed_slider_plate_envelope.stl": "ENVELOPE_ONLY_USE_DXF_FOR_HOLES_AND_SLOTS",
        "stage21_moving_side_plate_envelope.stl": "ENVELOPE_ONLY_USE_DXF_FOR_HOLES",
        "stage21_wheel_preload_assembly_envelope.stl": "REFERENCE_ASSEMBLY_ENVELOPE_NOT_FABRICATION_GEOMETRY",
        "stage21_wheel_preload_global_pair.png": "ENGINEERING_REVIEW_IMAGE",
    }
    manifest = {
        "stage": 21,
        "generator": "tools/build_stage21_wheel_preload_cad.py",
        "mode": "DEPENDENCY_LIGHT_FALLBACK_OPENSCAD_UNAVAILABLE",
        "manufacturing_release": False,
        "release_boundary": "DXF and STL outputs are fit references. Plate STL files omit holes and slots by design; use the DXF for 2D profiles. No output is released for a running robot.",
        "outputs": [],
    }
    for name, classification in classifications.items():
        path = OUT / name
        manifest["outputs"].append({
            "path": f"hardware/stage21_wheel_preload_adjuster/outputs/{name}",
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "classification": classification,
        })
    (OUT / "stage21_cad_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"STAGE21_FALLBACK_CAD_OUTPUT {OUT}")
    print("DXF profiles preserve holes and slots; plate STL files are explicitly envelope-only.")


if __name__ == "__main__":
    main()
