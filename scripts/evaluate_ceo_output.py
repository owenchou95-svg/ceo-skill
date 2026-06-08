#!/usr/bin/env python3
"""Validate whether a CEO skill response satisfies the executable-spec contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_SECTIONS = [
    "Triage",
    "Skill Inventory Report",
    "Skill Match",
    "Contract Check",
    "Final Prompt",
    "Assumptions",
]

REQUIRED_FINAL_PROMPT_HEADINGS = [
    "Role",
    "Objective",
    "Requirements",
    "Context",
    "Thinking Process",
    "Validation",
    "Output Format",
]

SKILL_INVOCATION_RE = re.compile(r"\$([A-Za-z0-9][A-Za-z0-9:_-]*)")
CANDIDATE_LINE_RE = re.compile(
    r"^\s*(?:\d+\.\s*)?`\$?([A-Za-z0-9][A-Za-z0-9:_-]*)`(?:\s+\(`([^`]+)`\))?"
)
SELECTED_SKILL_LINE_RE = re.compile(
    r"(?:use(?:\s+the\s+following\s+skill\(s\)\s+if\s+available)?|"
    r"selected\s+skills?|strong\s+match|supporting\s+match|route(?:\s+strongly)?\s+to|"
    r"invoke|调用|使用|选择|路由|强匹配|支持匹配)",
    re.IGNORECASE,
)
LISTED_SKILL_LINE_RE = re.compile(
    r"^\s*(?:[-*]|\d+\.)\s*(?:`?\$[A-Za-z0-9][A-Za-z0-9:_-]*`?)"
)

SEMANTIC_PATTERNS = {
    "requirements_inputs": re.compile(r"\binputs?\b|输入|上下文", re.IGNORECASE),
    "requirements_in_scope": re.compile(r"\bin\s+scope\b|范围内", re.IGNORECASE),
    "requirements_out_of_scope": re.compile(
        r"\bout\s+of\s+scope\b|\bnon[-\s]?goals?\b|\bnot\s+in\s+scope\b|"
        r"不在范围|范围外|非目标|不做",
        re.IGNORECASE,
    ),
    "requirements_deliverables": re.compile(r"\bdeliverables?\b|\bartifacts?\b|交付", re.IGNORECASE),
    "requirements_constraints": re.compile(
        r"\bconstraints?\b|\bassumptions?\b|\bboundar(?:y|ies)\b|\brisk\b|"
        r"\breversib(?:le|ility)\b|约束|假设|边界|风险|可逆",
        re.IGNORECASE,
    ),
    "requirements_failure": re.compile(
        r"\bfailure\b|\bescalation\b|\bstop\b|\bask\b|\bblocker\b|"
        r"失败|升级|停止|询问|阻塞",
        re.IGNORECASE,
    ),
}

CONTRACT_TERMS = [
    "objective",
    "inputs",
    "context",
    "scope",
    "non-goals",
    "deliverables",
    "assumptions",
    "boundaries",
    "validation",
    "failure",
    "output format",
    "skill provenance",
    "skill inventory",
    "目标",
    "输入",
    "上下文",
    "范围",
    "非目标",
    "交付",
    "假设",
    "边界",
    "验证",
    "失败",
    "输出",
    "技能来源",
    "技能清单",
]

VALIDATION_EVIDENCE_TERMS = [
    "command",
    "run",
    "test",
    "lint",
    "typecheck",
    "build",
    "pytest",
    "npm",
    "pnpm",
    "playwright",
    "browser",
    "screenshot",
    "console",
    "render",
    "open",
    "inspect",
    "diff",
    "ci",
    "logs",
    "verify",
    "check",
    "checklist",
    "field",
    "fields",
    "handoff",
    "spec",
    "clarified",
    "required",
    "acceptance",
    "criteria",
    "ready",
    "citation",
    "source",
    "artifact",
    "运行",
    "命令",
    "测试",
    "验证",
    "检查",
    "截图",
    "浏览器",
    "控制台",
    "渲染",
    "打开",
    "引用",
    "来源",
    "产物",
]

GENERIC_VALIDATION_RE = re.compile(
    r"^\s*(?:check|verify|test|run checks?|检查|验证|测试)(?:\s+(?:it|the result|结果))?\.?\s*$",
    re.IGNORECASE,
)

GENERIC_FIELD_VALUE_RE = re.compile(
    r"^\s*(?:tbd|todo|none|n/a|unknown|do the requested thing|"
    r"same as above|as requested|to be decided|检查|验证|待定|无|未知|按需求|按照要求)\.?\s*$",
    re.IGNORECASE,
)

REQUIREMENT_FIELD_LABELS = {
    "requirements_inputs": re.compile(r"^\s*[-*]\s*inputs?\s*:\s*(.+)$|^\s*[-*]\s*输入\s*[:：]\s*(.+)$", re.IGNORECASE),
    "requirements_in_scope": re.compile(r"^\s*[-*]\s*in\s+scope\s*:\s*(.+)$|^\s*[-*]\s*范围内\s*[:：]\s*(.+)$", re.IGNORECASE),
    "requirements_out_of_scope": re.compile(
        r"^\s*[-*]\s*(?:out\s+of\s+scope(?:\s*/\s*non[-\s]?goals?)?|non[-\s]?goals?)\s*:\s*(.+)$|"
        r"^\s*[-*]\s*(?:不在范围|范围外|非目标)\s*[:：]\s*(.+)$",
        re.IGNORECASE,
    ),
    "requirements_deliverables": re.compile(r"^\s*[-*]\s*deliverables?\s*:\s*(.+)$|^\s*[-*]\s*交付物?\s*[:：]\s*(.+)$", re.IGNORECASE),
    "requirements_constraints": re.compile(
        r"^\s*[-*]\s*(?:constraints?|assumptions?\s+and\s+boundaries|boundar(?:y|ies))\s*:\s*(.+)$|"
        r"^\s*[-*]\s*(?:约束|假设|边界)\s*[:：]\s*(.+)$",
        re.IGNORECASE,
    ),
    "requirements_failure": re.compile(
        r"^\s*[-*]\s*(?:failure\s*/\s*escalation\s+conditions?|failure|escalation)\s*:\s*(.+)$|"
        r"^\s*[-*]\s*(?:失败|升级|停止条件)\s*[:：]\s*(.+)$",
        re.IGNORECASE,
    ),
}


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    return sys.stdin.read()


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip(":")).strip()


def line_heading(line: str) -> str | None:
    match = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
    if not match:
        return None
    return normalize_heading(match.group(1))


def find_section_indices(text: str) -> dict[str, int]:
    sections: dict[str, int] = {}
    for index, line in enumerate(text.splitlines()):
        heading = line_heading(line)
        if not heading:
            continue
        for required in REQUIRED_TOP_LEVEL_SECTIONS:
            if heading == required and required not in sections:
                sections[required] = index
    return sections


def section_text(text: str, section: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        if normalize_heading(match.group(2)) == section:
            start = index + 1
            break
    if start is None:
        return ""

    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^\s*(#{1,6})\s+(.+?)\s*$", lines[index])
        if match and normalize_heading(match.group(2)) in REQUIRED_TOP_LEVEL_SECTIONS:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def final_prompt_heading_positions(final_prompt: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, line in enumerate(final_prompt.splitlines()):
        heading = line_heading(line)
        if heading in REQUIRED_FINAL_PROMPT_HEADINGS and heading not in positions:
            positions[heading] = index
    return positions


def final_prompt_section_text(final_prompt: str, section: str) -> str:
    lines = final_prompt.splitlines()
    start = None
    for index, line in enumerate(lines):
        heading = line_heading(line)
        if heading == section:
            start = index + 1
            break
    if start is None:
        return ""

    end = len(lines)
    for index in range(start, len(lines)):
        heading = line_heading(lines[index])
        if heading in REQUIRED_FINAL_PROMPT_HEADINGS:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def inventory_candidate_names(inventory_text: str) -> set[str]:
    names: set[str] = set()
    for line in inventory_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "path=" not in stripped and " - /" not in stripped:
            continue
        match = CANDIDATE_LINE_RE.match(stripped)
        if not match:
            continue
        names.add(match.group(1))
        if match.group(2):
            names.add(match.group(2))
    return names


def selected_skill_names_in_line(line: str, *, allow_list_style: bool) -> set[str]:
    if not SELECTED_SKILL_LINE_RE.search(line) and not (
        allow_list_style and LISTED_SKILL_LINE_RE.search(line)
    ):
        return set()

    names: set[str] = set()
    for name in SKILL_INVOCATION_RE.findall(line):
        if name.isupper() and ":" not in name and "-" not in name:
            continue
        names.add(name)
    return names


def invoked_skills(skill_match_text: str, final_prompt: str) -> set[str]:
    selected: set[str] = set()
    for line in skill_match_text.splitlines():
        selected.update(selected_skill_names_in_line(line, allow_list_style=True))
    for line in final_prompt.splitlines():
        selected.update(selected_skill_names_in_line(line, allow_list_style=False))
    return selected


def has_inventory_counts(inventory_text: str) -> bool:
    required_patterns = [
        r"Scanned files:\s*\d+",
        r"Unique skills:\s*\d+",
        r"Duplicates found:\s*\d+",
        r"Candidate limit:\s*\d+",
        r"Finalist limit:\s*\d+",
    ]
    return all(re.search(pattern, inventory_text, re.IGNORECASE) for pattern in required_patterns)


def has_inventory_operational_fields(inventory_text: str) -> bool:
    required_patterns = [
        r"Roots covered:",
        r"Complexity:\s*(?:standard|complex)",
        r"### Candidates",
        r"### Finalists To Read",
    ]
    return all(re.search(pattern, inventory_text, re.IGNORECASE) for pattern in required_patterns)


def has_meaningful_output_format(output_text: str) -> bool:
    stripped = output_text.strip()
    if len(stripped) < 20:
        return False
    placeholder_patterns = [
        r"^\[.*\]$",
        r"exact structure expected",
        r"output format",
        r"report\.?$",
    ]
    return not any(re.search(pattern, stripped, re.IGNORECASE) for pattern in placeholder_patterns)


def has_concrete_validation(validation_text: str) -> bool:
    stripped = validation_text.strip()
    if len(stripped) < 60 or GENERIC_VALIDATION_RE.match(stripped):
        return False
    if is_template_validation(stripped):
        return False
    evidence_hits = [
        term
        for term in VALIDATION_EVIDENCE_TERMS
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", stripped, re.IGNORECASE)
        or (not term.isascii() and term in stripped)
    ]
    return len(set(evidence_hits)) >= 2


def is_template_validation(validation_text: str) -> bool:
    lines = [line.strip(" -\t") for line in validation_text.splitlines() if line.strip()]
    if not lines:
        return True
    generic_lines = 0
    for line in lines:
        if re.fullmatch(
            r"(?:run|check|verify|test|inspect|open|capture)\s+"
            r"(?:the\s+)?(?:relevant\s+)?(?:available\s+)?"
            r"(?:checks?|tests?|commands?|app|result|artifact|output|browser|screenshots?)\.?",
            line,
            re.IGNORECASE,
        ):
            generic_lines += 1
    return generic_lines == len(lines)


def field_value_from_match(match: re.Match[str]) -> str:
    for group in match.groups():
        if group:
            return group.strip()
    return ""


def weak_requirement_fields(requirements_text: str) -> list[str]:
    weak: list[str] = []
    for label, pattern in REQUIREMENT_FIELD_LABELS.items():
        values = [
            field_value_from_match(match)
            for line in requirements_text.splitlines()
            if (match := pattern.match(line))
        ]
        if not values:
            continue
        meaningful = [
            value
            for value in values
            if len(value.strip()) >= 12 and not GENERIC_FIELD_VALUE_RE.match(value.strip())
        ]
        if not meaningful:
            weak.append(label)
    return weak


def contract_term_count(contract_text: str) -> int:
    normalized = contract_text.lower()
    return sum(1 for term in CONTRACT_TERMS if term.lower() in normalized)


def semantic_failures_for_final_prompt(final_prompt: str, contract_text: str) -> list[str]:
    failures: list[str] = []

    objective_text = final_prompt_section_text(final_prompt, "Objective")
    requirements_text = final_prompt_section_text(final_prompt, "Requirements")
    context_text = final_prompt_section_text(final_prompt, "Context")
    thinking_text = final_prompt_section_text(final_prompt, "Thinking Process")
    validation_text = final_prompt_section_text(final_prompt, "Validation")
    output_text = final_prompt_section_text(final_prompt, "Output Format")

    if len(objective_text.strip()) < 12:
        failures.append("Final Prompt Objective is too short to be actionable.")
    if not context_text.strip() or context_text.strip().lower() in {"none", "none.", "n/a"}:
        failures.append("Final Prompt Context is empty or only says none.")
    if len(thinking_text.strip()) < 40:
        failures.append("Final Prompt Thinking Process lacks an observable workflow.")

    missing_requirement_fields = [
        label
        for label, pattern in SEMANTIC_PATTERNS.items()
        if not pattern.search(requirements_text)
    ]
    if missing_requirement_fields:
        failures.append(
            "Final Prompt Requirements is missing semantic fields: "
            + ", ".join(missing_requirement_fields)
        )
    weak_fields = weak_requirement_fields(requirements_text)
    if weak_fields:
        failures.append(
            "Final Prompt Requirements has placeholder or too-generic field values: "
            + ", ".join(weak_fields)
        )

    if not has_concrete_validation(validation_text):
        failures.append("Final Prompt Validation lacks concrete evidence, commands, artifacts, or checks.")
    if not has_meaningful_output_format(output_text):
        failures.append("Final Prompt Output Format is empty, generic, or placeholder-like.")
    if contract_term_count(contract_text) < 4 or not re.search(r"\b(pass|fail|check|checklist)\b|通过|失败|检查", contract_text, re.IGNORECASE):
        failures.append("Contract Check lacks a pass/fail checklist tied to the executable-spec contract.")

    return failures


def check_contract(text: str) -> dict[str, Any]:
    section_indices = find_section_indices(text)
    missing_sections = [
        section for section in REQUIRED_TOP_LEVEL_SECTIONS if section not in section_indices
    ]

    inventory_text = section_text(text, "Skill Inventory Report")
    skill_match_text = section_text(text, "Skill Match")
    final_prompt = section_text(text, "Final Prompt")
    contract_text = section_text(text, "Contract Check")

    final_positions = final_prompt_heading_positions(final_prompt)
    missing_final_headings = [
        heading for heading in REQUIRED_FINAL_PROMPT_HEADINGS if heading not in final_positions
    ]
    heading_order = [
        final_positions[heading]
        for heading in REQUIRED_FINAL_PROMPT_HEADINGS
        if heading in final_positions
    ]
    final_headings_in_order = heading_order == sorted(heading_order)

    inventory_names = inventory_candidate_names(inventory_text)
    selected_skills = invoked_skills(skill_match_text, final_prompt)
    untraceable_skills = sorted(skill for skill in selected_skills if skill not in inventory_names)
    semantic_failures = semantic_failures_for_final_prompt(final_prompt, contract_text)

    checks = {
        "required_top_level_sections": not missing_sections,
        "inventory_counts_present": has_inventory_counts(inventory_text),
        "inventory_operational_fields_present": has_inventory_operational_fields(inventory_text),
        "contract_check_present": bool(contract_text.strip()),
        "final_prompt_present": bool(final_prompt.strip()),
        "final_prompt_headings_present": not missing_final_headings,
        "final_prompt_headings_in_order": final_headings_in_order,
        "skill_source_traceable": not untraceable_skills,
        "semantic_contract_complete": not semantic_failures,
    }

    failures = []
    if missing_sections:
        failures.append("Missing top-level sections: " + ", ".join(missing_sections))
    if not checks["inventory_counts_present"]:
        failures.append("Skill Inventory Report is missing required count fields.")
    if not checks["inventory_operational_fields_present"]:
        failures.append("Skill Inventory Report is missing roots, complexity, candidates, or finalists.")
    if not checks["contract_check_present"]:
        failures.append("Contract Check section is empty or missing.")
    if not checks["final_prompt_present"]:
        failures.append("Final Prompt section is empty or missing.")
    if missing_final_headings:
        failures.append("Missing Final Prompt headings: " + ", ".join(missing_final_headings))
    if not final_headings_in_order:
        failures.append("Final Prompt headings are present but out of order.")
    if untraceable_skills:
        failures.append("Selected skills are not traceable to inventory candidates: " + ", ".join(untraceable_skills))
    failures.extend(semantic_failures)

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "failures": failures,
        "missing_sections": missing_sections,
        "missing_final_prompt_headings": missing_final_headings,
        "selected_skills": sorted(selected_skills),
        "inventory_candidate_names": sorted(inventory_names),
        "untraceable_skills": untraceable_skills,
        "semantic_failures": semantic_failures,
    }


def print_markdown(result: dict[str, Any]) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"## CEO Output Evaluation: {status}")
    print("\n### Checks")
    for name, passed in result["checks"].items():
        print(f"- {name}: {'pass' if passed else 'fail'}")
    print("\n### Skills")
    print(f"- Selected skills: {', '.join(result['selected_skills']) or 'none'}")
    print(f"- Untraceable skills: {', '.join(result['untraceable_skills']) or 'none'}")
    if result["failures"]:
        print("\n### Failures")
        for failure in result["failures"]:
            print(f"- {failure}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a CEO skill response for contract compliance.")
    parser.add_argument("path", nargs="?", help="CEO response markdown file. Reads stdin when omitted.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = check_contract(read_input(args.path))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_markdown(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
