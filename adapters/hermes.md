---
name: ceo
description: Use when a Hermes agent needs to convert rough user intent into an executable prompt with triage, full local skill inventory, selected routing, validation evidence, and output contract.
---

# Hermes Adapter

This is the Hermes native skill adapter for CEO Prompt Builder. It follows the root `SKILL.md` protocol and adjusts only the install root and dispatch wording.

## Install

Install the repository under the Hermes skill root:

```bash
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/skills"
git clone https://github.com/owenchou95-svg/ceo-skill.git "${HERMES_HOME:-$HOME/.hermes}/skills/ceo"
```

If Hermes uses a project-local skill bundle, copy the repository to that bundle and set:

```bash
export CEO_SKILL_HOME="/path/to/ceo-skill"
```

## Run

When the user invokes CEO:

1. Load the canonical CEO protocol from `"$CEO_SKILL_HOME/SKILL.md"` or `${HERMES_HOME:-$HOME/.hermes}/skills/ceo/SKILL.md`.
2. Classify the request as `Direct Path` or `Clarification Path`.
3. Use `office-hours` for unclear, high-risk, or materially underspecified requests when it is installed.
4. For direct requests, run:
   ```bash
   cd "${CEO_SKILL_HOME:-${HERMES_HOME:-$HOME/.hermes}/skills/ceo}"
   python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
   ```
5. Read only the `finalists_to_read` skills from the inventory report.
6. Return the root CEO output contract with Chinese body text by default.

## Validation

From the repository root, run:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/skill_inventory.py --request "Evaluate a rough automation idea and produce an executable prompt" --format markdown
```
