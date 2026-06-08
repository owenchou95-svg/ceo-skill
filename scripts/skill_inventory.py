#!/usr/bin/env python3
"""Full frontmatter inventory and deterministic candidate recall for the CEO skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def agents_home() -> Path:
    return Path(os.environ.get("AGENTS_HOME", Path.home() / ".agents")).expanduser()


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")).expanduser()


def openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", Path.home() / ".openclaw")).expanduser()


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def default_roots() -> list[str]:
    code_home = codex_home()
    return [
        str(code_home / "skills"),
        str(code_home / "plugins" / "cache"),
        str(agents_home() / "skills"),
        str(claude_home() / "skills"),
        str(openclaw_home() / "skills"),
        str(hermes_home() / "skills"),
    ]


def plugin_cache_root() -> Path:
    return codex_home() / "plugins" / "cache"

GENERIC_QUERY_TOKENS = {
    "about",
    "acceptance",
    "agent",
    "around",
    "back",
    "boundaries",
    "boundary",
    "brief",
    "checks",
    "clear",
    "constraints",
    "context",
    "current",
    "deliverable",
    "deliverables",
    "done",
    "existing",
    "final",
    "from",
    "goal",
    "handoff",
    "input",
    "inputs",
    "into",
    "local",
    "main",
    "none",
    "open",
    "output",
    "project",
    "report",
    "request",
    "rough",
    "scope",
    "short",
    "spec",
    "states",
    "summary",
    "target",
    "task",
    "turn",
    "using",
    "verify",
    "work",
    "workflow",
    "works",
}

MARKDOWN_DOC_TERMS = [
    "readme",
    "markdown",
    ".md",
    ".mdx",
    "安装步骤",
    "本地开发命令",
]

OFFICE_DOC_TERMS = [
    "docx",
    "word",
    "google docs",
    "google doc",
    "pptx",
    "powerpoint",
    "excel",
    "xlsx",
]

OUT_OF_SCOPE_HEADER_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:#{1,6}\s*)?"
    r"(?:out\s+of\s+scope(?:\s*/\s*non[-\s]?goals?)?|non[-\s]?goals?|"
    r"not\s+in\s+scope|不在范围|范围外|非目标|不做)\s*:?\s*(.*)$",
    re.IGNORECASE,
)

INLINE_EXCLUSION_RES = [
    re.compile(
        r"\b(?:do\s+not|don't|dont|without|skip|avoid|no)\s+([^.;\n。；]+)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:不要|不用|无需|不需要|别|避免|跳过|不做)([^.;\n。；]+)"),
]

POSITIVE_HEADER_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:#{1,6}\s*)?"
    r"(?:goal|objective|deliverables?|in\s+scope|inputs?\s*/\s*context|inputs?|context|"
    r"decision\s+boundaries|constraints?|acceptance\s+criteria|requirements?|"
    r"risks?\s+and\s+reversibility|open\s+questions|ceo\s+handoff\s+summary|"
    r"目标|交付物|范围内|输入|上下文|决策边界|约束|验收标准|需求|风险|开放问题)\s*:?\s*(.*)$",
    re.IGNORECASE,
)

TASK_TYPES = {
    "frontend": [
        "frontend",
        "front-end",
        "ui",
        "website",
        "web",
        "web app",
        "landing",
        "prototype",
        "demo",
        "game",
        "app",
        "tool",
        "前端",
        "网页",
        "网站",
        "页面",
        "界面",
        "应用",
        "原型",
        "游戏",
        "工具",
        "番茄钟",
    ],
    "browser": [
        "browser",
        "chrome",
        "playwright",
        "screenshot",
        "responsive",
        "浏览器",
        "网页",
        "截图",
        "响应式",
        "移动端",
        "番茄钟",
    ],
    "design": ["design", "visual", "ux", "ui", "mockup", "wireframe", "设计", "视觉", "交互", "原型"],
    "github": ["github", "pull request", "pr", "issue", "ci", "review comments", "github", "拉取请求"],
    "ci": ["ci", "check", "workflow", "github actions", "构建", "检查", "流水线"],
    "deploy": ["deploy", "deployment", "cloudflare", "netlify", "release", "部署", "发布", "上线"],
    "security": ["security", "auth", "threat", "vulnerability", "安全", "权限", "鉴权", "漏洞"],
    "legal": ["legal", "law", "case", "brief", "bar", "法律", "法学", "案例"],
    "document": ["document", "docx", "word", "docs", "文档"],
    "repo-doc": ["readme", "markdown", ".md", ".mdx", "安装步骤", "本地开发命令"],
    "spreadsheet": ["spreadsheet", "sheet", "excel", "csv", "表格", "电子表格"],
    "presentation": ["presentation", "slides", "ppt", "powerpoint", "deck", "演示文稿", "幻灯片"],
    "pdf": ["pdf", "pdf"],
    "research": ["research", "search", "source", "citation", "研究", "检索", "引用"],
    "debugging": ["debug", "bug", "fix", "error", "failure", "stack trace", "调试", "错误", "报错", "修复"],
    "testing": ["test", "qa", "playwright", "verify", "测试", "验证", "检查"],
    "refactor": ["refactor", "cleanup", "deslop", "simplify", "重构", "清理", "优化"],
    "planning": ["plan", "prd", "spec", "requirements", "strategy", "计划", "规划", "方案", "需求"],
    "ideation": [
        "idea",
        "brainstorm",
        "think through",
        "worth building",
        "office hours",
        "not sure",
        "uncertain",
        "想清楚",
        "不确定",
        "想法",
        "点子",
        "头脑风暴",
        "值得做",
        "探索",
        "概念",
    ],
    "code-review": ["code review", "api", "client", "breaking change", "代码审查", "接口", "客户端", "破坏"],
    "automation": ["automation", "automate", "reminder", "monitor", "自动化", "提醒", "监控"],
    "image": ["image", "photo", "picture", "canva", "figma", "图片", "图像", "设计图"],
    "video": ["video", "animation", "hyperframes", "remotion", "视频", "动画"],
    "chrome": ["chrome", "browser tab", "extension", "浏览器标签", "扩展"],
}

SKILL_DOMAIN_TERMS = {
    "frontend": ["frontend", "front-end", "website", "web app", "ui", "prototype", "landing", "html", "css", "react"],
    "browser": ["browser", "playwright", "chrome", "responsive", "browser-use"],
    "design": ["design", "visual", "ux", "ui", "figma", "canva", "mockup", "wireframe"],
    "github": ["github", "pull request", "pr", "issue", "review thread", "review comment"],
    "ci": ["ci", "github actions", "workflow", "check", "build log"],
    "deploy": ["deploy", "deployment", "release", "netlify", "cloudflare", "ship"],
    "security": ["security", "auth", "threat", "vulnerability", "csrf", "xss"],
    "legal": ["legal", "law", "case", "brief", "bar"],
    "document": ["document", "docx", "word", "docs"],
    "repo-doc": ["readme", "markdown", ".md", ".mdx", "repository docs", "developer docs"],
    "spreadsheet": ["spreadsheet", "sheet", "excel", "csv"],
    "presentation": ["presentation", "slides", "ppt", "powerpoint", "deck"],
    "pdf": ["pdf"],
    "research": ["research", "source", "citation", "web search"],
    "debugging": ["debug", "bug", "error", "failure", "stack trace", "diagnose"],
    "testing": ["test", "testing", "unit test", "integration test", "playwright"],
    "refactor": ["refactor", "cleanup", "simplify", "deslop"],
    "planning": ["plan", "prd", "spec", "requirements", "strategy"],
    "ideation": ["idea", "brainstorm", "office hours", "worth building", "think through", "startup", "product idea"],
    "code-review": ["code review", "pull request", "maintainability", "quality", "breaking change", "api"],
    "automation": ["automation", "automate", "monitor", "reminder"],
    "image": ["image", "photo", "picture", "canva", "figma"],
    "video": ["video", "animation", "hyperframes", "remotion"],
    "chrome": ["chrome", "browser tab", "extension"],
}

ROUTING_HINT_BOOSTS = {
    "frontend": {
        "frontend-skill": 14,
        "prototype": 4,
        "web-clone": 4,
        "design-html": 3,
        "figma-implement-design": 3,
    },
    "browser": {
        "playwright": 7,
        "playwright-interactive": 6,
        "control-in-app-browser": 6,
        "control-chrome": 4,
        "browse": 4,
    },
    "github": {
        "github": 8,
        "gh-address-comments": 7,
        "gh-fix-ci": 6,
        "code-review": 5,
        "review": 4,
    },
    "ci": {
        "gh-fix-ci": 8,
        "github": 5,
        "diagnose": 4,
        "doctor": 3,
    },
    "code-review": {
        "code-review": 9,
        "review": 7,
        "github": 4,
        "gh-address-comments": 4,
        "plan-eng-review": 3,
    },
    "security": {
        "security-review": 9,
        "security-best-practices": 8,
        "security-threat-model": 7,
        "cso": 5,
    },
    "deploy": {
        "cloudflare-deploy": 8,
        "netlify-deploy": 8,
        "ship": 6,
        "land-and-deploy": 6,
        "setup-deploy": 4,
    },
    "document": {"documents": 8, "pdf": 4},
    "repo-doc": {"devex-review": 2, "health": 1},
    "spreadsheet": {"spreadsheets": 8},
    "presentation": {"presentations": 8, "canva-branded-presentation": 6},
    "pdf": {"pdf": 8, "latex-compile": 5},
    "research": {"cocounsel-legal:deep-research": 8, "scrape": 4, "openai-docs": 3},
    "debugging": {"diagnose": 8, "investigate": 7, "gh-fix-ci": 4, "doctor": 4},
    "testing": {"tdd": 5, "qa": 6, "qa-only": 5, "playwright": 5},
    "refactor": {"ai-slop-cleaner": 7, "code-review": 5, "tdd": 4},
    "planning": {"plan": 6, "ralplan": 5, "plan-eng-review": 5, "plan-ceo-review": 5},
    "ideation": {"office-hours": 22, "plan-ceo-review": 4, "design-consultation": 3, "grill-me": 3},
    "image": {"canva-branded-presentation": 5, "imagegen": 5, "figma-generate-design": 4},
}

ADJACENT_TASK_TYPES = {
    "frontend": ["browser", "design", "testing"],
    "browser": ["frontend", "testing", "chrome"],
    "design": ["frontend", "image", "presentation"],
    "github": ["ci", "deploy", "code-review"],
    "ci": ["github", "testing", "debugging"],
    "deploy": ["ci", "github", "security"],
    "security": ["deploy", "debugging", "code-review"],
    "document": ["pdf", "presentation", "research"],
    "repo-doc": ["document", "testing", "ci"],
    "presentation": ["document", "image", "design"],
    "research": ["document", "legal", "security"],
    "debugging": ["testing", "ci", "code-review"],
    "testing": ["debugging", "browser", "ci"],
    "refactor": ["testing", "code-review"],
    "planning": ["research", "code-review", "design"],
    "ideation": ["planning", "design", "frontend"],
    "automation": ["browser", "github", "deploy"],
    "image": ["design", "presentation"],
    "video": ["image", "frontend"],
    "chrome": ["browser", "automation"],
}

CAPABILITIES = {
    "build": {
        "request": ["build", "create", "make", "generate", "implement", "做", "创建", "生成", "实现", "搭建"],
        "skill": ["build", "create", "generate", "implement", "scaffold", "prototype"],
    },
    "edit": {
        "request": ["edit", "modify", "update", "change", "revise", "修改", "编辑", "更新", "调整"],
        "skill": ["edit", "modify", "update", "change", "revise"],
    },
    "review": {
        "request": ["review", "evaluate", "audit", "assess", "评估", "审查", "审核", "分析"],
        "skill": ["review", "evaluate", "audit", "assess", "analyze"],
    },
    "fix": {
        "request": ["fix", "repair", "resolve", "debug", "修复", "解决", "排查"],
        "skill": ["fix", "repair", "resolve", "debug", "diagnose"],
    },
    "test": {
        "request": ["test", "verify", "qa", "check", "测试", "验证", "检查"],
        "skill": ["test", "verify", "qa", "check", "validate"],
    },
    "deploy": {
        "request": ["deploy", "ship", "release", "部署", "上线", "发布"],
        "skill": ["deploy", "ship", "release", "publish"],
    },
    "research": {
        "request": ["research", "search", "lookup", "cite", "研究", "检索", "查找", "引用"],
        "skill": ["research", "search", "lookup", "cite", "source"],
    },
    "summarize": {
        "request": ["summarize", "brief", "outline", "总结", "摘要", "提纲"],
        "skill": ["summarize", "brief", "outline", "extract"],
    },
    "translate": {
        "request": ["translate", "translation", "翻译"],
        "skill": ["translate", "translation", "localize"],
    },
    "scrape": {
        "request": ["scrape", "crawl", "extract", "抓取", "爬取", "提取"],
        "skill": ["scrape", "crawl", "extract"],
    },
    "automate": {
        "request": ["automate", "automation", "monitor", "remind", "自动化", "监控", "提醒"],
        "skill": ["automate", "automation", "monitor", "reminder"],
    },
    "inspect": {
        "request": ["inspect", "analyze", "investigate", "查看", "检查", "分析", "调查"],
        "skill": ["inspect", "analyze", "investigate", "diagnose"],
    },
}

VALIDATION_HINTS = {
    "browser-validation": {
        "request": ["browser", "frontend", "web", "responsive", "screenshot", "浏览器", "网页", "移动端", "截图"],
        "skill": ["playwright", "browser", "chrome", "screenshot", "visual"],
    },
    "visual-validation": {
        "request": ["visual", "design", "layout", "ui", "视觉", "设计", "布局", "界面"],
        "skill": ["visual", "design-review", "figma", "canva", "screenshot"],
    },
    "ci-validation": {
        "request": ["ci", "check", "build", "test", "构建", "测试", "检查"],
        "skill": ["ci", "github", "test", "build", "qa"],
    },
    "security-validation": {
        "request": ["security", "auth", "permission", "安全", "权限", "鉴权"],
        "skill": ["security", "threat", "audit", "review"],
    },
    "artifact-validation": {
        "request": ["document", "slides", "spreadsheet", "pdf", "文档", "幻灯片", "表格"],
        "skill": ["documents", "presentations", "spreadsheets", "pdf", "latex"],
    },
}

HIGH_RISK_TERMS = [
    "production",
    "database",
    "delete",
    "payment",
    "auth",
    "security",
    "legal",
    "deploy",
    "生产",
    "数据库",
    "删除",
    "支付",
    "权限",
    "安全",
    "法律",
    "部署",
]

COMPARISON_TERMS = [
    "compare",
    "multiple skills",
    "plugin",
    "skill",
    "alternative",
    "比较",
    "多个技能",
    "插件",
    "技能",
    "候选",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9:_-]*|[\u4e00-\u9fff]+", normalize(text))


def significant_query_token(token: str) -> bool:
    token = normalize(token)
    if not token or token in GENERIC_QUERY_TOKENS:
        return False
    if token.isascii():
        if len(token) < 5:
            return False
        if token.isdigit():
            return False
    return True


def contains_any(text: str, terms: list[str]) -> list[str]:
    haystack = normalize(text)
    matches = []
    for term in terms:
        normalized = normalize(term)
        if not normalized:
            continue
        if normalized.isascii() and re.fullmatch(r"[a-z0-9]+", normalized):
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", haystack):
                matches.append(term)
        elif normalized in haystack:
            matches.append(term)
    return matches


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            first = handle.readline()
            if first.strip() != "---":
                return {}
            lines = []
            for line in handle:
                if line.strip() == "---":
                    break
                lines.append(line.rstrip("\n"))
            else:
                return {}
    except OSError:
        return {}

    fm = lines
    data: dict[str, str] = {}
    i = 0
    key_re = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
    while i < len(fm):
        match = key_re.match(fm[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key not in {"name", "description"}:
            i += 1
            continue
        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            i += 1
            while i < len(fm):
                if key_re.match(fm[i]) and not fm[i].startswith((" ", "\t")):
                    break
                block.append(fm[i].strip())
                i += 1
            data[key] = " ".join(part for part in block if part).strip()
            continue
        data[key] = value.strip().strip('"').strip("'")
        i += 1
    return data


def split_request_context(request: str) -> dict[str, str]:
    """Separate the task the user wants from explicit out-of-scope/non-goal text."""
    positive_lines: list[str] = []
    route_lines: list[str] = []
    excluded_lines: list[str] = []
    mode = "positive"
    route_mode = False

    for line in request.splitlines():
        stripped = line.strip()
        out_match = OUT_OF_SCOPE_HEADER_RE.match(stripped)
        if out_match:
            mode = "excluded"
            route_mode = False
            if out_match.group(1).strip():
                excluded_lines.append(out_match.group(1).strip())
            continue

        positive_match = POSITIVE_HEADER_RE.match(stripped)
        if positive_match:
            mode = "positive"
            heading_text = stripped.lower()
            route_mode = any(
                label in heading_text
                for label in [
                    "goal",
                    "objective",
                    "deliverable",
                    "in scope",
                    "inputs",
                    "context",
                    "requirements",
                    "ceo handoff",
                    "目标",
                    "交付",
                    "范围内",
                    "输入",
                    "上下文",
                    "需求",
                ]
            )
            positive_lines.append(line)
            if route_mode:
                route_lines.append(line)
            continue

        if mode == "excluded":
            excluded_lines.append(line)
        else:
            positive_lines.append(line)
            if route_mode or not re.match(r"^\s*[-*]\s*[A-Za-z /-]+:", stripped):
                route_lines.append(line)

    positive_text = "\n".join(positive_lines).strip() or request
    route_text = "\n".join(route_lines).strip() or positive_text
    excluded_text = "\n".join(excluded_lines).strip()

    positive_text, positive_inline_exclusions = split_inline_exclusions(positive_text)
    route_text, route_inline_exclusions = split_inline_exclusions(route_text)
    inline_exclusions = positive_inline_exclusions + [
        item for item in route_inline_exclusions if item not in positive_inline_exclusions
    ]
    if inline_exclusions:
        excluded_text = "\n".join(
            part for part in [excluded_text, "\n".join(inline_exclusions)] if part
        ).strip()

    return {"positive_text": positive_text, "route_text": route_text, "excluded_text": excluded_text}


def split_inline_exclusions(text: str) -> tuple[str, list[str]]:
    """Extract natural-language exclusions such as 'do not deploy' from free text."""
    exclusions: list[str] = []
    spans: list[tuple[int, int]] = []
    for pattern in INLINE_EXCLUSION_RES:
        for match in pattern.finditer(text):
            body = match.group(1).strip(" ,，:：-")
            if not body:
                continue
            exclusions.append(body)
            spans.append(match.span())

    if not spans:
        return text, exclusions

    cleaned = text
    for start, end in sorted(spans, reverse=True):
        cleaned = cleaned[:start] + " " + cleaned[end:]
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, exclusions


def request_traits(text: str) -> dict[str, bool]:
    text_norm = normalize(text)
    return {
        "markdown_doc": bool(contains_any(text_norm, MARKDOWN_DOC_TERMS)),
        "office_doc": bool(contains_any(text_norm, OFFICE_DOC_TERMS)),
    }


def invocation_name_for_path(path: str, name: str) -> str:
    skill_path = Path(path)
    try:
        relative = skill_path.relative_to(plugin_cache_root())
    except ValueError:
        return name

    parts = relative.parts
    if len(parts) < 2 or "skills" not in parts:
        return name

    skills_index = parts.index("skills")
    plugin = None
    if skills_index >= 2:
        plugin = parts[skills_index - 2]
    elif skills_index >= 1:
        plugin = parts[skills_index - 1]

    if not plugin:
        return name
    if name == plugin or name.startswith(f"{plugin}:"):
        return name
    return f"{plugin}:{name}"


def canonical_family_for_record(record: dict[str, Any]) -> str:
    invocation = normalize(record.get("invocation_name") or record["name"])
    name = normalize(record["name"])
    path = record.get("path", "")
    base = invocation.split(":")[-1]
    if base.startswith("gstack-"):
        base = base.removeprefix("gstack-")
    path_base = Path(path).parent.name
    if path_base.startswith("gstack-"):
        path_base = path_base.removeprefix("gstack-")
    description = normalize(record.get("description", ""))
    digest = hashlib.sha1(description.encode("utf-8")).hexdigest()[:10] if description else ""
    if digest:
        return f"{path_base or base}:{digest}"
    return path_base or base or name or invocation


def finalist_role(candidate: dict[str, Any]) -> str:
    terms = set(candidate.get("matched_terms", []))
    invocation = normalize(candidate.get("invocation_name", ""))
    name = normalize(candidate.get("name", ""))
    if any(term.startswith("validation:") for term in terms) or any(
        key in invocation or key == name for key in ["playwright", "qa", "test", "health", "browse", "browser", "chrome"]
    ):
        return "validation"
    if any(key in invocation or key == name for key in ["github", "documents", "spreadsheets", "presentations", "browser:control", "chrome:control"]):
        return "source-access"
    if any(term.startswith("routing:ideation") for term in terms) or any(
        key in invocation or key == name for key in ["office-hours", "plan", "ralplan", "security", "deploy", "cso"]
    ):
        return "risk-planning"
    return "primary"


def detect_map(request: str, mapping: dict[str, Any], request_key: str | None = None) -> list[str]:
    found = []
    for key, value in mapping.items():
        terms = value[request_key] if request_key else value
        if contains_any(request, terms):
            found.append(key)
    return found


def domain_terms_for_request(task_type: str) -> list[str]:
    return SKILL_DOMAIN_TERMS.get(task_type, TASK_TYPES.get(task_type, []))


def scan_roots(roots: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root_reports = []
    records = []
    for root in roots:
        root_path = Path(root).expanduser()
        skill_paths = sorted(root_path.rglob("SKILL.md")) if root_path.exists() else []
        root_reports.append({"path": str(root_path), "exists": root_path.exists(), "skill_files": len(skill_paths)})
        for skill_path in skill_paths:
            fm = parse_frontmatter(skill_path)
            name = fm.get("name") or skill_path.parent.name
            description = fm.get("description", "")
            if not name:
                continue
            invocation_name = invocation_name_for_path(str(skill_path), name)
            records.append(
                {
                    "name": name,
                    "invocation_name": invocation_name,
                    "description": description,
                    "path": str(skill_path),
                    "source_root": str(root_path),
                }
            )
    return root_reports, records


def collapse_duplicates(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_name.setdefault(record["invocation_name"], []).append(record)

    unique = []
    duplicates = []
    for invocation_name in sorted(by_name):
        items = sorted(by_name[invocation_name], key=lambda item: item["path"])
        unique.append(items[0])
        if len(items) > 1:
            duplicates.append(
                {
                    "name": items[0]["name"],
                    "invocation_name": invocation_name,
                    "count": len(items),
                    "paths": [item["path"] for item in items],
                }
            )
    return unique, duplicates


def collapse_alias_families(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        family = candidate.get("canonical_family") or canonical_family_for_record(candidate)
        candidate["canonical_family"] = family
        by_family.setdefault(family, []).append(candidate)

    collapsed = []
    aliases = []
    for family in sorted(by_family):
        items = sorted(
            by_family[family],
            key=lambda item: (-item["score"], item["invocation_name"].lower(), item["path"]),
        )
        winner = items[0]
        if len(items) > 1:
            alias_names = [item["invocation_name"] for item in items[1:]]
            winner["aliases"] = alias_names
            winner["matched_terms"] = sorted(set(winner.get("matched_terms", []) + ["alias-family:" + family]))
            aliases.append(
                {
                    "canonical_family": family,
                    "winner": winner["invocation_name"],
                    "aliases": alias_names,
                    "paths": [item["path"] for item in items],
                }
            )
        collapsed.append(winner)
    collapsed.sort(key=lambda item: (-item["score"], item["invocation_name"].lower(), item["path"]))
    return collapsed, aliases


def select_coverage_aware_finalists(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    selected: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    preferred_roles = ["primary", "source-access", "validation", "risk-planning"]

    for role in preferred_roles:
        if len(selected) >= limit:
            break
        for candidate in candidates:
            family = candidate.get("canonical_family") or canonical_family_for_record(candidate)
            if candidate.get("finalist_role") != role or family in seen_families:
                continue
            selected.append(candidate)
            seen_families.add(family)
            break

    for candidate in candidates:
        if len(selected) >= limit:
            break
        family = candidate.get("canonical_family") or canonical_family_for_record(candidate)
        if family in seen_families:
            continue
        selected.append(candidate)
        seen_families.add(family)

    return selected


def should_recommend_no_special_skill(
    traits: dict[str, bool],
    task_hints: list[str],
    capability_hints: list[str],
    candidates: list[dict[str, Any]],
) -> bool:
    if not traits.get("markdown_doc") or "repo-doc" not in task_hints:
        return False
    if any(capability not in {"edit", "test", "inspect"} for capability in capability_hints):
        return False
    primary_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("finalist_role") == "primary"
        and (
            "task:repo-doc" in candidate.get("matched_terms", [])
            or "query:readme" in candidate.get("matched_terms", [])
            or "query:markdown" in candidate.get("matched_terms", [])
            or "readme" in normalize(candidate.get("description", ""))
        )
    ]
    return not primary_candidates


def score_skill(
    record: dict[str, Any],
    request: str,
    request_tokens: list[str],
    task_hints: list[str],
    capability_hints: list[str],
    validation_hints: list[str],
    excluded_task_hints: list[str],
    excluded_capability_hints: list[str],
    traits: dict[str, bool],
) -> dict[str, Any]:
    name = normalize(record["name"])
    invocation_name = normalize(record.get("invocation_name", record["name"]))
    description = normalize(record.get("description", ""))
    text = f"{name} {invocation_name} {description}"
    path = record["path"]
    name_parts = [part for part in re.split(r"[:_\-/]+", f"{name} {invocation_name}") if part]

    breakdown = {
        "query": 0,
        "task_type": 0,
        "capability": 0,
        "validation": 0,
        "routing_hint": 0,
        "source": 0,
        "out_of_scope_penalty": 0,
    }
    matched_terms: set[str] = set()

    request_norm = normalize(request)
    if name and re.search(rf"(^|\s){re.escape(name)}($|\s)", request_norm):
        breakdown["query"] += 8
        matched_terms.add(f"name:{record['name']}")
    elif invocation_name and re.search(rf"(^|\s){re.escape(invocation_name)}($|\s)", request_norm):
        breakdown["query"] += 8
        matched_terms.add(f"invocation:{record['invocation_name']}")
    else:
        part_matches = [
            part for part in name_parts if significant_query_token(part) and part in request_tokens
        ]
        if part_matches:
            breakdown["query"] += 5
            matched_terms.update(f"name-token:{part}" for part in part_matches[:3])

    phrase_tokens = [token for token in request_tokens if token.isascii() and significant_query_token(token)]
    phrase_matches = [token for token in phrase_tokens if token in description]
    if phrase_matches:
        breakdown["query"] += min(12, 2 * len(set(phrase_matches)))
        matched_terms.update(f"query:{token}" for token in sorted(set(phrase_matches))[:6])

    skill_domains = {
        task_type: bool(contains_any(text, [task_type] + domain_terms_for_request(task_type)))
        for task_type in task_hints
    }
    direct_domain_count = sum(1 for matched in skill_domains.values() if matched)

    for task_type in task_hints:
        direct_terms = [task_type] + domain_terms_for_request(task_type)
        direct = contains_any(text, direct_terms)
        if direct:
            breakdown["task_type"] += 5
            matched_terms.add(f"task:{task_type}")
            continue
        adjacent = []
        for adjacent_type in ADJACENT_TASK_TYPES.get(task_type, []):
            adjacent.extend([adjacent_type] + TASK_TYPES.get(adjacent_type, []))
        if contains_any(text, adjacent):
            breakdown["task_type"] += 1
            matched_terms.add(f"adjacent:{task_type}")

    excluded_domain_count = 0
    for task_type in excluded_task_hints:
        direct_terms = [task_type] + domain_terms_for_request(task_type)
        if contains_any(text, direct_terms):
            excluded_domain_count += 1
            matched_terms.add(f"out-of-scope:{task_type}")

    if excluded_domain_count:
        penalty = min(12, 4 * excluded_domain_count)
        if direct_domain_count == 0:
            penalty += 4
        breakdown["out_of_scope_penalty"] -= penalty

    excluded_capability_count = 0
    for capability in excluded_capability_hints:
        skill_terms = CAPABILITIES[capability]["skill"]
        if contains_any(text, skill_terms):
            excluded_capability_count += 1
            matched_terms.add(f"out-of-scope-capability:{capability}")

    if excluded_capability_count:
        penalty = min(12, 4 * excluded_capability_count)
        if direct_domain_count == 0 and breakdown["query"] == 0:
            penalty += 4
        breakdown["out_of_scope_penalty"] -= penalty

    if traits.get("markdown_doc") and not traits.get("office_doc"):
        if invocation_name.startswith("documents:") or name == "documents":
            breakdown["out_of_scope_penalty"] -= 24
            matched_terms.add("mismatch:markdown-not-office-doc")

    for capability in capability_hints:
        skill_terms = CAPABILITIES[capability]["skill"]
        if contains_any(text, skill_terms) and (direct_domain_count > 0 or breakdown["query"] > 0):
            breakdown["capability"] += 4
            matched_terms.add(f"capability:{capability}")

    for validation in validation_hints:
        skill_terms = VALIDATION_HINTS[validation]["skill"]
        if contains_any(text, skill_terms) and (direct_domain_count > 0 or breakdown["query"] > 0):
            breakdown["validation"] += 4
            matched_terms.add(f"validation:{validation}")

    boost_contexts = list(task_hints)
    if "browser-validation" in validation_hints:
        boost_contexts.append("browser")
    for context in dict.fromkeys(boost_contexts):
        for skill_name, boost in ROUTING_HINT_BOOSTS.get(context, {}).items():
            if name == skill_name or invocation_name == skill_name or invocation_name.endswith(f":{skill_name}"):
                breakdown["routing_hint"] += boost
                matched_terms.add(f"routing:{context}")

    code_home = codex_home()
    if Path(path).is_relative_to(code_home / "skills"):
        breakdown["source"] += 1
        matched_terms.add("source:codex-skill")
    if Path(path).is_relative_to(plugin_cache_root()) and any(
        contains_any(text, TASK_TYPES.get(task_type, [])) for task_type in task_hints
    ):
        breakdown["source"] += 1
        matched_terms.add("source:domain-plugin")

    breakdown = {key: min(value, 20) for key, value in breakdown.items()}
    score = sum(breakdown.values())
    reasons = []
    if task_hints:
        reasons.append("task=" + ",".join(task_hints))
    if capability_hints:
        reasons.append("capability=" + ",".join(capability_hints))
    if validation_hints:
        reasons.append("validation=" + ",".join(validation_hints))
    if not reasons:
        reasons.append("lexical request matching")

    return {
        **record,
        "score": score,
        "score_breakdown": breakdown,
        "matched_terms": sorted(matched_terms),
        "reason": "; ".join(reasons),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    roots = args.roots or default_roots()
    root_reports, records = scan_roots(roots)
    unique_records, duplicates = collapse_duplicates(records)

    request_context = split_request_context(args.request)
    positive_request = request_context["positive_text"]
    route_request = request_context["route_text"]
    excluded_request = request_context["excluded_text"]
    traits = request_traits(positive_request)
    request_tokens = tokens(route_request)
    task_hints = detect_map(route_request, TASK_TYPES)
    capability_hints = detect_map(route_request, CAPABILITIES, "request")
    validation_hints = detect_map(positive_request, VALIDATION_HINTS, "request")
    excluded_task_hints = detect_map(excluded_request, TASK_TYPES) if excluded_request else []
    excluded_capability_hints = detect_map(excluded_request, CAPABILITIES, "request") if excluded_request else []
    high_risk_terms = contains_any(positive_request, HIGH_RISK_TERMS)
    comparison_terms = contains_any(positive_request, COMPARISON_TERMS)

    scored = [
        score_skill(
            record,
            positive_request,
            request_tokens,
            task_hints,
            capability_hints,
            validation_hints,
            excluded_task_hints,
            excluded_capability_hints,
            traits,
        )
        for record in unique_records
    ]
    scored = [
        record
        for record in scored
        if record["score"] > 0
        and any(
            record["score_breakdown"].get(key, 0) > 0
            for key in ("query", "task_type", "capability", "validation", "routing_hint")
        )
    ]
    for record in scored:
        record["canonical_family"] = canonical_family_for_record(record)
        record["finalist_role"] = finalist_role(record)
        if traits.get("markdown_doc") and "repo-doc" in task_hints and record["finalist_role"] == "validation":
            invocation = normalize(record["invocation_name"])
            broad_validation = [
                "qa",
                "qa-only",
                "diagnose",
                "tdd",
                "gh-fix-ci",
                "browser",
                "browse",
                "benchmark",
                "design-review",
                "playwright",
            ]
            if any(invocation == item or invocation.endswith(f":{item}") or item in invocation for item in broad_validation):
                record["score_breakdown"]["out_of_scope_penalty"] -= 16
                record["matched_terms"] = sorted(set(record["matched_terms"] + ["mismatch:repo-doc-validation-primary"]))
                record["score"] = sum(record["score_breakdown"].values())
            elif invocation == "grill-with-docs":
                record["score_breakdown"]["out_of_scope_penalty"] -= 10
                record["matched_terms"] = sorted(set(record["matched_terms"] + ["mismatch:repo-doc-interview-overhead"]))
                record["score"] = sum(record["score_breakdown"].values())
    scored, alias_families = collapse_alias_families(scored)
    scored.sort(key=lambda item: (-item["score"], item["invocation_name"].lower(), item["path"]))

    top_five = scored[:5]
    close_scores = (
        len(top_five) >= 5
        and top_five[0]["score"] >= 8
        and top_five[0]["score"] - top_five[-1]["score"] <= 3
        and any(
            item["score_breakdown"].get(key, 0) > 0
            for item in top_five
            for key in ("query", "task_type", "capability", "validation", "routing_hint")
        )
    )
    complexity_reasons = []
    if len(task_hints) >= 3:
        complexity_reasons.append("three-or-more-task-types")
    if high_risk_terms:
        complexity_reasons.append("high-risk-terms:" + ",".join(high_risk_terms[:5]))
    if comparison_terms:
        complexity_reasons.append("explicit-skill-or-plugin-comparison")
    if close_scores:
        complexity_reasons.append("top-candidate-scores-close")
    complexity = "complex" if complexity_reasons else "standard"

    candidate_limit = args.complex_candidate_limit if complexity == "complex" else args.candidate_limit
    candidates = scored[:candidate_limit]
    no_special_skill = should_recommend_no_special_skill(traits, task_hints, capability_hints, candidates)
    finalists = [] if no_special_skill else select_coverage_aware_finalists(candidates, max(0, min(args.finalist_limit, len(candidates))))

    ranked_candidates = []
    for index, candidate in enumerate(candidates, start=1):
        ranked_candidates.append(
            {
                "rank": index,
                "name": candidate["name"],
                "invocation_name": candidate["invocation_name"],
                "path": candidate["path"],
                "score": candidate["score"],
                "score_breakdown": candidate["score_breakdown"],
                "matched_terms": candidate["matched_terms"],
                "reason": candidate["reason"],
                "description": candidate.get("description", ""),
                "canonical_family": candidate.get("canonical_family", ""),
                "finalist_role": candidate.get("finalist_role", ""),
                "aliases": candidate.get("aliases", []),
            }
        )

    finalists_to_read = [
        {
            "rank": index,
            "name": candidate["name"],
            "invocation_name": candidate["invocation_name"],
            "path": candidate["path"],
            "why_read_full": f"Coverage-aware finalist role: {candidate.get('finalist_role', 'primary')}",
            "finalist_role": candidate.get("finalist_role", ""),
            "canonical_family": candidate.get("canonical_family", ""),
        }
        for index, candidate in enumerate(finalists, start=1)
    ]

    return {
        "inventory": {
            "scanned_files": len(records),
            "unique_skills": len(unique_records),
            "roots_configured": roots,
            "roots_covered": root_reports,
            "duplicates_found": len(duplicates),
            "duplicate_names": duplicates[:25],
            "alias_families_found": len(alias_families),
            "alias_families": alias_families[:25],
        },
        "request_analysis": {
            "raw_request": args.request,
            "positive_request": positive_request,
            "route_request": route_request,
            "out_of_scope_request": excluded_request,
            "request_traits": traits,
            "task_type_hints": task_hints,
            "capability_hints": capability_hints,
            "validation_hints": validation_hints,
            "out_of_scope_task_type_hints": excluded_task_hints,
            "out_of_scope_capability_hints": excluded_capability_hints,
            "complexity": complexity,
            "complexity_reasons": complexity_reasons,
            "candidate_limit": candidate_limit,
            "finalist_limit": args.finalist_limit,
            "no_special_skill_recommended": no_special_skill,
            "scoring": "deterministic weighted lexical frontmatter recall",
            "finalist_selection": "coverage-aware role and alias-family selection",
        },
        "candidates": ranked_candidates,
        "finalists_to_read": finalists_to_read,
    }


def print_markdown(report: dict[str, Any]) -> None:
    inventory = report["inventory"]
    analysis = report["request_analysis"]
    print("## Skill Inventory Report")
    print(f"- Scanned files: {inventory['scanned_files']}")
    print(f"- Unique skills: {inventory['unique_skills']}")
    print(f"- Duplicates found: {inventory['duplicates_found']}")
    print(f"- Alias families found: {inventory['alias_families_found']}")
    print("- Roots covered:")
    for root in inventory["roots_covered"]:
        status = "yes" if root["exists"] else "missing"
        print(f"  - {root['path']} ({status}, {root['skill_files']} files)")
    print(f"- Complexity: {analysis['complexity']}")
    if analysis["complexity_reasons"]:
        print(f"- Complexity reasons: {', '.join(analysis['complexity_reasons'])}")
    print(f"- Candidate limit: {analysis['candidate_limit']}")
    print(f"- Finalist limit: {analysis['finalist_limit']}")
    print(f"- Task type hints: {', '.join(analysis['task_type_hints']) or 'none'}")
    print(f"- Capability hints: {', '.join(analysis['capability_hints']) or 'none'}")
    print(f"- Validation hints: {', '.join(analysis['validation_hints']) or 'none'}")
    if analysis.get("no_special_skill_recommended"):
        print("- No special skill recommended: yes (clear low-risk repository markdown/docs edit; use ordinary file inspection and available project checks)")
    if analysis["out_of_scope_request"]:
        print(f"- Out-of-scope task hints ignored/penalized: {', '.join(analysis['out_of_scope_task_type_hints']) or 'none'}")
        print(f"- Out-of-scope capability hints ignored/penalized: {', '.join(analysis['out_of_scope_capability_hints']) or 'none'}")
    print("\n### Candidates")
    if not report["candidates"]:
        print("- No positive-score skill candidates found.")
    for candidate in report["candidates"]:
        print(
            f"{candidate['rank']}. `${candidate['invocation_name']}` (`{candidate['name']}`) score={candidate['score']} "
            f"path={candidate['path']}"
        )
        print(f"   - Breakdown: {json.dumps(candidate['score_breakdown'], ensure_ascii=False)}")
        print(f"   - Matched: {', '.join(candidate['matched_terms']) or 'none'}")
        print(f"   - Role: {candidate.get('finalist_role') or 'primary'}")
        if candidate.get("aliases"):
            print(f"   - Aliases: {', '.join(candidate['aliases'])}")
    print("\n### Finalists To Read")
    if analysis.get("no_special_skill_recommended"):
        print("- None. No full `SKILL.md` read needed unless local evidence reveals a specific documentation skill.")
        return
    if not report["finalists_to_read"]:
        print("- None.")
    for finalist in report["finalists_to_read"]:
        print(
            f"{finalist['rank']}. `${finalist['invocation_name']}` (`{finalist['name']}`) "
            f"[{finalist.get('finalist_role') or 'primary'}] - {finalist['path']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan skill frontmatter and rank candidate skills.")
    parser.add_argument("--request", required=True, help="Raw user request to route.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--candidate-limit", type=int, default=10)
    parser.add_argument("--complex-candidate-limit", type=int, default=15)
    parser.add_argument("--finalist-limit", type=int, default=4)
    parser.add_argument("--roots", nargs="*", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args)
    if args.format == "markdown":
        print_markdown(report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
