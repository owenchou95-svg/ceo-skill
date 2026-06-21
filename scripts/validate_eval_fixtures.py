#!/usr/bin/env python3
"""Validate structured CEO eval fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from contract_schema import load_contract_schema
from evaluate_ceo_output import expected_triage_for_request


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURES = REPO_ROOT / "references" / "eval-fixtures.json"


def validate_fixture_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    schema = load_contract_schema()
    valid_triage = {
        schema["triage"]["direct_label"],
        schema["triage"]["clarification_label"],
    }
    valid_modes = {"Task Mode", "Goal Mode"}
    valid_inventory_runs = {"Yes", "No"}
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        return ["fixtures must be a non-empty list"]

    seen_ids: set[str] = set()
    legacy_required_ids = {"DT-01", "DT-02", "DT-03", "DT-04", "DT-05", "DT-06", "DT-07", "DT-08"}
    for index, fixture in enumerate(fixtures):
        prefix = f"fixture[{index}]"
        fixture_id = fixture.get("id")
        if not fixture_id or fixture_id in seen_ids:
            failures.append(f"{prefix}: id must be present and unique")
        seen_ids.add(str(fixture_id))
        raw_request = fixture.get("rawRequest")
        if not isinstance(raw_request, str) or not raw_request.strip():
            failures.append(f"{prefix}: rawRequest must be non-empty")
            continue
        expected = fixture.get("expected")
        if not isinstance(expected, dict):
            failures.append(f"{prefix}: expected must be an object")
            continue
        mode = expected.get("mode")
        if mode is not None and mode not in valid_modes:
            failures.append(f"{prefix}: expected.mode must be one of {sorted(valid_modes)}")
        domain_gate = expected.get("domainGate")
        if domain_gate is not None and domain_gate not in {"Green", "Yellow", "Red"}:
            failures.append(f"{prefix}: expected.domainGate must be Green, Yellow, or Red")
        inventory_run = expected.get("inventoryRun")
        if inventory_run not in valid_inventory_runs:
            failures.append(f"{prefix}: expected.inventoryRun must be one of {sorted(valid_inventory_runs)}")
        triage = expected.get("triage")
        goal_status = expected.get("goalModeStatus")
        if mode == "Goal Mode":
            if goal_status not in {"Incomplete", "Complete", "Routed"}:
                failures.append(f"{prefix}: expected.goalModeStatus must be Incomplete, Complete, or Routed for Goal Mode")
            if goal_status in {"Complete", "Routed"} and domain_gate is None:
                failures.append(f"{prefix}: Goal Mode Complete/Routed fixtures must set expected.domainGate")
            if goal_status == "Complete" and domain_gate == "Red":
                failures.append(f"{prefix}: Goal Mode Complete fixtures cannot set expected.domainGate to Red")
            if goal_status == "Incomplete" and inventory_run != "No":
                failures.append(f"{prefix}: Goal Mode Incomplete fixtures must set expected.inventoryRun to No")
            if goal_status == "Complete" and inventory_run != "Yes":
                failures.append(f"{prefix}: Goal Mode Complete fixtures must set expected.inventoryRun to Yes")
            clarification_type = expected.get("clarificationType")
            if goal_status == "Complete" and clarification_type != "Not Required":
                failures.append(f"{prefix}: Goal Mode Complete fixtures must set expected.clarificationType to Not Required")
            if goal_status == "Routed":
                if clarification_type not in {"Discovery", "Risk Boundary"}:
                    failures.append(f"{prefix}: Goal Mode Routed fixtures must set expected.clarificationType to Discovery or Risk Boundary")
                if clarification_type == "Discovery" and inventory_run != "Yes":
                    failures.append(f"{prefix}: Discovery routed fixtures must set expected.inventoryRun to Yes")
                if expected.get("expectedRoute") != "Clarification":
                    failures.append(f"{prefix}: Goal Mode Routed fixtures must set expected.expectedRoute to Clarification")
            if triage is not None:
                failures.append(f"{prefix}: Goal Mode fixtures must not set expected.triage")
        else:
            if inventory_run != "Yes":
                failures.append(f"{prefix}: Task Mode fixtures must set expected.inventoryRun to Yes")
            if triage not in valid_triage:
                failures.append(f"{prefix}: expected.triage must be one of {sorted(valid_triage)}")
            computed = expected_triage_for_request(raw_request)["expected"]
            if triage != computed:
                failures.append(f"{prefix}: expected triage {triage!r} disagrees with evaluator {computed!r}")
        for key in ["requiredSkills", "forbiddenSkills"]:
            value = expected.get(key, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                failures.append(f"{prefix}: expected.{key} must be a list of strings")
    missing = sorted(legacy_required_ids - seen_ids)
    if missing:
        failures.append("missing required fixture ids: " + ", ".join(missing))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    failures = validate_fixture_payload(payload)
    if args.format == "json":
        print(json.dumps({"passed": not failures, "failures": failures}, indent=2, ensure_ascii=False))
    elif failures:
        print("Structured eval fixtures: FAIL")
        for failure in failures:
            print(f"- {failure}")
    else:
        print("Structured eval fixtures: PASS")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
