#!/usr/bin/env python3
"""Build dependency-light Stage-22 reference DXF/STL/PNG outputs."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "engineering" / "stage22_drivetrain_interface_contract.json"
RESULTS = ROOT / "engineering" / "stage22_drivetrain_interface_results.json"
OUT = ROOT / "hardware" / "stage22_drivetrain_interface" / "outputs"

PLATE_L = 140.0
PLATE_W = 68.0
PLATE_T = 6.0
WHEEL_X = 110.0
MOTOR_X = 20.0
AXIS_SPACING = 90.0
WHEEL_R = 48.0
WHEEL_W = 26.0
SHAFT_D = 12.0
BEARING_OD = 28.0
BEARING_W = 8.0
BEARING_Z = (-19.0, 19.0)
PULLEY_R = 20.0
PULLEY_W = 15.0
PULLEY_Z = 33.5
SHELL_R = 254.0


class Mesh:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []

    def add(self, other: "Mesh") -> None:
        offset = len(self.vertices)
        self.vertices.extend(other.vertices)
        self.faces.extend(
            tuple(index + offset for index in face) for face in other.faces
        )


def box(size, center=(0.0, 0.0, 0.0)) -> Mesh:
    sx, sy, sz = (value / 2.0 for value in size)
    cx, cy, cz = center
    mesh = Mesh()
    mesh.vertices = [
        (cx + x * sx, cy + y * sy, cz + z * sz)
        for x, y, z in [
            (-1, -1, -1),
            (1, -1, -1),
            (1, 1, -1),
            (-1, 1, -1),
            (-1, -1, 1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, 1, 1),
        ]
    ]
    mesh.faces = [
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    ]
    return mesh


def cylinder(radius: float, length: float, center=(0.0, 0.0, 0.0), segments=64) -> Mesh:
    cx, cy, cz = center
    mesh = Mesh()
    for z in (-length / 2.0, length / 2.0):
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            mesh.vertices.append(
                (cx + radius * math.cos(angle), cy + radius * math.sin(angle), cz + z)
            )
    bottom_center = len(mesh.vertices)
    mesh.vertices.append((cx, cy, cz - length / 2.0))
    top_center = len(mesh.vertices)
    mesh.vertices.append((cx, cy, cz + length / 2.0))
    for index in range(segments):
        next_index = (index + 1) % segments
        mesh.faces.extend(
            [
                (index, next_index, segments + next_index),
                (index, segments + next_index, segments + index),
                (bottom_center, next_index, index),
                (top_center, segments + index, segments + next_index),
            ]
        )
    return mesh


def triangle_normal(a, b, c):
    ux, uy, uz = (b[i] - a[i] for i in range(3))
    vx, vy, vz = (c[i] - a[i] for i in range(3))
    nx, ny, nz = (
        uy * vz - uz * vy,
        uz * vx - ux * vz,
        ux * vy - uy * vx,
    )
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0.0:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def write_binary_stl(path: Path, mesh: Mesh, name: str) -> None:
    header = name.encode("ascii", "replace")[:80].ljust(80, b"\0")
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(mesh.faces)))
        for face in mesh.faces:
            vertices = [mesh.vertices[index] for index in face]
            normal = triangle_normal(*vertices)
            handle.write(struct.pack("<3f", *normal))
            for vertex in vertices:
                handle.write(struct.pack("<3f", *vertex))
            handle.write(struct.pack("<H", 0))


def dxf_header() -> list[str]:
    return [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
    ]


def dxf_line(lines, x1, y1, x2, y2, layer="CUT"):
    lines.extend(
        [
            "0",
            "LINE",
            "8",
            layer,
            "10",
            str(x1),
            "20",
            str(y1),
            "11",
            str(x2),
            "21",
            str(y2),
        ]
    )


def dxf_arc(lines, cx, cy, radius, start, end, layer="CUT"):
    lines.extend(
        [
            "0",
            "ARC",
            "8",
            layer,
            "10",
            str(cx),
            "20",
            str(cy),
            "40",
            str(radius),
            "50",
            str(start),
            "51",
            str(end),
        ]
    )


def dxf_circle(lines, cx, cy, diameter, layer="CUT"):
    lines.extend(
        [
            "0",
            "CIRCLE",
            "8",
            layer,
            "10",
            str(cx),
            "20",
            str(cy),
            "40",
            str(diameter / 2.0),
        ]
    )


def rounded_outline(lines, length, width, radius=5.0):
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


def write_bearing_retainer_dxf(path: Path) -> None:
    lines = dxf_header()
    dxf_circle(lines, 0, 0, 42.0)
    dxf_circle(lines, 0, 0, 28.4)
    for angle in (45, 135, 225, 315):
        dxf_circle(
            lines,
            17.5 * math.cos(math.radians(angle)),
            17.5 * math.sin(math.radians(angle)),
            4.5,
        )
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_rail_bracket_dxf(path: Path) -> None:
    lines = dxf_header()
    rounded_outline(lines, PLATE_L, PLATE_W)
    for x in (48.0, 92.0):
        for y in (-24.0, 24.0):
            dxf_circle(lines, x, y, 6.6, "M6_CLEARANCE")
    for x in (12.0, 128.0):
        dxf_circle(lines, x, 0.0, 6.0, "REAMED_DOWEL")
    dxf_circle(lines, WHEEL_X, 0.0, 28.2, "BEARING_ENVELOPE")
    dxf_circle(lines, MOTOR_X, 0.0, 9.0, "MOTOR_BORE_ENVELOPE")
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def keyed_shaft(center_x=0.0) -> Mesh:
    mesh = cylinder(SHAFT_D / 2.0, 82.0, (center_x, 0.0, 0.0))
    mesh.add(
        box(
            (4.0, 2.0, 20.0),
            (center_x, SHAFT_D / 2.0 + 1.0, 21.0),
        )
    )
    return mesh


def assembly() -> Mesh:
    mesh = Mesh()
    for z in (-26.0, 26.0):
        mesh.add(box((PLATE_L, PLATE_W, PLATE_T), (PLATE_L / 2.0, 0.0, z)))
    mesh.add(cylinder(WHEEL_R, WHEEL_W, (WHEEL_X, 0.0, 0.0)))
    mesh.add(cylinder(22.5, 125.2, (MOTOR_X, 0.0, 0.0)))
    mesh.add(keyed_shaft(WHEEL_X))
    for z in BEARING_Z:
        mesh.add(cylinder(BEARING_OD / 2.0, BEARING_W, (WHEEL_X, 0.0, z)))
    mesh.add(cylinder(PULLEY_R, PULLEY_W, (WHEEL_X, 0.0, PULLEY_Z)))
    mesh.add(cylinder(PULLEY_R, PULLEY_W, (MOTOR_X, 0.0, PULLEY_Z)))
    mesh.add(
        box(
            (AXIS_SPACING, 4.0, PULLEY_W),
            ((MOTOR_X + WHEEL_X) / 2.0, PULLEY_R, PULLEY_Z),
        )
    )
    mesh.add(
        box(
            (AXIS_SPACING, 4.0, PULLEY_W),
            ((MOTOR_X + WHEEL_X) / 2.0, -PULLEY_R, PULLEY_Z),
        )
    )
    for x in (12.0, 128.0):
        mesh.add(cylinder(3.0, 64.0, (x, 0.0, 0.0)))
    return mesh


def draw_preview(path: Path, result: dict) -> None:
    bearing = result["bearing_screen"]
    shaft = result["shaft_key_screen"]
    interface = result["rail_interface_screen"]
    package = result["packaging_screen"]

    fig = plt.figure(figsize=(16, 10), dpi=110)
    grid = fig.add_gridspec(2, 2, width_ratios=[1.05, 0.95], height_ratios=[1.1, 0.9])
    ax_global = fig.add_subplot(grid[:, 0])
    ax_local = fig.add_subplot(grid[0, 1])
    ax_gate = fig.add_subplot(grid[1, 1])

    ax_global.add_patch(Circle((0, 0), SHELL_R, fill=False, linewidth=3, color="#151713"))
    for side in (-1, 1):
        wheel = (side * 155.0, -math.sqrt(206.0**2 - 155.0**2))
        radial = (wheel[0] / 206.0, wheel[1] / 206.0)
        motor = (
            wheel[0] - radial[0] * AXIS_SPACING,
            wheel[1] - radial[1] * AXIS_SPACING,
        )
        ax_global.add_patch(Circle(wheel, WHEEL_R, color="#20221e"))
        ax_global.add_patch(Circle(motor, 22.5, color="#9a9e97"))
        ax_global.plot(
            [wheel[0], motor[0]],
            [wheel[1], motor[1]],
            color="#fb5416",
            linewidth=9,
            alpha=0.65,
        )
    ax_global.text(0, 230, "254 mm INNER SHELL", ha="center", fontsize=11)
    ax_global.text(
        0,
        -280,
        "90 mm radial motor offset · current Blender master preserved",
        ha="center",
        color="#9e3518",
        fontsize=10,
    )
    ax_global.set_title(
        "GLOBAL X–Z PACKAGING\nStage-22 drivetrain reference envelope",
        loc="left",
        fontweight="bold",
    )
    ax_global.set_aspect("equal")
    ax_global.set_xlim(-290, 290)
    ax_global.set_ylim(-305, 285)
    ax_global.axis("off")

    ax_local.add_patch(
        FancyBboxPatch(
            (0, -PLATE_W / 2.0),
            PLATE_L,
            PLATE_W,
            boxstyle="round,pad=0,rounding_size=5",
            facecolor="#ece7db",
            edgecolor="#151713",
            linewidth=2,
        )
    )
    ax_local.add_patch(Circle((MOTOR_X, 0), PULLEY_R, color="#fb5416"))
    ax_local.add_patch(Circle((WHEEL_X, 0), PULLEY_R, color="#fb5416"))
    ax_local.plot([MOTOR_X, WHEEL_X], [PULLEY_R, PULLEY_R], color="#151713", linewidth=4)
    ax_local.plot([MOTOR_X, WHEEL_X], [-PULLEY_R, -PULLEY_R], color="#151713", linewidth=4)
    ax_local.add_patch(Circle((WHEEL_X, 0), BEARING_OD / 2.0, fill=False, linewidth=2))
    for x in (12.0, 128.0):
        ax_local.add_patch(Circle((x, 0.0), 3.0, color="#28778f"))
    for x in (48.0, 92.0):
        for y in (-24.0, 24.0):
            ax_local.add_patch(Rectangle((x - 3.3, y - 3.3), 6.6, 6.6, fill=False))
    ax_local.annotate(
        "90 mm",
        xy=(MOTOR_X, 28),
        xytext=(WHEEL_X, 28),
        arrowprops={"arrowstyle": "<->"},
        ha="center",
    )
    ax_local.set_title(
        "LOCAL CASSETTE / POSITIVE LOAD PATH",
        loc="left",
        fontweight="bold",
    )
    ax_local.text(
        1,
        -44,
        "5MGT-300-15 · 24T / 24T · 2×6001 · keyed Ø12 shaft · 2 dowels + 4 M6",
        fontsize=9,
    )
    ax_local.set_aspect("equal")
    ax_local.set_xlim(-12, 150)
    ax_local.set_ylim(-52, 52)
    ax_local.axis("off")

    ax_gate.axis("off")
    ax_gate.set_title("ANALYTICAL GATE / PHYSICAL HOLD", loc="left", fontweight="bold")
    rows = [
        ("BELT", "5MGT-300-15", "300 mm · 60 teeth · product 92706002"),
        (
            "BEARING LOAD",
            f"{bearing['worst_outboard_equivalent_radial_load_n']:.1f} N",
            f"L10 {bearing['l10_hours_at_analysis_speed']:.0f} h @ 1000 rpm",
        ),
        (
            "KEYED SHAFT",
            f"SF {shaft['yield_safety_factor']:.2f}",
            f"{shaft['keyway_factored_von_mises_mpa']:.1f} MPa · 7.2 Nm proof open",
        ),
        (
            "DOWEL SHEAR",
            f"{interface['dowel_single_shear_mpa']:.1f} MPa",
            "1000 N/cassette · no friction credit",
        ),
        (
            "SHELL CLEARANCE",
            f"{package['plate_shell_clearance_mm']:.1f} mm plate",
            f"{package['guarded_pulley_shell_clearance_mm']:.1f} mm guarded pulley",
        ),
    ]
    for index, (label, value, note) in enumerate(rows):
        y = 0.86 - index * 0.17
        ax_gate.text(0.0, y, label, transform=ax_gate.transAxes, family="monospace", color="#666")
        ax_gate.text(0.34, y, value, transform=ax_gate.transAxes, fontsize=14, fontweight="bold")
        ax_gate.text(0.64, y, note, transform=ax_gate.transAxes, fontsize=8.5, color="#9e3518")
    ax_gate.text(
        0.0,
        -0.03,
        "HOLD · supplier rating/tension · fits/GD&T · 7.2 Nm proof · guard access · Blender clash · physical commissioning",
        transform=ax_gate.transAxes,
        fontsize=9,
        color="white",
        bbox={"facecolor": "#151713", "pad": 8, "edgecolor": "none"},
    )

    fig.patch.set_facecolor("#f2eee3")
    for axis in (ax_global, ax_local, ax_gate):
        axis.set_facecolor("#f2eee3")
    fig.suptitle(
        "BB-8 STAGE 22 · CATALOG BELT + BEARING/SHAFT/RAIL INTERFACE",
        x=0.04,
        y=0.98,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    result = json.loads(RESULTS.read_text(encoding="utf-8"))

    write_bearing_retainer_dxf(OUT / "stage22_bearing_retainer.dxf")
    write_rail_bracket_dxf(OUT / "stage22_rail_interface_bracket.dxf")
    write_binary_stl(
        OUT / "stage22_keyed_shaft_envelope.stl",
        keyed_shaft(),
        "stage22_keyed_shaft_envelope",
    )
    write_binary_stl(
        OUT / "stage22_drivetrain_interface_assembly_envelope.stl",
        assembly(),
        "stage22_drivetrain_interface_assembly_envelope",
    )
    draw_preview(OUT / "stage22_drivetrain_interface_global.png", result)

    classifications = {
        "stage22_bearing_retainer.dxf": "NOMINAL_2D_REFERENCE_PROFILE_FIT_AND_GDT_NOT_RELEASED",
        "stage22_rail_interface_bracket.dxf": "NOMINAL_2D_REFERENCE_PROFILE_REAM_AND_GDT_NOT_RELEASED",
        "stage22_keyed_shaft_envelope.stl": "REFERENCE_ENVELOPE_KEYWAY_AND_RETAINERS_NOT_MANUFACTURING_GEOMETRY",
        "stage22_drivetrain_interface_assembly_envelope.stl": "REFERENCE_ASSEMBLY_ENVELOPE_NOT_FABRICATION_GEOMETRY",
        "stage22_drivetrain_interface_global.png": "ENGINEERING_REVIEW_IMAGE",
    }
    manifest = {
        "stage": 22,
        "architecture": contract["selected_architecture"]["id"],
        "generator": "tools/build_stage22_drivetrain_interface_cad.py",
        "manufacturing_release": False,
        "blender_application_status": result["blender_application_status"],
        "release_boundary": (
            "All outputs are nominal fit and packaging references. Bearing fits, "
            "reamed dowels, shaft keyway, hub/pulley retention, material certificates, "
            "GD&T and physical validation remain HOLD."
        ),
        "outputs": [],
    }
    for name, classification in classifications.items():
        output = OUT / name
        manifest["outputs"].append(
            {
                "path": f"hardware/stage22_drivetrain_interface/outputs/{name}",
                "bytes": output.stat().st_size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "classification": classification,
            }
        )
    (OUT / "stage22_cad_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"STAGE22_REFERENCE_CAD_OUTPUT {OUT}")
    print("REFERENCE_ONLY manufacturing_release=false Blender_master=preserved")


if __name__ == "__main__":
    main()
