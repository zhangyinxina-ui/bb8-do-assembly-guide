import copy
import csv
import importlib.util
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_stage21_wheel_preload",
    ROOT / "tools" / "verify_stage21_wheel_preload.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Stage21WheelPreloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (ROOT / "engineering" / "stage21_wheel_preload_contract.json").read_text(encoding="utf-8")
        )
        with (ROOT / "engineering" / "internal_assembly_manifest.csv").open(
            newline="", encoding="utf-8-sig"
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.by_name = {row["object"]: row for row in cls.rows}

    def verify(self, contract=None, rows=None):
        active_contract = contract if contract is not None else self.contract
        active_rows = rows if rows is not None else self.rows
        return MODULE.verify(active_contract, active_rows, {row["object"]: row for row in active_rows})

    def test_nominal_contract_detects_old_contact_bug_and_holds_physical_release(self):
        result = self.verify()
        self.assertTrue(result["analytical_screen_passed"])
        self.assertEqual(
            result["overall"],
            "HOLD_PHYSICAL_CONTACT_BELT_BEARING_AND_CHASSIS_INTEGRATION_REQUIRED",
        )
        self.assertFalse(result["manufacturing_release"])
        self.assertEqual(result["physical_test_status"], "NOT_RUN")
        self.assertEqual(result["blender_application_status"], "NOT_APPLIED_USER_MASTER_PRESERVED")
        self.assertGreater(result["baseline_correction"]["minimum_exact_shell_gap_mm"], 5.0)
        self.assertGreater(result["baseline_correction"]["minimum_axis_to_tangent_error_deg"], 48.0)
        self.assertGreater(result["baseline_correction"]["minimum_legacy_support_overstatement_mm"], 5.0)
        self.assertEqual(len(result["unresolved_freeze_gates"]), 13)

    def test_selected_tangent_axis_and_crown_reach_nominal_shell(self):
        result = self.verify()
        contact = result["selected_contact_geometry"]
        radial = contact["right_radial_unit"]
        tangent = contact["right_tangent_axis_unit"]
        self.assertAlmostEqual(sum(a * b for a, b in zip(radial, tangent)), 0.0, places=8)
        self.assertAlmostEqual(contact["nominal_max_support_mm"], 254.0, places=3)
        self.assertGreater(contact["selected_crown_drop_mm"], contact["minimum_crown_drop_mm"])
        self.assertGreater(contact["edge_shell_clearance_mm"], 0.4)

    def test_belt_and_kinematic_contract_are_explicit(self):
        result = self.verify()
        belt = result["parallel_belt_drive"]
        calibration = result["kinematic_calibration_gate"]
        self.assertAlmostEqual(belt["calculated_belt_pitch_length_mm"], 280.0, places=6)
        self.assertEqual(belt["belt_teeth"], 56)
        self.assertGreater(belt["motor_shell_clearance_mm"], 90.0)
        self.assertAlmostEqual(calibration["nominal_wheel_center_track_mm"], 310.0, places=3)
        self.assertGreater(calibration["analytic_shell_contact_patch_track_mm"], 380.0)
        self.assertFalse(calibration["automatic_firmware_change_allowed"])

    def test_insufficient_crown_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["wheel"]["selected_crown_drop_at_edge_mm"] = 0.1
        result = self.verify(contract=contract)
        self.assertEqual(result["overall"], "FAIL_STAGE21_CONTACT_OR_PACKAGING_SCREEN")
        self.assertFalse(result["analytical_screen_passed"])

    def test_insufficient_travel_fails(self):
        contract = copy.deepcopy(self.contract)
        slide = contract["selected_architecture"]["radial_slide"]
        slide["total_usable_travel_mm"] = 5.0
        slide["outward_reserve_from_nominal_mm"] = 2.0
        slide["slot_overall_length_mm"] = 11.6
        result = self.verify(contract=contract)
        self.assertEqual(result["overall"], "FAIL_STAGE21_CONTACT_OR_PACKAGING_SCREEN")
        self.assertFalse(result["analytical_screen_passed"])

    def test_wrong_belt_length_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["parallel_belt_drive"]["candidate_belt_pitch_length_mm"] = 275.0
        result = self.verify(contract=contract)
        self.assertEqual(result["overall"], "FAIL_STAGE21_CONTACT_OR_PACKAGING_SCREEN")

    def test_missing_wheel_fails(self):
        rows = [row for row in self.rows if row["object"] != "Internal drive wheel R"]
        result = self.verify(rows=rows)
        self.assertEqual(result["overall"], "FAIL_STAGE21_CONTACT_OR_PACKAGING_SCREEN")
        self.assertFalse(result["analytical_screen_passed"])

    def test_finite_cylinder_support_matches_direct_geometry(self):
        center = (155.0, 0.0, -math.sqrt(206.0**2 - 155.0**2))
        support = MODULE.finite_cylinder_support_radius(center, (1.0, 0.0, 0.0), 48.0, 13.0)
        expected = math.hypot(168.0, abs(center[2]) + 48.0)
        self.assertAlmostEqual(support, expected, places=9)


if __name__ == "__main__":
    unittest.main()
