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

TRIAGE_DIRECT = "Direct Path"
TRIAGE_CLARIFICATION = "Clarification Path"
CANONICAL_CLARIFICATION_SKILL = "office-hours"

CLARIFIED_SPEC_FIELDS = [
    "Goal",
    "Deliverables",
    "In Scope",
    "Out of Scope / Non-goals",
    "Inputs / Context",
    "Decision Boundaries",
    "Constraints",
    "Acceptance Criteria",
    "Risks and Reversibility",
    "Open Questions",
    "CEO Handoff Summary",
]

VAGUE_REQUEST_TERMS = [
    "not sure",
    "uncertain",
    "still vague",
    "figure out",
    "think through",
    "don't assume",
    "do not assume",
    "help me decide",
    "不确定",
    "还不确定",
    "还不清楚",
    "想清楚",
    "帮我想",
    "不要假设",
    "别假设",
    "模糊",
]

HIGH_RISK_REQUEST_TERMS = [
    "production",
    "database",
    "delete",
    "drop",
    "deploy",
    "payment",
    "security",
    "legal advice",
    "investment advice",
    "生产",
    "数据库",
    "删除",
    "清掉",
    "部署",
    "上线",
    "支付",
    "安全",
    "法律意见",
    "投资建议",
]

HIGH_RISK_BOUNDARY_TERMS = [
    "authority",
    "approval",
    "approved",
    "environment",
    "backup",
    "rollback",
    "deletion criteria",
    "target environment",
    "授权",
    "批准",
    "审批",
    "环境",
    "备份",
    "回滚",
    "删除标准",
    "目标环境",
]

EXECUTION_TERMS = [
    "build",
    "implement",
    "create",
    "scaffold",
    "write code",
    "deploy",
    "delete",
    "drop",
    "ship",
    "构建",
    "实现",
    "创建",
    "写代码",
    "部署",
    "删除",
    "清掉",
    "上线",
]

NEGATION_TERMS = [
    "do not",
    "don't",
    "dont",
    "not",
    "not yet",
    "avoid",
    "without",
    "禁止",
    "不要",
    "不做",
    "无需",
    "避免",
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

FIELD_LINE_RE = re.compile(r"^\s*[-*]\s*([^:：]+)\s*[:：]\s*(.*)$")

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


def contains_any_phrase(text: str, terms: list[str]) -> list[str]:
    text_l = text.lower()
    matches = []
    for term in terms:
        term_l = term.lower()
        if not term_l:
            continue
        if term_l.isascii() and re.fullmatch(r"[a-z0-9 -]+", term_l):
            pattern = rf"(?<![a-z0-9]){re.escape(term_l)}(?![a-z0-9])"
            if re.search(pattern, text_l):
                matches.append(term)
        elif term_l in text_l:
            matches.append(term)
    return matches


def has_unnegated_phrase(text: str, phrase: str) -> bool:
    text_l = text.lower()
    phrase_l = phrase.lower()
    start = 0
    while True:
        index = text_l.find(phrase_l, start)
        if index < 0:
            return False
        prefix = text_l[max(0, index - 36):index]
        if not any(term in prefix for term in NEGATION_TERMS):
            return True
        start = index + len(phrase_l)


def has_any_unnegated_phrase(text: str, phrases: list[str]) -> bool:
    return any(has_unnegated_phrase(text, phrase) for phrase in phrases)


def has_unnegated_execution_action(text: str) -> bool:
    """Detect direct execution actions while allowing clarification about those actions."""
    text_l = text.lower()
    for phrase in EXECUTION_TERMS:
        phrase_l = phrase.lower()
        start = 0
        while True:
            if phrase_l.isascii():
                match = re.search(rf"(?<![a-z0-9]){re.escape(phrase_l)}(?![a-z0-9])", text_l[start:])
                if not match:
                    break
                index = start + match.start()
                match_end = start + match.end()
            else:
                index = text_l.find(phrase_l, start)
                if index < 0:
                    break
                match_end = index + len(phrase_l)
            if index < 0:
                break
            prefix = text_l[max(0, index - 96):index]
            suffix = text_l[match_end: match_end + 32]
            if any(term in prefix for term in NEGATION_TERMS):
                start = match_end
                continue
            if any(term in prefix for term in ["out of scope", "non-goals", "not in scope", "不在范围", "范围外", "非目标"]):
                start = match_end
                continue
            if any(term in prefix for term in ["clarify", "clarifies", "requirements for", "澄清", "明确"]):
                start = match_end
                continue
            if re.match(r"\s*(?:prompt|request|boundary|criteria|plan|context|提示词|请求|边界|标准|计划)", suffix):
                start = match_end
                continue
            return True
    return False


def actual_triage(text: str) -> str | None:
    triage_text = section_text(text, "Triage")
    if re.search(r"\bclarification\s+path\b|澄清", triage_text, re.IGNORECASE):
        return TRIAGE_CLARIFICATION
    if re.search(r"\bdirect\s+path\b|直接", triage_text, re.IGNORECASE):
        return TRIAGE_DIRECT
    return None


def parse_clarified_spec(request: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in request.splitlines():
        match = FIELD_LINE_RE.match(line)
        if not match:
            continue
        label = normalize_heading(match.group(1))
        value = match.group(2).strip()
        for field in CLARIFIED_SPEC_FIELDS:
            if label.lower() == field.lower():
                fields[field] = value
                break
    return fields


def clarified_spec_readiness(request: str) -> dict[str, Any]:
    if "Clarified Spec" not in request:
        return {
            "present": False,
            "ready": None,
            "missing_fields": [],
            "blocking_fields": [],
            "reason": "no clarified spec supplied",
        }

    fields = parse_clarified_spec(request)
    missing = [field for field in CLARIFIED_SPEC_FIELDS if field not in fields]
    blocking = []
    for field, value in fields.items():
        value_l = value.lower().strip()
        if not value_l or GENERIC_FIELD_VALUE_RE.match(value_l):
            blocking.append(field)
            continue
        if field != "Open Questions" and any(term in value_l for term in ["unknown", "blocking", "待定", "未知", "未定"]):
            blocking.append(field)
        if field == "Open Questions" and not re.search(r"\bnone\s+blocking\b|\bno\s+blocking\b|无阻塞|没有阻塞|none\b", value_l, re.IGNORECASE):
            blocking.append(field)
        if field == "Decision Boundaries" and any(term in value_l for term in ["choose", "decide later", "待定", "未定", "用户选择"]):
            blocking.append(field)

    ready = not missing and not blocking
    reason = "ready" if ready else "missing or blocking clarified spec fields"
    return {
        "present": True,
        "ready": ready,
        "missing_fields": missing,
        "blocking_fields": sorted(set(blocking)),
        "reason": reason,
    }


def expected_triage_for_request(request: str | None) -> dict[str, Any]:
    if not request:
        return {
            "expected": None,
            "requires_clarification": False,
            "reasons": [],
            "clarified_spec_readiness": clarified_spec_readiness(""),
        }

    readiness = clarified_spec_readiness(request)
    if readiness["present"]:
        if readiness["ready"]:
            return {
                "expected": TRIAGE_DIRECT,
                "requires_clarification": False,
                "reasons": ["clarified-spec-ready"],
                "clarified_spec_readiness": readiness,
            }
        return {
            "expected": TRIAGE_CLARIFICATION,
            "requires_clarification": True,
            "reasons": ["clarified-spec-not-ready"],
            "clarified_spec_readiness": readiness,
        }

    reasons = []
    vague_hits = contains_any_phrase(request, VAGUE_REQUEST_TERMS)
    if vague_hits:
        reasons.append("vague-intent:" + ",".join(vague_hits[:4]))

    high_risk_hits = contains_any_phrase(request, HIGH_RISK_REQUEST_TERMS)
    if high_risk_hits:
        boundary_hits = contains_any_phrase(request, HIGH_RISK_BOUNDARY_TERMS)
        if len(boundary_hits) < 2:
            reasons.append("high-risk-missing-boundary:" + ",".join(high_risk_hits[:4]))

    request_l = request.lower()
    if re.search(r"\bpr\b|pull request|拉取请求", request_l) and not re.search(r"https?://|#\d+|/pull/\d+|\brepo\b|repository|仓库", request_l):
        reasons.append("missing-critical-input:pr-or-repo")
    if contains_any_phrase(request, ["legal", "法律", "case brief", "法律意见"]) and not contains_any_phrase(request, ["jurisdiction", "管辖", "法域", "china", "us", "美国", "中国"]):
        reasons.append("missing-critical-input:jurisdiction")
    if contains_any_phrase(request, ["investment", "portfolio", "投资", "理财"]) and not contains_any_phrase(request, ["risk profile", "risk tolerance", "风险偏好", "风险承受"]):
        reasons.append("missing-critical-input:risk-profile")

    expected = TRIAGE_CLARIFICATION if reasons else TRIAGE_DIRECT
    return {
        "expected": expected,
        "requires_clarification": bool(reasons),
        "reasons": reasons,
        "clarified_spec_readiness": readiness,
    }


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


def triage_failures_for_request(text: str, request: str | None) -> tuple[dict[str, Any], list[str]]:
    expected = expected_triage_for_request(request)
    actual = actual_triage(text)
    final_prompt = section_text(text, "Final Prompt")
    skill_match_text = section_text(text, "Skill Match")
    selected_skills = invoked_skills(skill_match_text, final_prompt)
    final_objective = final_prompt_section_text(final_prompt, "Objective")
    final_requirements = final_prompt_section_text(final_prompt, "Requirements")
    final_output = final_prompt_section_text(final_prompt, "Output Format")
    final_combined = "\n".join([final_objective, final_requirements, final_output])

    failures = []
    if expected["expected"] and actual != expected["expected"]:
        failures.append(
            f"Triage mismatch for request: expected {expected['expected']}, got {actual or 'unknown'}."
        )

    clarification_route_passed = True
    if expected["requires_clarification"]:
        has_office_hours = CANONICAL_CLARIFICATION_SKILL in selected_skills or f"${CANONICAL_CLARIFICATION_SKILL}" in text
        has_ceo_handoff = "$ceo" in text or re.search(r"back to\s+\$?ceo|return to\s+\$?ceo|回到\s*\$?ceo", text, re.IGNORECASE)
        asks_for_clarified_spec = "Clarified Spec" in final_prompt
        direct_execution = has_unnegated_execution_action(final_combined)
        clarification_route_passed = has_office_hours and has_ceo_handoff and asks_for_clarified_spec and not direct_execution
        if not has_office_hours:
            failures.append("Clarification Path must route to $office-hours.")
        if not has_ceo_handoff:
            failures.append("Clarification Path must hand off back to $ceo.")
        if not asks_for_clarified_spec:
            failures.append("Clarification Path must require a ## Clarified Spec artifact.")
        if direct_execution:
            failures.append("Clarification Path Final Prompt contains unnegated direct-execution language.")

    triage_result = {
        "triage_expected": expected["expected"],
        "triage_actual": actual,
        "triage_passed": not failures,
        "triage_reasons": expected["reasons"],
        "clarification_route_passed": clarification_route_passed,
        "clarified_spec_readiness": expected["clarified_spec_readiness"],
    }
    return triage_result, failures


def check_contract(text: str, request: str | None = None) -> dict[str, Any]:
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
    triage_result, triage_failures = triage_failures_for_request(text, request)

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
        "triage_request_alignment": not triage_failures,
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
    failures.extend(triage_failures)

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
        **triage_result,
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
    print("\n### Triage")
    print(f"- Expected: {result.get('triage_expected') or 'not checked'}")
    print(f"- Actual: {result.get('triage_actual') or 'unknown'}")
    print(f"- Request alignment: {'pass' if result.get('triage_passed') else 'fail'}")
    print(f"- Clarification route: {'pass' if result.get('clarification_route_passed') else 'fail'}")
    if result.get("triage_reasons"):
        print(f"- Reasons: {', '.join(result['triage_reasons'])}")
    if result["failures"]:
        print("\n### Failures")
        for failure in result["failures"]:
            print(f"- {failure}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a CEO skill response for contract compliance.")
    parser.add_argument("path", nargs="?", help="CEO response markdown file. Reads stdin when omitted.")
    parser.add_argument("--request", help="Raw user request. Enables request-aware triage validation.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = check_contract(read_input(args.path), args.request)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_markdown(result)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
