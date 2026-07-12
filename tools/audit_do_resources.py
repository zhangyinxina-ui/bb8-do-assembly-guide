#!/usr/bin/env python3
"""Audit the locally pinned Printed Droid D-O resources."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "third_party" / "D-O-Printed-Droid"
OUT = ROOT / "engineering" / "do_resource_manifest.json"

MECHANICAL_SUFFIXES = {".stl", ".step", ".stp", ".f3d", ".obj", ".3mf", ".scad"}
LICENSE_MARKER = "NON-COMMERCIAL LICENSE"
RECOMMENDED_SKETCH = "D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino"


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not (REPO / ".git").is_dir():
        raise SystemExit(f"FAIL missing repository: {REPO}")

    files = sorted(path for path in REPO.rglob("*") if path.is_file() and ".git" not in path.parts)
    sketches = [str(path.relative_to(REPO)) for path in files if path.suffix.lower() == ".ino"]
    mechanical = [str(path.relative_to(REPO)) for path in files if path.suffix.lower() in MECHANICAL_SUFFIXES]
    readmes = sorted(REPO.rglob("README.md"))
    licensed_readmes = [
        str(path.relative_to(REPO))
        for path in readmes
        if LICENSE_MARKER in path.read_text(encoding="utf-8", errors="replace")
    ]

    downloads = []
    for name in ("DO-Instructions-Pt1.1.pdf", "DOV2-Wiring-diagram-notes.pdf", "DO-Stand-60mm.stl"):
        path = ROOT / "third_party" / name
        downloads.append(
            {
                "path": str(path.relative_to(ROOT)),
                "present": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256(path) if path.is_file() else None,
                "redistribution": "not bundled into public site; retain for personal build reference because upstream redistribution terms are not explicit",
            }
        )

    manifest = {
        "audit_date": "2026-07-12",
        "repository": {
            "url": git("remote", "get-url", "origin"),
            "commit": git("rev-parse", "HEAD"),
            "commit_date": git("log", "-1", "--format=%cI"),
            "branch": git("branch", "--show-current"),
            "working_tree_clean": not bool(git("status", "--porcelain")),
        },
        "license": {
            "root_license_file_present": any((REPO / name).is_file() for name in ("LICENSE", "LICENSE.md", "COPYING")),
            "classification": "public source under a custom personal non-commercial license; not OSI open source",
            "licensed_readmes": licensed_readmes,
            "required_conditions": [
                "personal non-commercial use only",
                "retain copyright and permission notice",
                "attribute original authors and Printed-Droid.com community",
                "no commercial products, services, selling, or licensing",
            ],
        },
        "firmware": {
            "recommended": RECOMMENDED_SKETCH,
            "recommended_present": (REPO / RECOMMENDED_SKETCH).is_file(),
            "sketch_count": len(sketches),
            "sketches": sketches,
            "target": "Arduino Mega 2560",
            "dependencies": ["IBusBM", "Servo", "EEPROM", "SoftwareSerial", "DFRobotDFPlayerMini", "Wire", "avr/wdt"],
        },
        "mechanical_models": {
            "count": len(mechanical),
            "files": mechanical,
            "status": "absent from this repository" if not mechanical else "present",
        },
        "separate_public_model": {
            "path": "third_party/DO-Stand-60mm.stl",
            "purpose": "60 mm wheel-off electronics test stand; not a D-O body component",
            "license": "publicly downloadable but no explicit redistribution license found",
        },
        "reference_downloads": downloads,
        "conclusion": "Firmware and documentation are usable for a personal non-commercial build; complete mechanical CAD/STL is still missing from the public repository.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failures = []
    if manifest["repository"]["url"] != "https://github.com/PrintedDroid/D-O-Printed-Droid.git":
        failures.append("unexpected origin")
    if not manifest["firmware"]["recommended_present"]:
        failures.append("recommended firmware missing")
    if len(licensed_readmes) != 3:
        failures.append(f"expected 3 licensed version READMEs, found {len(licensed_readmes)}")
    if mechanical:
        failures.append("unexpected mechanical CAD detected; review licensing before use")
    if not all(item["present"] for item in downloads):
        failures.append("reference PDF missing")

    if failures:
        raise SystemExit("FAIL " + "; ".join(failures))
    print(
        "PASS D-O RESOURCE AUDIT "
        f"commit={manifest['repository']['commit']} sketches={len(sketches)} "
        f"licensed_readmes={len(licensed_readmes)} mechanical_models={len(mechanical)}"
    )


if __name__ == "__main__":
    main()
