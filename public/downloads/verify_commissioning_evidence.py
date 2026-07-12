#!/usr/bin/env python3
"""Validate Stage-16 physical commissioning evidence without inventing PASS results."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"NOT_RUN", "BLOCKED", "PASS", "FAIL"}
PLACEHOLDERS = {"", "UNASSIGNED", "NOT_RUN", "TBD"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top level must be an object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_evidence_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise ValueError("absolute evidence paths are forbidden")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("evidence path escapes the project root") from exc
    return resolved


def metric_error(name: str, value: Any, contract: dict[str, Any]) -> str | None:
    if "equals" in contract:
        if value != contract["equals"]:
            return f"{name}={value!r} does not equal {contract['equals']!r}"
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return f"{name} must be a finite number"
    if "min" in contract and value < contract["min"]:
        return f"{name}={value} is below {contract['min']} {contract.get('unit', '')}".rstrip()
    if "max" in contract and value > contract["max"]:
        return f"{name}={value} is above {contract['max']} {contract.get('unit', '')}".rstrip()
    return None


def evaluate(
    plan: dict[str, Any],
    evidence: dict[str, Any],
    root: Path,
    *,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if plan.get("schema_version") != 1 or evidence.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if plan.get("stage") != 16 or evidence.get("stage") != 16:
        errors.append("plan and evidence stage must both be 16")

    tests = plan.get("tests")
    records = evidence.get("records")
    if not isinstance(tests, list) or not isinstance(records, list):
        errors.append("tests and records must be arrays")
        tests = tests if isinstance(tests, list) else []
        records = records if isinstance(records, list) else []

    plan_by_id: dict[str, dict[str, Any]] = {}
    for test in tests:
        test_id = test.get("id") if isinstance(test, dict) else None
        if not isinstance(test_id, str) or not test_id:
            errors.append("every plan test requires a non-empty id")
        elif test_id in plan_by_id:
            errors.append(f"duplicate plan test id {test_id}")
        else:
            plan_by_id[test_id] = test

    records_by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        test_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(test_id, str) or not test_id:
            errors.append("every evidence record requires a non-empty id")
        elif test_id in records_by_id:
            errors.append(f"duplicate evidence record id {test_id}")
        else:
            records_by_id[test_id] = record

    missing = sorted(set(plan_by_id) - set(records_by_id))
    extra = sorted(set(records_by_id) - set(plan_by_id))
    if missing:
        errors.append(f"missing evidence records: {', '.join(missing)}")
    if extra:
        errors.append(f"unknown evidence records: {', '.join(extra)}")

    origin = evidence.get("physical_origin")
    if origin == "SYNTHETIC_TEST_ONLY" and not allow_synthetic:
        errors.append("synthetic evidence cannot certify physical hardware")
    if origin not in {"REAL_HARDWARE_REQUIRED", "REAL_HARDWARE", "SYNTHETIC_TEST_ONLY"}:
        errors.append("physical_origin is invalid")

    counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    verified_files: list[dict[str, str]] = []
    record_results: list[dict[str, Any]] = []

    for test_id, test in plan_by_id.items():
        record = records_by_id.get(test_id)
        if record is None:
            continue
        status = record.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{test_id}: invalid status {status!r}")
            continue
        counts[status] += 1
        record_errors: list[str] = []

        if status == "PASS":
            if origin not in {"REAL_HARDWARE", "SYNTHETIC_TEST_ONLY"}:
                record_errors.append("PASS requires physical_origin=REAL_HARDWARE")
            if record.get("run_id") in PLACEHOLDERS:
                record_errors.append("PASS requires a non-placeholder run_id")

            metrics = record.get("metrics")
            if not isinstance(metrics, dict):
                record_errors.append("PASS metrics must be an object")
                metrics = {}
            required_metrics = test.get("required_metrics", {})
            if not isinstance(required_metrics, dict):
                record_errors.append("plan required_metrics must be an object")
                required_metrics = {}
            for name, contract in required_metrics.items():
                if name not in metrics:
                    record_errors.append(f"missing metric {name}")
                    continue
                failure = metric_error(name, metrics[name], contract)
                if failure:
                    record_errors.append(failure)

            files = record.get("evidence")
            if not isinstance(files, list):
                record_errors.append("PASS evidence must be an array")
                files = []
            minimum = test.get("minimum_evidence_files", 1)
            if len(files) < minimum:
                record_errors.append(f"requires at least {minimum} evidence files")
            accepted_kinds = set(test.get("accepted_evidence_kinds", []))
            for index, item in enumerate(files):
                prefix = f"evidence[{index}]"
                if not isinstance(item, dict):
                    record_errors.append(f"{prefix} must be an object")
                    continue
                kind = item.get("kind")
                path_text = item.get("path")
                claimed_hash = item.get("sha256")
                if kind not in accepted_kinds:
                    record_errors.append(f"{prefix} kind {kind!r} is not accepted")
                if not isinstance(path_text, str) or not path_text:
                    record_errors.append(f"{prefix} requires path")
                    continue
                if not isinstance(claimed_hash, str) or len(claimed_hash) != 64:
                    record_errors.append(f"{prefix} requires a 64-character sha256")
                    continue
                try:
                    file_path = safe_evidence_path(root, path_text)
                except ValueError as exc:
                    record_errors.append(f"{prefix}: {exc}")
                    continue
                if not file_path.is_file():
                    record_errors.append(f"{prefix} file does not exist: {path_text}")
                    continue
                actual_hash = sha256(file_path)
                if actual_hash != claimed_hash.lower():
                    record_errors.append(f"{prefix} sha256 mismatch")
                    continue
                verified_files.append({"test_id": test_id, "path": path_text, "sha256": actual_hash})

        if status == "FAIL" and not record.get("notes"):
            warnings.append(f"{test_id}: FAIL should include failure notes")
        if record_errors:
            errors.extend(f"{test_id}: {message}" for message in record_errors)
        record_results.append({"id": test_id, "status": status, "valid": not record_errors})

    mandatory_ids = {test_id for test_id, test in plan_by_id.items() if test.get("mandatory") is True}
    mandatory_passed = {
        result["id"]
        for result in record_results
        if result["id"] in mandatory_ids and result["status"] == "PASS" and result["valid"]
    }
    header_ready = all(evidence.get(field) not in PLACEHOLDERS for field in ("hardware_serial", "operator", "test_date"))
    if errors:
        overall = "INVALID_EVIDENCE"
    elif counts["FAIL"]:
        overall = "FAIL_PHYSICAL_TESTS"
    elif mandatory_passed == mandatory_ids and header_ready and origin in {"REAL_HARDWARE", "SYNTHETIC_TEST_ONLY"}:
        overall = "PASS_PHYSICAL_COMMISSIONING"
    else:
        overall = "HOLD_PHYSICAL_TESTS_NOT_RUN"

    declared = evidence.get("physical_test_status")
    expected_declared = {
        "PASS_PHYSICAL_COMMISSIONING": "PASS",
        "FAIL_PHYSICAL_TESTS": "FAIL",
        "HOLD_PHYSICAL_TESTS_NOT_RUN": "NOT_RUN",
    }.get(overall)
    if expected_declared is not None and declared != expected_declared:
        errors.append(f"physical_test_status={declared!r} must be {expected_declared!r} for {overall}")
        overall = "INVALID_EVIDENCE"

    return {
        "schema_version": 1,
        "stage": 16,
        "overall": overall,
        "physical_origin": origin,
        "mandatory_total": len(mandatory_ids),
        "mandatory_passed": len(mandatory_passed),
        "counts": counts,
        "verified_evidence_files": verified_files,
        "records": record_results,
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=Path("engineering/commissioning_test_plan.json"))
    parser.add_argument("--evidence", type=Path, default=Path("engineering/commissioning_evidence.json"))
    parser.add_argument("--output", type=Path, default=Path("engineering/commissioning_results.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--expect-overall")
    parser.add_argument("--allow-synthetic", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = evaluate(
            load_json(args.plan),
            load_json(args.evidence),
            args.root,
            allow_synthetic=args.allow_synthetic,
        )
        result["plan_sha256"] = sha256(args.plan)
        result["evidence_sha256"] = sha256(args.evidence)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR commissioning evidence: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.quiet:
        print(
            f"{result['overall']} stage=16 mandatory={result['mandatory_passed']}/{result['mandatory_total']} "
            f"pass={result['counts']['PASS']} fail={result['counts']['FAIL']} "
            f"blocked={result['counts']['BLOCKED']} not_run={result['counts']['NOT_RUN']}"
        )
        for error in result["errors"]:
            print(f"ERROR {error}")

    if result["overall"] == "INVALID_EVIDENCE":
        return 1
    if args.expect_overall and result["overall"] != args.expect_overall:
        print(f"ERROR expected {args.expect_overall}, got {result['overall']}", file=sys.stderr)
        return 3
    if args.require_pass and result["overall"] != "PASS_PHYSICAL_COMMISSIONING":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
