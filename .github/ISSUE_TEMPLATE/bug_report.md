---
name: Bug report
about: Report a CEO routing, contract, inventory, or documentation bug
title: "[Bug]: "
labels: bug
assignees: ""
---

## What happened

Describe the behavior you saw.

## Request that triggered it

```text
Paste the raw user request here.
```

## Expected CEO route

- [ ] `Direct Path`
- [ ] `Clarification Path`
- [ ] Not sure

## Actual CEO output

Paste the relevant `Triage`, `Skill Inventory Report`, `Skill Match`, and `Contract Check` sections.

## Environment

- Host: Codex / Claude Code / OpenClaw / Hermes / other
- OS:
- Python version:
- Install method: `npx skills add` / git clone / other

## Verification

Run the closest applicable command and paste the output:

```bash
python3 scripts/evaluate_ceo_output.py --request "<raw user request>" path/to/ceo-output.md
python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
```

