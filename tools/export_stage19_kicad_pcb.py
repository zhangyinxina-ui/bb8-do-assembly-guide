#!/usr/bin/env python3
"""Export Stage-19 PCB review images; never emits fabrication files."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = (
    ROOT
    / "hardware"
    / "stage19_dual_permissive_gate"
    / "stage19_dual_permissive_gate.kicad_pcb"
)
DEFAULT_OUTPUT = ROOT / "output" / "pcb"
DEFAULT_PUBLIC = ROOT / "public" / "images"
PREFIX = "BB8_stage19_gate_pcb"


def executable(explicit: Path | None, names: tuple[str, ...], candidates: list[Path]) -> Path:
    possible = [explicit]
    possible.extend(Path(found) for name in names if (found := shutil.which(name)))
    possible.extend(candidates)
    for candidate in possible:
        if candidate and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise FileNotFoundError(f"Required executable not found: {', '.join(names)}")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def normalize_svg(path: Path) -> None:
    """Remove exporter-only trailing whitespace without changing SVG geometry."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--public-output", type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--rsvg-convert", type=Path)
    args = parser.parse_args()

    cli = executable(
        args.kicad_cli,
        ("kicad-cli",),
        [
            Path.home() / "Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        ],
    )
    rsvg = executable(
        args.rsvg_convert,
        ("rsvg-convert",),
        [Path("/opt/homebrew/bin/rsvg-convert"), Path("/usr/local/bin/rsvg-convert")],
    )
    board = args.board.resolve()
    output = args.output.resolve()
    public = args.public_output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    top_svg = output / f"{PREFIX}_top.svg"
    bottom_svg = output / f"{PREFIX}_bottom.svg"
    top_png = output / f"{PREFIX}_top.png"
    bottom_png = output / f"{PREFIX}_bottom.png"
    isometric_png = output / f"{PREFIX}_isometric.png"

    run(
        [
            str(cli),
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--subtract-soldermask",
            "--layers",
            "F.Cu,F.Silkscreen,Edge.Cuts",
            "--output",
            str(top_svg),
            str(board),
        ]
    )
    run(
        [
            str(cli),
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--mirror",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--subtract-soldermask",
            "--layers",
            "B.Cu,B.Silkscreen,Edge.Cuts",
            "--output",
            str(bottom_svg),
            str(board),
        ]
    )
    normalize_svg(top_svg)
    normalize_svg(bottom_svg)
    run([str(rsvg), "--width", "1800", "--output", str(top_png), str(top_svg)])
    run([str(rsvg), "--width", "1800", "--output", str(bottom_png), str(bottom_svg)])
    run(
        [
            str(cli),
            "pcb",
            "render",
            "--quality",
            "high",
            "--background",
            "opaque",
            "--width",
            "1800",
            "--height",
            "1250",
            "--side",
            "top",
            "--rotate",
            "-35,0,25",
            "--zoom",
            "1.1",
            "--output",
            str(isometric_png),
            str(board),
        ]
    )

    artifacts = [top_svg, bottom_svg, top_png, bottom_png, isometric_png]
    for artifact in artifacts:
        shutil.copy2(artifact, public / artifact.name)
        print(f"exported={artifact.relative_to(ROOT)} bytes={artifact.stat().st_size}")
    print("release=REFERENCE_REVIEW_IMAGES_ONLY_NO_GERBER_NO_DRILL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
