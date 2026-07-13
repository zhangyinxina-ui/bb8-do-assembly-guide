from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.verify_dual_permissive_gate import evaluate, gate_outputs, truth_rows

ROOT = Path(__file__).resolve().parents[1]


class DualPermissiveGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "engineering" / "stage19_dual_permissive_gate_contract.json").read_text(
                encoding="utf-8"
            )
        )

    def test_reference_design_passes_all_analytical_checks_but_stays_hold(self) -> None:
        result = evaluate(self.contract)
        self.assertTrue(result["analytical_checks_pass"])
        self.assertEqual(
            result["overall"], "HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED"
        )
        self.assertEqual(result["physical_test_status"], "NOT_RUN")
        self.assertEqual(result["manufacturing_release"], "NOT_RELEASED_NO_KICAD_GERBER")
        self.assertFalse(result["timing_boundary"]["combined_deenergise_maximum_proven"])

    def test_truth_table_is_exhaustive_and_unique(self) -> None:
        rows = truth_rows()
        self.assertEqual(len(rows), 64)
        self.assertEqual(
            len(
                {
                    tuple(row[name] for name in (
                        "logic_power_ok",
                        "safe_a_ok",
                        "safe_b_ok",
                        "alert_n",
                        "pwm_l_in",
                        "pwm_r_in",
                    ))
                    for row in rows
                }
            ),
            64,
        )

    def test_each_permissive_independently_blocks_stuck_high_pwm(self) -> None:
        self.assertEqual(gate_outputs(True, False, True, True, True, True), (False, False))
        self.assertEqual(gate_outputs(True, True, False, True, True, True), (False, False))
        self.assertEqual(gate_outputs(True, True, True, False, True, True), (False, False))
        self.assertEqual(gate_outputs(False, True, True, True, True, True), (False, False))
        self.assertEqual(gate_outputs(True, True, True, True, True, True), (True, True))

    def test_underdriven_opto_input_fails_analytical_gate(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["electrical_design"]["safe_input_resistor_ohm"] = 10000.0
        result = evaluate(mutated)
        self.assertFalse(result["analytical_checks_pass"])
        self.assertEqual(result["overall"], "HOLD_ANALYTICAL_GATE_CHECK_FAILED")
        self.assertFalse(
            result["checks"]["minimum_opto_input_current_reaches_ctr_test_point"]
        )


if __name__ == "__main__":
    unittest.main()
