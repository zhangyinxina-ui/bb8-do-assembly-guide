#!/usr/bin/env python3
"""Audit the locally pinned Printed Droid D-O resources."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "third_party" / "D-O-Printed-Droid"
PUBLIC_RESOURCE_DIR = ROOT / "third_party" / "do_public_resources"
OUT = ROOT / "engineering" / "do_resource_manifest.json"
PUBLIC_OUT = ROOT / "public" / "downloads" / "do_resource_manifest.json"
AIO32_COMPILE_EVIDENCE = ROOT / "engineering" / "do_aio32_firmware_compile.json"
AIO32_PUBLIC_COMPILE_EVIDENCE = ROOT / "public" / "downloads" / "do_aio32_firmware_compile.json"

MECHANICAL_SUFFIXES = {".stl", ".step", ".stp", ".f3d", ".obj", ".3mf", ".scad"}
LICENSE_MARKER = "NON-COMMERCIAL LICENSE"
RECOMMENDED_SKETCH = "D-O_ibus_v3.4/D_O_printed_droid_rc_ibus_v3.4.3.ino"
EXPECTED_PINS = {
    "MAINBAR_SERVO_PIN": 0,
    "HEAD1_SERVO_PIN": 1,
    "HEAD2_SERVO_PIN": 5,
    "HEAD3_SERVO_PIN": 6,
}
EXPECTED_NUMERIC_SIGNAL_PINS = {
    "DIR1_PIN": 13,
    "PWM1_PIN": 12,
    "DIR2_PIN": 11,
    "PWM2_PIN": 10,
    "PWM_DRIVE1_PIN": 3,
    "PWM_DRIVE2_PIN": 4,
    "PWM_SOUND_CH1_PIN": 14,
    "PWM_SOUND_CH2_PIN": 15,
    "PWM_SOUND_CH3_PIN": 16,
    "PWM_SOUND_CH4_PIN": 17,
    **EXPECTED_PINS,
    "DFPLAYER_RX_PIN": 7,
    "DFPLAYER_TX_PIN": 8,
}
PUBLISHED_V21_PAGE_PINS = {
    "mainbar": 2,
    "head1": 3,
    "head2": 4,
    "head3": 5,
}
OFFICIAL_CONTROL_PAGE = "https://www.printed-droid.com/kb/d-o-control-and-power-board/"
PUBLIC_ATTACHMENT_SPECS = (
    {
        "name": "D-O_AIO32_v2_User_Handbook_v2.1.1.pdf",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2_User_Handbook_v2.1.1.pdf",
        "sha256": "44153b54a8d7a7f57adc8d02b961dc4547ce28f94810edc93c07a915e4ab07f8",
        "kind": "AIO32 English user handbook",
    },
    {
        "name": "D-O_AIO32_v2_User_Handbook_v2.1.1_DE.pdf",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2_User_Handbook_v2.1.1_DE.pdf",
        "sha256": "7a5f2ca961fef03a73f4af0800688025b1d81843a94d09a60f5681d311828ec3",
        "kind": "AIO32 German user handbook",
    },
    {
        "name": "D-O_AIO32_v2.1.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_AIO32_v2.1.zip",
        "sha256": "d873d673d42f6318f051afab0a146145324783d303a3a44f27ccdf604f7365dd",
        "kind": "experimental ESP32-S3 firmware source archive",
    },
    {
        "name": "D-O_Control__Power_Board_System_Documentation_v2.2.pdf",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Control__Power_Board_System_Documentation_v2.2.pdf",
        "sha256": "9f50880e6bf84bca5d970136bf026e9ff77d85b032e82c65e710a75a5f616c45",
        "kind": "Mega control and power board English handbook",
    },
    {
        "name": "D-O_Control__Power_Board_System_Documentation_v2.2_DE.pdf",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Control__Power_Board_System_Documentation_v2.2_DE.pdf",
        "sha256": "aa8f4b2e12e2284a75f3f55c2d3ae18771e23c54cbec130c892f76939ca4ace0",
        "kind": "Mega control and power board German handbook",
    },
    {
        "name": "D-O_ibus_v3.4.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_ibus_v3.4.zip",
        "sha256": "9e55e08d5b339690275b1714df292a2f0536c0303e6f58867ec5355dafcee478",
        "kind": "Mega v3.4.0 historical firmware archive",
    },
    {
        "name": "D-O_ibus_v2.1.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_ibus_v2.1.zip",
        "sha256": "4124593350b164e80e3d04d53bd8e550751cd57c8833922d9bc6a48406f7e4ad",
        "kind": "Mega v2.1 legacy firmware archive",
    },
    {
        "name": "D-O-AIO-1.4-v1.3.pdf",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/11/D-O-AIO-1.4-v1.3.pdf",
        "sha256": "ecf7700d3526041021215001aeccd95ed7be4b934458de4653469dba8c293fae",
        "kind": "legacy AIO wiring sheet",
    },
    {
        "name": "dov2_printed_droid_rc_ibus_v1.1.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/dov2_printed_droid_rc_ibus_v1.1.zip",
        "sha256": "13c08a4b16afe7084c75e32f3042994ecac3725dbdbe6f142f712f97f5f1a311",
        "kind": "Mega v1.1 legacy firmware archive",
    },
    {
        "name": "D_O_Nano_Sketch_v2.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D_O_Nano_Sketch_v2.zip",
        "sha256": "2ac4bfcee9f54182c65c803c09899c06620d9d2b4fb78ba9d9ac02f6502d219b",
        "kind": "Nano v2 legacy sound firmware archive",
    },
    {
        "name": "D-O_Nano_Sketch.zip",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/D-O_Nano_Sketch.zip",
        "sha256": "04fb652e1b055e888a4a9e3b212cc467b15a509c668e3d83142c635f970961e4",
        "kind": "Nano v1 legacy sound firmware archive",
    },
    {
        "name": "DO-Stand-60mm.stl",
        "url": "https://www.printed-droid.com/wp-content/uploads/2020/09/DO-Stand-60mm.stl",
        "sha256": "429cbcf27c94d840007da24ea2b297d22b6ac3a8bc4b79d90d6dd86d8724af57",
        "kind": "60 mm wheel-off test stand; not a complete droid model",
    },
)
SOURCE_SUFFIXES = {".ino", ".cpp", ".h", ".c", ".hpp"}
PCB_CAD_SUFFIXES = {".kicad_pro", ".kicad_sch", ".kicad_pcb", ".sch", ".brd", ".gbr"}
EXTERNAL_MODEL_CANDIDATES = (
    {
        "id": "DO-MODEL-001",
        "name": "Denton V1 D-O Droid (Based on Baddeley V1 Design)",
        "publisher": "mantisrobot / Thingiverse",
        "url": "https://www.thingiverse.com/thing:4189546",
        "checked_date": "2026-07-15",
        "availability": "free listing",
        "listing_license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "model_class": "functional mechanical WIP",
        "listing_evidence": [
            "description says the head is unfinished and currently missing",
            "description says STL files are provided for each subassembly",
            "description says 3D PDF assembly files are provided",
            "STEP files are promised after completion, not confirmed as present",
            "2021-11-30 note says XL330 neck and head brackets were added",
        ],
        "electronics_source_included": "not confirmed by the public listing",
        "archive_audit": "NOT_DOWNLOADED_OR_ENUMERATED",
        "provenance_boundary": "the listing says it is based on Michael Baddeley CAD sent directly to the publisher; authority to relicense the derived geometry was not independently verified",
        "status": "HOLD_INCOMPLETE_HEAD_ARCHIVE_AND_PROVENANCE_REVIEW",
        "self_build_use": "promising free functional reference, but not a verified complete build package",
    },
    {
        "id": "DO-MODEL-002",
        "name": "Star Wars D-O Droid",
        "publisher": "WF3D / Printables",
        "url": "https://www.printables.com/model/147063-star-wars-d-o-droid",
        "checked_date": "2026-07-15",
        "availability": "free listing",
        "listing_license": "CC BY-NC-SA 4.0",
        "license_evidence": "Printables GraphQL licence id 4 maps to CC-BY-NC-SA",
        "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "model_class": "static display model",
        "listing_evidence": [
            "about 300 mm total height",
            "32 model files",
            "split by colour for a 250 x 210 x 210 mm build volume",
            "requires only printed parts, filament strips and 6 mm black electrical wire",
            "publisher marks the model as an original creation",
        ],
        "electronics_source_included": False,
        "archive_audit": "LISTING_METADATA_ONLY",
        "status": "REFERENCE_STATIC_NOT_DRIVEABLE",
        "self_build_use": "appearance, colour separation and display-model reference only",
    },
    {
        "id": "DO-MODEL-003",
        "name": "D-O Droid - Star Wars Home Decor",
        "publisher": "CalebTimoteo / Printables",
        "url": "https://www.printables.com/model/1269542-d-o-droid-star-wars-home-decor",
        "checked_date": "2026-07-15",
        "availability": "free listing",
        "listing_license": "CC BY-NC 4.0",
        "license_evidence": "Printables GraphQL licence id 3 maps to CC-BY-NC",
        "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
        "model_class": "static home-decor WIP remix",
        "listing_evidence": [
            "11 model files",
            "description labels the model work in progress",
            "remix source is Thingiverse thing 4824097",
        ],
        "electronics_source_included": False,
        "archive_audit": "LISTING_METADATA_ONLY",
        "status": "REFERENCE_STATIC_WIP_NOT_DRIVEABLE",
        "self_build_use": "small static print reference only",
    },
    {
        "id": "DO-MODEL-004",
        "name": "D-O Droid - Star Wars Droid",
        "publisher": "JRIZZ / Cults",
        "url": "https://cults3d.com/en/3d-model/gadget/d-o-droid-star-wars-droid",
        "checked_date": "2026-07-15",
        "availability": "paid listing; USD 33.68 observed on the checked page",
        "listing_license": "CULTS - Private Use",
        "license_url": "https://cults3d.com/en/licenses",
        "model_class": "functional robot WIP",
        "listing_evidence": [
            "listing says the robot works but the design remains under development",
            "listing exposes a Fusion 360 main assembly F3Z",
            "listing exposes Arduino sketches for the droid and transmitter",
            "listing exposes printable STL parts and a separate main assembly STL",
            "hardware description names two Nano boards, an NRF24L01 pair, TB6612FNG, MPU6050, two geared DC motors and three servos",
        ],
        "electronics_source_included": True,
        "archive_audit": "NOT_ACQUIRED; PURCHASE_REQUIRES_EXPLICIT_USER_CONFIRMATION",
        "redistribution_boundary": "CULTS Private Use forbids public sharing, distribution and public derivative release of the digital model",
        "status": "PAID_PRIVATE_USE_NOT_ACQUIRED_OR_VERIFIED",
        "self_build_use": "closest discovered integrated moving candidate, but paid, private-use and not independently bench-verified",
    },
    {
        "id": "DO-MODEL-005",
        "name": "D-O Droid 3D Printing Model | Assembly + Action",
        "publisher": "Gambody",
        "url": "https://www.gambody.com/premium/d-o-droid",
        "checked_date": "2026-07-15",
        "availability": "paid listing",
        "listing_license": "Personal use",
        "model_class": "articulated display model with conversion space",
        "listing_evidence": [
            "116 STL files across all listed versions and updates",
            "life-size FFF/FDM version is listed as 518 x 190 x 393 mm",
            "head and antennas articulate",
            "engine and battery mockups may be replaced with real parts",
            "no controller source, balancing design or electrical package is listed",
        ],
        "electronics_source_included": False,
        "archive_audit": "NOT_ACQUIRED; PURCHASE_REQUIRES_EXPLICIT_USER_CONFIRMATION",
        "status": "PAID_ARTICULATED_MODEL_NOT_A_DRIVE_PACKAGE",
        "self_build_use": "articulation and full-scale appearance reference, not a proven self-balancing robot package",
    },
    {
        "id": "DO-MODEL-006",
        "name": "Star Wars D-O Droid",
        "publisher": "MakerWorld model 23859",
        "url": "https://makerworld.com/en/models/23859-star-wars-d-o-droid",
        "checked_date": "2026-07-15",
        "availability": "discovered listing; access blocked by Cloudflare during audit",
        "listing_license": "UNVERIFIED",
        "model_class": "UNVERIFIED",
        "listing_evidence": [],
        "electronics_source_included": "UNVERIFIED",
        "archive_audit": "NOT_RETRIEVED",
        "status": "DISCOVERED_LICENSE_AND_CONTENT_NOT_VERIFIED",
        "self_build_use": "do not rely on this candidate until its files, attribution and licence are verified",
    },
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_uint8_constant(source: str, name: str) -> int | None:
    match = re.search(rf"const\s+uint8_t\s+{re.escape(name)}\s*=\s*(\d+)\s*;", source)
    return int(match.group(1)) if match else None


def inspect_zip(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        members = sorted(info.filename for info in archive.infolist() if not info.is_dir())
        license_files = [
            member
            for member in members
            if Path(member).name.lower() in {"license", "license.md", "license.txt", "copying"}
        ]
        source_files = [member for member in members if Path(member).suffix.lower() in SOURCE_SUFFIXES]
        pcb_cad_files = [member for member in members if Path(member).suffix.lower() in PCB_CAD_SUFFIXES]
        mechanical_files = [member for member in members if Path(member).suffix.lower() in MECHANICAL_SUFFIXES]
        apache_marked_files = []
        for member in source_files:
            text = archive.read(member).decode("utf-8", errors="replace")
            if "Apache License 2.0" in text or "Apache 2.0" in text:
                apache_marked_files.append(member)
    return {
        "member_count": len(members),
        "members": members,
        "source_file_count": len(source_files),
        "source_files": source_files,
        "package_license_file_present": bool(license_files),
        "package_license_files": license_files,
        "apache_marked_source_files": apache_marked_files,
        "pcb_cad_file_count": len(pcb_cad_files),
        "pcb_cad_files": pcb_cad_files,
        "mechanical_file_count": len(mechanical_files),
        "mechanical_files": mechanical_files,
    }


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
    recommended_path = REPO / RECOMMENDED_SKETCH
    recommended_source = recommended_path.read_text(encoding="utf-8", errors="replace")
    servo_pins = {
        name: extract_uint8_constant(recommended_source, name)
        for name in EXPECTED_PINS
    }
    numeric_signal_pins = {
        name: extract_uint8_constant(recommended_source, name)
        for name in EXPECTED_NUMERIC_SIGNAL_PINS
    }
    serial0_console = "Serial.begin(9600);" in recommended_source
    servo_attach_calls = {
        "mainbar": "mainbarServo.attach(MAINBAR_SERVO_PIN);" in recommended_source,
        "head1": "head1Servo.attach(HEAD1_SERVO_PIN);" in recommended_source,
        "head2": "head2Servo.attach(HEAD2_SERVO_PIN);" in recommended_source,
        "head3": "head3Servo.attach(HEAD3_SERVO_PIN);" in recommended_source,
    }

    public_attachments = []
    for spec in PUBLIC_ATTACHMENT_SPECS:
        path = PUBLIC_RESOURCE_DIR / spec["name"]
        actual_sha256 = sha256(path) if path.is_file() else None
        public_attachments.append(
            {
                "name": spec["name"],
                "kind": spec["kind"],
                "url": spec["url"],
                "local_path": str(path.relative_to(ROOT)),
                "present": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else None,
                "sha256": actual_sha256,
                "expected_sha256_checked_2026_07_13": spec["sha256"],
                "hash_matches_checked_copy": actual_sha256 == spec["sha256"],
                "redistribution": "local reference only; not bundled into the public site because package-level redistribution terms are not explicit",
            }
        )

    aio32_path = PUBLIC_RESOURCE_DIR / "D-O_AIO32_v2.1.zip"
    aio32_archive = inspect_zip(aio32_path) if aio32_path.is_file() else None
    aio32_compile = (
        json.loads(AIO32_COMPILE_EVIDENCE.read_text(encoding="utf-8"))
        if AIO32_COMPILE_EVIDENCE.is_file()
        else None
    )
    ibus_attachment_path = PUBLIC_RESOURCE_DIR / "D-O_ibus_v3.4.zip"
    ibus_attachment = inspect_zip(ibus_attachment_path) if ibus_attachment_path.is_file() else None
    ibus_attachment_version = None
    if ibus_attachment_path.is_file():
        with zipfile.ZipFile(ibus_attachment_path) as archive:
            attachment_source = archive.read(
                "D_O_printed_droid_rc_ibus_v3.4.ino"
            ).decode("utf-8", errors="replace")
        match = re.search(r"\* VERSION:\s*([^\r\n]+)", attachment_source)
        ibus_attachment_version = match.group(1).strip() if match else None

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
        "audit_date": "2026-07-15",
        "repository": {
            "url": git("remote", "get-url", "origin"),
            "commit": git("rev-parse", "HEAD"),
            "commit_date": git("log", "-1", "--format=%cI"),
            "branch": git("branch", "--show-current"),
            "working_tree_clean": not bool(git("status", "--porcelain")),
            "upstream_main_head_checked_2026_07_15": "e90aacdbe26a62fd4f0229d5504a3f2f3c409055",
            "upstream_main_matched_local_on_check": True,
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
            "recommended_sha256": sha256(recommended_path),
            "sketch_count": len(sketches),
            "sketches": sketches,
            "target": "Arduino Mega 2560",
            "dependencies": ["IBusBM", "Servo", "EEPROM", "SoftwareSerial", "DFRobotDFPlayerMini", "Wire", "avr/wdt"],
            "pin_contract": {
                "servo_pins": servo_pins,
                "all_numeric_signal_pins": numeric_signal_pins,
                "battery_monitor_pin": "A15",
                "serial1_receiver_pin": "D19/RX1",
                "i2c_pins": {"sda": "D20", "scl": "D21"},
                "serial0_console_enabled": serial0_console,
                "serial0_baud": 9600,
                "servo_attach_calls_present": servo_attach_calls,
            },
            "versioned_wiring_contract": {
                "status": "HOLD_D0_D1_REMAP_AND_PHYSICAL_CONTINUITY",
                "source_path": RECOMMENDED_SKETCH,
                "source_commit": git("rev-parse", "HEAD"),
                "source_sha256": sha256(recommended_path),
                "compile_evidence_path": "engineering/do_firmware_compile.json",
                "compile_evidence_sha256": sha256(ROOT / "engineering" / "do_firmware_compile.json"),
                "generated_from_source_constants": True,
                "physical_continuity_test": "NOT_RUN",
                "actuator_power_release": False,
            },
        },
        "source_conflicts": [
            {
                "id": "DO-SRC-001",
                "status": "HOLD_BENCH_VERIFICATION",
                "issue": "v3.4.3 assigns two servo outputs to Mega D0/D1 while also enabling the Serial0 console",
                "source_evidence": {
                    "mainbar_servo_pin": servo_pins["MAINBAR_SERVO_PIN"],
                    "head1_servo_pin": servo_pins["HEAD1_SERVO_PIN"],
                    "serial_begin_present": serial0_console,
                    "all_four_servo_attach_calls_present": all(servo_attach_calls.values()),
                },
                "board_mapping": "Arduino Mega 2560 maps D0 to RX0 and D1 to TX0",
                "risk": "Servo signalling and the USB/Serial0 upload or configuration path contend for the same physical pins; neither function is accepted without bench evidence",
                "verification_gate": [
                    "do not connect servos to D0/D1 during first USB upload or Serial0 configuration",
                    "choose and document a non-UART servo pin remap or a verified hardware isolation/multiplexing design",
                    "capture oscilloscope or logic-analyser evidence for servo pulse width and Serial0 RX/TX integrity",
                    "repeat upload, reset, configuration-menu, four-servo motion and failsafe tests",
                ],
                "authoritative_pin_reference": "https://docs.arduino.cc/language-reference/en/functions/communication/serial/",
            },
            {
                "id": "DO-SRC-002",
                "status": "HOLD_VERSIONED_WIRING_REQUIRED",
                "issue": "the official control-page v2.1 wiring table publishes D2/D3/D4/D5 servo pins while pinned v3.4.3 source and the current GitHub README use D0/D1/D5/D6",
                "source_evidence": {
                    "official_page_section": "D-O Droid Control System v2.1 -> Mega to Servos",
                    "official_page_pins": PUBLISHED_V21_PAGE_PINS,
                    "pinned_v3_4_3_pins": servo_pins,
                },
                "risk": "combining the embedded v2.1 webpage wiring table with v3.4.3 firmware can put each servo signal on the wrong connector and hides the D0/D1 Serial0 contention",
                "verification_gate": [
                    "record the exact firmware filename and SHA-256 beside every generated wiring diagram",
                    "derive the harness from the compiled source constants rather than the generic webpage table",
                    "continuity-test all four servo signal nets before power is applied",
                    "retain DO-SRC-001 until D0/D1 are remapped or independently isolated and bench-verified",
                ],
                "official_control_page": OFFICIAL_CONTROL_PAGE,
            },
            {
                "id": "DO-SRC-003",
                "status": "USE_PINNED_GITHUB_V3_4_3",
                "issue": "the official D-O_ibus_v3.4.zip attachment contains v3.4.0 while the pinned GitHub repository contains the later v3.4.3 source",
                "source_evidence": {
                    "attachment_filename": "D-O_ibus_v3.4.zip",
                    "attachment_version_header": ibus_attachment_version,
                    "pinned_source": RECOMMENDED_SKETCH,
                    "pinned_source_version": "3.4.3",
                },
                "risk": "a patch-unspecific attachment filename can silently roll a builder back past later watchdog, receiver and channel-map fixes",
                "verification_gate": [
                    "use the pinned GitHub v3.4.3 source for the current Mega route",
                    "record the flashed source SHA-256 and compiler report",
                    "treat the website v3.4 ZIP as a historical reference rather than the recommended binary input",
                ],
                "official_control_page": OFFICIAL_CONTROL_PAGE,
            },
        ],
        "official_attachment_catalog": {
            "source_page": OFFICIAL_CONTROL_PAGE,
            "checked_date": "2026-07-13",
            "attachment_count": len(public_attachments),
            "local_directory": str(PUBLIC_RESOURCE_DIR.relative_to(ROOT)),
            "local_directory_gitignored": True,
            "items": public_attachments,
            "aio32_archive_audit": {
                **(aio32_archive or {}),
                "status": "HOLD_PACKAGE_LICENSE_AND_HARDWARE_CAD_NOT_FOUND",
                "classification": "publicly downloadable experimental source archive; not proven OSI open source as a complete package",
                "compile_status": aio32_compile["result"] if aio32_compile else "NOT_RUN",
                "compile_evidence_path": str(AIO32_COMPILE_EVIDENCE.relative_to(ROOT)),
                "compile_evidence_sha256": sha256(AIO32_COMPILE_EVIDENCE) if aio32_compile else None,
                "compile_target": aio32_compile["fqbn"] if aio32_compile else None,
                "compile_release_boundary": aio32_compile["release_boundary"] if aio32_compile else None,
                "compiler_discovered_dependency": (
                    aio32_compile["dependency_audit"]["compiler_discovered_dependency"]
                    if aio32_compile
                    else None
                ),
                "handbook_claim": "the AIO32 handbook says source and hardware KiCad files live in the shared GitHub repository",
                "observed_repository_aio32_files": 0,
                "observed_repository_pcb_cad_files": 0,
                "observed_attachment_pcb_cad_files": 0 if aio32_archive else None,
                "boundary": "file-level Apache markers do not license every file in the archive; no package LICENSE or KiCad/Gerber was found in the checked attachment",
            },
            "ibus_v3_4_attachment_audit": {
                **(ibus_attachment or {}),
                "version_header": ibus_attachment_version,
                "recommended_for_current_build": False,
                "replacement": RECOMMENDED_SKETCH,
            },
        },
        "mechanical_models": {
            "count": len(mechanical),
            "files": mechanical,
            "status": "absent from this repository" if not mechanical else "present",
        },
        "external_model_candidates": {
            "checked_date": "2026-07-15",
            "count": len(EXTERNAL_MODEL_CANDIDATES),
            "scope": "publicly indexed D-O model listings discovered during this audit; listing evidence does not substitute for archive, licence-provenance or physical validation",
            "items": list(EXTERNAL_MODEL_CANDIDATES),
            "integrated_open_package_status": "NOT_FOUND",
            "integrated_open_package_definition": "one package with complete mechanics, controller source, electrical design, explicit redistribution terms and repeatable physical validation",
        },
        "separate_public_model": {
            "path": "third_party/DO-Stand-60mm.stl",
            "purpose": "60 mm wheel-off electronics test stand; not a D-O body component",
            "license": "publicly downloadable but no explicit redistribution license found",
        },
        "reference_downloads": downloads,
        "conclusion": "Pinned Mega firmware and public reference documents support a personal non-commercial bench route. Free and paid external model candidates now have an explicit classification, but no single complete, openly redistributable and physically validated mechanics-plus-control-plus-electrical package was found.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    encoded_manifest = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    OUT.write_text(encoded_manifest, encoding="utf-8")
    PUBLIC_OUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUT.write_text(encoded_manifest, encoding="utf-8")

    failures = []
    if manifest["repository"]["url"] != "https://github.com/PrintedDroid/D-O-Printed-Droid.git":
        failures.append("unexpected origin")
    if not manifest["firmware"]["recommended_present"]:
        failures.append("recommended firmware missing")
    if servo_pins != EXPECTED_PINS:
        failures.append(f"unexpected servo pin contract: {servo_pins}")
    if numeric_signal_pins != EXPECTED_NUMERIC_SIGNAL_PINS:
        failures.append(f"unexpected numeric signal pin contract: {numeric_signal_pins}")
    if not serial0_console:
        failures.append("expected Serial0 console initialization missing")
    if not all(servo_attach_calls.values()):
        failures.append(f"servo attach call missing: {servo_attach_calls}")
    if len(licensed_readmes) != 3:
        failures.append(f"expected 3 licensed version READMEs, found {len(licensed_readmes)}")
    if mechanical:
        failures.append("unexpected mechanical CAD detected; review licensing before use")
    if len(EXTERNAL_MODEL_CANDIDATES) != 6:
        failures.append("unexpected external D-O model candidate count")
    if any(
        item["status"].startswith("REFERENCE_STATIC")
        and "static" not in item["model_class"]
        for item in EXTERNAL_MODEL_CANDIDATES
    ):
        failures.append("static D-O model classification is inconsistent")
    if any(
        item["listing_license"] == "UNVERIFIED"
        and not item["status"].startswith("DISCOVERED_")
        for item in EXTERNAL_MODEL_CANDIDATES
    ):
        failures.append("unverified D-O model is not held")
    if not all(item["present"] for item in downloads):
        failures.append("reference PDF missing")
    if len(public_attachments) != 12:
        failures.append(f"expected 12 official page attachments, found {len(public_attachments)}")
    if not all(item["present"] for item in public_attachments):
        failures.append("official page attachment missing; run tools/fetch_do_public_resources.sh")
    if not all(item["hash_matches_checked_copy"] for item in public_attachments):
        failures.append("official page attachment hash changed; review upstream before accepting")
    if aio32_archive is None or aio32_archive["member_count"] != 23:
        failures.append("unexpected AIO32 attachment inventory")
    elif aio32_archive["pcb_cad_file_count"] or aio32_archive["package_license_file_present"]:
        failures.append("AIO32 licence/CAD state changed; review before updating classification")
    if aio32_compile is None:
        failures.append("AIO32 compile evidence missing")
    else:
        expected_aio32_compile = {
            "result": "PASS_COMPILE_ONLY",
            "source_archive_sha256": PUBLIC_ATTACHMENT_SPECS[2]["sha256"],
            "platform": "esp32:esp32@3.3.7",
            "program_bytes": 549831,
            "global_ram_bytes": 49652,
        }
        observed_aio32_compile = {
            key: aio32_compile.get(key) for key in expected_aio32_compile
        }
        if observed_aio32_compile != expected_aio32_compile:
            failures.append(
                f"unexpected AIO32 compile evidence: {observed_aio32_compile}"
            )
        if aio32_compile.get("dependency_audit", {}).get(
            "compiler_discovered_dependency"
        ) != "SensorLib":
            failures.append("AIO32 compiler-discovered SensorLib dependency missing")
        if not AIO32_PUBLIC_COMPILE_EVIDENCE.is_file() or (
            AIO32_COMPILE_EVIDENCE.read_bytes()
            != AIO32_PUBLIC_COMPILE_EVIDENCE.read_bytes()
        ):
            failures.append("public AIO32 compile evidence is missing or stale")
    if ibus_attachment_version is None or not ibus_attachment_version.startswith("3.4.0"):
        failures.append(f"unexpected website v3.4 attachment version: {ibus_attachment_version}")

    if failures:
        raise SystemExit("FAIL " + "; ".join(failures))
    print(
        "PASS D-O RESOURCE AUDIT "
        f"commit={manifest['repository']['commit']} sketches={len(sketches)} "
        f"licensed_readmes={len(licensed_readmes)} mechanical_models={len(mechanical)} "
        f"source_conflicts={len(manifest['source_conflicts'])} "
        f"external_model_candidates={len(EXTERNAL_MODEL_CANDIDATES)} "
        f"official_attachments={len(public_attachments)} aio32_compile={aio32_compile['result']} "
        f"aio32_pcb_cad={aio32_archive['pcb_cad_file_count']}"
    )


if __name__ == "__main__":
    main()
