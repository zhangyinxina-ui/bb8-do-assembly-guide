from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.verify_power_component_selection import evaluate


ROOT = Path(__file__).resolve().parents[1]


class PowerComponentSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(
            (ROOT / "engineering/power_component_candidates.json").read_text(encoding="utf-8")
        )

    def test_current_candidates_pass_rating_screen_but_remain_on_hold(self) -> None:
        result = evaluate(self.data)
        self.assertTrue(result["analytical_candidate_checks_pass"])
        self.assertEqual(result["overall"], "HOLD_COMPONENT_FREEZE_MEASUREMENTS_REQUIRED")
        self.assertIn("driver_has_no_independent_enable_input", result["unresolved_freeze_gates"])
        self.assertIn("bms_candidate_not_selected", result["unresolved_freeze_gates"])
        self.assertAlmostEqual(result["margins"]["driver_continuous_over_motor_rated_x"], 20 / 5.5)

    def test_underspecified_driver_is_rejected(self) -> None:
        bad = copy.deepcopy(self.data)
        bad["motor_driver"]["continuous_current_each_a"] = 7.0
        result = evaluate(bad)
        self.assertFalse(result["checks"]["driver_continuous_current"])
        self.assertEqual(result["overall"], "HOLD_CANDIDATE_RATING_CHECK_FAILED")

    def test_plain_flyback_diode_is_explicitly_slower_than_contract(self) -> None:
        contactor = self.data["main_contactor"]
        limit = self.data["system_requirements"]["maximum_hardware_deenergise_ms"]
        self.assertGreater(contactor["typical_drop_out_ms_diode_suppressed"], limit)
        self.assertLessEqual(contactor["typical_drop_out_ms_diode_resistor_max"], limit)


if __name__ == "__main__":
    unittest.main()
