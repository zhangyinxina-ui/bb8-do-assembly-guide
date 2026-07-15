import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_stage20_structural_load_path import read_manifest, verify


ROOT = Path(__file__).resolve().parents[1]


class Stage20StructuralLoadPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "engineering" / "stage20_structural_load_contract.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((ROOT / "engineering" / "stage19_blender_reopen_audit.json").read_text(encoding="utf-8"))
        cls.legacy = json.loads((ROOT / "engineering" / "physics_inputs.json").read_text(encoding="utf-8"))
        cls.rows, cls.by_name = read_manifest(ROOT / "engineering" / "internal_assembly_manifest.csv")

    def test_current_contract_is_analytical_hold(self):
        result = verify(self.contract, self.rows, self.by_name, self.audit, self.legacy)
        self.assertEqual(result["overall"], "HOLD_JOINT_TOLERANCE_MATERIAL_AND_PHYSICAL_VALIDATION_REQUIRED")
        self.assertTrue(result["analytical_screen_passed"])
        self.assertTrue(result["legacy_mismatch"]["detected"])
        self.assertFalse(result["tolerance_gate"]["passed"])
        self.assertEqual(result["tolerance_gate"]["adjustment_shortfall_mm"], 5.5)
        self.assertEqual(len(result["unresolved_freeze_gates"]), 15)

    def test_manifest_dimension_drift_fails(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            if row["object"] == "Internal magnetic mast":
                row["size_x_mm"] = "12.0"
                break
        by_name = {row["object"]: row for row in rows}
        result = verify(self.contract, rows, by_name, self.audit, self.legacy)
        self.assertEqual(result["overall"], "FAIL_ANALYTICAL_STRUCTURE")
        self.assertFalse(result["analytical_screen_passed"])

    def test_legacy_mismatch_must_be_detected(self):
        legacy = copy.deepcopy(self.legacy)
        legacy["mast_outer_diameter_m"] = 0.024
        legacy["mast_length_m"] = 0.340
        result = verify(self.contract, self.rows, self.by_name, self.audit, legacy)
        self.assertEqual(result["overall"], "FAIL_ANALYTICAL_STRUCTURE")
        self.assertFalse(result["legacy_mismatch"]["detected"])


if __name__ == "__main__":
    unittest.main()
