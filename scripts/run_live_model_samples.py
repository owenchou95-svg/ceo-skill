#!/usr/bin/env python3
"""Run or evaluate minimal live-model CEO output samples."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import evaluate_ceo_output as evaluator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = REPO_ROOT / "evals" / "live-model" / "cases.jsonl"
GENERATED_ROOT = REPO_ROOT / "evals" / "live-model" / "generated"
RESULTS_ROOT = REPO_ROOT / "evals" / "live-model" / "results"


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fixture_output(case: dict[str, Any]) -> str:
    if case["expected_triage"] == "Clarification Path":
        selected = "$office-hours"
        skill_match = "- Strong match: use `$office-hours` for requirements clarification before implementation."
        prompt_objective = "Clarify the request enough for `$ceo` to produce a safe executable prompt."
        requirements = (
            "- Inputs: the user's raw request and any additional context they provide.\n"
            "- In scope: clarify goal, deliverables, in-scope/out-of-scope boundaries, inputs/context, decision boundaries, constraints, acceptance criteria, risks, and open questions.\n"
            "- Out of scope / non-goals: do not implement, deploy, delete data, choose a final route, or fabricate missing authority.\n"
            "- Deliverables: a `## Clarified Spec` handoff for `$ceo`.\n"
            "- Constraints: keep missing material choices explicit and mark unresolved fields as blocking.\n"
            "- Assumptions and boundaries:\n"
            "  - Assumption: material inputs are missing.\n"
            "    Boundary: clarify only and return to `$ceo` before execution.\n"
            "    Risk: direct execution would invent unsafe requirements.\n"
            "    Reversibility: clean.\n"
            "- Failure / escalation conditions: stop if required fields remain unknown and mark them `Unknown and blocking`."
        )
        output_format = "Return `## Clarified Spec` with Goal, Deliverables, In Scope, Out of Scope / Non-goals, Inputs / Context, Decision Boundaries, Constraints, Acceptance Criteria, Risks and Reversibility, Open Questions, CEO Handoff Summary, and readiness for `$ceo`."
    else:
        selected = "$frontend-skill, $playwright"
        skill_match = "- Strong match: use `$frontend-skill` for implementation when available.\n- Supporting match: use `$playwright` for browser validation when available."
        prompt_objective = "Turn the clarified request into a scoped executable implementation brief."
        requirements = (
            "- Inputs: the current workspace, raw request, and existing project structure.\n"
            "- In scope: inspect context, implement the requested scoped change, preserve non-goals, and verify the main workflow.\n"
            "- Out of scope / non-goals: unrelated refactors, deployments, payments, production data changes, and invented requirements.\n"
            "- Deliverables: code or documentation changes plus a verification report with file paths and command evidence.\n"
            "- Constraints: reuse existing patterns and dependencies unless evidence proves otherwise.\n"
            "- Assumptions and boundaries:\n"
            "  - Assumption: the workspace contains the target artifact.\n"
            "    Boundary: inspect before editing and stop if the target is absent.\n"
            "    Risk: editing the wrong file would create unrelated churn.\n"
            "    Reversibility: clean.\n"
            "- Failure / escalation conditions: stop and report blockers if target files, authority, or validation commands are missing."
        )
        output_format = "Return Changed files, Implemented behavior, Verification commands, Evidence, Known gaps, and Follow-up risks."
    return f"""## Triage
{case['expected_triage']} - generated fixture sample for {case['id']}.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: ideation
- Capability hints: build
- Validation hints: browser-validation

### Candidates
1. `$office-hours` (`office-hours`) score=30 path=/tmp/office-hours/SKILL.md
2. `$frontend-skill` (`frontend-skill`) score=20 path=/tmp/frontend/SKILL.md
3. `$playwright` (`playwright`) score=12 path=/tmp/playwright/SKILL.md

### Finalists To Read
1. `$office-hours` (`office-hours`) - /tmp/office-hours/SKILL.md
2. `$frontend-skill` (`frontend-skill`) - /tmp/frontend/SKILL.md
3. `$playwright` (`playwright`) - /tmp/playwright/SKILL.md

## Skill Match
{skill_match}

## Contract Check
- Objective: pass
- Inputs/context: pass
- Scope/non-goals: pass
- Deliverables: pass
- Assumptions/boundaries: pass
- Validation evidence: pass
- Failure conditions: pass
- Output format: pass
- Skill provenance: pass
- Skill Inventory Report: pass

## Final Prompt
Use the following skill(s) if available: {selected}

## Role
You are an execution-focused agent using the selected skills only where they improve quality.

## Objective
{prompt_objective}

## Requirements
{requirements}

## Context
The CEO inventory evidence and triage decision determine whether to clarify first or execute directly.

## Thinking Process
Follow this visible workflow: inspect the request, confirm triage, preserve scope and non-goals, use selected skills only when justified, verify the required artifact, and report concrete evidence.

## Validation
Run the relevant evaluator or project checks, inspect generated artifacts, verify required fields and command evidence, and report exact pass/fail output. For clarification, check the `## Clarified Spec` fields and return readiness for `$ceo`; for direct work, run available lint, tests, build, or browser checks as applicable.

## Output Format
{output_format}

## Assumptions
- The sample output is generated for evaluator smoke coverage.
  Boundary: use it as sample evidence, not production proof.
  Risk: fixture mode can pass while a real model regresses.
  Reversibility: clean.
"""


def generate_with_command(command: str, case: dict[str, Any]) -> str:
    result = subprocess.run(
        command,
        input=case["raw_request"],
        shell=True,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    parser.add_argument("--timestamp")
    parser.add_argument("--model-command", default=os.environ.get("CEO_LIVE_MODEL_COMMAND", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_cases(Path(args.cases))
    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    generated_dir = GENERATED_ROOT / timestamp
    results_dir = RESULTS_ROOT / timestamp
    generated_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in cases:
        output = fixture_output(case) if args.mode == "fixture" else generate_with_command(args.model_command, case)
        output_path = generated_dir / f"{case['id']}.md"
        output_path.write_text(output, encoding="utf-8")
        result = evaluator.check_contract(output, case["raw_request"])
        result["case_id"] = case["id"]
        result["expected_triage"] = case["expected_triage"]
        result["output_path"] = str(output_path.relative_to(REPO_ROOT))
        rows.append(result)

    results_path = results_dir / "evaluator-results.jsonl"
    results_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    passed = sum(1 for row in rows if row["passed"])
    summary = [
        "# CEO Live-Model Sample Summary",
        "",
        f"- Mode: {args.mode}",
        f"- Cases: {len(rows)}",
        f"- Passed: {passed}",
        f"- Failed: {len(rows) - passed}",
        "",
    ]
    for row in rows:
        summary.append(f"- {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} triage={row.get('triage_actual')}")
        for failure in row.get("failures", []):
            summary.append(f"  - {failure}")
    summary_path = results_dir / "summary.md"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"generated_dir": str(generated_dir), "results_dir": str(results_dir), "passed": passed, "total": len(rows)}, ensure_ascii=False, indent=2))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
