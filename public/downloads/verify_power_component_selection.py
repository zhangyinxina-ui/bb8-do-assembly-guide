#!/usr/bin/env python3
"""Evaluate Stage-17 drive-power candidates without claiming physical validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "engineering" / "power_component_candidates.json"
DEFAULT_OUTPUT = ROOT / "engineering" / "power_component_selection_results.json"


def ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise ValueError("ratio denominator must be positive")
    return numerator / denominator


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    req = data["system_requirements"]
    motor = data["motor_reference"]
    driver = data["motor_driver"]
    fuse = data["main_fuse"]
    contactor = data["main_contactor"]
    pack = data["battery_cell_and_pack"]
    bms = data["bms"]
    gates = data["freeze_gates"]

    peak_each = req["analytical_peak_total_current_a"] / req["motor_count"]
    checks = {
        "driver_channel_count": driver["channels"] >= req["minimum_driver_channels"],
        "driver_voltage_range": (
            driver["operating_voltage_min_v"] <= req["analytical_low_soc_peak_loaded_v"]
            and driver["operating_voltage_max_v"] >= req["bus_max_v"] * req["minimum_voltage_rating_margin"]
        ),
        "driver_continuous_current": (
            driver["continuous_current_each_a"]
            >= motor["rated_current_a"] * req["minimum_driver_continuous_margin_over_motor_rated"]
        ),
        "driver_peak_current": driver["peak_current_each_a"] >= peak_each,
        "driver_logic_3v3": driver["logic_high_min_v"] <= 3.3 <= driver["logic_high_max_v"],
        "fuse_voltage": fuse["voltage_rating_vdc"] >= req["bus_max_v"] * req["minimum_voltage_rating_margin"],
        "fuse_above_analytical_peak": fuse["provisional_rating_a"] > req["analytical_peak_total_current_a"],
        "contactor_voltage": (
            contactor["maximum_recommended_contact_voltage_vdc"]
            >= req["bus_max_v"] * req["minimum_voltage_rating_margin"]
        ),
        "contactor_continuous_current": (
            contactor["thermal_current_rating_a"] >= req["analytical_peak_total_current_a"]
        ),
        "contactor_breaking_current": (
            contactor["resistive_breaking_current_a_at_48v"] >= req["analytical_peak_total_current_a"]
        ),
        "contactor_auxiliary_feedback": contactor["auxiliary_contact_required"],
        "contactor_suppression_can_meet_contract": (
            contactor["typical_drop_out_ms_diode_resistor_max"]
            <= req["maximum_hardware_deenergise_ms"]
        ),
        "pack_series_and_voltage": (
            pack["series"] == req["battery_series_cells"]
            and pack["pack_charge_voltage_v"] == req["bus_max_v"]
        ),
        "pack_discharge_current": (
            pack["pack_theoretical_maximum_discharge_a"] >= req["analytical_peak_total_current_a"]
        ),
        "pack_charge_current": (
            pack["pack_theoretical_maximum_charge_a"] >= req["minimum_bms_regen_charge_a"]
        ),
    }

    unresolved = [name for name, complete in gates.items() if not complete]
    if driver["independent_enable_input"] is False:
        unresolved.append("driver_has_no_independent_enable_input")
    if driver["regenerative_energy_handling"] != "OFFICIALLY_DOCUMENTED_AND_VERIFIED":
        unresolved.append("driver_regenerative_energy_handling_not_frozen")
    if motor["stall_current_a"] is None:
        unresolved.append("motor_stall_current_not_published_or_measured")
    if bms["selected_candidate"] is None:
        unresolved.append("bms_candidate_not_selected")
    unresolved = sorted(set(unresolved))

    analytical_pass = all(checks.values())
    if not analytical_pass:
        overall = "HOLD_CANDIDATE_RATING_CHECK_FAILED"
    elif unresolved:
        overall = "HOLD_COMPONENT_FREEZE_MEASUREMENTS_REQUIRED"
    else:
        overall = "PASS_COMPONENT_FREEZE_ANALYTICAL_ONLY"

    margins = {
        "driver_continuous_over_motor_rated_x": ratio(
            driver["continuous_current_each_a"], motor["rated_current_a"]
        ),
        "driver_peak_over_analytical_peak_each_x": ratio(driver["peak_current_each_a"], peak_each),
        "driver_voltage_over_bus_max_x": ratio(driver["operating_voltage_max_v"], req["bus_max_v"]),
        "fuse_rating_over_analytical_peak_x": ratio(
            fuse["provisional_rating_a"], req["analytical_peak_total_current_a"]
        ),
        "fuse_voltage_over_bus_max_x": ratio(fuse["voltage_rating_vdc"], req["bus_max_v"]),
        "contactor_thermal_over_analytical_peak_x": ratio(
            contactor["thermal_current_rating_a"], req["analytical_peak_total_current_a"]
        ),
        "contactor_breaking_over_analytical_peak_x": ratio(
            contactor["resistive_breaking_current_a_at_48v"], req["analytical_peak_total_current_a"]
        ),
        "pack_discharge_over_analytical_peak_x": ratio(
            pack["pack_theoretical_maximum_discharge_a"], req["analytical_peak_total_current_a"]
        ),
        "pack_estimated_dc_resistance_ohm": pack["pack_estimated_dc_resistance_mohm"] / 1000.0,
    }

    return {
        "stage": data["stage"],
        "overall": overall,
        "analytical_candidate_checks_pass": analytical_pass,
        "evidence_boundary": data["evidence_boundary"],
        "checks": checks,
        "margins": margins,
        "unresolved_freeze_gates": unresolved,
        "selected_or_provisional": {
            "motor": motor["seller_part"],
            "driver": driver["candidate"],
            "fuse": f"{fuse['candidate_family']} {fuse['provisional_rating_a']:.0f}A provisional",
            "contactor": contactor["candidate_family"],
            "cell_pack": pack["pack_candidate"],
            "bms": bms["selected_candidate"],
        },
        "physical_test_status": "NOT_RUN",
        "purchase_authorisation": "NOT_GRANTED_BY_THIS_ANALYSIS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expect-overall")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate(data)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['overall']} analytical={result['analytical_candidate_checks_pass']} "
        f"unresolved={len(result['unresolved_freeze_gates'])}"
    )
    print("RESULTS", args.output)
    if args.expect_overall and result["overall"] != args.expect_overall:
        print(f"EXPECTED {args.expect_overall} GOT {result['overall']}")
        return 1
    return 0 if result["analytical_candidate_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
