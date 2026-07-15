#!/usr/bin/env python3
"""Verify the Stage-19 KiCad schematic without granting fabrication release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "hardware" / "stage19_dual_permissive_gate"
SCHEMATIC = PROJECT_DIR / "stage19_dual_permissive_gate.kicad_sch"
SYMBOL_LIBRARY = PROJECT_DIR / "stage19_symbols.kicad_sym"
PROJECT_FILE = PROJECT_DIR / "stage19_dual_permissive_gate.kicad_pro"
CANONICAL_NETLIST = ROOT / "engineering" / "stage19_gate_netlist.csv"
DEFAULT_OUTPUT = ROOT / "engineering" / "stage19_kicad_verification.json"
GENERATOR = ROOT / "tools" / "generate_stage19_kicad.py"
PUBLISHED_ERC = ROOT / "engineering" / "stage19_kicad_erc.json"
PUBLISHED_NETLIST = ROOT / "engineering" / "stage19_kicad_netlist.xml"
PUBLISHED_BOM = ROOT / "engineering" / "stage19_kicad_bom.csv"
PUBLISHED_PDF = ROOT / "output" / "pdf" / "BB8_stage19_dual_permissive_gate_schematic.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def kicad_library_dirs(cli: Path) -> tuple[Path, Path]:
    shared = cli.parents[1] / "SharedSupport"
    symbol_dir = shared / "symbols"
    footprint_dir = shared / "footprints"
    if not (symbol_dir / "Device.kicad_sym").is_file():
        raise FileNotFoundError(f"KiCad symbol library not found: {symbol_dir}")
    if not footprint_dir.is_dir():
        raise FileNotFoundError(f"KiCad footprint library not found: {footprint_dir}")
    return symbol_dir, footprint_dir


def run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )


def canonical_connections(path: Path) -> dict[tuple[str, str], str]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["reference"], row["pin"]): row["net"] for row in rows}


def exported_connections(path: Path) -> tuple[dict[tuple[str, str], str], set[str], set[str]]:
    root = ET.parse(path).getroot()
    refs = {component.attrib["ref"] for component in root.findall("./components/comp")}
    nets: set[str] = set()
    connections: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        name = net.attrib["name"].removeprefix("/")
        nets.add(name)
        for node in net.findall("node"):
            connections[(node.attrib["ref"], node.attrib["pin"])] = name
    return connections, refs, nets


def bom_references(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    references: set[str] = set()
    for row in rows:
        references.update(row["Refs"].split())
    return references


def verify(kicad_cli: Path) -> dict[str, Any]:
    symbol_dir, footprint_dir = kicad_library_dirs(kicad_cli)
    env = os.environ.copy()
    env.update(
        {
            "KICAD_SYMBOL_DIR": str(symbol_dir),
            "KICAD10_SYMBOL_DIR": str(symbol_dir),
            "KICAD10_FOOTPRINT_DIR": str(footprint_dir),
        }
    )
    version = run([str(kicad_cli), "--version"], env).stdout.strip().splitlines()[-1]

    expected = canonical_connections(CANONICAL_NETLIST)
    expected_refs = {reference for reference, _pin in expected}
    expected_nets = set(expected.values())

    with tempfile.TemporaryDirectory(prefix="bb8-stage19-kicad-") as temporary:
        temp = Path(temporary)
        generated_schematic = temp / SCHEMATIC.name
        generated_library = temp / SYMBOL_LIBRARY.name
        run(
            [
                sys.executable,
                str(GENERATOR),
                "--symbol-dir",
                str(symbol_dir),
                "--output",
                str(generated_schematic),
                "--library-output",
                str(generated_library),
            ],
            env,
        )

        erc = temp / "stage19_kicad_erc.json"
        netlist = temp / "stage19_kicad_netlist.xml"
        bom = temp / "stage19_kicad_bom.csv"
        pdf = temp / "stage19_schematic.pdf"
        run(
            [
                str(kicad_cli),
                "sch",
                "erc",
                "--format",
                "json",
                "--severity-all",
                "--exit-code-violations",
                "-o",
                str(erc),
                str(SCHEMATIC),
            ],
            env,
        )
        run(
            [
                str(kicad_cli),
                "sch",
                "export",
                "netlist",
                "--format",
                "kicadxml",
                "-o",
                str(netlist),
                str(SCHEMATIC),
            ],
            env,
        )
        run(
            [str(kicad_cli), "sch", "export", "bom", "-o", str(bom), str(SCHEMATIC)],
            env,
        )
        run(
            [
                str(kicad_cli),
                "sch",
                "export",
                "pdf",
                "--black-and-white",
                "-o",
                str(pdf),
                str(SCHEMATIC),
            ],
            env,
        )

        erc_data = json.loads(erc.read_text(encoding="utf-8"))
        violations = [
            violation
            for sheet in erc_data.get("sheets", [])
            for violation in sheet.get("violations", [])
        ]
        actual, actual_refs, actual_nets = exported_connections(netlist)
        actual_for_expected_refs = {
            key: net for key, net in actual.items() if key[0] in expected_refs
        }
        exported_bom_refs = bom_references(bom)
        published_erc_data = json.loads(PUBLISHED_ERC.read_text(encoding="utf-8"))
        published_violations = [
            violation
            for sheet in published_erc_data.get("sheets", [])
            for violation in sheet.get("violations", [])
        ]
        published_connections, published_refs, published_nets = exported_connections(
            PUBLISHED_NETLIST
        )
        published_netlist_source = ET.parse(PUBLISHED_NETLIST).findtext("./design/source")
        published_for_expected_refs = {
            key: net
            for key, net in published_connections.items()
            if key[0] in expected_refs
        }
        published_bom_refs = bom_references(PUBLISHED_BOM)

        checks = {
            "kicad_major_version_10": version.startswith("10."),
            "tracked_schematic_matches_deterministic_generator": (
                generated_schematic.read_bytes() == SCHEMATIC.read_bytes()
            ),
            "tracked_symbol_library_matches_deterministic_generator": (
                generated_library.read_bytes() == SYMBOL_LIBRARY.read_bytes()
            ),
            "project_file_present": PROJECT_FILE.is_file(),
            "erc_zero_violations": len(violations) == 0,
            "published_erc_zero_violations": len(published_violations) == 0,
            "canonical_pin_connections_match_export": actual_for_expected_refs == expected,
            "published_netlist_matches_canonical": (
                published_for_expected_refs == expected
                and published_refs == expected_refs
                and published_nets == expected_nets
            ),
            "published_netlist_uses_repository_relative_source": (
                published_netlist_source
                == "hardware/stage19_dual_permissive_gate/"
                "stage19_dual_permissive_gate.kicad_sch"
            ),
            "component_reference_set_matches_canonical": actual_refs == expected_refs,
            "bom_reference_set_matches_canonical": exported_bom_refs == expected_refs,
            "published_bom_reference_set_matches_canonical": (
                published_bom_refs == expected_refs
            ),
            "net_name_set_matches_canonical": actual_nets == expected_nets,
            "schematic_pdf_is_nonempty": pdf.stat().st_size > 10_000,
            "schematic_pdf_signature_valid": pdf.read_bytes().startswith(b"%PDF-"),
            "published_schematic_pdf_valid": (
                PUBLISHED_PDF.stat().st_size > 10_000
                and PUBLISHED_PDF.read_bytes().startswith(b"%PDF-")
            ),
        }
        passed = all(checks.values())
        mismatches = {
            f"{reference}.{pin}": {"expected": net, "actual": actual.get((reference, pin))}
            for (reference, pin), net in expected.items()
            if actual.get((reference, pin)) != net
        }
        return {
            "stage": 19,
            "overall": (
                "HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED"
                if passed
                else "HOLD_KICAD_SCHEMATIC_VERIFICATION_FAILED"
            ),
            "schematic_verification": (
                "PASS_SCHEMATIC_ERC_AND_NETLIST_ONLY" if passed else "FAIL"
            ),
            "kicad_cli": kicad_cli.name,
            "kicad_version": version,
            "checks": checks,
            "counts": {
                "erc_violations": len(violations),
                "component_references": len(actual_refs),
                "canonical_pin_connections": len(expected),
                "exported_nets": len(actual_nets),
                "bom_references": len(exported_bom_refs),
                "pdf_bytes": pdf.stat().st_size,
            },
            "connection_mismatches": mismatches,
            "artifact_sha256": {
                "schematic": sha256(SCHEMATIC),
                "symbol_library": sha256(SYMBOL_LIBRARY),
                "erc_json": sha256(PUBLISHED_ERC),
                "netlist_xml": sha256(PUBLISHED_NETLIST),
                "bom_csv": sha256(PUBLISHED_BOM),
                "schematic_pdf": sha256(PUBLISHED_PDF),
            },
            "evidence_boundary": (
                "Deterministic KiCad 10 schematic, zero-violation ERC, canonical-netlist "
                "cross-audit, BOM-reference audit and PDF export only. The separate routed-PCB "
                "and zero-violation/zero-unconnected DRC evidence is recorded in "
                "engineering/stage19_kicad_pcb_verification.json. No independent schematic or "
                "layout peer review, Gerber/drill release review, fabricated board, power-up, "
                "bench waveform or physical commissioning release."
            ),
            "manufacturing_release": (
                "NOT_RELEASED_PEER_REVIEW_GERBER_AND_PHYSICAL_VALIDATION_REQUIRED"
            ),
            "physical_test_status": "NOT_RUN",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    result = verify(find_kicad_cli(args.kicad_cli))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"{result['schematic_verification']} overall={result['overall']} "
        f"erc={result['counts']['erc_violations']} refs={result['counts']['component_references']} "
        f"nets={result['counts']['exported_nets']}"
    )
    if args.expect_overall and result["overall"] != args.expect_overall:
        return 2
    return 0 if result["schematic_verification"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
