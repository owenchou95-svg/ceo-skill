## Triage
Direct Path - generated fixture sample for readme-direct.

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
- Strong match: use `$frontend-skill` for implementation when available.
- Supporting match: use `$playwright` for browser validation when available.

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
Use the following skill(s) if available: $frontend-skill, $playwright

## Role
You are an execution-focused agent using the selected skills only where they improve quality.

## Objective
Turn the clarified request into a scoped executable implementation brief.

## Requirements
- Inputs: the current workspace, raw request, and existing project structure.
- In scope: inspect context, implement the requested scoped change, preserve non-goals, and verify the main workflow.
- Out of scope / non-goals: unrelated refactors, deployments, payments, production data changes, and invented requirements.
- Deliverables: code or documentation changes plus a verification report with file paths and command evidence.
- Constraints: reuse existing patterns and dependencies unless evidence proves otherwise.
- Assumptions and boundaries:
  - Assumption: the workspace contains the target artifact.
    Boundary: inspect before editing and stop if the target is absent.
    Risk: editing the wrong file would create unrelated churn.
    Reversibility: clean.
- Failure / escalation conditions: stop and report blockers if target files, authority, or validation commands are missing.

## Context
The CEO inventory evidence and triage decision determine whether to clarify first or execute directly.

## Thinking Process
Follow this visible workflow: inspect the request, confirm triage, preserve scope and non-goals, use selected skills only when justified, verify the required artifact, and report concrete evidence.

## Validation
Run the relevant evaluator or project checks, inspect generated artifacts, verify required fields and command evidence, and report exact pass/fail output. For clarification, check the `## Clarified Spec` fields and return readiness for `$ceo`; for direct work, run available lint, tests, build, or browser checks as applicable.

## Output Format
Return Changed files, Implemented behavior, Verification commands, Evidence, Known gaps, and Follow-up risks.

## Assumptions
- The sample output is generated for evaluator smoke coverage.
  Boundary: use it as sample evidence, not production proof.
  Risk: fixture mode can pass while a real model regresses.
  Reversibility: clean.
