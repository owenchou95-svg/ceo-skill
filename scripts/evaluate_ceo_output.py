#!/usr/bin/env python3
"""Validate whether a CEO skill response satisfies the executable-spec contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from contract_schema import load_contract_schema

CONTRACT_SCHEMA = load_contract_schema()
REQUIRED_TOP_LEVEL_SECTIONS = list(CONTRACT_SCHEMA["required_top_level_sections"])
REQUIRED_FINAL_PROMPT_HEADINGS = list(CONTRACT_SCHEMA["required_final_prompt_headings"])

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
MODE_TASK = "Task Mode"
MODE_GOAL = "Goal Mode"
REQUIRED_MODE_ROUTER_FIELDS = [
    "Mode",
    "Confidence",
    "Reason",
    "Evidence",
    "Immediate User Intent",
    "Goal Signal",
    "Task Signal",
    "Risk / Strategy Signal",
    "Continue To",
]
GOAL_SPEC_REQUIRED_FIELDS = [
    "Goal",
    "Current State",
    "Desired End State",
    "In Scope",
    "Out of Scope / Non-goals",
    "Acceptance Criteria",
    "Validation Method",
    "First Executable Slice",
    "Stop / Ask / Escalate Conditions",
]
LOCAL_GOAL_RETURN_REQUIRED_FIELDS = GOAL_SPEC_REQUIRED_FIELDS + [
    "Open Questions",
]
RISK_BOUNDARY_PROMPT_FIELDS = [
    "Goal",
    "Risk Category",
    "Affected Systems / Data",
    "Target Environment",
    "Authority / Approval",
    "Backup / Recovery",
    "Rollback Plan",
    "Dry-run / Simulation",
    "Verification Method",
    "Audit Trail",
    "Stop Conditions",
    "Explicitly Forbidden Until Approved",
    "Remaining Blocking Questions",
    "Readiness",
    "CEO Handoff Summary",
]
DISCOVERY_RETURN_REQUIRED_FIELDS = [
    "Goal",
    "Target User / Audience",
    "Problem / Need",
    "Current Status Quo",
    "Desired End State",
    "In Scope",
    "Out of Scope / Non-goals",
    "Decision Boundaries",
    "Acceptance Criteria",
    "First Executable Slice",
    "Validation Method",
    "Open Questions",
]
DISCOVERY_PRODUCT_REQUIRED_FIELDS = [
    "Demand Evidence",
    "Status Quo Workaround",
    "Narrowest Wedge",
    "Why Now / Future Fit",
]
DOMAIN_GATE_REQUIRED_FIELDS = [
    "Domain",
    "Category",
    "Decision",
    "Required Clarification",
    "Reason",
]
DOMAIN_GREEN = "Green"
DOMAIN_YELLOW = "Yellow"
DOMAIN_RED = "Red"
CANONICAL_CLARIFICATION_SKILL = CONTRACT_SCHEMA["clarification_route"]["canonical_skill"]
CANONICAL_CLARIFICATION_ALIASES = set(CONTRACT_SCHEMA["clarification_route"].get("canonical_aliases", []))
CANONICAL_HANDOFF_SKILL = CONTRACT_SCHEMA["clarification_route"].get("required_handoff_skill", "ceo")
FORBIDDEN_HARD_CLARIFICATION_ROUTES = set(CONTRACT_SCHEMA["clarification_route"].get("forbidden_hard_routes", []))

CLARIFIED_SPEC_FIELDS = list(CONTRACT_SCHEMA["clarified_spec"]["required_fields"])

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

DISCOVERY_DOMAIN_TERMS = [
    "product direction",
    "product discovery",
    "user needs",
    "market positioning",
    "startup",
    "business",
    "career",
    "long-term",
    "okr",
    "worth building",
    "what should i do",
    "research direction",
    "产品方向",
    "产品发现",
    "用户需求",
    "市场定位",
    "创业",
    "赛道",
    "职业",
    "长期",
    "个人成长",
    "值得做",
    "该研究哪个",
    "研究方向",
]

RISK_DOMAIN_TERMS = [
    "security",
    "privacy",
    "auth",
    "permission",
    "bypass",
    "compliance",
    "legal",
    "financial",
    "medical",
    "production",
    "deployment",
    "deploy",
    "release",
    "delete",
    "deletion",
    "migration",
    "rollback",
    "monitoring",
    "external side effect",
    "database",
    "secrets",
    "安全",
    "隐私",
    "权限",
    "绕过",
    "合规",
    "法律",
    "金融",
    "医疗",
    "生产",
    "部署",
    "上线",
    "发布",
    "删除",
    "清理生产",
    "迁移",
    "回滚",
    "监控",
    "数据库",
    "密钥",
]

YELLOW_DOMAIN_TERMS = [
    "architecture",
    "system design",
    "refactor",
    "performance",
    "research",
    "feature scope",
    "cross-module",
    "migration plan",
    "架构",
    "系统设计",
    "重构",
    "性能",
    "研究",
    "功能范围",
    "跨模块",
]

YELLOW_ALLOWED_SLICE_TERMS = [
    "analysis",
    "assess",
    "assessment",
    "audit",
    "design",
    "document",
    "documentation",
    "spec",
    "plan",
    "test",
    "evaluator",
    "fixture",
    "report",
    "checklist",
    "分析",
    "评估",
    "审计",
    "设计",
    "文档",
    "规格",
    "计划",
    "测试",
    "报告",
    "清单",
]

YELLOW_DISALLOWED_SLICE_TERMS = [
    "implement",
    "rewrite",
    "refactor the whole",
    "refactor entire",
    "migrate",
    "deploy",
    "production",
    "delete",
    "cross-module rewrite",
    "实现",
    "重写",
    "重构整个",
    "迁移",
    "部署",
    "生产",
    "删除",
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

RISK_EXECUTION_COMMAND_RE = re.compile(
    r"(?i)(?:\brm\s+-rf\b|\bDROP\s+TABLE\b|\bDELETE\s+FROM\b|\bTRUNCATE\s+TABLE\b|"
    r"\bkubectl\s+delete\b|\bdocker\s+compose\s+down\b|\bterraform\s+apply\b|"
    r"\bdeploy\s+(?:now|latest|to|production)\b|\brun\s+[`'\"]?(?:rm|delete|drop|deploy|kubectl|terraform)\b|"
    r"执行(?:删除|部署|上线|清理)|运行(?:删除|部署|上线|清理))"
)

HARD_STOP_RE = re.compile(r"\bHard Stop\b|硬停止|终止任务|拒绝继续", re.IGNORECASE)

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

VAGUE_GOAL_FIELD_VALUE_RE = re.compile(
    r"^\s*(?:better|improve|optimize|enhance|smarter|good|clearer|robust|"
    r"完善|优化|更好|更智能|更清晰|提升|高级|看情况|待定|未知|不清楚)\.?\s*$",
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


def mode_router_text(text: str) -> str:
    return section_text(text, "Mode Router")


def actual_mode(text: str) -> str | None:
    router_text = mode_router_text(text)
    match = re.search(
        r"^\s*[-*]\s*Mode\s*[:：]\s*(Task Mode|Goal Mode)\b",
        router_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None
    value = match.group(1).lower()
    if value == "task mode":
        return MODE_TASK
    if value == "goal mode":
        return MODE_GOAL
    return None


def mode_continue_to(text: str) -> str:
    router_text = mode_router_text(text)
    match = re.search(
        r"^\s*[-*]\s*Continue To\s*[:：]\s*(.+?)\s*$",
        router_text,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def mode_router_missing_fields(text: str) -> list[str]:
    router_text = mode_router_text(text)
    missing = []
    for field in REQUIRED_MODE_ROUTER_FIELDS:
        if not field_value(router_text, field):
            missing.append(field)
    return missing


def h2_section_text(text: str, section: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        match = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if match and normalize_heading(match.group(1)) == section:
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^\s*##\s+.+?\s*$", lines[index]):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def h2_section_index(text: str, section: str) -> int | None:
    for index, line in enumerate(text.splitlines()):
        match = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if match and normalize_heading(match.group(1)) == section:
            return index
    return None


def goal_mode_status(text: str) -> str | None:
    goal_text = h2_section_text(text, "Goal Mode")
    match = re.search(
        r"^\s*[-*]\s*Status\s*[:：]\s*(Incomplete|Complete|Routed)\b",
        goal_text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None
    return match.group(1).capitalize()


def field_value(section_body: str, label: str) -> str:
    for line in section_body.splitlines():
        match = FIELD_LINE_RE.match(line)
        if match and normalize_heading(match.group(1)).lower() == label.lower():
            return match.group(2).strip()
    return ""


def field_map(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_LINE_RE.match(line)
        if not match:
            continue
        fields[normalize_heading(match.group(1)).lower()] = match.group(2).strip()
    return fields


def field_value_from_map(fields: dict[str, str], *labels: str) -> str:
    for label in labels:
        value = fields.get(normalize_heading(label).lower())
        if value is not None:
            return value
    return ""


def weak_clarified_value(value: str) -> bool:
    value_l = value.lower().strip()
    if not value_l or len(value_l) < 8:
        return True
    if GENERIC_FIELD_VALUE_RE.match(value_l) or VAGUE_GOAL_FIELD_VALUE_RE.match(value_l):
        return True
    return any(term in value_l for term in ["unknown", "blocking", "tbd", "待定", "未知", "不清楚"])


def open_questions_clear(value: str) -> bool:
    return bool(re.search(r"\bnone\s+blocking\b|\bno\s+blocking\b|无阻塞|没有阻塞|none\b", value, re.IGNORECASE))


def discovery_return_readiness(request: str) -> dict[str, Any]:
    present = "Clarified Spec" in request and (
        "Target User" in request
        or "Problem / Need" in request
        or "Demand Evidence" in request
        or "目标用户" in request
    )
    if not present:
        return {"present": False, "ready": None, "missing_fields": [], "weak_fields": []}

    fields = field_map(request)
    required = list(DISCOVERY_RETURN_REQUIRED_FIELDS)
    if re.search(r"\bproduct\b|\bstartup\b|产品|创业", request, re.IGNORECASE):
        required.extend(DISCOVERY_PRODUCT_REQUIRED_FIELDS)

    aliases = {
        "Target User / Audience": ["Target User / Audience", "Target User", "Audience", "目标用户", "受众"],
        "Problem / Need": ["Problem / Need", "Problem", "Need", "问题", "需求"],
        "Out of Scope / Non-goals": ["Out of Scope / Non-goals", "Out of Scope", "Non-goals", "范围外", "非目标"],
        "Why Now / Future Fit": ["Why Now / Future Fit", "Why Now", "Future Fit", "为什么现在"],
    }
    missing = []
    weak = []
    for field in required:
        value = field_value_from_map(fields, *aliases.get(field, [field]))
        if not value:
            missing.append(field)
            continue
        if field == "Open Questions":
            if not open_questions_clear(value):
                weak.append(field)
            continue
        if field == "Target User / Audience" and value.strip().lower() in {"developers", "users", "everyone", "开发者", "用户", "所有人"}:
            weak.append(field)
            continue
        if field == "Acceptance Criteria" and not re.search(r"\d|pass|fail|measure|measurable|验证|通过|失败|数量|比例|标准", value, re.IGNORECASE):
            weak.append(field)
            continue
        if field == "First Executable Slice" and re.fullmatch(r"\s*(?:build\s+(?:an?\s+)?mvp|做个\s*MVP|做一个\s*MVP|prototype|原型)\.?\s*", value, re.IGNORECASE):
            weak.append(field)
            continue
        if weak_clarified_value(value):
            weak.append(field)

    return {
        "present": True,
        "ready": not missing and not weak,
        "missing_fields": missing,
        "weak_fields": weak,
    }


def risk_boundary_return_readiness(request: str) -> dict[str, Any]:
    present = "Risk-Bounded Clarified Spec" in request
    if not present:
        return {"present": False, "ready": None, "missing_fields": [], "weak_fields": []}

    fields = field_map(request)
    aliases = {
        "Affected Systems / Data": ["Affected Systems / Data", "Data or System Affected", "Affected Data", "影响系统 / 数据"],
        "Dry-run / Simulation": ["Dry-run / Simulation", "Dry-run", "Simulation", "演练", "模拟"],
    }
    missing = []
    weak = []
    for field in RISK_BOUNDARY_PROMPT_FIELDS:
        value = field_value_from_map(fields, *aliases.get(field, [field]))
        if not value:
            missing.append(field)
            continue
        if field == "Readiness":
            if not re.search(r"Ready for CEO Re-evaluation", value, re.IGNORECASE):
                weak.append(field)
            continue
        if field in {
            "Authority / Approval",
            "Target Environment",
            "Backup / Recovery",
            "Rollback Plan",
            "Dry-run / Simulation",
            "Verification Method",
            "Stop Conditions",
        } and weak_clarified_value(value):
            weak.append(field)

    return {
        "present": True,
        "ready": not missing and not weak,
        "missing_fields": missing,
        "weak_fields": weak,
    }


def local_goal_return_readiness(request: str) -> dict[str, Any]:
    present = bool(re.search(r"\bLocal Goal Clarified Spec\b|\bClarified Local Goal\b", request, re.IGNORECASE))
    if not present:
        return {"present": False, "ready": None, "missing_fields": [], "weak_fields": []}

    fields = field_map(request)
    aliases = {
        "Out of Scope / Non-goals": ["Out of Scope / Non-goals", "Out of Scope", "Non-goals", "范围外", "非目标"],
        "Stop / Ask / Escalate Conditions": [
            "Stop / Ask / Escalate Conditions",
            "Stop Conditions",
            "Escalate Conditions",
            "停止 / 询问 / 升级条件",
        ],
        "Open Questions": ["Open Questions", "Remaining Questions", "Blocking Questions", "开放问题", "剩余问题"],
    }
    missing = []
    weak = []
    for field in LOCAL_GOAL_RETURN_REQUIRED_FIELDS:
        value = field_value_from_map(fields, *aliases.get(field, [field]))
        if not value:
            missing.append(field)
            continue
        if field == "Open Questions":
            if not open_questions_clear(value):
                weak.append(field)
            continue
        if field == "Acceptance Criteria" and not re.search(
            r"\d|pass|fail|measure|measurable|verify|验证|通过|失败|数量|比例|标准",
            value,
            re.IGNORECASE,
        ):
            weak.append(field)
            continue
        if field == "Validation Method" and not re.search(
            r"test|check|verify|run|inspect|pytest|fixture|smoke|验证|测试|检查|运行",
            value,
            re.IGNORECASE,
        ):
            weak.append(field)
            continue
        if field == "First Executable Slice" and re.fullmatch(
            r"\s*(?:improve|optimi[sz]e|make\s+.+\s+better|改进|优化|提升|让.+更好|改善.+)\.?\s*",
            value,
            re.IGNORECASE,
        ):
            weak.append(field)
            continue
        if weak_clarified_value(value):
            weak.append(field)

    return {
        "present": True,
        "ready": not missing and not weak,
        "missing_fields": missing,
        "weak_fields": weak,
    }


def clarified_return_context(request: str) -> dict[str, Any]:
    discovery = discovery_return_readiness(request)
    risk = risk_boundary_return_readiness(request)
    local_goal = local_goal_return_readiness(request)
    if risk["present"]:
        return {"type": "Risk Boundary", **risk}
    if discovery["present"]:
        return {"type": "Discovery", **discovery}
    if local_goal["present"]:
        return {"type": "Local Goal", **local_goal}
    return {"type": None, "present": False, "ready": None, "missing_fields": [], "weak_fields": []}


def inventory_decision_text(text: str) -> str:
    return h2_section_text(text, "Inventory Decision")


def inventory_run_value(text: str) -> str | None:
    value = field_value(inventory_decision_text(text), "Inventory Run")
    if re.fullmatch(r"yes", value, re.IGNORECASE):
        return "Yes"
    if re.fullmatch(r"no", value, re.IGNORECASE):
        return "No"
    return None


def inventory_input_value(text: str) -> str:
    return field_value(inventory_decision_text(text), "Inventory Input")


def inventory_decision_checks(text: str) -> tuple[dict[str, bool], list[str]]:
    mode_index = h2_section_index(text, "Mode Router")
    decision_index = h2_section_index(text, "Inventory Decision")
    report_index = h2_section_index(text, "Skill Inventory Report")
    decision_text = inventory_decision_text(text)
    inventory_run = inventory_run_value(text)
    reason = field_value(decision_text, "Reason")
    inventory_input = field_value(decision_text, "Inventory Input")

    checks = {
        "inventory_decision_present": decision_index is not None,
        "mode_router_before_inventory_decision": (
            mode_index is not None and decision_index is not None and mode_index < decision_index
        ),
        "inventory_decision_before_skill_inventory_report": (
            report_index is None or (
                decision_index is not None and decision_index < report_index
            )
        ),
        "inventory_run_allowed_value": inventory_run in {"Yes", "No"},
        "inventory_decision_reason_present": bool(reason.strip()),
        "inventory_decision_input_present": bool(inventory_input.strip()),
        "inventory_no_omits_skill_inventory_report": (
            inventory_run != "No" or report_index is None
        ),
        "skill_inventory_report_requires_inventory_yes": (
            report_index is None or inventory_run == "Yes"
        ),
        "inventory_yes_includes_skill_inventory_report": (
            inventory_run != "Yes" or report_index is not None
        ),
    }

    failures = []
    if decision_index is None:
        failures.append("Missing top-level sections: Inventory Decision")
    if not checks["mode_router_before_inventory_decision"]:
        failures.append("Mode Router must appear before Inventory Decision.")
    if not checks["inventory_decision_before_skill_inventory_report"]:
        failures.append("Inventory Decision must appear before Skill Inventory Report.")
    if inventory_run not in {"Yes", "No"}:
        failures.append("Inventory Decision must set Inventory Run to Yes or No.")
    if not reason.strip():
        failures.append("Inventory Decision must include a non-empty Reason.")
    if not inventory_input.strip():
        failures.append("Inventory Decision must include a non-empty Inventory Input.")
    if inventory_run == "No" and report_index is not None:
        failures.append("Inventory Run: No must not include Skill Inventory Report.")
    if report_index is not None and inventory_run != "Yes":
        failures.append("Skill Inventory Report may appear only when Inventory Run is Yes.")
    if inventory_run == "Yes" and report_index is None:
        failures.append("Inventory Run: Yes requires Skill Inventory Report.")
    return checks, failures


def clarification_type_value(text: str) -> str:
    value = field_value(h2_section_text(text, "Clarification Type"), "Type")
    return value.strip()


def goal_spec_text(text: str) -> str:
    return h2_section_text(text, "Goal Spec") or h2_section_text(text, "Partial Goal Spec")


def goal_spec_missing_fields(text: str) -> list[str]:
    spec = goal_spec_text(text)
    return [field for field in GOAL_SPEC_REQUIRED_FIELDS if not field_value(spec, field)]


def goal_spec_weak_fields(text: str) -> list[str]:
    spec = goal_spec_text(text)
    weak = []
    for field in GOAL_SPEC_REQUIRED_FIELDS:
        value = field_value(spec, field)
        if not value:
            continue
        if len(value.strip()) < 12 or GENERIC_FIELD_VALUE_RE.match(value) or VAGUE_GOAL_FIELD_VALUE_RE.match(value):
            weak.append(field)
    return weak


def has_first_slice_ready_yes(text: str) -> bool:
    combined = "\n".join([
        goal_spec_text(text),
        h2_section_text(text, "Task Mode Handoff"),
    ])
    return bool(re.search(r"Ready for Task Mode\s*[:：]\s*Yes\b", combined, re.IGNORECASE))


def route_decision_mentions(text: str, expected: str) -> bool:
    route_text = h2_section_text(text, "Route Decision")
    return bool(re.search(re.escape(expected), route_text, re.IGNORECASE))


def route_decision_next_route(text: str) -> str:
    return field_value(h2_section_text(text, "Route Decision"), "Next Route")


def route_decision_next_is(text: str, expected: str) -> bool:
    return bool(re.search(re.escape(expected), route_decision_next_route(text), re.IGNORECASE))


def hard_stop_violations(text: str) -> list[str]:
    violations = []
    for line in text.splitlines():
        if HARD_STOP_RE.search(line):
            violations.append(line.strip())
    return violations


def finalize_result(result: dict[str, Any], text: str) -> dict[str, Any]:
    violations = hard_stop_violations(text)
    result.setdefault("checks", {})["no_hard_stop"] = not violations
    if violations:
        result.setdefault("failures", []).append(
            "CEO outputs must route to clarification instead of using Hard Stop: "
            + " | ".join(violations[:3])
        )
    result["passed"] = bool(result.get("passed")) and not violations
    return result


def domain_gate_text(text: str) -> str:
    return h2_section_text(text, "Domain Gate")


def domain_gate_category(text: str) -> str:
    value = field_value(domain_gate_text(text), "Category")
    if re.search(r"\bGreen\b", value, re.IGNORECASE):
        return DOMAIN_GREEN
    if re.search(r"\bYellow\b", value, re.IGNORECASE):
        return DOMAIN_YELLOW
    if re.search(r"\bRed\b", value, re.IGNORECASE):
        return DOMAIN_RED
    return value.strip()


def missing_domain_gate_fields(text: str) -> list[str]:
    gate_text = domain_gate_text(text)
    return [field for field in DOMAIN_GATE_REQUIRED_FIELDS if not field_value(gate_text, field)]


def expected_domain_gate_for_request(request: str | None) -> dict[str, Any]:
    if not request:
        return {"category": None, "reason": None, "clarification_type": None}

    risk_hits = [term for term in RISK_DOMAIN_TERMS if has_unnegated_phrase(request, term)]
    discovery_hits = [term for term in DISCOVERY_DOMAIN_TERMS if has_unnegated_phrase(request, term)]
    yellow_hits = [term for term in YELLOW_DOMAIN_TERMS if has_unnegated_phrase(request, term)]

    return_context = clarified_return_context(request)
    if return_context["present"] and return_context["type"] == "Local Goal":
        if risk_hits:
            return {
                "category": DOMAIN_RED,
                "reason": "risk:" + ",".join(risk_hits[:4]),
                "clarification_type": "Risk Boundary",
            }
        if discovery_hits:
            return {
                "category": DOMAIN_RED,
                "reason": "discovery:" + ",".join(discovery_hits[:4]),
                "clarification_type": "Discovery",
            }
    if return_context["present"] and return_context["ready"]:
        return {"category": DOMAIN_GREEN, "reason": "ready-clarified-return", "clarification_type": None}
    if return_context["present"] and return_context["type"] == "Risk Boundary":
        return {"category": DOMAIN_RED, "reason": "risk-return-not-ready", "clarification_type": "Risk Boundary"}
    if return_context["present"] and return_context["type"] == "Discovery":
        return {"category": DOMAIN_RED, "reason": "discovery-return-not-ready", "clarification_type": "Discovery"}

    if risk_hits:
        return {
            "category": DOMAIN_RED,
            "reason": "risk:" + ",".join(risk_hits[:4]),
            "clarification_type": "Risk Boundary",
        }
    if discovery_hits:
        return {
            "category": DOMAIN_RED,
            "reason": "discovery:" + ",".join(discovery_hits[:4]),
            "clarification_type": "Discovery",
        }
    if yellow_hits:
        return {
            "category": DOMAIN_YELLOW,
            "reason": "yellow:" + ",".join(yellow_hits[:4]),
            "clarification_type": None,
        }
    return {"category": DOMAIN_GREEN, "reason": "green-default", "clarification_type": None}


def first_slice_text(text: str) -> str:
    combined = "\n".join([
        field_value(goal_spec_text(text), "First Executable Slice"),
        h2_section_text(text, "Task Mode Handoff"),
        h2_section_text(text, "Final Prompt"),
    ])
    return combined.strip()


def yellow_first_slice_bounded(text: str) -> bool:
    slice_text = first_slice_text(text)
    if not slice_text:
        return False
    has_allowed = bool(contains_any_phrase(slice_text, YELLOW_ALLOWED_SLICE_TERMS))
    has_disallowed = has_any_unnegated_phrase(slice_text, YELLOW_DISALLOWED_SLICE_TERMS)
    has_boundary = bool(
        re.search(
            r"\bbounded\b|\breversible\b|\bscope\b|\bnon[-\s]?goals?\b|"
            r"边界|可逆|范围|非目标|不做|no code changes|without code changes",
            slice_text,
            re.IGNORECASE,
        )
    )
    return has_allowed and has_boundary and not has_disallowed


def domain_gate_result(text: str, request: str | None) -> tuple[dict[str, Any], list[str]]:
    expected = expected_domain_gate_for_request(request)
    gate_present = h2_section_index(text, "Domain Gate") is not None
    missing_fields = missing_domain_gate_fields(text) if gate_present else DOMAIN_GATE_REQUIRED_FIELDS
    actual_category = domain_gate_category(text) if gate_present else ""
    status = goal_mode_status(text)
    clarification_type = clarification_type_value(text)
    failures: list[str] = []

    if not gate_present:
        failures.append("Goal Mode must include Domain Gate before Route Decision.")
    if missing_fields:
        failures.append("Domain Gate missing required fields: " + ", ".join(missing_fields))

    expected_category = expected["category"]
    if expected_category and actual_category != expected_category:
        failures.append(
            f"Domain Gate mismatch for request: expected {expected_category}, got {actual_category or 'unknown'}."
        )

    if expected_category == DOMAIN_RED:
        if status == "Complete" or route_decision_next_is(text, "Task Mode"):
            failures.append("Domain Gate Red must not route directly to Task Mode.")
        expected_clarification_type = expected["clarification_type"]
        if expected_clarification_type and not re.search(expected_clarification_type, clarification_type, re.IGNORECASE):
            failures.append(f"Domain Gate Red must route to {expected_clarification_type} clarification.")

    if expected_category == DOMAIN_YELLOW and status == "Complete":
        if not yellow_first_slice_bounded(text):
            failures.append(
                "Domain Gate Yellow may route to Task Mode only with a bounded, reversible analysis/design/doc/test slice."
            )

    if actual_category == DOMAIN_RED and status == "Complete":
        failures.append("Domain Gate Category Red cannot be paired with Goal Mode Complete -> Task Mode.")

    result = {
        "domain_gate_present": gate_present,
        "domain_gate_required_fields": not missing_fields,
        "domain_gate_expected": expected_category,
        "domain_gate_actual": actual_category,
        "domain_gate_matches_request": not expected_category or actual_category == expected_category,
        "domain_gate_red_blocks_task_mode": not (
            expected_category == DOMAIN_RED and (status == "Complete" or route_decision_next_is(text, "Task Mode"))
        ),
        "domain_gate_yellow_slice_bounded": not (
            expected_category == DOMAIN_YELLOW and status == "Complete" and not yellow_first_slice_bounded(text)
        ),
        "domain_gate_reason": expected["reason"],
    }
    return result, failures


def has_clarification_prompt_contract(prompt_text: str) -> bool:
    has_clarified_spec = "Clarified Spec" in prompt_text
    has_ceo_handoff = "$ceo" in prompt_text or re.search(
        r"back to\s+\$?ceo|return to\s+\$?ceo|回到\s*\$?ceo",
        prompt_text,
        re.IGNORECASE,
    )
    return has_clarified_spec and bool(has_ceo_handoff)


def missing_risk_boundary_prompt_fields(prompt_text: str) -> list[str]:
    return [field for field in RISK_BOUNDARY_PROMPT_FIELDS if not field_value(prompt_text, field)]


def risk_prompt_has_forbidden_readiness(prompt_text: str) -> bool:
    readiness = field_value(prompt_text, "Readiness")
    if re.fullmatch(r"\s*Ready for Execution\.?\s*", readiness, re.IGNORECASE):
        return True
    for line in prompt_text.splitlines():
        if re.search(r"\bReady for Execution\b", line, re.IGNORECASE) and not re.search(
            r"\bNot Ready for Execution\b", line, re.IGNORECASE
        ):
            return True
    return False


def text_has_shared_gap_phrase(gap_text: str, question_text: str) -> bool:
    gap_l = gap_text.lower()
    question_l = question_text.lower()
    quoted_phrases = re.findall(r'"([^"]{2,})"|“([^”]{2,})”|`([^`]{2,})`', gap_text)
    for groups in quoted_phrases:
        phrase = next((item for item in groups if item), "")
        if phrase and phrase.lower() in question_l:
            return True

    tokens = re.findall(r"[a-zA-Z][a-zA-Z-]{3,}|[\u4e00-\u9fff]{2,}", gap_text)
    stop_tokens = {
        "missing", "fields", "field", "vague", "route", "changing", "none",
        "detected", "enough", "defined", "method", "exists",
        "缺失", "字段", "模糊", "没有", "需要", "当前",
    }
    for token in tokens:
        token_l = token.lower()
        if token_l in stop_tokens:
            continue
        if token_l in question_l:
            return True
    return False


def blocking_question_targets_gap(gap_text: str, question_text: str) -> bool:
    if not gap_text.strip() or not question_text.strip():
        return False
    if text_has_shared_gap_phrase(gap_text, question_text):
        return True

    category_patterns = [
        (
            r"desired\s+end\s+state|observable|目标状态|期望状态|可观察",
            r"desired|end\s+state|observable|behavior|具体|体现|可观察|行为|目标状态|期望状态",
        ),
        (
            r"current\s+state|当前状态|现状",
            r"current|state|现在|当前|现状",
        ),
        (
            r"acceptance\s+criteria|pass/fail|验收|通过|失败|标准",
            r"acceptance|criteria|pass|fail|验收|通过|失败|标准|怎么算",
        ),
        (
            r"first\s+executable\s+slice|bounded\s+task|first\s+slice|首个|切片|可执行任务",
            r"first|slice|task|bounded|首个|切片|任务|哪一步|先做",
        ),
        (
            r"scope|non-goals|in\s+scope|out\s+of\s+scope|范围|非目标",
            r"scope|non-goal|范围|不做|包括|排除",
        ),
        (
            r"decision\s+boundar|route-changing|route|边界|路线|路径",
            r"decision|boundary|route|choose|边界|路线|路径|选择",
        ),
        (
            r"validation\s+method|proof|验证|证明",
            r"validation|prove|proof|verify|验证|证明|如何检查",
        ),
        (
            r"risk|authority|approval|production|security|风险|权限|授权|批准|审批|生产|安全",
            r"risk|authority|approval|permission|风险|权限|授权|批准|审批|生产|安全",
        ),
        (
            r"motivation|why|动机|为什么|原因",
            r"motivation|why|purpose|动机|为什么|原因",
        ),
    ]
    gap_l = gap_text.lower()
    question_l = question_text.lower()
    return any(
        re.search(gap_pattern, gap_l, re.IGNORECASE)
        and re.search(question_pattern, question_l, re.IGNORECASE)
        for gap_pattern, question_pattern in category_patterns
    )


def risk_prompt_execution_violations(prompt_text: str) -> list[str]:
    violations: list[str] = []
    exempt_markers = [
        "explicitly forbidden until approved",
        "out of scope",
        "non-goals",
        "stop conditions",
        "forbidden",
        "禁止",
        "不得",
        "不要",
        "不执行",
        "非目标",
        "停止条件",
    ]
    for line in prompt_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        line_l = stripped.lower()
        if any(marker in line_l for marker in exempt_markers):
            continue
        if RISK_EXECUTION_COMMAND_RE.search(stripped) or has_unnegated_execution_action(stripped):
            violations.append(stripped)
    return violations


def blocking_question_count(text: str) -> int:
    question_text = h2_section_text(text, "Blocking Question")
    if not question_text.strip():
        return 0
    markers = re.findall(r"[?？]", question_text)
    if markers:
        return len(markers)
    lines = [line for line in question_text.splitlines() if line.strip()]
    return len(lines)


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
    selected.discard(CANONICAL_HANDOFF_SKILL)
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
        elif any(is_semantically_generic_requirement_value(value) for value in meaningful):
            weak.append(label)
    return weak


def is_semantically_generic_requirement_value(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value.strip().lower()).strip(".")
    generic_patterns = [
        r"^(?:the\s+)?inputs?\s+and\s+context\s+are\s+covered$",
        r"^in\s+scope\s+is\s+handled$",
        r"^(?:non[-\s]?goals?|out\s+of\s+scope)\s+are\s+(?:considered|covered)$",
        r"^deliverables?\s+are\s+(?:produced|covered|handled)$",
        r"^(?:assumptions?,?\s*)?boundaries?,?\s*risk,?\s*and\s*reversibility\s+are\s+(?:included|covered|handled)$",
        r"^failure\s+and\s+escalation\s+are\s+handled$",
    ]
    return any(re.match(pattern, normalized) for pattern in generic_patterns)


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
        has_office_hours = (
            CANONICAL_CLARIFICATION_SKILL in selected_skills
            or any(alias in selected_skills for alias in CANONICAL_CLARIFICATION_ALIASES)
            or f"${CANONICAL_CLARIFICATION_SKILL}" in text
            or any(f"${alias}" in text for alias in CANONICAL_CLARIFICATION_ALIASES)
        )
        has_ceo_handoff = "$ceo" in text or re.search(r"back to\s+\$?ceo|return to\s+\$?ceo|回到\s*\$?ceo", text, re.IGNORECASE)
        asks_for_clarified_spec = "Clarified Spec" in final_prompt
        direct_execution = has_unnegated_execution_action(final_combined)
        forbidden_hard_route = forbidden_clarification_route_required(text)
        clarification_route_passed = (
            has_office_hours
            and has_ceo_handoff
            and asks_for_clarified_spec
            and not direct_execution
            and not forbidden_hard_route
        )
        if not has_office_hours:
            failures.append("Clarification Path must route to $office-hours.")
        if forbidden_hard_route:
            failures.append("Clarification Path must not make $deep-interview --quick or $deep-interview the canonical hard route.")
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


def forbidden_clarification_route_required(text: str) -> bool:
    """Detect forbidden clarification routes only when they are required/canonical, not historical notes."""
    route_patterns = [
        r"must\s+(?:route|use|invoke|call)\s+(?:to\s+)?[`'\"]?\$?{route}[`'\"]?",
        r"requires?\s+[`'\"]?\$?{route}[`'\"]?",
        r"canonical\s+(?:clarification\s+)?route\s*(?:is|:)?\s*[`'\"]?\$?{route}[`'\"]?",
        r"hard\s+(?:clarification\s+)?route\s*(?:is|:)?\s*[`'\"]?\$?{route}[`'\"]?",
        r"必须(?:路由|使用|调用)\s*[`'\"]?\$?{route}[`'\"]?",
        r"规范(?:澄清)?路由\s*(?:是|:)?\s*[`'\"]?\$?{route}[`'\"]?",
    ]
    text_l = text.lower()
    for route in FORBIDDEN_HARD_CLARIFICATION_ROUTES:
        escaped = re.escape(route.lower()).replace("\\ ", r"\s+")
        for pattern in route_patterns:
            if re.search(pattern.format(route=escaped), text_l, re.IGNORECASE):
                return True
    return False


def check_contract(text: str, request: str | None = None) -> dict[str, Any]:
    section_indices = find_section_indices(text)
    missing_sections = [
        section for section in REQUIRED_TOP_LEVEL_SECTIONS if section not in section_indices
    ]
    mode_actual = actual_mode(text)
    continue_to = mode_continue_to(text)
    missing_mode_router_fields = mode_router_missing_fields(text)
    inventory_checks, inventory_failures = inventory_decision_checks(text)
    inventory_run = inventory_run_value(text)
    return_context = clarified_return_context(request or "")

    if mode_actual == MODE_GOAL and goal_mode_status(text) == "Incomplete":
        required_goal_sections = [
            "Mode Router",
            "Goal Mode",
            "Goal Contract Check",
            "Clarification Type",
            "Inventory Decision",
            "Route Decision",
            "Blocking Question",
            "Why This Question Comes First",
        ]
        goal_missing_sections = [
            section
            for section in required_goal_sections
            if not h2_section_text(text, section).strip()
            and not re.search(rf"^\s*##\s+{re.escape(section)}\s*$", text, re.MULTILINE)
        ]
        final_prompt = section_text(text, "Final Prompt")
        inventory_text = h2_section_text(text, "Skill Inventory Report")
        route_text = h2_section_text(text, "Route Decision")
        gap_text = h2_section_text(text, "Goal Contract Check")
        clarification_type_text = h2_section_text(text, "Clarification Type")
        question_count = blocking_question_count(text)
        question_text = h2_section_text(text, "Blocking Question")
        checks = {
            "mode_router_present": "Mode Router" in section_indices,
            "mode_router_required_fields": not missing_mode_router_fields,
            "mode_router_goal_mode": mode_actual == MODE_GOAL,
            "goal_mode_status_incomplete": goal_mode_status(text) == "Incomplete",
            "goal_mode_required_sections": not goal_missing_sections,
            "goal_contract_gap_report_present": bool(gap_text.strip()),
            "clarification_type_local_goal": bool(re.search(r"Local Goal", clarification_type_text, re.IGNORECASE)),
            "inventory_decision_contract": not inventory_failures,
            "inventory_run_no": inventory_run == "No",
            "route_decision_stays_in_goal_mode": bool(re.search(r"Stay in Goal Mode", route_text, re.IGNORECASE)),
            "blocking_question_count_one": question_count == 1,
            "blocking_question_targets_gap": blocking_question_targets_gap(gap_text, question_text),
            "no_skill_inventory_report": not inventory_text.strip(),
            "no_final_prompt": not final_prompt.strip(),
        }
        failures = []
        if "Mode Router" not in section_indices:
            failures.append("Missing top-level sections: Mode Router")
        if missing_mode_router_fields:
            failures.append("Mode Router missing required fields: " + ", ".join(missing_mode_router_fields))
        if mode_actual != MODE_GOAL:
            failures.append("Mode Router must classify incomplete goals as Goal Mode.")
        if goal_mode_status(text) != "Incomplete":
            failures.append("Goal Mode section must set Status: Incomplete.")
        if goal_missing_sections:
            failures.append("Missing Goal Mode incomplete sections: " + ", ".join(goal_missing_sections))
        if not gap_text.strip():
            failures.append("Goal Contract Check section is empty or missing.")
        if not checks["clarification_type_local_goal"]:
            failures.append("Goal Mode Incomplete must set Clarification Type: Local Goal.")
        failures.extend(inventory_failures)
        if inventory_run != "No":
            failures.append("Goal Mode Incomplete must set Inventory Run: No.")
        if not checks["route_decision_stays_in_goal_mode"]:
            failures.append("Route Decision must keep incomplete goals in Goal Mode.")
        if question_count != 1:
            failures.append(f"Goal Mode Incomplete must ask exactly one Blocking Question, found {question_count}.")
        if not checks["blocking_question_targets_gap"]:
            failures.append("Goal Mode Incomplete Blocking Question must target a reported gap.")
        if inventory_text.strip():
            failures.append("Goal Mode Incomplete must not include Skill Inventory Report.")
        if final_prompt.strip():
            failures.append("Goal Mode Incomplete must not include Final Prompt.")
        return finalize_result({
            "passed": all(checks.values()),
            "checks": checks,
            "failures": failures,
            "missing_sections": goal_missing_sections,
            "missing_final_prompt_headings": [],
            "selected_skills": [],
            "inventory_candidate_names": [],
            "untraceable_skills": [],
            "semantic_failures": [],
            "triage_expected": None,
            "triage_actual": None,
            "triage_passed": True,
            "triage_reasons": [],
            "clarification_route_passed": True,
            "clarified_spec_readiness": clarified_spec_readiness(request or ""),
            "clarified_return_context": return_context,
            "mode_actual": mode_actual,
            "mode_continue_to": continue_to,
            "goal_mode_status": goal_mode_status(text),
        }, text)

    if mode_actual == MODE_GOAL and goal_mode_status(text) == "Complete":
        required_goal_sections = [
            "Mode Router",
            "Goal Mode",
            "Goal Spec",
            "Goal Contract Check",
            "Domain Gate",
            "Clarification Type",
            "Inventory Decision",
            "Skill Inventory Report",
            "Route Decision",
            "Task Mode Handoff",
            "Skill Match",
            "Contract Check",
            "Final Prompt",
            "Assumptions",
        ]
        goal_missing_sections = [
            section
            for section in required_goal_sections
            if h2_section_index(text, section) is None
        ]
        spec_missing_fields = goal_spec_missing_fields(text)
        spec_weak_fields = goal_spec_weak_fields(text)
        domain_result, domain_failures = domain_gate_result(text, request)
        clarification_type = clarification_type_value(text)
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
            "mode_router_present": "Mode Router" in section_indices,
            "mode_router_required_fields": not missing_mode_router_fields,
            "mode_router_goal_mode": mode_actual == MODE_GOAL,
            "goal_mode_status_complete": goal_mode_status(text) == "Complete",
            "goal_mode_required_sections": not goal_missing_sections,
            "goal_spec_required_fields": not spec_missing_fields,
            "goal_spec_field_quality": not spec_weak_fields,
            "domain_gate_contract": not domain_failures,
            "clarification_type_not_required": bool(re.search(r"Not Required", clarification_type, re.IGNORECASE)),
            "first_executable_slice_ready": has_first_slice_ready_yes(text),
            "clarified_return_ready": (not return_context["present"] or return_context["ready"]),
            "inventory_decision_contract": not inventory_failures,
            "inventory_run_yes": inventory_run == "Yes",
            "inventory_input_first_slice": bool(re.search(r"First Executable Slice", inventory_input_value(text), re.IGNORECASE)),
            "inventory_input_return_context": (
                not return_context["present"]
                or (
                    return_context["type"] == "Discovery"
                    and bool(re.search(r"Discovery Context|Clarified Spec", inventory_input_value(text), re.IGNORECASE))
                )
                or (
                    return_context["type"] == "Risk Boundary"
                    and bool(re.search(r"Risk-Bounded Clarified Spec", inventory_input_value(text), re.IGNORECASE))
                )
                or (
                    return_context["type"] == "Local Goal"
                    and bool(
                        re.search(
                            r"Local Goal Clarified Spec|Goal Spec|compact Goal Spec context|Clarified Spec",
                            inventory_input_value(text),
                            re.IGNORECASE,
                        )
                    )
                )
            ),
            "inventory_counts_present": has_inventory_counts(inventory_text),
            "inventory_operational_fields_present": has_inventory_operational_fields(inventory_text),
            "route_decision_task_mode": route_decision_mentions(text, "Task Mode"),
            "final_prompt_present": bool(final_prompt.strip()),
            "final_prompt_headings_present": not missing_final_headings,
            "final_prompt_headings_in_order": final_headings_in_order,
            "skill_source_traceable": not untraceable_skills,
            "semantic_contract_complete": not semantic_failures,
        }
        failures = []
        if missing_mode_router_fields:
            failures.append("Mode Router missing required fields: " + ", ".join(missing_mode_router_fields))
        if goal_missing_sections:
            failures.append("Missing Goal Mode Complete sections: " + ", ".join(goal_missing_sections))
        if spec_missing_fields:
            failures.append("Goal Spec missing required fields: " + ", ".join(spec_missing_fields))
        if spec_weak_fields:
            failures.append("Goal Spec has vague or placeholder fields: " + ", ".join(spec_weak_fields))
        failures.extend(domain_failures)
        if not checks["clarification_type_not_required"]:
            failures.append("Goal Mode Complete must set Clarification Type: Not Required.")
        if not checks["first_executable_slice_ready"]:
            failures.append("Goal Mode Complete must mark First Executable Slice Ready for Task Mode: Yes.")
        if return_context["present"] and not return_context["ready"]:
            failures.append(
                f"{return_context['type']} Clarified Spec return is not ready for Task Mode: "
                + ", ".join(return_context["missing_fields"] + return_context["weak_fields"])
            )
        failures.extend(inventory_failures)
        if inventory_run != "Yes":
            failures.append("Goal Mode Complete -> Task Mode must set Inventory Run: Yes.")
        if not checks["inventory_input_first_slice"]:
            failures.append("Goal Mode Complete -> Task Mode Inventory Input must mention First Executable Slice.")
        if not checks["inventory_input_return_context"]:
            failures.append(
                f"Goal Mode Complete -> Task Mode Inventory Input must mention {return_context['type']} return context."
            )
        if not checks["route_decision_task_mode"]:
            failures.append("Goal Mode Complete Route Decision must route to Task Mode.")
        if not checks["inventory_counts_present"]:
            failures.append("Skill Inventory Report is missing required count fields.")
        if not checks["inventory_operational_fields_present"]:
            failures.append("Skill Inventory Report is missing roots, complexity, candidates, or finalists.")
        if not final_prompt.strip():
            failures.append("Final Prompt section is empty or missing.")
        if missing_final_headings:
            failures.append("Missing Final Prompt headings: " + ", ".join(missing_final_headings))
        if not final_headings_in_order:
            failures.append("Final Prompt headings are present but out of order.")
        if untraceable_skills:
            failures.append("Selected skills are not traceable to inventory candidates: " + ", ".join(untraceable_skills))
        failures.extend(semantic_failures)
        return finalize_result({
            "passed": all(checks.values()),
            "checks": checks,
            "failures": failures,
            "missing_sections": goal_missing_sections,
            "missing_final_prompt_headings": missing_final_headings,
            "selected_skills": sorted(selected_skills),
            "inventory_candidate_names": sorted(inventory_names),
            "untraceable_skills": untraceable_skills,
            "semantic_failures": semantic_failures,
            "triage_expected": None,
            "triage_actual": None,
            "triage_passed": True,
            "triage_reasons": [],
            "clarification_route_passed": True,
            "clarified_spec_readiness": clarified_spec_readiness(request or ""),
            "clarified_return_context": return_context,
            "domain_gate": domain_result,
            "mode_actual": mode_actual,
            "mode_continue_to": continue_to,
            "goal_mode_status": goal_mode_status(text),
        }, text)

    if mode_actual == MODE_GOAL and goal_mode_status(text) == "Routed":
        clarification_type = clarification_type_value(text)
        discovery_route = bool(re.search(r"Discovery", clarification_type, re.IGNORECASE))
        risk_route = bool(re.search(r"Risk Boundary", clarification_type, re.IGNORECASE))
        required_goal_sections = [
            "Mode Router",
            "Goal Mode",
            "Goal Contract Check",
            "Domain Gate",
            "Clarification Type",
            "Inventory Decision",
            "Route Decision",
        ]
        if discovery_route:
            required_goal_sections.extend(["Skill Inventory Report", "Final Prompt"])
        if risk_route:
            required_goal_sections.append("Clarification Prompt")
        goal_missing_sections = [
            section
            for section in required_goal_sections
            if h2_section_index(text, section) is None
        ]
        if not goal_spec_text(text).strip():
            goal_missing_sections.append("Goal Spec or Partial Goal Spec")

        domain_result, domain_failures = domain_gate_result(text, request)
        inventory_text = section_text(text, "Skill Inventory Report")
        skill_match_text = section_text(text, "Skill Match")
        final_prompt = section_text(text, "Final Prompt")
        risk_prompt = h2_section_text(text, "Clarification Prompt")
        route_text = h2_section_text(text, "Route Decision")
        inventory_names = inventory_candidate_names(inventory_text)
        selected_skills = invoked_skills(skill_match_text, final_prompt)
        untraceable_skills = sorted(skill for skill in selected_skills if skill not in inventory_names)
        risk_missing_fields = missing_risk_boundary_prompt_fields(risk_prompt) if risk_route else []
        risk_execution_violations = risk_prompt_execution_violations(risk_prompt) if risk_route else []
        discovery_direct_execution = (
            has_unnegated_execution_action(final_prompt)
            or has_unnegated_execution_action(final_prompt_section_text(final_prompt, "Objective"))
            or has_unnegated_execution_action(final_prompt_section_text(final_prompt, "Requirements"))
        )
        recommended_office_hours = (
            "$office-hours" in route_text
            or "$office-hours" in final_prompt
            or CANONICAL_CLARIFICATION_SKILL in selected_skills
            or any(alias in selected_skills for alias in CANONICAL_CLARIFICATION_ALIASES)
        )
        checks = {
            "mode_router_present": "Mode Router" in section_indices,
            "mode_router_required_fields": not missing_mode_router_fields,
            "mode_router_goal_mode": mode_actual == MODE_GOAL,
            "goal_mode_status_routed": goal_mode_status(text) == "Routed",
            "goal_mode_required_sections": not goal_missing_sections,
            "domain_gate_contract": not domain_failures,
            "clarification_type_supported": discovery_route or risk_route,
            "inventory_decision_contract": not inventory_failures,
            "route_decision_clarification": route_decision_mentions(text, "Clarification"),
            "discovery_inventory_run_yes": (not discovery_route or inventory_run == "Yes"),
            "discovery_inventory_report_present": (not discovery_route or bool(inventory_text.strip())),
            "discovery_recommends_office_hours": (not discovery_route or recommended_office_hours),
            "discovery_prompt_is_clarification": (not discovery_route or has_clarification_prompt_contract(final_prompt)),
            "discovery_prompt_not_execution": (not discovery_route or not discovery_direct_execution),
            "risk_prompt_required_fields": (not risk_route or not risk_missing_fields),
            "risk_prompt_readiness_not_execution": (not risk_route or not risk_prompt_has_forbidden_readiness(risk_prompt)),
            "risk_prompt_no_execution_commands": (not risk_route or not risk_execution_violations),
            "skill_source_traceable": not untraceable_skills,
        }
        failures = []
        if missing_mode_router_fields:
            failures.append("Mode Router missing required fields: " + ", ".join(missing_mode_router_fields))
        if goal_missing_sections:
            failures.append("Missing Goal Mode Routed sections: " + ", ".join(goal_missing_sections))
        failures.extend(domain_failures)
        if not checks["clarification_type_supported"]:
            failures.append("Goal Mode Routed must set Clarification Type to Discovery or Risk Boundary.")
        failures.extend(inventory_failures)
        if not checks["route_decision_clarification"]:
            failures.append("Goal Mode Routed Route Decision must route to Clarification.")
        if discovery_route:
            if inventory_run != "Yes":
                failures.append("Discovery Clarification must set Inventory Run: Yes.")
            if not inventory_text.strip():
                failures.append("Discovery Clarification must include Skill Inventory Report.")
            elif not has_inventory_counts(inventory_text) or not has_inventory_operational_fields(inventory_text):
                failures.append("Discovery Clarification Skill Inventory Report is incomplete.")
            if not recommended_office_hours:
                failures.append("Discovery Clarification must recommend $office-hours when available.")
            if not has_clarification_prompt_contract(final_prompt):
                failures.append("Discovery Clarification Final Prompt must require a Clarified Spec and $ceo handoff.")
            if discovery_direct_execution:
                failures.append("Discovery Clarification must not produce an execution prompt.")
        if risk_route:
            if risk_missing_fields:
                failures.append("Risk Boundary Clarification Prompt missing fields: " + ", ".join(risk_missing_fields))
            if risk_prompt_has_forbidden_readiness(risk_prompt):
                failures.append("Risk Boundary Clarification must not claim Ready for Execution.")
            if risk_execution_violations:
                failures.append(
                    "Risk Boundary Clarification must not include execution commands or operational steps: "
                    + " | ".join(risk_execution_violations[:3])
                )
        if untraceable_skills:
            failures.append("Selected skills are not traceable to inventory candidates: " + ", ".join(untraceable_skills))
        return finalize_result({
            "passed": all(checks.values()),
            "checks": checks,
            "failures": failures,
            "missing_sections": goal_missing_sections,
            "missing_final_prompt_headings": [],
            "selected_skills": sorted(selected_skills),
            "inventory_candidate_names": sorted(inventory_names),
            "untraceable_skills": untraceable_skills,
            "semantic_failures": [],
            "triage_expected": None,
            "triage_actual": None,
            "triage_passed": True,
            "triage_reasons": [],
            "clarification_route_passed": discovery_route and not failures if discovery_route else True,
            "clarified_spec_readiness": clarified_spec_readiness(request or ""),
            "clarified_return_context": return_context,
            "domain_gate": domain_result,
            "mode_actual": mode_actual,
            "mode_continue_to": continue_to,
            "goal_mode_status": goal_mode_status(text),
            "clarification_type": clarification_type,
        }, text)

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
        "mode_router_present": "Mode Router" in section_indices,
        "mode_router_required_fields": not missing_mode_router_fields,
        "mode_router_task_mode": mode_actual == MODE_TASK,
        "mode_router_continue_to_demand_triage": bool(re.search(r"Demand Triage", continue_to, re.IGNORECASE)),
        "clarified_goal_return_uses_goal_mode": not return_context["present"],
        "required_top_level_sections": not missing_sections,
        "inventory_decision_contract": not inventory_failures,
        "inventory_run_yes": inventory_run == "Yes",
        "inventory_input_raw_user_request": bool(
            re.search(r"Raw user request", inventory_input_value(text), re.IGNORECASE)
        ),
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
    if missing_mode_router_fields:
        failures.append("Mode Router missing required fields: " + ", ".join(missing_mode_router_fields))
    if "Mode Router" in section_indices and mode_actual != MODE_TASK:
        failures.append("Task Mode executable outputs must set Mode Router Mode: Task Mode.")
    if "Mode Router" in section_indices and not re.search(r"Demand Triage", continue_to, re.IGNORECASE):
        failures.append("Task Mode executable outputs must set Mode Router Continue To: Demand Triage.")
    if return_context["present"]:
        failures.append(f"{return_context['type']} Clarified Spec return must be re-evaluated through Goal Mode.")
    failures.extend(inventory_failures)
    if inventory_run != "Yes":
        failures.append("Task Mode executable outputs must set Inventory Run: Yes.")
    if not re.search(r"Raw user request", inventory_input_value(text), re.IGNORECASE):
        failures.append("Task Mode Inventory Input must be Raw user request.")
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

    return finalize_result({
        "passed": all(checks.values()),
        "checks": checks,
        "failures": failures,
        "missing_sections": missing_sections,
        "missing_final_prompt_headings": missing_final_headings,
        "selected_skills": sorted(selected_skills),
        "inventory_candidate_names": sorted(inventory_names),
        "untraceable_skills": untraceable_skills,
        "semantic_failures": semantic_failures,
        "mode_actual": mode_actual,
        "mode_continue_to": continue_to,
        "goal_mode_status": goal_mode_status(text),
        "clarified_return_context": return_context,
        **triage_result,
    }, text)


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
