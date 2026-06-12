#!/usr/bin/env python3
"""Check that the CEO contract schema, evaluator, skill, and docs have not drifted."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import evaluate_ceo_output as evaluator
from contract_schema import load_contract_schema


REPO_ROOT = Path(__file__).resolve().parent.parent


def text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def route_line_violations(file_text: str, path: str) -> list[str]:
    failures: list[str] = []
    for number, line in enumerate(file_text.splitlines(), start=1):
        line_l = line.lower()
        if "deep-interview --quick" not in line_l:
            continue
        if any(allowed in line_l for allowed in ["不会重新成为", "forbidden", "not satisfy", "not a hard", "must not", "legacy", "previously", "replaced"]):
            continue
        if any(bad in line_l for bad in ["route", "requires", "must", "canonical", "hard route", "澄清路由", "必须"]):
            failures.append(f"{path}:{number}: $deep-interview --quick appears as an active clarification route")
    return failures


def validate_contract_drift() -> list[str]:
    schema = load_contract_schema()
    failures: list[str] = []

    if evaluator.REQUIRED_TOP_LEVEL_SECTIONS != schema["required_top_level_sections"]:
        failures.append("REQUIRED_TOP_LEVEL_SECTIONS differs from schema")
    if evaluator.REQUIRED_FINAL_PROMPT_HEADINGS != schema["required_final_prompt_headings"]:
        failures.append("REQUIRED_FINAL_PROMPT_HEADINGS differs from schema")
    if evaluator.CANONICAL_CLARIFICATION_SKILL != schema["clarification_route"]["canonical_skill"]:
        failures.append("CANONICAL_CLARIFICATION_SKILL differs from schema")
    if evaluator.CLARIFIED_SPEC_FIELDS != schema["clarified_spec"]["required_fields"]:
        failures.append("CLARIFIED_SPEC_FIELDS differs from schema")

    skill_text = text("SKILL.md")
    readme_text = text("README.md")
    prompt_template = text("references/prompt-template.md")
    for section in schema["required_top_level_sections"]:
        if section not in skill_text and section not in readme_text:
            failures.append(f"required top-level section {section!r} is absent from SKILL.md/README.md")
    for heading in schema["required_final_prompt_headings"]:
        if f"## {heading}" not in prompt_template and f"`## {heading}`" not in skill_text:
            failures.append(f"required Final Prompt heading {heading!r} is absent from prompt template/SKILL.md")
    for field in schema["clarified_spec"]["required_fields"]:
        if f"- {field}:" not in skill_text and f"- {field}:" not in readme_text:
            failures.append(f"clarified spec field {field!r} is absent from SKILL.md/README.md")

    if "$office-hours" not in skill_text:
        failures.append("SKILL.md must mention $office-hours as the canonical clarification route")
    for relative in [
        "SKILL.md",
        "README.md",
        "references/test-fixtures.md",
        "references/eval-fixtures.json",
        "scripts/evaluate_ceo_output.py",
    ]:
        failures.extend(route_line_violations(text(relative), relative))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = validate_contract_drift()
    if args.format == "json":
        print(json.dumps({"passed": not failures, "failures": failures}, indent=2, ensure_ascii=False))
    elif failures:
        print("CEO contract drift check: FAIL")
        for failure in failures:
            print(f"- {failure}")
    else:
        print("CEO contract drift check: PASS")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
