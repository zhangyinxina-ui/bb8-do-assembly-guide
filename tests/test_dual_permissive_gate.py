from __future__ import annotations

import copy
import csv
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
        self.assertEqual(
            result["manufacturing_release"],
            "NOT_RELEASED_PEER_REVIEW_GERBER_AND_PHYSICAL_VALIDATION_REQUIRED",
        )
        self.assertTrue(self.contract["freeze_gates"]["kicad_schematic_captured"])
        self.assertTrue(self.contract["freeze_gates"]["erc_passed"])
        self.assertTrue(self.contract["freeze_gates"]["kicad_netlist_cross_audited"])
        self.assertTrue(self.contract["freeze_gates"]["pcb_routed_and_drc_passed"])
        self.assertFalse(self.contract["freeze_gates"]["kicad_schematic_peer_reviewed"])
        self.assertFalse(
            self.contract["freeze_gates"]["gerber_and_drill_release_reviewed"]
        )
        self.assertFalse(result["timing_boundary"]["combined_deenergise_maximum_proven"])
        self.assertTrue(result["checks"]["six_unique_test_points_declared"])
        self.assertTrue(
            result["checks"]["installed_height_with_standoffs_within_stage18_keepout"]
        )
        self.assertEqual(result["computed"]["installed_height_margin_mm"], 0.6)

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

    def test_netlist_exposes_every_declared_test_point(self) -> None:
        with (ROOT / "engineering" / "stage19_gate_netlist.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        actual = {
            (row["reference"], row["net"])
            for row in rows
            if row["reference"].startswith("TP")
        }
        expected = {
            (item["reference"], item["net"])
            for item in self.contract["test_points"]
        }
        self.assertEqual(actual, expected)

    def test_reverse_clamp_diodes_use_kicad_device_d_pin_polarity(self) -> None:
        with (ROOT / "engineering" / "stage19_gate_netlist.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        diode_connections = {
            (row["reference"], row["pin"]): row["net"]
            for row in rows
            if row["reference"] in {"D1", "D2"}
        }
        self.assertEqual(
            diode_connections,
            {
                ("D1", "1"): "SAFE_A_LED_A",
                ("D1", "2"): "SAFE_A_RETURN",
                ("D2", "1"): "SAFE_B_LED_A",
                ("D2", "2"): "SAFE_B_RETURN",
            },
        )

    def test_formal_kicad_artifacts_pass_schematic_only_verification(self) -> None:
        evidence = json.loads(
            (ROOT / "engineering" / "stage19_kicad_verification.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(evidence["kicad_version"], "10.0.4")
        self.assertEqual(
            evidence["schematic_verification"],
            "PASS_SCHEMATIC_ERC_AND_NETLIST_ONLY",
        )
        self.assertEqual(
            evidence["overall"],
            "HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED",
        )
        self.assertTrue(all(evidence["checks"].values()))
        self.assertEqual(evidence["counts"]["erc_violations"], 0)
        self.assertEqual(evidence["counts"]["component_references"], 34)
        self.assertEqual(evidence["counts"]["canonical_pin_connections"], 91)
        self.assertEqual(evidence["counts"]["exported_nets"], 21)
        self.assertEqual(
            evidence["manufacturing_release"],
            "NOT_RELEASED_PEER_REVIEW_GERBER_AND_PHYSICAL_VALIDATION_REQUIRED",
        )

    def test_routed_pcb_is_reproducible_and_drc_clean_but_not_released(self) -> None:
        evidence = json.loads(
            (ROOT / "engineering" / "stage19_kicad_pcb_verification.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            evidence["pcb_verification"],
            "PASS_ROUTED_PCB_DRC_REFERENCE_DESIGN_ONLY",
        )
        self.assertEqual(
            evidence["overall"],
            "HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED",
        )
        self.assertTrue(all(evidence["checks"].values()))
        self.assertEqual(
            evidence["counts"],
            {
                "footprints": 38,
                "component_references": 34,
                "mounting_holes": 4,
                "canonical_pin_connections": 91,
                "named_nets": 21,
                "track_segments": 1614,
                "vias": 54,
                "zones": 2,
                "tracked_drc_violations": 0,
                "tracked_unconnected_items": 0,
                "generated_drc_violations": 0,
                "generated_unconnected_items": 0,
            },
        )
        self.assertEqual(evidence["board"]["width_mm"], 50.0)
        self.assertEqual(evidence["board"]["height_mm"], 35.0)
        self.assertEqual(evidence["board"]["copper_layers"], 2)
        expected_centres = {
            "H1": [3.0, 3.0],
            "H2": [47.0, 3.0],
            "H3": [3.0, 32.0],
            "H4": [47.0, 32.0],
        }
        self.assertEqual(
            {
                reference: hole["centre_from_board_origin_mm"]
                for reference, hole in evidence["board"]["mounting_holes"].items()
            },
            expected_centres,
        )
        self.assertTrue(
            all(
                hole["drill_mm"] == 3.2 and hole["non_plated"]
                for hole in evidence["board"]["mounting_holes"].values()
            )
        )
        self.assertEqual(
            evidence["manufacturing_release"],
            "NOT_RELEASED_PEER_REVIEW_GERBER_AND_PHYSICAL_VALIDATION_REQUIRED",
        )
        self.assertEqual(evidence["physical_test_status"], "NOT_RUN")

    def test_pre_cad_blender_geometry_cannot_enter_fabrication_exports(self) -> None:
        geometry = (ROOT / "blender" / "stage19_dual_permissive_gate_geometry.py").read_text(
            encoding="utf-8"
        )
        exporter = (ROOT / "blender" / "export_bb8.py").read_text(encoding="utf-8")
        manifest_exporter = (ROOT / "blender" / "export_internal_manifest.py").read_text(
            encoding="utf-8"
        )
        audit = (ROOT / "blender" / "audit_bb8.py").read_text(encoding="utf-8")

        self.assertIn('obj["non_fabrication_reference"] = True', geometry)
        self.assertIn('obj.get("non_fabrication_reference")', exporter)
        self.assertIn("export_extras=True", exporter)
        self.assertIn('not o.get("non_fabrication_reference")', manifest_exporter)
        self.assertIn("stage-19 expects the fabrication set to remain 150 objects", audit)
        self.assertIn("pre_cad_reference=", audit)

    def test_stage19_reopen_audit_preserves_the_fabrication_boundary(self) -> None:
        evidence = json.loads(
            (ROOT / "engineering" / "stage19_blender_reopen_audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(evidence["result"], "PASS_REOPEN_AUDIT_ONLY")
        self.assertEqual(evidence["engineering_stage"], 19)
        self.assertEqual(
            evidence["object_counts"],
            {
                "total": 386,
                "internal": 182,
                "fabrication": 150,
                "engineering_annotations": 9,
                "pre_cad_references": 23,
                "stage19_gate": 23,
                "internal_manifest_rows": 150,
            },
        )
        self.assertEqual(
            evidence["stage19_boundary"]["physical_test_status"], "NOT_RUN"
        )
        self.assertEqual(
            evidence["stage19_boundary"]["manufacturing_release"],
            "NOT_RELEASED_NO_KICAD_GERBER",
        )
        self.assertFalse(evidence["stage19_boundary"]["fabrication_export"])
        self.assertTrue(all(item["present"] for item in evidence["renders"]))
        self.assertTrue(all(item["present"] for item in evidence["exports"]))
        self.assertEqual(
            (ROOT / "public" / "downloads" / "stage19_blender_reopen_audit.json").read_bytes(),
            (ROOT / "engineering" / "stage19_blender_reopen_audit.json").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
