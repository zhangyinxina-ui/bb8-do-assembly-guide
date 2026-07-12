from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.parse_bb8_telemetry import parse_lines, parse_telemetry_line, summarise
from tools.verify_commissioning_evidence import evaluate


ROOT = Path(__file__).resolve().parents[1]


class TelemetryParserTests(unittest.TestCase):
    def test_parse_sample_and_summary(self) -> None:
        source = ROOT / "tests/fixtures/esp32_telemetry_sample.log"
        with source.open("r", encoding="utf-8") as handle:
            rows = parse_lines(handle)
        summary = summarise(rows, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(len(rows), 4)
        self.assertEqual(summary["duration_s"], 0.6)
        self.assertEqual(summary["enabled_samples"], 2)
        self.assertEqual(summary["fault_counts"], {"none": 3, "remote_timeout": 1})
        self.assertEqual(summary["remote_stale_samples"], 1)
        self.assertAlmostEqual(summary["maximum_abs_left_current_a"], 1.31)

    def test_missing_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing keys"):
            parse_telemetry_line("t_ms=1 enabled=0 fault=none")

    def test_non_monotonic_time_is_rejected(self) -> None:
        good = (ROOT / "tests/fixtures/esp32_telemetry_sample.log").read_text(encoding="utf-8").splitlines()
        telemetry = [line for line in good if line.startswith("t_ms=")]
        with self.assertRaisesRegex(ValueError, "increase strictly"):
            parse_lines([telemetry[1], telemetry[0]])


class CommissioningEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads((ROOT / "engineering/commissioning_test_plan.json").read_text(encoding="utf-8"))
        self.current = json.loads((ROOT / "engineering/commissioning_evidence.json").read_text(encoding="utf-8"))

    def test_current_real_hardware_state_is_honest_hold(self) -> None:
        result = evaluate(self.plan, self.current, ROOT)
        self.assertEqual(result["overall"], "HOLD_PHYSICAL_TESTS_NOT_RUN")
        self.assertEqual(result["mandatory_total"], 19)
        self.assertEqual(result["mandatory_passed"], 0)
        self.assertEqual(result["errors"], [])

    def test_forged_pass_without_files_is_invalid(self) -> None:
        forged = copy.deepcopy(self.current)
        forged["physical_origin"] = "REAL_HARDWARE"
        forged["physical_test_status"] = "PASS"
        forged["hardware_serial"] = "BB8-FORGED"
        forged["operator"] = "test"
        forged["test_date"] = "2026-07-12"
        for record in forged["records"]:
            record["status"] = "PASS"
            record["run_id"] = "forged"
        result = evaluate(self.plan, forged, ROOT)
        self.assertEqual(result["overall"], "INVALID_EVIDENCE")
        self.assertTrue(any("missing metric" in error for error in result["errors"]))
        self.assertTrue(any("evidence files" in error for error in result["errors"]))

    def test_synthetic_fixture_only_passes_when_explicitly_allowed(self) -> None:
        synthetic = copy.deepcopy(self.current)
        synthetic.update({
            "physical_origin": "SYNTHETIC_TEST_ONLY",
            "physical_test_status": "PASS",
            "hardware_serial": "SYNTHETIC",
            "operator": "unit-test",
            "test_date": "2026-07-12",
        })
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence_file = root / "synthetic.txt"
            evidence_file.write_text("synthetic verifier fixture\n", encoding="utf-8")
            digest = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
            tests = {test["id"]: test for test in self.plan["tests"]}
            for record in synthetic["records"]:
                test = tests[record["id"]]
                record["status"] = "PASS"
                record["run_id"] = f"synthetic-{record['id']}"
                metrics = {}
                for name, contract in test["required_metrics"].items():
                    if "equals" in contract:
                        value = contract["equals"]
                    elif "min" in contract and "max" in contract:
                        value = (contract["min"] + contract["max"]) / 2
                    elif "min" in contract:
                        value = contract["min"]
                    elif "max" in contract:
                        value = contract["max"]
                    else:
                        value = 1.0
                    metrics[name] = value
                record["metrics"] = metrics
                record["evidence"] = [
                    {
                        "kind": test["accepted_evidence_kinds"][0],
                        "path": "synthetic.txt",
                        "sha256": digest,
                    }
                    for _ in range(test["minimum_evidence_files"])
                ]
            rejected = evaluate(self.plan, synthetic, root)
            accepted = evaluate(self.plan, synthetic, root, allow_synthetic=True)
            self.assertEqual(rejected["overall"], "INVALID_EVIDENCE")
            self.assertEqual(accepted["overall"], "PASS_PHYSICAL_COMMISSIONING")
            self.assertEqual(accepted["mandatory_passed"], 19)


if __name__ == "__main__":
    unittest.main()
