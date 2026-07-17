import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_stage22_drivetrain_interface",
    ROOT / "tools" / "verify_stage22_drivetrain_interface.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Stage22DrivetrainInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (ROOT / "engineering" / "stage22_drivetrain_interface_contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.stage21_contract = json.loads(
            (ROOT / "engineering" / "stage21_wheel_preload_contract.json").read_text(
                encoding="utf-8"
            )
        )
        cls.stage21_results = json.loads(
            (ROOT / "engineering" / "stage21_wheel_preload_results.json").read_text(
                encoding="utf-8"
            )
        )

    def verify(self, contract=None):
        return MODULE.verify(
            contract if contract is not None else self.contract,
            self.stage21_contract,
            self.stage21_results,
        )

    def test_nominal_screen_passes_analytically_and_holds_physical_release(self):
        result = self.verify()
        self.assertTrue(result["analytical_screen_passed"])
        self.assertEqual(
            result["overall"],
            "HOLD_SUPPLIER_FITS_TENSION_TORQUE_PROOF_AND_PHYSICAL_INTEGRATION_REQUIRED",
        )
        self.assertFalse(result["manufacturing_release"])
        self.assertEqual(result["physical_test_status"], "NOT_RUN")
        self.assertEqual(
            result["blender_application_status"],
            "NOT_APPLIED_USER_MASTER_PRESERVED",
        )
        self.assertEqual(len(result["unresolved_freeze_gates"]), 13)

    def test_catalog_correction_selects_300mm_60tooth_belt_at_90mm_centres(self):
        result = self.verify()
        correction = result["catalog_correction"]
        belt = result["belt_geometry"]
        self.assertFalse(correction["stage21_candidate_in_official_stock_list"])
        self.assertEqual(correction["selected_part"], "5MGT-300-15")
        self.assertEqual(correction["selected_product_number"], "92706002")
        self.assertEqual(correction["selected_teeth"], 60)
        self.assertAlmostEqual(belt["nominal_center_distance_mm"], 90.0, places=6)
        self.assertAlmostEqual(belt["calculated_pitch_length_mm"], 300.0, places=6)

    def test_undersized_pulley_fails(self):
        contract = copy.deepcopy(self.contract)
        belt = contract["selected_architecture"]["belt_drive"]
        belt["pulley_teeth_motor"] = 16
        belt["pulley_teeth_wheel"] = 16
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_historical_280mm_belt_selection_fails(self):
        contract = copy.deepcopy(self.contract)
        belt = contract["selected_architecture"]["belt_drive"]
        belt["selected_belt_part"] = "5M-280-15"
        belt["pitch_length_mm"] = 280.0
        belt["teeth"] = 56
        belt["nominal_axis_center_distance_mm"] = 80.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_bearing_rating_below_reference_floor_fails(self):
        contract = copy.deepcopy(self.contract)
        bearings = contract["selected_architecture"]["bearing_stack"]
        bearings["minimum_dynamic_rating_n"] = 1000.0
        bearings["minimum_static_rating_n"] = 600.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_excessive_pulley_overhang_fails_bearing_or_shaft_screen(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["bearing_stack"][
            "pulley_overhang_from_outboard_bearing_mm"
        ] = 150.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_unacceptably_weak_shaft_material_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["shaft_and_hubs"][
            "minimum_certified_shaft_yield_mpa"
        ] = 100.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_short_key_engagement_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["shaft_and_hubs"][
            "minimum_key_engagement_mm"
        ] = 2.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_invalid_dowel_edge_distance_fails_without_division_by_zero(self):
        contract = copy.deepcopy(self.contract)
        interface = contract["selected_architecture"]["rail_interface"]
        interface["minimum_dowel_edge_distance_mm"] = 3.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")
        self.assertEqual(result["rail_interface_screen"]["plate_tearout_mpa"], float("inf"))

    def test_single_dowel_does_not_form_positive_interface_load_path(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["rail_interface"][
            "dowel_pins_per_cassette"
        ] = 1
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_insufficient_tension_adjustment_fails(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["belt_drive"][
            "motor_mount_tension_adjustment_total_mm"
        ] = 0.5
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")

    def test_oversized_motor_package_fails_shell_clearance(self):
        contract = copy.deepcopy(self.contract)
        contract["selected_architecture"]["packaging"][
            "motor_envelope_diameter_mm"
        ] = 500.0
        result = self.verify(contract)
        self.assertEqual(result["overall"], "FAIL_STAGE22_DRIVETRAIN_INTERFACE_SCREEN")


if __name__ == "__main__":
    unittest.main()
