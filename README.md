# CEO Prompt Builder

CEO Prompt Builder is a Codex skill for turning rough user intent into executable agent specifications.

It is not a prompt-polishing helper. Its job is to decide whether a request is ready for execution, route unclear requests to clarification, inspect local skill/plugin metadata, and produce a final prompt that another agent can act on with explicit requirements, boundaries, validation, and output format.

## What It Does

- Classifies requests as `Direct Path` or `Clarification Path`.
- Routes unclear requirements to `$office-hours` for a structured `## Clarified Spec`.
- Requires a full local skill inventory before selecting skills.
- Uses deterministic local metadata recall instead of model memory for skill discovery.
- Keeps default candidate recall at 10 skills, complex recall at 15 skills, and final full-read candidates at 3-4 skills.
- Selects finalists with role coverage so source/access and validation skills are not crowded out by near-duplicate high scorers.
- Requires selected skills/plugins to be traceable to the inventory report.
- Outputs an executable prompt with fixed sections:
  - `## Role`
  - `## Objective`
  - `## Requirements`
  - `## Context`
  - `## Thinking Process`
  - `## Validation`
  - `## Output Format`
- Defaults to Chinese output while preserving required headings, commands, paths, code identifiers, and skill invocation names.

## When To Use It

Use `$ceo` when the user:

- has a rough idea and needs it turned into an executable agent brief
- asks to improve, structure, or evaluate a prompt
- wants requirements, context, assumptions, validation, and output format in one prompt
- wants local skills/plugins searched and compared before selecting an execution route
- needs the agent to decide whether the request is clear enough or should be clarified first

## Core Workflow

1. Capture the raw request.
2. Decide `Direct Path` vs `Clarification Path`.
3. Run `scripts/skill_inventory.py` against local skill roots.
4. Compare candidate skills and read only the top 3-4 finalists.
5. Produce a structured final prompt.
6. Validate the output against the executable-spec contract.

## Demand Triage

`Direct Path` is used when the request has a clear action, target, deliverable, and low-risk route. Material assumptions must become execution boundaries:

```md
- Assumption: [what is being assumed]
  Boundary: [what the agent may and may not do because of this assumption]
  Risk: [what could go wrong if the assumption is false]
  Reversibility: [clean, messy, or irreversible]
```

`Clarification Path` is used when the request is vague, high-risk, irreversible, missing material boundaries, or has multiple plausible routes. In that case, CEO routes to `$office-hours` and asks for:

```md
## Clarified Spec
- Goal:
- Deliverables:
- In Scope:
- Out of Scope / Non-goals:
- Inputs / Context:
- Decision Boundaries:
- Constraints:
- Acceptance Criteria:
- Risks and Reversibility:
- Open Questions:
- CEO Handoff Summary:
```

After a clarified spec is provided, CEO reruns triage and generates an execution prompt only if material gaps are resolved.

## Skill Inventory

The inventory helper scans configured local roots:

- `${CODEX_HOME:-$HOME/.codex}/skills`
- `${CODEX_HOME:-$HOME/.codex}/plugins/cache`
- `${AGENTS_HOME:-$HOME/.agents}/skills`
- `${CLAUDE_HOME:-$HOME/.claude}/skills`

Run it directly:

```bash
python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
```

The report includes scanned files, unique skills, duplicates, covered roots, complexity, candidate limits, top candidates, finalists to read, exact `invocation_name` values, and out-of-scope hints when detected.

## Output Contract

A CEO response should include:

1. `Triage`
2. `Skill Inventory Report`
3. `Skill Match`
4. `Conflicts / Choices` when needed
5. `Contract Check`
6. `Final Prompt`
7. `Assumptions`

The final prompt is considered executable only when it defines:

- objective
- inputs and context
- scope and non-goals
- deliverables
- skill inventory evidence
- skill/tool routing
- assumptions as boundaries
- concrete validation evidence
- failure or escalation conditions
- exact output format

## Validation

Validate the skill structure:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
```

Run helper tests:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Evaluate a generated CEO output:

```bash
python3 scripts/evaluate_ceo_output.py --request "<raw user request>" path/to/ceo-output.md
```

## Repository Layout

```text
.
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── docs/
│   ├── ceo-optimization-report.md
│   ├── ceo-optimization-test-matrix.md
│   └── review-packet.md
├── references/
│   ├── prompt-template.md
│   └── test-fixtures.md
└── scripts/
    ├── evaluate_ceo_output.py
    ├── skill_inventory.py
    └── test_ceo_scripts.py
```

## Current Optimization Status

The repository includes a reviewed optimization packet. The approved P0/P1 implementation has landed request-aware evaluator checks, coverage-aware inventory finalist selection, and `$office-hours` synchronization in SkillOpt. Final SkillOpt acceptance passed on the aggregate train/val/test eval.

Review entry point:

- `docs/review-packet.md`

Detailed plan:

- `docs/ceo-optimization-report.md`

Acceptance matrix:

- `docs/ceo-optimization-test-matrix.md`

Implemented from the approved P0/P1 plan:

- request-aware demand-triage evaluation
- executable positive/negative fixture tests
- `$office-hours` synchronization in SkillOpt
- coverage-aware skill finalists
- single-critical-gap clarification rule
- clarified-spec readiness checks
- alias/canonical-family handling for duplicate skill families
- stream-based frontmatter parsing

Verification evidence:

- CEO local helper tests: `python3 -m unittest discover -s scripts -p 'test_*.py'`
- Skill creator validation: `quick_validate.py "${CODEX_HOME:-$HOME/.codex}/skills/ceo"`
- SkillOpt full eval: hard=1.0, soft=0.976859375, n=16

## Remaining Public Release Gaps

- None. The repository is ready for public use.

## Public Release Notes

This skill uses portable defaults based on `CODEX_HOME`, `AGENTS_HOME`, and `CLAUDE_HOME`. If unset, they resolve to `$HOME/.codex`, `$HOME/.agents`, and `$HOME/.claude`.

No new runtime dependencies are required for the current helper scripts beyond Python 3.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
