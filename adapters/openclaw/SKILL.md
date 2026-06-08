---
name: ceo
description: Use when an OpenClaw user wants to turn a rough goal into an executable agent specification with demand triage, local skill inventory, selected agent routing, concrete validation, and a final prompt that another coding agent can run.
---

# CEO Prompt Builder for OpenClaw

This is the OpenClaw native skill adapter for CEO Prompt Builder. OpenClaw can use this as a conversational methodology skill or as a prompt prefix before spawning an ACP coding session.

## Install

Install the repository under the OpenClaw skill root:

```bash
mkdir -p "${OPENCLAW_HOME:-$HOME/.openclaw}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo"
```

If OpenClaw uses a project-local skill bundle, copy the repository to that bundle and set:

```bash
export CEO_SKILL_HOME="/path/to/ceo-skill"
```

## Dispatch

When the user asks for CEO prompt building, planning, or skill routing:

1. Do not implement the underlying task yet.
2. Load the root CEO protocol from `"$CEO_SKILL_HOME/SKILL.md"` or from `${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo/SKILL.md`.
3. Run demand triage.
4. If the request is vague or high-risk, route to `office-hours` when available and return a `## Clarified Spec`.
5. If the request is direct, run:
   ```bash
   cd "${CEO_SKILL_HOME:-${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo}"
   python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
   ```
6. Use the inventory report to choose the final execution route. For spawned ACP sessions, include the generated `Final Prompt` as the session prompt.

## Skill Roots

The inventory helper searches these roots by default:

- `${CODEX_HOME:-$HOME/.codex}/skills`
- `${CODEX_HOME:-$HOME/.codex}/plugins/cache`
- `${AGENTS_HOME:-$HOME/.agents}/skills`
- `${CLAUDE_HOME:-$HOME/.claude}/skills`
- `${OPENCLAW_HOME:-$HOME/.openclaw}/skills`
- `${HERMES_HOME:-$HOME/.hermes}/skills`

## Validation

From the repository root, run:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/skill_inventory.py --request "Plan a Claude Code project with skill routing and validation" --format markdown
```
