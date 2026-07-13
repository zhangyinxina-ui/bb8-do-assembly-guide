#!/usr/bin/env python3
"""Verify the Stage-19 PWM gate contract without claiming a fabricated PCB."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "engineering" / "stage19_dual_permissive_gate_contract.json"
DEFAULT_OUTPUT = ROOT / "engineering" / "stage19_dual_permissive_gate_results.json"
DEFAULT_TRUTH_TABLE = ROOT / "engineering" / "stage19_gate_truth_table.csv"

INPUT_NAMES = (
    "logic_power_ok",
    "safe_a_ok",
    "safe_b_ok",
    "alert_n",
    "pwm_l_in",
    "pwm_r_in",
)


def gate_outputs(
    logic_power_ok: bool,
    safe_a_ok: bool,
    safe_b_ok: bool,
    alert_n: bool,
    pwm_l_in: bool,
    pwm_r_in: bool,
) -> tuple[bool, bool]:
    common_permissive = logic_power_ok and safe_a_ok and safe_b_ok and alert_n
    return pwm_l_in and common_permissive, pwm_r_in and common_permissive


def truth_rows() -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for values in itertools.product((0, 1), repeat=len(INPUT_NAMES)):
        inputs = dict(zip(INPUT_NAMES, values, strict=True))
        left, right = gate_outputs(*(bool(inputs[name]) for name in INPUT_NAMES))
        rows.append({**inputs, "pwm_l_out": int(left), "pwm_r_out": int(right)})
    return rows


def _all_blocked(rows: Iterable[dict[str, int]], input_name: str) -> bool:
    relevant = (row for row in rows if row[input_name] == 0)
    return all(row["pwm_l_out"] == 0 and row["pwm_r_out"] == 0 for row in relevant)


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    logic = data["logic_contract"]
    electrical = data["electrical_design"]
    board = data["board_envelope"]
    gates = data["freeze_gates"]
    rows = truth_rows()

    min_input_current_ma = (
        electrical["safe_input_voltage_min_v"]
        - electrical["opto_forward_voltage_max_v_at_60_ma"]
    ) / electrical["safe_input_resistor_ohm"] * 1000.0
    max_input_current_ma = (
        electrical["safe_input_voltage_max_v"]
        - electrical["opto_forward_voltage_min_v"]
    ) / electrical["safe_input_resistor_ohm"] * 1000.0
    resistor_worst_power_w = (
        electrical["safe_input_voltage_max_v"]
        - electrical["opto_forward_voltage_min_v"]
    ) ** 2 / electrical["safe_input_resistor_ohm"]
    resistor_derating_x = (
        electrical["safe_input_resistor_power_rating_w"] / resistor_worst_power_w
    )
    opto_high_min_v = (
        electrical["logic_supply_nominal_v"]
        - electrical["opto_vce_sat_max_v_at_5ma_1ma_25c"]
    )
    opto_emitter_load_ma = (
        opto_high_min_v / electrical["safe_ok_emitter_pulldown_ohm"] * 1000.0
    )
    cascaded_logic_tpd_max_ns = (
        3 * electrical["lvc_gate_tpd_max_ns_at_3v3_minus40_to_125c"]
    )

    expected_rows = 2 ** logic["truth_table_input_count"]
    checks = {
        "truth_table_row_count": len(rows) == expected_rows == logic["truth_table_expected_rows"],
        "truth_table_unique_inputs": len({tuple(row[name] for name in INPUT_NAMES) for row in rows}) == expected_rows,
        "equations_match_exhaustive_truth_table": all(
            row["pwm_l_out"] == (
                row["logic_power_ok"]
                & row["safe_a_ok"]
                & row["safe_b_ok"]
                & row["alert_n"]
                & row["pwm_l_in"]
            )
            and row["pwm_r_out"] == (
                row["logic_power_ok"]
                & row["safe_a_ok"]
                & row["safe_b_ok"]
                & row["alert_n"]
                & row["pwm_r_in"]
            )
            for row in rows
        ),
        "safe_a_loss_blocks_both_pwm": _all_blocked(rows, "safe_a_ok"),
        "safe_b_loss_blocks_both_pwm": _all_blocked(rows, "safe_b_ok"),
        "alert_assertion_blocks_both_pwm": _all_blocked(rows, "alert_n"),
        "logic_power_loss_blocks_both_pwm": _all_blocked(rows, "logic_power_ok"),
        "stuck_high_mcu_pwm_blocked_by_each_permissive": all(
            gate_outputs(*values) == (False, False)
            for values in (
                (True, False, True, True, True, True),
                (True, True, False, True, True, True),
                (True, True, True, False, True, True),
                (False, True, True, True, True, True),
            )
        ),
        "minimum_opto_input_current_reaches_ctr_test_point": min_input_current_ma >= 5.0,
        "maximum_opto_input_current_within_design_limit": max_input_current_ma <= 10.0,
        "input_resistor_power_derating_at_least_3x": resistor_derating_x >= 3.0,
        "opto_emitter_high_exceeds_lvc_vih": opto_high_min_v >= electrical["lvc_vih_min_v_at_3_to_3_6_v"],
        "opto_emitter_load_within_vcesat_test_current": opto_emitter_load_ma <= 1.0,
        "lvc_output_high_exceeds_mdd20a_3v3_compatibility": (
            electrical["lvc_voh_min_v_at_3_v_16_ma"] >= electrical["lvc_vih_min_v_at_3_to_3_6_v"]
            and 3.3 in electrical["mdd20a_compatible_logic_levels_v"]
        ),
        "board_xy_matches_stage18_keepout": board["length_mm"] <= 50.0 and board["width_mm"] <= 35.0,
        "assembled_height_within_stage18_keepout": board["maximum_assembled_height_mm"] <= board["stage18_keepout_height_mm"],
        "four_mount_holes_declared": len(board["mount_hole_centres_mm"]) == 4,
        "opto_switching_not_misrepresented_as_maximum": electrical["opto_switching_value_is_maximum_bound"] is False,
    }

    analytical_pass = all(checks.values())
    unresolved = sorted(name for name, complete in gates.items() if not complete)
    if not analytical_pass:
        overall = "HOLD_ANALYTICAL_GATE_CHECK_FAILED"
    elif unresolved:
        overall = data["status"]
    else:
        overall = "PASS_REFERENCE_DESIGN_ONLY_PHYSICAL_RELEASE_SEPARATE"

    return {
        "stage": data["stage"],
        "overall": overall,
        "release_class": data["release_class"],
        "analytical_checks_pass": analytical_pass,
        "evidence_boundary": data["evidence_boundary"],
        "checks": checks,
        "computed": {
            "truth_table_rows": len(rows),
            "minimum_safe_input_current_ma_at_12v": round(min_input_current_ma, 4),
            "maximum_safe_input_current_ma_at_16v8": round(max_input_current_ma, 4),
            "safe_input_resistor_worst_power_w": round(resistor_worst_power_w, 5),
            "safe_input_resistor_derating_x": round(resistor_derating_x, 3),
            "opto_emitter_high_min_v_at_25c_model": round(opto_high_min_v, 3),
            "opto_emitter_load_ma_at_25c_model": round(opto_emitter_load_ma, 4),
            "three_package_logic_tpd_max_ns": round(cascaded_logic_tpd_max_ns, 1),
            "assembled_height_margin_mm": round(
                board["stage18_keepout_height_mm"] - board["maximum_assembled_height_mm"], 3
            ),
        },
        "timing_boundary": {
            "logic_gate_chain_has_datasheet_maximum": True,
            "opto_saturated_turn_off_us_is_typical_only": electrical["opto_saturated_turn_off_typ_us_at_5ma"],
            "combined_deenergise_maximum_proven": False,
            "required_physical_limit_ms": data["system_context"]["maximum_pwm_gate_deenergise_ms"],
        },
        "unresolved_freeze_gates": unresolved,
        "physical_test_status": "NOT_RUN",
        "safety_certification": "NONE",
        "manufacturing_release": "NOT_RELEASED_NO_KICAD_GERBER",
        "purchase_authorisation": "NOT_GRANTED_BY_THIS_ANALYSIS",
    }


def write_truth_table(path: Path, rows: list[dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [*INPUT_NAMES, "pwm_l_out", "pwm_r_out"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--truth-table", type=Path, default=DEFAULT_TRUTH_TABLE)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_truth_table(args.truth_table, truth_rows())

    print(
        f"{result['overall']} analytical={result['analytical_checks_pass']} "
        f"truth_rows={result['computed']['truth_table_rows']} "
        f"physical={result['physical_test_status']}"
    )
    if args.expect_overall and result["overall"] != args.expect_overall:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
