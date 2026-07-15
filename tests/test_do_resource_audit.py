from __future__ import annotations

import csv
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DOResourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            ["python3", str(ROOT / "tools" / "audit_do_resources.py")],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        cls.manifest = json.loads(
            (ROOT / "engineering" / "do_resource_manifest.json").read_text(encoding="utf-8")
        )

    def test_serial0_servo_pin_contention_is_a_hold_gate(self) -> None:
        pin_contract = self.manifest["firmware"]["pin_contract"]
        self.assertEqual(pin_contract["servo_pins"]["MAINBAR_SERVO_PIN"], 0)
        self.assertEqual(pin_contract["servo_pins"]["HEAD1_SERVO_PIN"], 1)
        self.assertTrue(pin_contract["serial0_console_enabled"])
        self.assertTrue(all(pin_contract["servo_attach_calls_present"].values()))

        conflict = next(
            item for item in self.manifest["source_conflicts"] if item["id"] == "DO-SRC-001"
        )
        self.assertEqual(conflict["id"], "DO-SRC-001")
        self.assertEqual(conflict["status"], "HOLD_BENCH_VERIFICATION")
        self.assertIn("RX0", conflict["board_mapping"])
        self.assertIn("TX0", conflict["board_mapping"])

    def test_versioned_wiring_conflict_is_a_separate_hold_gate(self) -> None:
        conflicts = {item["id"]: item for item in self.manifest["source_conflicts"]}
        self.assertEqual(set(conflicts), {"DO-SRC-001", "DO-SRC-002", "DO-SRC-003"})
        mismatch = conflicts["DO-SRC-002"]
        self.assertEqual(mismatch["status"], "HOLD_VERSIONED_WIRING_REQUIRED")
        self.assertEqual(
            mismatch["source_evidence"]["official_page_pins"],
            {"mainbar": 2, "head1": 3, "head2": 4, "head3": 5},
        )
        self.assertEqual(
            mismatch["source_evidence"]["pinned_v3_4_3_pins"],
            {
                "MAINBAR_SERVO_PIN": 0,
                "HEAD1_SERVO_PIN": 1,
                "HEAD2_SERVO_PIN": 5,
                "HEAD3_SERVO_PIN": 6,
            },
        )
        stale_attachment = conflicts["DO-SRC-003"]
        self.assertEqual(stale_attachment["status"], "USE_PINNED_GITHUB_V3_4_3")
        self.assertTrue(
            stale_attachment["source_evidence"]["attachment_version_header"].startswith(
                "3.4.0"
            )
        )

        contract = self.manifest["firmware"]["versioned_wiring_contract"]
        self.assertEqual(
            contract["status"], "HOLD_D0_D1_REMAP_AND_PHYSICAL_CONTINUITY"
        )
        self.assertEqual(
            contract["source_sha256"], self.manifest["firmware"]["recommended_sha256"]
        )
        self.assertEqual(len(contract["source_sha256"]), 64)
        self.assertEqual(len(contract["compile_evidence_sha256"]), 64)
        self.assertTrue(contract["generated_from_source_constants"])
        self.assertEqual(contract["physical_continuity_test"], "NOT_RUN")
        self.assertFalse(contract["actuator_power_release"])

    def test_all_twelve_public_page_attachments_are_hashed_but_not_republished(self) -> None:
        catalog = self.manifest["official_attachment_catalog"]
        self.assertEqual(catalog["attachment_count"], 12)
        self.assertTrue(catalog["local_directory_gitignored"])
        self.assertTrue(all(item["present"] for item in catalog["items"]))
        self.assertTrue(all(item["hash_matches_checked_copy"] for item in catalog["items"]))
        self.assertTrue(
            all("not bundled into the public site" in item["redistribution"] for item in catalog["items"])
        )

        aio32 = catalog["aio32_archive_audit"]
        self.assertEqual(aio32["member_count"], 23)
        self.assertEqual(aio32["source_file_count"], 22)
        self.assertEqual(aio32["pcb_cad_file_count"], 0)
        self.assertEqual(aio32["mechanical_file_count"], 0)
        self.assertFalse(aio32["package_license_file_present"])
        self.assertEqual(
            aio32["status"], "HOLD_PACKAGE_LICENSE_AND_HARDWARE_CAD_NOT_FOUND"
        )
        self.assertEqual(aio32["compile_status"], "PASS_COMPILE_ONLY")
        self.assertEqual(aio32["compiler_discovered_dependency"], "SensorLib")
        self.assertEqual(len(aio32["compile_evidence_sha256"]), 64)

        compile_evidence = json.loads(
            (ROOT / "engineering" / "do_aio32_firmware_compile.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(compile_evidence["platform"], "esp32:esp32@3.3.7")
        self.assertEqual(compile_evidence["program_bytes"], 549831)
        self.assertEqual(compile_evidence["global_ram_bytes"], 49652)
        self.assertFalse(
            compile_evidence["dependency_audit"]["handbook_list_complete"]
        )
        self.assertEqual(
            compile_evidence["dependency_audit"]["missing_header_before_install"],
            "SensorQMI8658.hpp",
        )

    def test_procurement_bom_contains_26_gated_items(self) -> None:
        with (ROOT / "engineering" / "do_self_build_bom.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 26)
        serial_gate = next(row for row in rows if row["item_id"] == "D031")
        self.assertEqual(serial_gate["procurement_state"], "HOLD_BENCH_VERIFICATION")
        wiring_gate = next(row for row in rows if row["item_id"] == "D032")
        self.assertEqual(
            wiring_gate["procurement_state"], "HOLD_VERSIONED_WIRING_REQUIRED"
        )

    def test_mantis_playlist_descriptions_do_not_claim_a_source_release(self) -> None:
        mantis = json.loads(
            (ROOT / "engineering" / "do_mantis_video_audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(mantis["playlist"]["entry_count"], 6)
        self.assertEqual(len(mantis["entries"]), 6)
        self.assertEqual(
            {entry["id"] for entry in mantis["entries"]},
            {
                "zplirkxl6iM",
                "a1trQXC5bqI",
                "NxBvnvnvBc0",
                "DK3hTPibldo",
                "2cIdjQiS2ZE",
                "XyuE0PggtiE",
            },
        )
        findings = mantis["description_link_findings"]
        self.assertFalse(findings["direct_matt_modified_cad_download_found"])
        self.assertFalse(findings["direct_matt_control_source_download_found"])
        self.assertFalse(findings["github_gitlab_drive_dropbox_release_link_found"])

    def test_external_model_candidates_keep_functional_and_static_models_separate(self) -> None:
        catalog = self.manifest["external_model_candidates"]
        self.assertEqual(catalog["count"], 6)
        self.assertEqual(catalog["integrated_open_package_status"], "NOT_FOUND")
        candidates = {item["id"]: item for item in catalog["items"]}

        denton = candidates["DO-MODEL-001"]
        self.assertEqual(denton["listing_license"], "CC BY 4.0")
        self.assertIn("functional mechanical WIP", denton["model_class"])
        self.assertIn("INCOMPLETE_HEAD", denton["status"])
        self.assertEqual(denton["archive_audit"], "NOT_DOWNLOADED_OR_ENUMERATED")

        printables = candidates["DO-MODEL-002"]
        self.assertEqual(printables["listing_license"], "CC BY-NC-SA 4.0")
        self.assertEqual(printables["model_class"], "static display model")
        self.assertFalse(printables["electronics_source_included"])
        self.assertEqual(printables["status"], "REFERENCE_STATIC_NOT_DRIVEABLE")

        cults = candidates["DO-MODEL-004"]
        self.assertEqual(cults["listing_license"], "CULTS - Private Use")
        self.assertTrue(cults["electronics_source_included"])
        self.assertIn("PURCHASE_REQUIRES_EXPLICIT_USER_CONFIRMATION", cults["archive_audit"])
        self.assertIn("NOT_ACQUIRED", cults["status"])

        makerworld = candidates["DO-MODEL-006"]
        self.assertEqual(makerworld["listing_license"], "UNVERIFIED")
        self.assertTrue(makerworld["status"].startswith("DISCOVERED_"))

    def test_public_manifest_matches_engineering_manifest(self) -> None:
        self.assertEqual(
            (ROOT / "public" / "downloads" / "do_resource_manifest.json").read_bytes(),
            (ROOT / "engineering" / "do_resource_manifest.json").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "public" / "downloads" / "do_aio32_firmware_compile.json").read_bytes(),
            (ROOT / "engineering" / "do_aio32_firmware_compile.json").read_bytes(),
        )

    def test_public_downloads_match_the_canonical_do_documents(self) -> None:
        pairs = {
            ROOT / "docs" / "DO_资源审计与自组入口.md":
                ROOT / "public" / "downloads" / "DO_resource_audit.md",
            ROOT / "docs" / "DO_合法自组资源索引.md":
                ROOT / "public" / "downloads" / "DO_resources.md",
            ROOT / "docs" / "DO_自组采购与调试路线.md":
                ROOT / "public" / "downloads" / "DO_self_build_route.md",
            ROOT / "engineering" / "do_self_build_bom.csv":
                ROOT / "public" / "downloads" / "do_self_build_bom.csv",
            ROOT / "engineering" / "do_mantis_video_audit.json":
                ROOT / "public" / "downloads" / "do_mantis_video_audit.json",
        }
        for canonical, public_copy in pairs.items():
            with self.subTest(public_copy=public_copy.name):
                self.assertEqual(public_copy.read_bytes(), canonical.read_bytes())


if __name__ == "__main__":
    unittest.main()
