#!/usr/bin/env python3
"""Verify the routed Stage-19 PCB without granting fabrication release.

The script re-executes itself with KiCad's bundled Python when necessary,
regenerates the board in a temporary directory, compares a UUID-independent
structural manifest, and runs KiCad DRC on temporary copies of both boards.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "hardware" / "stage19_dual_permissive_gate"
BOARD = PROJECT_DIR / "stage19_dual_permissive_gate.kicad_pcb"
PROJECT = PROJECT_DIR / "stage19_dual_permissive_gate.kicad_pro"
CANONICAL_NETLIST = ROOT / "engineering" / "stage19_gate_netlist.csv"
GENERATOR = ROOT / "tools" / "generate_stage19_kicad_pcb.py"
DEFAULT_OUTPUT = ROOT / "engineering" / "stage19_kicad_pcb_verification.json"
DEFAULT_DRC_OUTPUT = ROOT / "engineering" / "stage19_kicad_pcb_drc.json"

EXPECTED_BOARD_MM = (50.0, 35.0)
EXPECTED_MOUNT_HOLES_MM = {
    "H1": (3.0, 3.0),
    "H2": (47.0, 3.0),
    "H3": (3.0, 32.0),
    "H4": (47.0, 32.0),
}


def find_kicad_cli(explicit: Path | None = None) -> Path:
    candidates = [
        explicit,
        Path(found) if (found := shutil.which("kicad-cli")) else None,
        Path.home() / "Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
        Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise FileNotFoundError("KiCad CLI not found; install KiCad 10 or pass --kicad-cli")


def find_kicad_python(cli: Path) -> Path:
    candidates = [
        cli.parents[1] / "Frameworks/Python.framework/Versions/3.9/bin/python3",
        cli.parents[1] / "Frameworks/Python.framework/Versions/Current/bin/python3",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise FileNotFoundError(f"KiCad bundled Python not found beside {cli}")


def ensure_pcbnew(cli: Path) -> None:
    if importlib.util.find_spec("pcbnew") is not None:
        return
    if os.environ.get("BB8_STAGE19_PCBNEW_REEXEC") == "1":
        raise ModuleNotFoundError("pcbnew is unavailable in KiCad's bundled Python")
    python = find_kicad_python(cli)
    env = os.environ.copy()
    env["BB8_STAGE19_PCBNEW_REEXEC"] = "1"
    os.execve(
        str(python),
        [str(python), str(Path(__file__).resolve()), *sys.argv[1:]],
        env,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def round_mm(value: int) -> float:
    return round(value / 1_000_000.0, 6)


def point_mm(point: Any) -> list[float]:
    return [round_mm(point.x), round_mm(point.y)]


def canonical_connections() -> dict[tuple[str, str], str]:
    with CANONICAL_NETLIST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["reference"], row["pin"]): row["net"] for row in rows}


def board_connections(board: Any, refs: set[str]) -> dict[tuple[str, str], str]:
    actual: dict[tuple[str, str], str] = {}
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference not in refs:
            continue
        for pad in footprint.Pads():
            actual[(reference, pad.GetNumber())] = pad.GetNetname()
    return actual


def outline(board: Any, pcbnew: Any) -> dict[str, Any]:
    segments = []
    points = []
    for drawing in board.GetDrawings():
        if drawing.GetLayer() != pcbnew.Edge_Cuts:
            continue
        start = point_mm(drawing.GetStart())
        end = point_mm(drawing.GetEnd())
        segments.append({"shape": drawing.GetShapeStr(), "start_mm": start, "end_mm": end})
        points.extend((start, end))
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    return {
        "segments": sorted(segments, key=lambda item: json.dumps(item, sort_keys=True)),
        "origin_mm": [min_x, min_y],
        "width_mm": round(max_x - min_x, 6),
        "height_mm": round(max_y - min_y, 6),
    }


def footprint_manifest(board: Any) -> list[dict[str, Any]]:
    footprints = []
    for footprint in board.GetFootprints():
        pads = []
        for pad in footprint.Pads():
            pads.append(
                {
                    "number": pad.GetNumber(),
                    "net": pad.GetNetname(),
                    "position_mm": point_mm(pad.GetPosition()),
                    "size_mm": point_mm(pad.GetSize()),
                    "drill_mm": point_mm(pad.GetDrillSize()),
                    "attribute": int(pad.GetAttribute()),
                }
            )
        footprints.append(
            {
                "reference": footprint.GetReference(),
                "value": footprint.GetValue(),
                "library_id": footprint.GetFPID().GetUniStringLibId(),
                "position_mm": point_mm(footprint.GetPosition()),
                "rotation_deg": round(footprint.GetOrientationDegrees(), 6),
                "pads": sorted(pads, key=lambda item: (item["number"], item["position_mm"])),
            }
        )
    return sorted(footprints, key=lambda item: item["reference"])


def routing_manifest(board: Any, pcbnew: Any) -> dict[str, Any]:
    tracks = []
    vias = []
    per_net_track_length: dict[str, float] = {}
    for item in board.GetTracks():
        net = item.GetNetname()
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append(
                {
                    "net": net,
                    "position_mm": point_mm(item.GetPosition()),
                    "diameter_mm": round_mm(item.GetWidth(pcbnew.F_Cu)),
                    "drill_mm": round_mm(item.GetDrillValue()),
                }
            )
            continue
        length = round_mm(item.GetLength())
        per_net_track_length[net] = per_net_track_length.get(net, 0.0) + length
        tracks.append(
            {
                "net": net,
                "layer": pcbnew.LayerName(item.GetLayer()),
                "start_mm": point_mm(item.GetStart()),
                "end_mm": point_mm(item.GetEnd()),
                "width_mm": round_mm(item.GetWidth()),
            }
        )
    zones = []
    for zone in board.Zones():
        zones.append(
            {
                "net": zone.GetNetname(),
                "layer": pcbnew.LayerName(zone.GetLayer()),
                "corners_mm": [
                    point_mm(zone.GetCornerPosition(index))
                    for index in range(zone.GetNumCorners())
                ],
            }
        )
    return {
        "tracks": sorted(tracks, key=lambda item: json.dumps(item, sort_keys=True)),
        "vias": sorted(vias, key=lambda item: json.dumps(item, sort_keys=True)),
        "zones": sorted(zones, key=lambda item: (item["layer"], item["net"])),
        "per_net_track_length_mm": {
            net: round(length, 3) for net, length in sorted(per_net_track_length.items())
        },
    }


def structural_manifest(board: Any, pcbnew: Any) -> dict[str, Any]:
    return {
        "copper_layers": board.GetCopperLayerCount(),
        "outline": outline(board, pcbnew),
        "footprints": footprint_manifest(board),
        "routing": routing_manifest(board, pcbnew),
        "named_nets": sorted(
            str(name) for name in board.GetNetInfo().NetsByName() if str(name)
        ),
    }


def structural_sha256(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def mounting_holes(board: Any, origin: list[float], pcbnew: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for reference in sorted(EXPECTED_MOUNT_HOLES_MM):
        footprint = board.FindFootprintByReference(reference)
        pads = list(footprint.Pads()) if footprint else []
        pad = pads[0] if len(pads) == 1 else None
        if not footprint or not pad:
            result[reference] = {"present": False}
            continue
        absolute = point_mm(footprint.GetPosition())
        result[reference] = {
            "present": True,
            "centre_from_board_origin_mm": [
                round(absolute[0] - origin[0], 6),
                round(absolute[1] - origin[1], 6),
            ],
            "drill_mm": round_mm(pad.GetDrillSize().x),
            "non_plated": int(pad.GetAttribute()) == int(pcbnew.PAD_ATTRIB_NPTH),
        }
    return result


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def drc(cli: Path, board: Path, output: Path) -> tuple[dict[str, Any], str, int]:
    completed = run(
        [
            str(cli),
            "pcb",
            "drc",
            "--refill-zones",
            "--save-board",
            "--format",
            "json",
            "--severity-all",
            "--units",
            "mm",
            "--exit-code-violations",
            "--output",
            str(output),
            str(board),
        ]
    )
    if not output.is_file():
        raise RuntimeError(f"KiCad DRC did not create {output}:\n{completed.stdout}")
    return json.loads(output.read_text(encoding="utf-8")), completed.stdout, completed.returncode


def verify(kicad_cli: Path, pcbnew: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = canonical_connections()
    expected_refs = {reference for reference, _pin in expected}
    expected_nets = set(expected.values())
    version_result = run([str(kicad_cli), "--version"])
    version = version_result.stdout.strip().splitlines()[-1]

    with tempfile.TemporaryDirectory(prefix="bb8-stage19-pcb-") as temporary:
        temp = Path(temporary)
        tracked_dir = temp / "tracked"
        generated_dir = temp / "generated"
        tracked_dir.mkdir()
        generated_dir.mkdir()

        tracked_board_path = tracked_dir / BOARD.name
        tracked_project_path = tracked_dir / PROJECT.name
        shutil.copy2(BOARD, tracked_board_path)
        shutil.copy2(PROJECT, tracked_project_path)

        generated_board_path = generated_dir / BOARD.name
        generated_project_path = generated_dir / PROJECT.name
        generated = run([sys.executable, str(GENERATOR), "--output", str(generated_board_path)])
        if generated.returncode != 0:
            raise RuntimeError(f"PCB generator failed:\n{generated.stdout}")
        shutil.copy2(PROJECT, generated_project_path)

        tracked_drc_path = tracked_dir / "drc.json"
        generated_drc_path = generated_dir / "drc.json"
        tracked_drc, _tracked_log, tracked_returncode = drc(
            kicad_cli, tracked_board_path, tracked_drc_path
        )
        generated_drc, _generated_log, generated_returncode = drc(
            kicad_cli, generated_board_path, generated_drc_path
        )

        tracked_board = pcbnew.LoadBoard(str(tracked_board_path))
        generated_board = pcbnew.LoadBoard(str(generated_board_path))
        tracked_manifest = structural_manifest(tracked_board, pcbnew)
        generated_manifest = structural_manifest(generated_board, pcbnew)
        tracked_structure_sha = structural_sha256(tracked_manifest)
        generated_structure_sha = structural_sha256(generated_manifest)
        board_outline = tracked_manifest["outline"]
        actual_connections = board_connections(tracked_board, expected_refs)
        holes = mounting_holes(tracked_board, board_outline["origin_mm"], pcbnew)
        routing = tracked_manifest["routing"]
        named_nets = set(tracked_manifest["named_nets"])
        all_refs = {item["reference"] for item in tracked_manifest["footprints"]}
        expected_all_refs = expected_refs | set(EXPECTED_MOUNT_HOLES_MM)
        expected_zone_pairs = {("F.Cu", "3V3"), ("B.Cu", "GND")}
        actual_zone_pairs = {(zone["layer"], zone["net"]) for zone in routing["zones"]}

        checks = {
            "kicad_major_version_10": version.startswith("10."),
            "tracked_board_present": BOARD.is_file(),
            "tracked_project_present": PROJECT.is_file(),
            "generator_reproduces_uuid_independent_structure": (
                tracked_structure_sha == generated_structure_sha
            ),
            "tracked_drc_exit_code_zero": tracked_returncode == 0,
            "tracked_drc_zero_violations": len(tracked_drc.get("violations", [])) == 0,
            "tracked_drc_zero_unconnected_items": (
                len(tracked_drc.get("unconnected_items", [])) == 0
            ),
            "generated_drc_exit_code_zero": generated_returncode == 0,
            "generated_drc_zero_violations": len(generated_drc.get("violations", [])) == 0,
            "generated_drc_zero_unconnected_items": (
                len(generated_drc.get("unconnected_items", [])) == 0
            ),
            "two_copper_layers": tracked_manifest["copper_layers"] == 2,
            "board_outline_is_four_segments": len(board_outline["segments"]) == 4,
            "board_dimensions_are_50_by_35_mm": (
                board_outline["width_mm"], board_outline["height_mm"]
            )
            == EXPECTED_BOARD_MM,
            "footprint_reference_set_matches_34_components_plus_4_holes": (
                all_refs == expected_all_refs
            ),
            "canonical_91_pin_connections_match_board": actual_connections == expected,
            "named_net_set_matches_canonical_21_nets": named_nets == expected_nets,
            "power_planes_are_fcu_3v3_and_bcu_gnd": actual_zone_pairs == expected_zone_pairs,
            "four_m3_npth_holes_match_contract": all(
                item.get("present")
                and item.get("non_plated")
                and item.get("drill_mm") == 3.2
                and item.get("centre_from_board_origin_mm")
                == list(EXPECTED_MOUNT_HOLES_MM[reference])
                for reference, item in holes.items()
            ),
        }
        passed = all(checks.values())
        result = {
            "stage": 19,
            "overall": "HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED",
            "pcb_verification": (
                "PASS_ROUTED_PCB_DRC_REFERENCE_DESIGN_ONLY"
                if passed
                else "FAIL_PCB_VERIFICATION"
            ),
            "kicad_cli": "kicad-cli",
            "kicad_version": version,
            "checks": checks,
            "counts": {
                "footprints": len(tracked_manifest["footprints"]),
                "component_references": len(expected_refs),
                "mounting_holes": len(holes),
                "canonical_pin_connections": len(expected),
                "named_nets": len(named_nets),
                "track_segments": len(routing["tracks"]),
                "vias": len(routing["vias"]),
                "zones": len(routing["zones"]),
                "tracked_drc_violations": len(tracked_drc.get("violations", [])),
                "tracked_unconnected_items": len(tracked_drc.get("unconnected_items", [])),
                "generated_drc_violations": len(generated_drc.get("violations", [])),
                "generated_unconnected_items": len(
                    generated_drc.get("unconnected_items", [])
                ),
            },
            "board": {
                "width_mm": board_outline["width_mm"],
                "height_mm": board_outline["height_mm"],
                "copper_layers": tracked_manifest["copper_layers"],
                "mounting_holes": holes,
                "zones": routing["zones"],
                "per_net_track_length_mm": routing["per_net_track_length_mm"],
            },
            "artifact_sha256": {
                "tracked_board": sha256(BOARD),
                "tracked_structure": tracked_structure_sha,
                "generated_structure": generated_structure_sha,
            },
            "tool_results": {
                "generator_exit_code": generated.returncode,
                "tracked_drc_exit_code": tracked_returncode,
                "generated_drc_exit_code": generated_returncode,
            },
            "evidence_boundary": (
                "Deterministic KiCad 10 two-layer routed PCB, UUID-independent structural "
                "regeneration, canonical-netlist cross-audit, exact 50 x 35 mm mechanical "
                "interface and zero-violation/zero-unconnected DRC only. No independent "
                "schematic or layout peer review, Gerber/drill release review, fabricated "
                "board, continuity, power-up, oscilloscope timing, EMC, thermal or physical "
                "commissioning evidence."
            ),
            "manufacturing_release": (
                "NOT_RELEASED_PEER_REVIEW_GERBER_AND_PHYSICAL_VALIDATION_REQUIRED"
            ),
            "physical_test_status": "NOT_RUN",
        }
        return result, tracked_drc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--drc-output", type=Path, default=DEFAULT_DRC_OUTPUT)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    cli = find_kicad_cli(args.kicad_cli)
    ensure_pcbnew(cli)
    import pcbnew  # type: ignore[import-not-found]

    result, drc_result = verify(cli, pcbnew)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.drc_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.drc_output.write_text(json.dumps(drc_result, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['pcb_verification']} "
        f"violations={result['counts']['tracked_drc_violations']} "
        f"unconnected={result['counts']['tracked_unconnected_items']} "
        f"footprints={result['counts']['footprints']} "
        f"vias={result['counts']['vias']}"
    )
    if args.expect_overall and result["overall"] != args.expect_overall:
        return 2
    if not all(result["checks"].values()):
        for name, passed in result["checks"].items():
            if not passed:
                print(f"FAIL {name}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
