# Multi-Agent Usage

CEO Prompt Builder is distributed as a Codex skill, but the repository is intentionally host-light: the executable protocol lives in `SKILL.md`, the helper scripts are plain Python, and the adapter notes under `adapters/` provide host-specific install and dispatch instructions.

## Supported Hosts

| Host | Install Root | Adapter |
| --- | --- | --- |
| Codex | `${CODEX_HOME:-$HOME/.codex}/skills/ceo` | root `SKILL.md` |
| Claude Code | `${CLAUDE_HOME:-$HOME/.claude}/skills/ceo` | root `SKILL.md` plus `adapters/claude-code.md` |
| OpenClaw | `${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo` | root `SKILL.md` plus `adapters/openclaw.md` |
| Hermes | `${HERMES_HOME:-$HOME/.hermes}/skills/ceo` | root `SKILL.md` plus `adapters/hermes.md` |

## Install

Codex:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
```

Claude Code:

```bash
mkdir -p "${CLAUDE_HOME:-$HOME/.claude}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${CLAUDE_HOME:-$HOME/.claude}/skills/ceo"
```

OpenClaw:

```bash
mkdir -p "${OPENCLAW_HOME:-$HOME/.openclaw}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo"
```

Hermes:

```bash
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${HERMES_HOME:-$HOME/.hermes}/skills/ceo"
```

For project-local installs or custom host layouts, set:

```bash
export CEO_SKILL_HOME="/path/to/ceo-skill"
```

## Invocation Pattern

Use CEO before implementation when a rough request needs to become an executable agent brief:

```text
Use CEO to turn this request into an executable prompt:
<raw request>
```

The expected output is the same across hosts:

1. `Triage`
2. `Skill Inventory Report`
3. `Skill Match`
4. `Conflicts / Choices` when needed
5. `Contract Check`
6. `Final Prompt`
7. `Assumptions`

## Inventory Behavior

CEO always runs `scripts/skill_inventory.py` before selecting skills. By default it scans:

- `${CODEX_HOME:-$HOME/.codex}/skills`
- `${CODEX_HOME:-$HOME/.codex}/plugins/cache`
- `${AGENTS_HOME:-$HOME/.agents}/skills`
- `${CLAUDE_HOME:-$HOME/.claude}/skills`
- `${OPENCLAW_HOME:-$HOME/.openclaw}/skills`
- `${HERMES_HOME:-$HOME/.hermes}/skills`

This prevents the model from repeatedly choosing a small remembered subset of skills. It also lets one host route work to skills installed for another host when those skills are visible on disk.

## Host Notes

Codex uses the root `SKILL.md` directly.

Claude Code can use the repository as a normal `SKILL.md`-based skill. The Claude adapter documents how to resolve the repository root and run the same helper scripts.

OpenClaw can use the root `SKILL.md` as a native conversational skill, with `adapters/openclaw.md` as dispatch guidance, or as a prompt prefix before spawning an ACP coding session. The generated `Final Prompt` should become the spawned session prompt.

Hermes can use the root `SKILL.md` as a native `SKILL.md` skill, with `adapters/hermes.md` as dispatch guidance. If Hermes is coordinating another coding agent, pass the generated `Final Prompt` to that agent unchanged.

## Verify

From the repository root:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/skill_inventory.py --request "为一个粗略的前端应用想法生成可执行 prompt，并选择验证技能" --format markdown
python3 scripts/verify_multi_agent_install.py
```

For Codex structure validation:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
```
