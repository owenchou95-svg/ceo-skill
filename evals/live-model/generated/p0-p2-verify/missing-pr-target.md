## Triage
Clarification Path - generated fixture sample for missing-pr-target.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: ideation
- Capability hints: build
- Validation hints: browser-validation

### Candidates
1. `$office-hours` (`office-hours`) score=30 path=/tmp/office-hours/SKILL.md
2. `$frontend-skill` (`frontend-skill`) score=20 path=/tmp/frontend/SKILL.md
3. `$playwright` (`playwright`) score=12 path=/tmp/playwright/SKILL.md

### Finalists To Read
1. `$office-hours` (`office-hours`) - /tmp/office-hours/SKILL.md
2. `$frontend-skill` (`frontend-skill`) - /tmp/frontend/SKILL.md
3. `$playwright` (`playwright`) - /tmp/playwright/SKILL.md

## Skill Match
- Strong match: use `$office-hours` for requirements clarification before implementation.

## Contract Check
- Objective: pass
- Inputs/context: pass
- Scope/non-goals: pass
- Deliverables: pass
- Assumptions/boundaries: pass
- Validation evidence: pass
- Failure conditions: pass
- Output format: pass
- Skill provenance: pass
- Skill Inventory Report: pass

## Final Prompt
Use the following skill(s) if available: $office-hours

## Role
You are an execution-focused agent using the selected skills only where they improve quality.

## Objective
Clarify the request enough for `$ceo` to produce a safe executable prompt.

## Requirements
- Inputs: the user's raw request and any additional context they provide.
- In scope: clarify goal, deliverables, in-scope/out-of-scope boundaries, inputs/context, decision boundaries, constraints, acceptance criteria, risks, and open questions.
- Out of scope / non-goals: do not implement, deploy, delete data, choose a final route, or fabricate missing authority.
- Deliverables: a `## Clarified Spec` handoff for `$ceo`.
- Constraints: keep missing material choices explicit and mark unresolved fields as blocking.
- Assumptions and boundaries:
  - Assumption: material inputs are missing.
    Boundary: clarify only and return to `$ceo` before execution.
    Risk: direct execution would invent unsafe requirements.
    Reversibility: clean.
- Failure / escalation conditions: stop if required fields remain unknown and mark them `Unknown and blocking`.

## Context
The CEO inventory evidence and triage decision determine whether to clarify first or execute directly.

## Thinking Process
Follow this visible workflow: inspect the request, confirm triage, preserve scope and non-goals, use selected skills only when justified, verify the required artifact, and report concrete evidence.

## Validation
Run the relevant evaluator or project checks, inspect generated artifacts, verify required fields and command evidence, and report exact pass/fail output. For clarification, check the `## Clarified Spec` fields and return readiness for `$ceo`; for direct work, run available lint, tests, build, or browser checks as applicable.

## Output Format
Return `## Clarified Spec` with Goal, Deliverables, In Scope, Out of Scope / Non-goals, Inputs / Context, Decision Boundaries, Constraints, Acceptance Criteria, Risks and Reversibility, Open Questions, CEO Handoff Summary, and readiness for `$ceo`.

## Assumptions
- The sample output is generated for evaluator smoke coverage.
  Boundary: use it as sample evidence, not production proof.
  Risk: fixture mode can pass while a real model regresses.
  Reversibility: clean.
