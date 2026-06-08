---
name: ceo
description: Turn rough user ideas, goals, or task descriptions into executable agent specifications. Use when the user asks to create, improve, structure, or evaluate a prompt; wants requirements plus validation; or wants local skills searched before selecting an execution route.
---

# Claude Code Adapter

This is the Claude Code adapter for CEO Prompt Builder. It keeps the same operating contract as the root `SKILL.md`, with Claude Code installation and path resolution rules.

## Install

Copy this repository to a Claude Code skill directory:

```bash
mkdir -p "${CLAUDE_HOME:-$HOME/.claude}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${CLAUDE_HOME:-$HOME/.claude}/skills/ceo"
```

If you already cloned the repository elsewhere, set:

```bash
export CEO_SKILL_HOME="/path/to/ceo-skill"
```

## Run

When the user invokes `$ceo`, follow the root CEO protocol:

1. Read `"$CEO_SKILL_HOME/SKILL.md"` if `CEO_SKILL_HOME` is set; otherwise read the `SKILL.md` in this adapter repository root.
2. Classify the request as `Direct Path` or `Clarification Path`.
3. For direct requests, run the inventory helper from the repository root:
   ```bash
   cd "${CEO_SKILL_HOME:-${CLAUDE_HOME:-$HOME/.claude}/skills/ceo}"
   python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
   ```
4. Scan all configured roots, including Codex, Claude Code, Agents, OpenClaw, and Hermes skill folders.
5. Read only the top 3-4 finalists from the inventory report.
6. Return the same CEO sections required by the root skill: `Triage`, `Skill Inventory Report`, `Skill Match`, `Contract Check`, `Final Prompt`, and `Assumptions`.

## Clarification

If the request is vague, high-risk, or missing material boundaries, route to `$office-hours` when available. If `$office-hours` is not installed in Claude Code, produce the same `## Clarified Spec` handoff shape defined in the root CEO skill and ask the user to return it to `$ceo`.

## Validation

Validate the install from the repository root:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/skill_inventory.py --request "Create an executable prompt for a frontend app and browser validation" --format markdown
```
