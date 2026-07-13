import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from verify_power_cassette_layout import verify


class PowerCassetteLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = json.loads((ROOT / "engineering" / "stage18_power_cassette_layout.json").read_text())
        cls.baseline = json.loads((ROOT / "engineering" / "stage18_layout_baseline.json").read_text())

    def test_current_layout_is_analytical_hold_not_physical_pass(self):
        result = verify(copy.deepcopy(self.layout), copy.deepcopy(self.baseline))
        self.assertEqual(result["overall"], "HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED")
        self.assertTrue(result["analytical_packaging_passed"])
        self.assertFalse(result["physical_fit_tested"])
        self.assertGreaterEqual(result["minimum_shell_clearance_mm"], 12.0)
        self.assertGreaterEqual(result["minimum_candidate_pair_clearance_mm"], 5.0)
        self.assertGreaterEqual(result["minimum_protected_hardware_clearance_mm"], 5.0)

    def test_shell_intrusion_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        next(item for item in layout["components"] if item["id"] == "FUS01")["centre_mm"][0] = 245.0
        result = verify(layout, copy.deepcopy(self.baseline))
        self.assertEqual(result["overall"], "FAIL_ANALYTICAL_PACKAGING")
        self.assertFalse(result["analytical_packaging_passed"])

    def test_motor_collision_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        driver = next(item for item in layout["components"] if item["id"] == "DRV01")
        driver["centre_mm"] = [72.4, 0.0, -135.687]
        result = verify(layout, copy.deepcopy(self.baseline))
        self.assertEqual(result["overall"], "FAIL_ANALYTICAL_PACKAGING")
        self.assertLess(result["minimum_protected_hardware_clearance_mm"], 0.0)

    def test_single_temperature_channel_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["bms_candidate"]["temperature_sensor_channels"] = 1
        result = verify(layout, copy.deepcopy(self.baseline))
        self.assertEqual(result["overall"], "FAIL_ANALYTICAL_PACKAGING")


if __name__ == "__main__":
    unittest.main()
