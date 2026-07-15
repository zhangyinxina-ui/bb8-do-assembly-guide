#!/usr/bin/env python3
"""Build a version-locked D-O v3.4.3 Mega safe-servo-pin variant.

The upstream firmware remains in the gitignored third_party checkout under its
custom personal non-commercial terms. This tool publishes only the deterministic
transformation, hashes, compile evidence and wiring contract; it does not publish
the transformed third-party source or a binary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "third_party" / "D-O-Printed-Droid"
SOURCE_RELATIVE = Path(
    "D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino"
)
SOURCE = REPO / SOURCE_RELATIVE
LICENSE_README = REPO / "D-O_ibus_v3.4/README.md"
EXPECTED_COMMIT = "e90aacdbe26a62fd4f0229d5504a3f2f3c409055"
EXPECTED_SOURCE_SHA256 = (
    "6cb3ce0d96c83724aaf9170eaef592c3d7cc866b9da66819db9e9f3fe134a707"
)
ORIGINAL_SERVO_PINS = {
    "MAINBAR_SERVO_PIN": 0,
    "HEAD1_SERVO_PIN": 1,
    "HEAD2_SERVO_PIN": 5,
    "HEAD3_SERVO_PIN": 6,
}
SAFE_SERVO_PINS = {
    "MAINBAR_SERVO_PIN": 22,
    "HEAD1_SERVO_PIN": 23,
    "HEAD2_SERVO_PIN": 24,
    "HEAD3_SERVO_PIN": 25,
}
STAGE = (
    ROOT
    / "engineering"
    / "do-safe-pin-stage"
    / "D_O_printed_droid_rc_ibus_v3.4.3_safe_pins"
)
STAGED_SOURCE = STAGE / "D_O_printed_droid_rc_ibus_v3.4.3_safe_pins.ino"
BUILD_ROOT = ROOT / "engineering" / "do-safe-pin-build"
CONFIG = ROOT / "engineering" / "arduino-cli-do.yaml"
EVIDENCE = ROOT / "engineering" / "do_safe_pin_variant_compile.json"
PUBLIC_EVIDENCE = ROOT / "public" / "downloads" / EVIDENCE.name
WIRING = ROOT / "engineering" / "do_safe_pin_variant_wiring.csv"
PUBLIC_WIRING = ROOT / "public" / "downloads" / WIRING.name
FQBN = "arduino:avr:mega"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO), *args], text=True
    ).strip()


def numeric_pin_constants(source: str) -> dict[str, int]:
    return {
        name: int(value)
        for name, value in re.findall(
            r"const\s+uint8_t\s+([A-Z0-9_]+_PIN)\s*=\s*(\d+)\s*;",
            source,
        )
    }


def transform_source(source: str) -> tuple[str, dict[str, Any]]:
    observed = numeric_pin_constants(source)
    original_observed = {
        name: observed.get(name) for name in ORIGINAL_SERVO_PINS
    }
    if original_observed != ORIGINAL_SERVO_PINS:
        raise ValueError(
            f"upstream servo pin contract changed: {original_observed}"
        )
    if "Serial.begin(9600);" not in source:
        raise ValueError("expected Serial0 console initialization is missing")

    non_servo_pins = {
        name: pin
        for name, pin in observed.items()
        if name not in ORIGINAL_SERVO_PINS
    }
    occupied_targets = {
        name: pin
        for name, pin in non_servo_pins.items()
        if pin in SAFE_SERVO_PINS.values()
    }
    if occupied_targets:
        raise ValueError(f"safe-pin target collision: {occupied_targets}")
    if len(set(SAFE_SERVO_PINS.values())) != len(SAFE_SERVO_PINS):
        raise ValueError("safe servo pins are not unique")

    transformed = source.replace(
        "// Servos - matched to v1.1/v2.1 pinout",
        "// Servos - BB8/DO guide safe-pin variant; version-locked wiring required",
        1,
    )
    if transformed == source:
        raise ValueError("servo section marker changed upstream")

    for name, old_pin in ORIGINAL_SERVO_PINS.items():
        new_pin = SAFE_SERVO_PINS[name]
        pattern = rf"(const\s+uint8_t\s+{re.escape(name)}\s*=\s*){old_pin}(\s*;)"
        transformed, count = re.subn(
            pattern,
            rf"\g<1>{new_pin}\g<2>",
            transformed,
            count=1,
        )
        if count != 1:
            raise ValueError(f"failed to transform {name}")

    transformed_pins = numeric_pin_constants(transformed)
    safe_observed = {name: transformed_pins.get(name) for name in SAFE_SERVO_PINS}
    if safe_observed != SAFE_SERVO_PINS:
        raise ValueError(f"safe-pin transform mismatch: {safe_observed}")

    return transformed, {
        "original_servo_pins": ORIGINAL_SERVO_PINS,
        "safe_servo_pins": SAFE_SERVO_PINS,
        "released_serial0_pins": [0, 1],
        "other_numeric_pin_constants": non_servo_pins,
        "target_pin_collisions": occupied_targets,
        "serial0_console_preserved": True,
        "all_safe_pins_unique": True,
    }


def parse_compile_output(output: str) -> dict[str, int]:
    program = re.search(
        r"Sketch uses\s+(\d+)\s+bytes\s+\((\d+)%\).*?Maximum is\s+(\d+)\s+bytes",
        output,
        re.DOTALL,
    )
    ram = re.search(
        r"Global variables use\s+(\d+)\s+bytes\s+\((\d+)%\).*?leaving\s+(\d+)\s+bytes.*?Maximum is\s+(\d+)\s+bytes",
        output,
        re.DOTALL,
    )
    if not program or not ram:
        raise ValueError(f"unable to parse Arduino compile summary:\n{output}")
    return {
        "program_bytes": int(program.group(1)),
        "program_percent": int(program.group(2)),
        "program_max_bytes": int(program.group(3)),
        "global_ram_bytes": int(ram.group(1)),
        "global_ram_percent": int(ram.group(2)),
        "global_ram_remaining_bytes": int(ram.group(3)),
        "ram_max_bytes": int(ram.group(4)),
    }


def write_wiring(path: Path, pins: dict[str, int]) -> None:
    rows = [
        {
            "signal": "MAINBAR_SERVO",
            "source_constant": "MAINBAR_SERVO_PIN",
            "mega_pin": f"D{pins['MAINBAR_SERVO_PIN']}",
            "interface": "servo PWM",
            "variant_status": "COMPILED_SAFE_PIN_VARIANT",
            "physical_verification": "NOT_RUN",
        },
        {
            "signal": "HEAD1_SERVO",
            "source_constant": "HEAD1_SERVO_PIN",
            "mega_pin": f"D{pins['HEAD1_SERVO_PIN']}",
            "interface": "servo PWM",
            "variant_status": "COMPILED_SAFE_PIN_VARIANT",
            "physical_verification": "NOT_RUN",
        },
        {
            "signal": "HEAD2_SERVO",
            "source_constant": "HEAD2_SERVO_PIN",
            "mega_pin": f"D{pins['HEAD2_SERVO_PIN']}",
            "interface": "servo PWM",
            "variant_status": "COMPILED_SAFE_PIN_VARIANT",
            "physical_verification": "NOT_RUN",
        },
        {
            "signal": "HEAD3_SERVO",
            "source_constant": "HEAD3_SERVO_PIN",
            "mega_pin": f"D{pins['HEAD3_SERVO_PIN']}",
            "interface": "servo PWM",
            "variant_status": "COMPILED_SAFE_PIN_VARIANT",
            "physical_verification": "NOT_RUN",
        },
        {
            "signal": "USB_SERIAL_RX0",
            "source_constant": "Serial0 RX",
            "mega_pin": "D0/RX0",
            "interface": "USB configuration console",
            "variant_status": "RELEASED_FROM_SERVO_OUTPUT",
            "physical_verification": "NOT_RUN",
        },
        {
            "signal": "USB_SERIAL_TX0",
            "source_constant": "Serial0 TX",
            "mega_pin": "D1/TX0",
            "interface": "USB configuration console",
            "variant_status": "RELEASED_FROM_SERVO_OUTPUT",
            "physical_verification": "NOT_RUN",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build() -> dict[str, Any]:
    if not (REPO / ".git").is_dir():
        raise SystemExit(
            "FAIL missing gitignored upstream checkout; run tools/fetch_do_public_resources.sh"
        )
    commit = git("rev-parse", "HEAD")
    if commit != EXPECTED_COMMIT:
        raise SystemExit(f"FAIL unexpected upstream commit: {commit}")
    if git("status", "--porcelain"):
        raise SystemExit("FAIL upstream checkout is dirty")
    if not SOURCE.is_file() or not LICENSE_README.is_file():
        raise SystemExit("FAIL pinned source or licence README is missing")

    source_bytes = SOURCE.read_bytes()
    source_sha256 = sha256_bytes(source_bytes)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"FAIL unexpected upstream source SHA-256: {source_sha256}")
    source_text = source_bytes.decode("utf-8")
    transformed, transform_checks = transform_source(source_text)
    transformed_bytes = transformed.encode("utf-8")
    transformed_sha256 = sha256_bytes(transformed_bytes)

    STAGE.mkdir(parents=True, exist_ok=True)
    STAGED_SOURCE.write_bytes(transformed_bytes)
    shutil.copyfile(LICENSE_README, STAGE / "README.md")
    build_path = BUILD_ROOT / transformed_sha256[:16]
    build_path.mkdir(parents=True, exist_ok=True)

    command = [
        "arduino-cli",
        "compile",
        "--config-file",
        str(CONFIG),
        "--fqbn",
        FQBN,
        "--build-path",
        str(build_path),
        str(STAGE),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        raise SystemExit(f"FAIL Arduino compile\n{result.stdout}")
    memory = parse_compile_output(result.stdout)
    cli_version = subprocess.check_output(
        ["arduino-cli", "version"], text=True
    ).strip()

    write_wiring(WIRING, SAFE_SERVO_PINS)
    PUBLIC_WIRING.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WIRING, PUBLIC_WIRING)

    evidence = {
        "verified_at": date.today().isoformat(),
        "result": "PASS_COMPILE_ONLY_HOLD_PHYSICAL_CONTINUITY",
        "source": {
            "repository": "https://github.com/PrintedDroid/D-O-Printed-Droid.git",
            "commit": commit,
            "path": str(SOURCE_RELATIVE),
            "sha256": source_sha256,
            "licence_boundary": "custom personal non-commercial upstream terms; retain notice and attribution",
        },
        "variant": {
            "name": "v3.4.3 Mega safe servo pins D22-D25",
            "transformation_tool": "tools/build_do_safe_pin_variant.py",
            "transformed_source_sha256": transformed_sha256,
            "transformed_source_published": False,
            "binary_published": False,
            "wiring_contract": "engineering/do_safe_pin_variant_wiring.csv",
            **transform_checks,
        },
        "compile": {
            "fqbn": FQBN,
            "arduino_cli": cli_version,
            "platform": "arduino:avr@1.8.8",
            "libraries": {
                "IBusBM": "1.1.4",
                "DFRobotDFPlayerMini": "1.0.6",
                "Servo": "1.3.0",
            },
            **memory,
        },
        "release_boundary": {
            "physical_continuity_test": "NOT_RUN",
            "usb_upload_and_reset_test": "NOT_RUN",
            "serial0_9600_baud_menu_test": "NOT_RUN",
            "four_servo_pulse_test": "NOT_RUN",
            "failsafe_motion_test": "NOT_RUN",
            "actuator_power_release": False,
            "flash_release": False,
            "claim": "software transformation and compilation only; no powered hardware evidence",
        },
    }
    encoded = json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    EVIDENCE.write_text(encoded, encoding="utf-8")
    PUBLIC_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_EVIDENCE.write_text(encoded, encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    evidence = build()
    compile_data = evidence["compile"]
    print(
        f"{evidence['result']} "
        f"sha256={evidence['variant']['transformed_source_sha256']} "
        f"flash={compile_data['program_bytes']}B/{compile_data['program_percent']}% "
        f"ram={compile_data['global_ram_bytes']}B/{compile_data['global_ram_percent']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
