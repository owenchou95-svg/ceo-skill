#!/usr/bin/env python3
"""Regression tests for CEO helper scripts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import evaluate_ceo_output as evaluator
import skill_inventory
import validate_contract_drift
import validate_eval_fixtures


def inventory_args(request: str, roots: list[str] | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        request=request,
        format="json",
        candidate_limit=10,
        complex_candidate_limit=15,
        finalist_limit=4,
        roots=roots,
        triage="auto",
        cache_path=None,
        no_cache=True,
        rebuild_cache=False,
    )


def valid_ceo_output() -> str:
    return """## Mode Router
- Mode: Task Mode
- Confidence: High
- Reason: The user supplied a concrete app target, requested behavior, and validation surface.
- Evidence: browser-based Pomodoro timer, start/pause/reset, mobile usable.
- Immediate User Intent: execute
- Goal Signal: None beyond task outcome.
- Task Signal: target browser app, action build, deliverable timer implementation, validation browser checks.
- Risk / Strategy Signal: Low-risk local UI task.
- Continue To: Demand Triage

## Triage
Direct Path - the user provided a concrete app target and deliverable.

## Inventory Decision
- Inventory Run: Yes
- Reason: Task Mode requires skill routing evidence before producing Final Prompt.
- Inventory Input: Raw user request.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: frontend, browser
- Capability hints: build
- Validation hints: browser-validation

### Candidates
1. `$frontend-skill` (`frontend-skill`) score=20 path=/tmp/frontend/SKILL.md
2. `$playwright` (`playwright`) score=12 path=/tmp/playwright/SKILL.md

### Finalists To Read
1. `$frontend-skill` (`frontend-skill`) - /tmp/frontend/SKILL.md
2. `$playwright` (`playwright`) - /tmp/playwright/SKILL.md

## Skill Match
- Strong match: use `$frontend-skill` for frontend implementation quality.
- Supporting match: use `$playwright` for browser interaction and screenshots.

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
You are a frontend-focused coding agent.

## Objective
Build a browser-based Pomodoro timer that works on desktop and mobile.

## Requirements
- Inputs: the current workspace and existing app structure.
- In scope: start, pause, reset, long-break mode, short-break mode, sound alert, responsive UI, and accessible controls.
- Out of scope / non-goals: backend persistence, payments, deployment, and authentication.
- Deliverables: code changes for the timer and a short verification report with changed file paths.
- Constraints: reuse existing framework and dependencies; no new dependency unless necessary.
- Assumptions and boundaries:
  - Assumption: an existing frontend app is available.
    Boundary: inspect the app before changing files and keep edits scoped to UI code.
    Risk: if no app exists, implementation cannot proceed safely.
    Reversibility: clean.
- Failure / escalation conditions: stop and report a blocker if no app entrypoint exists or if audio cannot be tested in the browser.

## Context
The skill inventory selected frontend implementation plus Playwright validation because the task requires browser UI behavior, responsive layout, and screenshots.

## Thinking Process
Follow this visible workflow: inspect the app, confirm scope and non-goals, implement in small steps, test interactions, verify responsive states, collect evidence, and report remaining gaps.

## Validation
Run the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.

## Output Format
Return a completion report with sections: Changed files, Implemented behavior, Verification commands, Browser evidence, Known gaps, and Follow-up risks.

## Assumptions
- The workspace contains a frontend app.
  Boundary: inspect before editing.
  Risk: no app means no safe implementation target.
  Reversibility: clean.
"""


def valid_clarification_output() -> str:
    return """## Mode Router
- Mode: Task Mode
- Confidence: Medium
- Reason: The request is being handled through the existing clarification branch of Task Mode.
- Evidence: missing style, content, deliverables, and success criteria.
- Immediate User Intent: clarify
- Goal Signal: Vague desired future state.
- Task Signal: clarification deliverable can be routed through existing Demand Triage.
- Risk / Strategy Signal: Discovery needed before implementation.
- Continue To: Demand Triage

## Triage
Clarification Path - the user is missing style, content, deliverables, and success criteria.

## Inventory Decision
- Inventory Run: Yes
- Reason: Task Mode Clarification Path is selecting a clarification skill and must prove the route from inventory.
- Inventory Input: Raw user request.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: frontend, ideation
- Capability hints: build
- Validation hints: none

### Candidates
1. `$office-hours` (`office-hours`) score=30 path=/tmp/office-hours/SKILL.md

### Finalists To Read
1. `$office-hours` (`office-hours`) - /tmp/office-hours/SKILL.md

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
You are a YC office-hours partner clarifying requirements before implementation.

## Objective
Clarify the vague personal website idea enough for `$ceo` to produce an executable build prompt.

## Requirements
- Inputs: the user's vague website idea and any portfolio, audience, content, or style references they provide.
- In scope: clarify goal, target audience, content inventory, style direction, decision boundaries, constraints, and acceptance criteria.
- Out of scope / non-goals: do not choose the final style, write code, scaffold a site, deploy, or fabricate missing content.
- Deliverables: a `## Clarified Spec` handoff with all required CEO fields.
- Constraints: ask focused questions and keep implementation decisions as decision boundaries rather than assumptions.
- Assumptions and boundaries:
  - Assumption: the user is still exploring.
    Boundary: clarify requirements only; do not produce an implementation prompt yet.
    Risk: building now would overfit invented content and style.
    Reversibility: clean.
- Failure / escalation conditions: stop and mark fields `Unknown and blocking` if goal, deliverables, scope, or acceptance criteria remain unresolved.

## Context
The user is unsure about style, content, and what to show, so CEO must route to office-hours and receive a clarified spec before direct execution.

## Thinking Process
Follow this visible workflow: identify missing decisions, ask office-hours questions, separate in-scope work from non-goals, capture decision boundaries, and produce the clarified handoff.

## Validation
Verify the output includes `## Clarified Spec` with Goal, Deliverables, In Scope, Out of Scope / Non-goals, Inputs / Context, Decision Boundaries, Constraints, Acceptance Criteria, Risks and Reversibility, Open Questions, and CEO Handoff Summary. Check each required field is concrete or marked `None blocking` / `Unknown and blocking`, then state whether the spec is ready for `$ceo`.

## Output Format
Return exactly one markdown artifact headed `## Clarified Spec`, followed by the required bullet fields and a short readiness note for `$ceo` execution-prompt generation.

## Assumptions
- The site idea is still vague.
  Boundary: requirements clarification only.
  Risk: premature implementation would invent core choices.
  Reversibility: clean.
"""


def production_clarification_output() -> str:
    return valid_clarification_output().replace(
        "Clarification Path - the user is missing style, content, deliverables, and success criteria.",
        "Clarification Path - the user requested production data deletion and deployment without authority, environment, backup, rollback, or approval boundaries.",
        1,
    ).replace(
        "Clarify the vague personal website idea enough for `$ceo` to produce an executable build prompt.",
        "Clarify the production database cleanup and deployment request enough for `$ceo` to decide whether an execution prompt is safe.",
        1,
    ).replace(
        "- Inputs: the user's vague website idea and any portfolio, audience, content, or style references they provide.",
        "- Inputs: the user's production database cleanup and deployment request, target environment, authority, backup plan, rollback plan, deletion criteria, and approver.",
        1,
    ).replace(
        "- In scope: clarify goal, target audience, content inventory, style direction, decision boundaries, constraints, and acceptance criteria.",
        "- In scope: clarify authority, target environment, deletion criteria, backup requirements, rollback plan, deployment boundary, approval owner, and acceptance criteria.",
        1,
    ).replace(
        "- Out of scope / non-goals: do not choose the final style, write code, scaffold a site, deploy, or fabricate missing content.",
        "- Out of scope / non-goals: do not delete data, deploy, run commands, or fabricate approval or rollback details.",
        1,
    )


def goal_mode_incomplete_output() -> str:
    return """## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The user describes an outcome-shaped improvement but has not defined observable behavior or a first executable slice.
- Evidence: "更智能".
- Immediate User Intent: define
- Goal Signal: desired quality bar for CEO behavior.
- Task Signal: no concrete target/action/deliverable/validation yet.
- Risk / Strategy Signal: route could change depending on what "smarter" means.
- Continue To: Goal Contract

## Goal Mode
- Status: Incomplete

## Goal Contract Check
- Ready Fields:
  - Goal: improve CEO behavior.
- Missing Fields:
  - Desired End State: "更智能" is not observable enough.
  - Acceptance Criteria: no pass/fail behavior is defined.
  - First Executable Slice: no bounded task can be handed to Task Mode yet.
- Vague Fields:
  - Goal: "更智能" does not name concrete behavior.
- Unverifiable Fields:
  - Validation Method: no proof method exists yet.
- Route-Changing Ambiguities:
  - Motivation: could mean routing, inventory, output quality, or long-term goal management.
- High-Risk Boundaries:
  - None detected.

## Clarification Type
- Type: Local Goal

## Inventory Decision
- Inventory Run: No
- Reason: Goal Contract is incomplete and CEO is asking one local blocking question without selecting a skill.
- Inventory Input: Not applicable.

## Route Decision
- Next Route: Stay in Goal Mode

## Blocking Question
你希望“更智能”具体体现为哪些可观察的 CEO 行为？

## Why This Question Comes First
Without an observable desired end state, CEO cannot form acceptance criteria or a first executable slice.
"""


def goal_mode_complete_output() -> str:
    return """## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The user supplied a complete operational goal and a task-ready first executable slice.
- Evidence: CEO should classify Task Mode and Goal Mode while preserving the current Task Mode path.
- Immediate User Intent: define
- Goal Signal: desired future capability for CEO routing.
- Task Signal: first executable slice names target, action, deliverable, and validation.
- Risk / Strategy Signal: Low-risk local skill contract change.
- Continue To: Goal Contract

## Goal Mode
- Status: Complete

## Goal Spec
- Goal: CEO can classify user input as Task Mode or Goal Mode before producing downstream prompts.
- Current State: CEO already has a Task Mode path and needs a bounded Goal Mode router contract.
- Desired End State: CEO outputs Mode Router, handles incomplete goals without Final Prompt, and hands task-ready slices back to Task Mode.
- In Scope: SKILL.md instructions, evaluator checks, fixtures, and generated sample outputs for the routing contract.
- Out of Scope / Non-goals: long-term goal management, product discovery ownership, deployment, and unrelated skill rewrites.
- Inputs / Context: Current CEO skill files, goal-mode design notes, evaluator fixtures, and test scripts.
- Constraints: Preserve existing Task Mode behavior and keep edits scoped to the CEO skill contract.
- Decision Boundaries: CEO may add structural routing checks but must not invent unrelated execution workflows.
- Assumptions: The first slice is local and reversible.
- Risks and Reversibility: Contract drift is the main risk; changes are reversible by reverting the skill files.
- Acceptance Criteria: Task Mode fixtures still pass, Goal Mode Incomplete forbids Final Prompt, and Goal Complete requires inventory on the first executable slice.
- Validation Method: Run quick validation, fixture validation, contract drift checks, unit tests, and fixture-mode live samples.
- First Executable Slice: Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff.
- Stop / Ask / Escalate Conditions: Stop if tests show existing Task Mode behavior regresses or if a route requires product/risk discovery.

## Goal Contract Check
- Goal: PASS
- Current State: PASS
- Desired End State: PASS
- Scope / Non-goals: PASS
- Acceptance Criteria: PASS
- Validation Method: PASS
- First Executable Slice: PASS
- Stop / Ask / Escalate Conditions: PASS

## Domain Gate
- Domain: Local CEO skill workflow contract.
- Category: Green
- Decision: May route to Task Mode after the first executable slice is task-ready.
- Required Clarification: None.
- Reason: Low-risk, local, reversible skill/evaluator work with bounded validation.

## Clarification Type
- Type: Not Required

## Inventory Decision
- Inventory Run: Yes
- Reason: First Executable Slice is task-ready and CEO must select execution and validation skills.
- Inventory Input: First Executable Slice plus compact Goal Spec context.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: skill, evaluator
- Capability hints: validate
- Validation hints: tests

### Candidates
1. `$skill-creator` (`skill-creator`) score=25 path=/tmp/skill-creator/SKILL.md
2. `$code-review` (`code-review`) score=12 path=/tmp/code-review/SKILL.md

### Finalists To Read
1. `$skill-creator` (`skill-creator`) - /tmp/skill-creator/SKILL.md
2. `$code-review` (`code-review`) - /tmp/code-review/SKILL.md

## Route Decision
- Next Route: Task Mode
- Reason: Goal Contract is complete and the first executable slice is bounded, local, reversible, and testable.

## Task Mode Handoff
- Ready for Task Mode: Yes
- Task Input: Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff.
- Scope Boundary: CEO skill contract files only.
- Validation: quick validation, fixture validation, contract drift checks, unit tests, and fixture live samples.

## Skill Match
- Strong match: use `$skill-creator` for skill contract editing and validation.
- Supporting match: use `$code-review` for review-oriented verification if available.

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
Use the following skill(s) if available: $skill-creator, $code-review

## Role
You are a coding agent updating a local Codex skill contract.

## Objective
Add evaluator and fixture coverage for the CEO Goal Mode Complete to Task Mode handoff.

## Requirements
- Inputs: the current CEO skill files, evaluator scripts, schema, and goal-mode design notes.
- In scope: update SKILL.md, evaluator checks, schema fixtures, and generated fixture samples for this handoff.
- Out of scope / non-goals: do not redesign Task Mode, rewrite unrelated inventory ranking, or implement long-term goal management.
- Deliverables: small code and documentation changes plus a verification report with exact commands.
- Constraints: preserve existing Task Mode behavior and avoid new dependencies.
- Assumptions and boundaries:
  - Assumption: the first executable slice is local to the CEO skill.
    Boundary: keep edits scoped to CEO skill contract surfaces.
    Risk: broad edits could break existing demand triage behavior.
    Reversibility: clean.
- Failure / escalation conditions: stop if tests show Task Mode regression or if the route needs product/risk discovery.

## Context
The Goal Spec is complete and the inventory evidence selected skill contract editing plus review validation.

## Thinking Process
Follow this visible workflow: inspect the current contract, update the smallest set of skill surfaces, add regression tests, run validation commands, and report evidence plus remaining gaps.

## Validation
Run quick_validate.py, validate_eval_fixtures.py, validate_contract_drift.py, python3 -m unittest discover, and run_live_model_samples.py fixture mode. Inspect failing output if any command fails, fix the contract, and rerun until the checks pass.

## Output Format
Return Changed files, Contract behavior added, Verification commands, Evidence, Known gaps, and Follow-up risks.

## Assumptions
- The first slice is limited to evaluator and fixture coverage.
  Boundary: do not alter unrelated skill inventory ranking.
  Risk: touching ranking logic could cause unrelated regressions.
  Reversibility: clean.
"""


def goal_mode_yellow_architecture_output() -> str:
    text = goal_mode_complete_output()
    replacements = [
        (
            "- Reason: The user supplied a complete operational goal and a task-ready first executable slice.",
            "- Reason: The user supplied a complete architecture goal with a bounded assessment slice.",
        ),
        (
            "- Evidence: CEO should classify Task Mode and Goal Mode while preserving the current Task Mode path.",
            "- Evidence: architecture refactor goal with assessment-only first slice.",
        ),
        (
            "- Goal Signal: desired future capability for CEO routing.",
            "- Goal Signal: desired future architecture quality and extensibility.",
        ),
        (
            "- Risk / Strategy Signal: Low-risk local skill contract change.",
            "- Risk / Strategy Signal: Yellow architecture/refactor domain; broad implementation is not allowed yet.",
        ),
        (
            "- Goal: CEO can classify user input as Task Mode or Goal Mode before producing downstream prompts.",
            "- Goal: Identify a safe path to make the system architecture more extensible.",
        ),
        (
            "- Current State: CEO already has a Task Mode path and needs a bounded Goal Mode router contract.",
            "- Current State: The current architecture has suspected extensibility limits but no reviewed assessment yet.",
        ),
        (
            "- Desired End State: CEO outputs Mode Router, handles incomplete goals without Final Prompt, and hands task-ready slices back to Task Mode.",
            "- Desired End State: A reviewed architecture assessment identifies bounded improvement options before any code rewrite.",
        ),
        (
            "- In Scope: SKILL.md instructions, evaluator checks, fixtures, and generated sample outputs for the routing contract.",
            "- In Scope: architecture assessment report, module boundary map, risk list, and candidate first implementation slices.",
        ),
        (
            "- Out of Scope / Non-goals: long-term goal management, product discovery ownership, deployment, and unrelated skill rewrites.",
            "- Out of Scope / Non-goals: direct code rewrite, migration, deployment, broad cross-module refactor, and production changes.",
        ),
        (
            "- Inputs / Context: Current CEO skill files, goal-mode design notes, evaluator fixtures, and test scripts.",
            "- Inputs / Context: Current repository structure, architecture notes, module boundaries, tests, and known pain points.",
        ),
        (
            "- Risks and Reversibility: Contract drift is the main risk; changes are reversible by reverting the skill files.",
            "- Risks and Reversibility: Assessment-only work is cleanly reversible; broad implementation would be higher risk.",
        ),
        (
            "- Acceptance Criteria: Task Mode fixtures still pass, Goal Mode Incomplete forbids Final Prompt, and Goal Complete requires inventory on the first executable slice.",
            "- Acceptance Criteria: Assessment names current boundaries, top 3 risks, candidate slices, non-goals, and validation evidence.",
        ),
        (
            "- Validation Method: Run quick validation, fixture validation, contract drift checks, unit tests, and fixture-mode live samples.",
            "- Validation Method: Inspect the architecture assessment report against repository evidence and required checklist fields.",
        ),
        (
            "- First Executable Slice: Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff.",
            "- First Executable Slice: Produce a bounded, reversible architecture assessment report with no code changes.",
        ),
        (
            "- Domain: Local CEO skill workflow contract.\n- Category: Green\n- Decision: May route to Task Mode after the first executable slice is task-ready.\n- Required Clarification: None.\n- Reason: Low-risk, local, reversible skill/evaluator work with bounded validation.",
            "- Domain: Architecture refactor strategy.\n- Category: Yellow\n- Decision: May route to Task Mode only for bounded assessment, design, documentation, or test-oriented slices.\n- Required Clarification: None for assessment-only slice; required before broad implementation or migration.\n- Reason: Architecture goals are conditionally allowed when the first slice is bounded, reversible, and does not choose strategy for the user.",
        ),
        (
            "- Reason: Goal Contract is complete and the first executable slice is bounded, local, reversible, and testable.",
            "- Reason: Goal Contract is complete and Domain Gate Yellow allows this assessment-only first slice.",
        ),
        (
            "- Task Input: Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff.",
            "- Task Input: Produce a bounded, reversible architecture assessment report with no code changes.",
        ),
        (
            "- Scope Boundary: CEO skill contract files only.",
            "- Scope Boundary: repository inspection and assessment report only; no code changes.",
        ),
        (
            "- Validation: quick validation, fixture validation, contract drift checks, unit tests, and fixture live samples.",
            "- Validation: architecture assessment checklist, evidence-backed module map, and no code diff.",
        ),
        (
            "Add evaluator and fixture coverage for the CEO Goal Mode Complete to Task Mode handoff.",
            "Produce a bounded, reversible architecture assessment report with no code changes.",
        ),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def goal_mode_discovery_routed_output() -> str:
    return """## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The user is asking for product direction discovery rather than an executable implementation task.
- Evidence: find a worthwhile AI product direction.
- Immediate User Intent: decide direction
- Goal Signal: desired future product direction.
- Task Signal: no concrete target, deliverable, or validation method for execution.
- Risk / Strategy Signal: product discovery and strategy required.
- Continue To: Goal Contract

## Goal Mode
- Status: Routed

## Partial Goal Spec
- Goal: Identify a worthwhile AI product direction.
- Current State: User has not chosen target users, problem, market wedge, or acceptance criteria.
- Desired End State: A clarified product direction with target user, problem, constraints, and first executable slice.
- In Scope: product discovery clarification.
- Out of Scope / Non-goals: implementation, deployment, market claims, and fabricated validation.
- Acceptance Criteria: target user, problem, demand evidence, and first slice are concrete.
- Validation Method: office-hours clarification returns a complete Clarified Spec.
- First Executable Slice: not ready until discovery is clarified.
- Stop / Ask / Escalate Conditions: route to clarification before any execution prompt.

## Goal Contract Check
- Route-Changing Ambiguities:
  - Product direction depends on target user, problem, demand, and constraints.
- Missing Fields:
  - Current State: no target user or market context.
  - Acceptance Criteria: no measurable success criteria.

## Domain Gate
- Domain: Product direction discovery.
- Category: Red
- Decision: Must route to clarification before Task Mode.
- Required Clarification: Discovery.
- Reason: Product direction requires user, demand, market wedge, and strategic boundaries before execution.

## Clarification Type
- Type: Discovery
- Recommended Route: $office-hours
- Inventory Required: Yes

## Inventory Decision
- Inventory Run: Yes
- Reason: CEO is selecting a discovery clarification route and must prove the recommended skill exists.
- Inventory Input: Raw goal with clarification intent.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: product, discovery
- Capability hints: clarify
- Validation hints: handoff

### Candidates
1. `$office-hours` (`office-hours`) score=30 path=/tmp/office-hours/SKILL.md

### Finalists To Read
1. `$office-hours` (`office-hours`) - /tmp/office-hours/SKILL.md

## Route Decision
- Next Route: Clarification
- Recommended Skill: $office-hours
- Reason: Product direction requires discovery before CEO can form an executable slice.

## Final Prompt
Use the following skill(s) if available: $office-hours

## Role
You are a product discovery partner clarifying an AI product direction before implementation.

## Objective
Clarify the AI product direction enough for $ceo to decide whether a first executable slice exists.

## Requirements
- Inputs: the user's raw goal, existing context, target users, product constraints, and any demand evidence they provide.
- In scope: clarify target user, problem, urgency, alternatives, wedge, constraints, acceptance criteria, and first executable slice.
- Out of scope / non-goals: do not implement, choose a final product direction without user evidence, deploy, or fabricate market validation.
- Deliverables: a `## Clarified Spec` handoff for `$ceo`.
- Constraints: keep unknowns explicit and preserve user decision boundaries.
- Assumptions and boundaries:
  - Assumption: product direction is still unresolved.
    Boundary: clarify only and return to `$ceo` before execution.
    Risk: direct execution would build around invented demand.
    Reversibility: clean.
- Failure / escalation conditions: stop if target user, problem, or acceptance criteria remain unknown and mark them blocking.

## Context
CEO routed this goal to discovery clarification because the goal is strategic and not yet executable.

## Thinking Process
Follow this visible workflow: identify missing discovery fields, ask focused office-hours questions, separate evidence from assumptions, define non-goals, and prepare a handoff for CEO.

## Validation
Verify the result includes `## Clarified Spec` with target user, problem, in-scope and out-of-scope boundaries, decision boundaries, constraints, acceptance criteria, risks, open questions, and a readiness note for `$ceo`.

## Output Format
Return exactly one markdown artifact headed `## Clarified Spec`, include CEO Handoff Summary, and include the exact next step: Return this Clarified Spec to $ceo for the final execution prompt.
"""


def goal_mode_risk_boundary_output() -> str:
    return """## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The user describes a high-risk production deletion and deployment goal without authority or rollback boundaries.
- Evidence: clean production database and redeploy.
- Immediate User Intent: clarify risk
- Goal Signal: desired future production state.
- Task Signal: no safe execution target, authority, or validation boundary.
- Risk / Strategy Signal: production deletion and deployment.
- Continue To: Goal Contract

## Goal Mode
- Status: Routed

## Partial Goal Spec
- Goal: Clean production data and redeploy safely.
- Current State: target environment, authority, data criteria, backup, and rollback are not provided.
- Desired End State: risk-bounded clarified spec for CEO re-evaluation.
- In Scope: risk boundary clarification.
- Out of Scope / Non-goals: execution commands, deletion, deployment, and approval fabrication.
- Acceptance Criteria: authority, target environment, backup, rollback, dry-run, verification, and stop conditions are explicit.
- Validation Method: inspect the Risk-Bounded Clarified Spec fields.
- First Executable Slice: not ready until risk boundaries are clarified.
- Stop / Ask / Escalate Conditions: stay in clarification until authority and rollback are explicit.

## Goal Contract Check
- High-Risk Boundaries:
  - Production deletion and deployment need authority, backup, rollback, and audit trail.
- Missing Fields:
  - Authority / Approval: not supplied.
  - Target Environment: not supplied.
  - Backup / Recovery: not supplied.

## Domain Gate
- Domain: Production deletion and deployment.
- Category: Red
- Decision: Must route to clarification before Task Mode.
- Required Clarification: Risk Boundary.
- Reason: Production mutation and deployment require authority, backup, rollback, dry-run, verification, and audit boundaries.

## Clarification Type
- Type: Risk Boundary

## Inventory Decision
- Inventory Run: No
- Reason: CEO is collecting risk boundaries directly and is not recommending a specific safety, security, deployment, or review skill.
- Inventory Input: Not applicable.

## Route Decision
- Next Route: Clarification
- Reason: Production deletion and deployment require explicit risk boundaries before Task Mode.

## Clarification Prompt
- Goal: Clean production data and redeploy safely.
- Risk Category: Production deletion and deployment.
- Affected Systems / Data: Unknown and blocking.
- Target Environment: Unknown and blocking.
- Authority / Approval: Unknown and blocking.
- Backup / Recovery: Unknown and blocking.
- Rollback Plan: Unknown and blocking.
- Dry-run / Simulation: Unknown and blocking.
- Verification Method: Unknown and blocking.
- Audit Trail: Unknown and blocking.
- Stop Conditions: Stop until authority, backup, rollback, and target environment are explicit.
- Explicitly Forbidden Until Approved: deletion, deployment, permission bypass, and production commands.
- Remaining Blocking Questions: Who approves the production data deletion, what exact data is in scope, and what backup and rollback plan exists?
- Readiness: Not Ready for Execution.
- CEO Handoff Summary: Return the completed Risk-Bounded Clarified Spec to $ceo for re-evaluation.
"""


def clarified_spec_request(*, blocking: bool = False) -> str:
    open_questions = "Choose React or Vue first." if blocking else "None blocking."
    return f"""## Clarified Spec
- Goal: Turn my rough app idea into a local web prototype.
- Deliverables: A single-page prototype and a short verification report.
- In Scope: Main workflow, responsive layout, and basic empty/error states.
- Out of Scope / Non-goals: Backend persistence, authentication, payments, deployment.
- Inputs / Context: Existing Vite app in the current workspace.
- Decision Boundaries: Use existing framework and dependencies; no new dependency unless necessary.
- Constraints: Keep changes small and run available checks.
- Acceptance Criteria: The prototype opens locally, main workflow works, mobile layout is usable, and checks pass or gaps are reported.
- Risks and Reversibility: UI-only changes are cleanly reversible; dependency changes are higher risk.
- Open Questions: {open_questions}
- CEO Handoff Summary: Build a focused local prototype using the existing app and verify it in browser.
"""


def discovery_return_request(*, ready: bool = True) -> str:
    target_user = "independent AI workflow builders who already use local agent skills weekly" if ready else "开发者"
    acceptance = (
        "Interview 5 target users, collect 3 repeated pain signals, and produce a pass/fail demand evidence report."
        if ready
        else "有人喜欢"
    )
    first_slice = (
        "Create a user interview plan and demand-evidence checklist for the narrow AI workflow-builder segment."
        if ready
        else "做个 MVP"
    )
    return f"""## Clarified Spec
- Goal: Validate whether an AI workflow assistant direction is worth pursuing.
- Target User / Audience: {target_user}
- Problem / Need: Local skill-heavy agent users cannot tell which workflow should handle ambiguous goals.
- Current Status Quo: They manually choose between planning, office-hours, and execution skills.
- Desired End State: A validated direction with a narrow wedge and first non-build validation slice.
- In Scope: user interview plan, demand evidence checklist, and decision criteria.
- Out of Scope / Non-goals: building an MVP, deployment, pricing, or broad market claims.
- Decision Boundaries: CEO may define validation artifacts but must not choose a product direction without evidence.
- Acceptance Criteria: {acceptance}
- First Executable Slice: {first_slice}
- Validation Method: Inspect completed interview plan and demand evidence checklist against acceptance criteria.
- Demand Evidence: 3 prior conversations show confusion around goal routing and clarification handoff.
- Status Quo Workaround: Users manually ask for office-hours or write custom prompts.
- Narrowest Wedge: Goal-router clarification for local agent skill users.
- Why Now / Future Fit: Agent skill libraries are growing and routing ambiguity is becoming frequent.
- Open Questions: None blocking.
- CEO Handoff Summary: Return this Clarified Spec to $ceo for final execution prompt decision.
"""


def risk_bounded_return_request(*, ready: bool = True) -> str:
    authority = "Approved by production owner Alice in ticket OPS-123 for staging-only dry-run planning." if ready else "有权限"
    backup = "Latest production backup verified at 2026-06-20 09:00 UTC; restore owner is named." if ready else "应该有"
    rollback = "Rollback plan restores from verified backup and aborts before any production mutation." if ready else "可以回滚"
    dry_run = "Dry-run must run against staging snapshot only; no production writes." if ready else "看情况"
    verification = "Compare row counts, audit logs, and dry-run report; no production mutation allowed." if ready else "看一下是否正常"
    readiness = "Ready for CEO Re-evaluation" if ready else "Not Ready for Execution"
    return f"""## Risk-Bounded Clarified Spec
- Goal: Prepare a production data cleanup and redeploy plan for CEO re-evaluation.
- Risk Category: Production deletion and deployment.
- Affected Systems / Data: production users table and deployment pipeline.
- Target Environment: staging snapshot only for the first executable slice.
- Authority / Approval: {authority}
- Backup / Recovery: {backup}
- Rollback Plan: {rollback}
- Dry-run / Simulation: {dry_run}
- Verification Method: {verification}
- Audit Trail: Record ticket, approver, dry-run output, and verification report.
- Stop Conditions: Stop before any production write, missing backup, missing owner, or failed dry-run.
- Explicitly Forbidden Until Approved: production deletion, production deployment, permission bypass, and destructive commands.
- Remaining Blocking Questions: None blocking.
- Readiness: {readiness}.
- CEO Handoff Summary: Return this Risk-Bounded Clarified Spec to $ceo for mode routing, skill inventory, and final execution-prompt decision.
"""


def local_goal_return_request(*, ready: bool = True) -> str:
    goal = (
        "Improve CEO skill routing so local goal clarification answers are re-evaluated before Task Mode handoff."
        if ready
        else "Make CEO better."
    )
    current_state = (
        "CEO has Goal Mode routing and contract checks, but local goal returns need explicit ready/not-ready regression coverage."
        if ready
        else "It is not good enough."
    )
    desired = (
        "Ready local goal returns route through Goal Mode Complete, vague local goal returns stay incomplete, and direct Task Mode skip fails."
        if ready
        else "More useful and smarter."
    )
    in_scope = (
        "Evaluator checks, structured fixtures, live fixture cases, and sample outputs for local goal return handling."
        if ready
        else "Improve everything."
    )
    out_scope = (
        "Unrelated skill ranking changes, new runtime workflows, broad rewrites, and downstream implementation work."
        if ready
        else "TBD."
    )
    acceptance = (
        "Ready return passes with Local Goal context, vague return fails Task Mode readiness, direct skip fails, and 4 focused unit tests pass."
        if ready
        else "It feels better."
    )
    validation = (
        "Run evaluator unit tests, fixture validation, contract drift validation, and fixture-mode sample checks."
        if ready
        else "Check if output is good."
    )
    first_slice = (
        "Add local goal return ready/not-ready evaluator tests and fixture cases."
        if ready
        else "Improve CEO."
    )
    stop_conditions = (
        "Stop if existing return-context behavior regresses or if the local answer is still too vague to form a first slice."
        if ready
        else "Unknown."
    )
    open_questions = "None blocking." if ready else "Still blocking."
    return f"""## Local Goal Clarified Spec
- Goal: {goal}
- Current State: {current_state}
- Desired End State: {desired}
- In Scope: {in_scope}
- Out of Scope / Non-goals: {out_scope}
- Acceptance Criteria: {acceptance}
- Validation Method: {validation}
- First Executable Slice: {first_slice}
- Stop / Ask / Escalate Conditions: {stop_conditions}
- Open Questions: {open_questions}
- CEO Handoff Summary: Return this Local Goal Clarified Spec to $ceo for Goal Mode re-evaluation.
"""


class EvaluatorTests(unittest.TestCase):
    def test_valid_output_passes(self) -> None:
        result = evaluator.check_contract(valid_ceo_output())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Task Mode", result["mode_actual"])

    def test_valid_clarification_output_passes(self) -> None:
        result = evaluator.check_contract(valid_clarification_output())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Task Mode", result["mode_actual"])

    def test_goal_mode_incomplete_output_passes_without_final_prompt(self) -> None:
        result = evaluator.check_contract(
            goal_mode_incomplete_output(),
            "我想把 CEO skill 做得更智能。",
        )
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Goal Mode", result["mode_actual"])
        self.assertEqual("Incomplete", result["goal_mode_status"])
        self.assertTrue(result["checks"]["inventory_run_no"])
        self.assertTrue(result["checks"]["no_final_prompt"])
        self.assertTrue(result["checks"]["no_skill_inventory_report"])

    def test_missing_inventory_decision_fails(self) -> None:
        text = valid_ceo_output().replace(
            "\n## Inventory Decision\n- Inventory Run: Yes\n- Reason: Task Mode requires skill routing evidence before producing Final Prompt.\n- Inventory Input: Raw user request.\n",
            "\n",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Inventory Decision", "\n".join(result["failures"]))

    def test_inventory_run_no_with_skill_inventory_report_fails(self) -> None:
        text = valid_ceo_output().replace("- Inventory Run: Yes", "- Inventory Run: No", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Inventory Run: No must not include Skill Inventory Report", "\n".join(result["failures"]))

    def test_skill_inventory_report_requires_inventory_run_yes(self) -> None:
        text = valid_ceo_output().replace("- Inventory Run: Yes", "- Inventory Run: Maybe", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Skill Inventory Report may appear only when Inventory Run is Yes", "\n".join(result["failures"]))

    def test_inventory_decision_after_skill_inventory_report_fails(self) -> None:
        decision = (
            "## Inventory Decision\n"
            "- Inventory Run: Yes\n"
            "- Reason: Task Mode requires skill routing evidence before producing Final Prompt.\n"
            "- Inventory Input: Raw user request.\n\n"
        )
        text = valid_ceo_output().replace(decision, "", 1)
        text = text.replace("## Skill Match\n", decision + "## Skill Match\n", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Inventory Decision must appear before Skill Inventory Report", "\n".join(result["failures"]))

    def test_goal_mode_incomplete_requires_clarification_type(self) -> None:
        text = goal_mode_incomplete_output().replace(
            "\n## Clarification Type\n- Type: Local Goal\n",
            "\n",
            1,
        )
        result = evaluator.check_contract(text, "我想把 CEO skill 做得更智能。")
        self.assertFalse(result["passed"])
        self.assertIn("Clarification Type", "\n".join(result["failures"]))

    def test_goal_mode_incomplete_blocking_question_must_target_gap(self) -> None:
        text = goal_mode_incomplete_output().replace(
            "你希望“更智能”具体体现为哪些可观察的 CEO 行为？",
            "你喜欢使用哪一种字体？",
            1,
        )
        result = evaluator.check_contract(text, "我想把 CEO skill 做得更智能。")
        self.assertFalse(result["passed"])
        self.assertIn("Blocking Question must target a reported gap", "\n".join(result["failures"]))

    def test_goal_mode_complete_to_task_mode_output_passes(self) -> None:
        result = evaluator.check_contract(goal_mode_complete_output())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Goal Mode", result["mode_actual"])
        self.assertEqual("Complete", result["goal_mode_status"])
        self.assertTrue(result["checks"]["inventory_run_yes"])
        self.assertTrue(result["checks"]["inventory_input_first_slice"])

    def test_goal_mode_complete_requires_domain_gate(self) -> None:
        text = goal_mode_complete_output().replace(
            "\n## Domain Gate\n"
            "- Domain: Local CEO skill workflow contract.\n"
            "- Category: Green\n"
            "- Decision: May route to Task Mode after the first executable slice is task-ready.\n"
            "- Required Clarification: None.\n"
            "- Reason: Low-risk, local, reversible skill/evaluator work with bounded validation.\n",
            "\n",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Domain Gate", "\n".join(result["failures"]))

    def test_goal_mode_product_direction_cannot_route_to_task_mode(self) -> None:
        result = evaluator.check_contract(
            goal_mode_complete_output(),
            "我想做一个 AI 产品，但还不确定方向，帮我找到值得做的方向。",
        )
        self.assertFalse(result["passed"])
        failures = "\n".join(result["failures"])
        self.assertIn("Domain Gate mismatch", failures)
        self.assertIn("must not route directly to Task Mode", failures)

    def test_goal_mode_yellow_architecture_assessment_can_route_to_task_mode(self) -> None:
        result = evaluator.check_contract(
            goal_mode_yellow_architecture_output(),
            "我想重构整个系统架构，让它更可扩展。首个切片是先产出架构评估报告，不改代码。",
        )
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Yellow", result["domain_gate"]["domain_gate_actual"])
        self.assertTrue(result["checks"]["domain_gate_contract"])

    def test_goal_mode_yellow_architecture_broad_implementation_fails(self) -> None:
        text = goal_mode_yellow_architecture_output().replace(
            "- First Executable Slice: Produce a bounded, reversible architecture assessment report with no code changes.",
            "- First Executable Slice: Implement a cross-module rewrite of the whole architecture.",
            1,
        ).replace(
            "- Task Input: Produce a bounded, reversible architecture assessment report with no code changes.",
            "- Task Input: Implement a cross-module rewrite of the whole architecture.",
            1,
        )
        result = evaluator.check_contract(text, "我想重构整个系统架构，让它更可扩展。")
        self.assertFalse(result["passed"])
        self.assertIn("Domain Gate Yellow may route to Task Mode only", "\n".join(result["failures"]))

    def test_goal_mode_complete_fails_when_inventory_uses_raw_goal(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: Raw goal.",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Inventory Input must mention First Executable Slice", "\n".join(result["failures"]))

    def test_goal_mode_complete_fails_with_vague_goal_spec_field(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Desired End State: CEO outputs Mode Router, handles incomplete goals without Final Prompt, and hands task-ready slices back to Task Mode.",
            "- Desired End State: 更智能",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Goal Spec has vague or placeholder fields", "\n".join(result["failures"]))

    def test_discovery_return_ready_allows_goal_complete_with_discovery_context_inventory(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Discovery Context from Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, discovery_return_request())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Discovery", result["clarified_return_context"]["type"])
        self.assertTrue(result["clarified_return_context"]["ready"])

    def test_discovery_return_not_ready_cannot_route_to_task_mode(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Discovery Context from Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, discovery_return_request(ready=False))
        self.assertFalse(result["passed"])
        self.assertIn("Discovery Clarified Spec return is not ready for Task Mode", "\n".join(result["failures"]))

    def test_discovery_return_must_not_skip_goal_mode(self) -> None:
        result = evaluator.check_contract(valid_ceo_output(), discovery_return_request())
        self.assertFalse(result["passed"])
        self.assertIn("Discovery Clarified Spec return must be re-evaluated through Goal Mode", "\n".join(result["failures"]))

    def test_risk_bounded_return_ready_requires_risk_context_inventory(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Risk-Bounded Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, risk_bounded_return_request())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Risk Boundary", result["clarified_return_context"]["type"])
        self.assertTrue(result["clarified_return_context"]["ready"])

    def test_risk_bounded_return_not_ready_cannot_route_to_task_mode(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Risk-Bounded Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, risk_bounded_return_request(ready=False))
        self.assertFalse(result["passed"])
        self.assertIn("Risk Boundary Clarified Spec return is not ready for Task Mode", "\n".join(result["failures"]))

    def test_risk_bounded_return_must_not_skip_goal_mode(self) -> None:
        result = evaluator.check_contract(valid_ceo_output(), risk_bounded_return_request())
        self.assertFalse(result["passed"])
        self.assertIn("Risk Boundary Clarified Spec return must be re-evaluated through Goal Mode", "\n".join(result["failures"]))

    def test_local_goal_return_ready_allows_goal_complete_with_local_context_inventory(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Local Goal Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, local_goal_return_request())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Local Goal", result["clarified_return_context"]["type"])
        self.assertTrue(result["clarified_return_context"]["ready"])

    def test_local_goal_return_not_ready_stays_goal_incomplete(self) -> None:
        result = evaluator.check_contract(goal_mode_incomplete_output(), local_goal_return_request(ready=False))
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Local Goal", result["clarified_return_context"]["type"])
        self.assertFalse(result["clarified_return_context"]["ready"])
        self.assertTrue(result["checks"]["inventory_run_no"])
        self.assertTrue(result["checks"]["no_final_prompt"])

    def test_local_goal_return_not_ready_cannot_route_to_task_mode(self) -> None:
        text = goal_mode_complete_output().replace(
            "- Inventory Input: First Executable Slice plus compact Goal Spec context.",
            "- Inventory Input: First Executable Slice plus Local Goal Clarified Spec.",
            1,
        )
        result = evaluator.check_contract(text, local_goal_return_request(ready=False))
        self.assertFalse(result["passed"])
        self.assertIn("Local Goal Clarified Spec return is not ready for Task Mode", "\n".join(result["failures"]))

    def test_local_goal_return_must_not_skip_goal_mode(self) -> None:
        result = evaluator.check_contract(valid_ceo_output(), local_goal_return_request())
        self.assertFalse(result["passed"])
        self.assertIn("Local Goal Clarified Spec return must be re-evaluated through Goal Mode", "\n".join(result["failures"]))

    def test_goal_mode_discovery_routed_output_passes(self) -> None:
        result = evaluator.check_contract(goal_mode_discovery_routed_output())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Routed", result["goal_mode_status"])
        self.assertEqual("Discovery", result["clarification_type"])
        self.assertTrue(result["checks"]["discovery_recommends_office_hours"])

    def test_goal_mode_discovery_fails_with_execution_prompt(self) -> None:
        text = goal_mode_discovery_routed_output().replace(
            "## Objective\nClarify the AI product direction enough for $ceo to decide whether a first executable slice exists.",
            "## Objective\nImplement the AI product direction now.",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("must not produce an execution prompt", "\n".join(result["failures"]))

    def test_goal_mode_risk_boundary_routed_output_passes_without_inventory(self) -> None:
        result = evaluator.check_contract(goal_mode_risk_boundary_output())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Routed", result["goal_mode_status"])
        self.assertEqual("Risk Boundary", result["clarification_type"])
        self.assertTrue(result["checks"]["risk_prompt_required_fields"])

    def test_goal_mode_risk_boundary_fails_ready_for_execution(self) -> None:
        text = goal_mode_risk_boundary_output().replace(
            "- Readiness: Not Ready for Execution.",
            "- Readiness: Ready for Execution.",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("must not claim Ready for Execution", "\n".join(result["failures"]))

    def test_goal_mode_risk_boundary_fails_with_execution_command(self) -> None:
        text = goal_mode_risk_boundary_output().replace(
            "- CEO Handoff Summary: Return the completed Risk-Bounded Clarified Spec to $ceo for re-evaluation.",
            "- Operational Step: Run `DELETE FROM users WHERE inactive = true;` after collecting answers.\n"
            "- CEO Handoff Summary: Return the completed Risk-Bounded Clarified Spec to $ceo for re-evaluation.",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("must not include execution commands", "\n".join(result["failures"]))

    def test_goal_mode_risk_boundary_fails_with_hard_stop(self) -> None:
        text = goal_mode_risk_boundary_output().replace(
            "## Route Decision\n",
            "## Hard Stop\nTerminate the task because it is risky.\n\n## Route Decision\n",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("route to clarification instead of using Hard Stop", "\n".join(result["failures"]))

    def test_goal_mode_incomplete_fails_when_final_prompt_is_present(self) -> None:
        text = goal_mode_incomplete_output() + "\n## Final Prompt\nDo the implementation now.\n"
        result = evaluator.check_contract(text, "我想把 CEO skill 做得更智能。")
        self.assertFalse(result["passed"])
        self.assertIn("must not include Final Prompt", "\n".join(result["failures"]))

    def test_goal_mode_incomplete_fails_with_more_than_one_blocking_question(self) -> None:
        text = goal_mode_incomplete_output().replace(
            "你希望“更智能”具体体现为哪些可观察的 CEO 行为？",
            "你希望“更智能”具体体现为哪些可观察的 CEO 行为？还需要改哪些文件？",
        )
        result = evaluator.check_contract(text, "我想把 CEO skill 做得更智能。")
        self.assertFalse(result["passed"])
        self.assertIn("exactly one Blocking Question", "\n".join(result["failures"]))

    def test_request_aware_direct_output_passes_clear_frontend(self) -> None:
        result = evaluator.check_contract(
            valid_ceo_output(),
            "做一个浏览器里的番茄钟工具，要有开始暂停、重置、长短休息切换、声音提示和移动端可用。",
        )
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Direct Path", result["triage_expected"])
        self.assertTrue(result["triage_passed"])

    def test_vague_request_direct_path_fails(self) -> None:
        result = evaluator.check_contract(
            valid_ceo_output(),
            "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。",
        )
        self.assertFalse(result["passed"])
        self.assertEqual("Clarification Path", result["triage_expected"])
        self.assertFalse(result["triage_passed"])
        self.assertIn("Triage mismatch", "\n".join(result["failures"]))

    def test_vague_request_office_hours_clarification_passes(self) -> None:
        result = evaluator.check_contract(
            valid_clarification_output(),
            "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。",
        )
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Clarification Path", result["triage_expected"])
        self.assertTrue(result["clarification_route_passed"])

    def test_deep_interview_quick_hard_route_fails_even_with_clarified_spec(self) -> None:
        text = valid_clarification_output().replace("$office-hours", "$deep-interview --quick")
        result = evaluator.check_contract(
            text,
            "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。",
        )
        self.assertFalse(result["passed"])
        self.assertIn("Clarification Path must route to $office-hours.", result["failures"])

    def test_deep_interview_quick_canonical_wording_fails_even_when_office_hours_present(self) -> None:
        text = valid_clarification_output().replace(
            "## Skill Match\n",
            "## Skill Match\n- Required canonical hard route: `$deep-interview --quick` before `$office-hours`.\n",
            1,
        )
        result = evaluator.check_contract(
            text,
            "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。",
        )
        self.assertFalse(result["passed"])
        self.assertIn("must not make $deep-interview --quick", "\n".join(result["failures"]))

    def test_keyword_rich_but_weak_requirements_fail(self) -> None:
        text = valid_ceo_output().replace(
            "## Requirements\n- Inputs: the current workspace and existing app structure.\n- In scope: start, pause, reset, long-break mode, short-break mode, sound alert, responsive UI, and accessible controls.\n- Out of scope / non-goals: backend persistence, payments, deployment, and authentication.\n- Deliverables: code changes for the timer and a short verification report with changed file paths.\n- Constraints: reuse existing framework and dependencies; no new dependency unless necessary.\n- Assumptions and boundaries:\n  - Assumption: an existing frontend app is available.\n    Boundary: inspect the app before changing files and keep edits scoped to UI code.\n    Risk: if no app exists, implementation cannot proceed safely.\n    Reversibility: clean.\n- Failure / escalation conditions: stop and report a blocker if no app entrypoint exists or if audio cannot be tested in the browser.\n",
            "## Requirements\n- Inputs: inputs and context are covered.\n- In scope: in scope is handled.\n- Out of scope / non-goals: non-goals are considered.\n- Deliverables: deliverables are produced.\n- Constraints: assumptions, boundaries, risk, and reversibility are included.\n- Failure / escalation conditions: failure and escalation are handled.\n",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("placeholder or too-generic", "\n".join(result["semantic_failures"]))

    def test_production_delete_execution_prompt_fails(self) -> None:
        result = evaluator.check_contract(
            valid_ceo_output(),
            "把生产数据库里旧用户数据清掉，然后部署最新版本。",
        )
        self.assertFalse(result["passed"])
        self.assertEqual("Clarification Path", result["triage_expected"])
        self.assertFalse(result["triage_passed"])

    def test_production_delete_clarification_prompt_passes(self) -> None:
        result = evaluator.check_contract(
            production_clarification_output(),
            "把生产数据库里旧用户数据清掉，然后部署最新版本。",
        )
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Clarification Path", result["triage_expected"])

    def test_ready_clarified_spec_allows_direct_path(self) -> None:
        result = evaluator.check_contract(valid_ceo_output(), clarified_spec_request())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual("Direct Path", result["triage_expected"])
        self.assertTrue(result["clarified_spec_readiness"]["ready"])

    def test_blocking_clarified_spec_direct_path_fails(self) -> None:
        result = evaluator.check_contract(valid_ceo_output(), clarified_spec_request(blocking=True))
        self.assertFalse(result["passed"])
        self.assertEqual("Clarification Path", result["triage_expected"])
        self.assertFalse(result["clarified_spec_readiness"]["ready"])

    def test_missing_pr_target_requires_clarification(self) -> None:
        result = evaluator.check_contract(
            valid_ceo_output(),
            "审查这个 PR 里 API 变更是否会破坏现有客户端，并给我一个可执行的修复计划。",
        )
        self.assertFalse(result["passed"])
        self.assertIn("missing-critical-input:pr-or-repo", result["triage_reasons"])

    def test_missing_top_level_section_fails(self) -> None:
        text = valid_ceo_output().replace("## Assumptions\n", "## Notes\n", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Assumptions", result["missing_sections"])

    def test_out_of_order_final_headings_fail(self) -> None:
        text = valid_ceo_output().replace("## Objective\nBuild", "## Validation\nBuild", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Objective", result["missing_final_prompt_headings"])

    def test_untraceable_skill_fails(self) -> None:
        text = valid_ceo_output().replace(
            "- Supporting match: use `$playwright`",
            "- Supporting match: use `$not-in-inventory`",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("not-in-inventory", result["untraceable_skills"])

    def test_shell_variables_are_not_selected_skills(self) -> None:
        text = valid_ceo_output().replace(
            "## Context\n",
            "## Context\nUse shell variable `$HOME` only as an example, not as a skill.\n",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertTrue(result["passed"], result["failures"])
        self.assertNotIn("HOME", result["selected_skills"])

    def test_semantically_empty_requirements_and_validation_fail(self) -> None:
        text = valid_ceo_output()
        text = text.replace(
            "## Requirements\n- Inputs: the current workspace and existing app structure.\n- In scope: start, pause, reset, long-break mode, short-break mode, sound alert, responsive UI, and accessible controls.\n- Out of scope / non-goals: backend persistence, payments, deployment, and authentication.\n- Deliverables: code changes for the timer and a short verification report with changed file paths.\n- Constraints: reuse existing framework and dependencies; no new dependency unless necessary.\n- Assumptions and boundaries:\n  - Assumption: an existing frontend app is available.\n    Boundary: inspect the app before changing files and keep edits scoped to UI code.\n    Risk: if no app exists, implementation cannot proceed safely.\n    Reversibility: clean.\n- Failure / escalation conditions: stop and report a blocker if no app entrypoint exists or if audio cannot be tested in the browser.\n",
            "## Requirements\nDo the requested thing.\n",
        )
        text = text.replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\nCheck it.\n",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertTrue(result["semantic_failures"])

    def test_placeholder_requirement_fields_fail(self) -> None:
        text = valid_ceo_output().replace(
            "- Inputs: the current workspace and existing app structure.",
            "- Inputs: TBD.",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("placeholder or too-generic field values", "\n".join(result["semantic_failures"]))

    def test_template_validation_lines_fail(self) -> None:
        text = valid_ceo_output().replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\n- Run checks.\n- Verify output.\n- Capture screenshots.\n",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Validation lacks concrete evidence", "\n".join(result["semantic_failures"]))

    def test_evaluator_cli_markdown_pass_and_fail(self) -> None:
        command = [sys.executable, str(SCRIPT_DIR / "evaluate_ceo_output.py"), "--format", "markdown"]
        valid = subprocess.run(
            command,
            input=valid_ceo_output(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, valid.returncode, valid.stderr)
        self.assertIn("CEO Output Evaluation: PASS", valid.stdout)

        invalid_text = valid_ceo_output().replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\nCheck it.\n",
        )
        invalid = subprocess.run(
            command,
            input=invalid_text,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, invalid.returncode)
        self.assertIn("CEO Output Evaluation: FAIL", invalid.stdout)
        self.assertIn("Validation lacks concrete evidence", invalid.stdout)

    def test_evaluator_cli_json_reports_request_triage(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "evaluate_ceo_output.py"),
            "--request",
            "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。",
            "--format",
            "json",
        ]
        result = subprocess.run(
            command,
            input=valid_clarification_output(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = __import__("json").loads(result.stdout)
        self.assertEqual("Clarification Path", payload["triage_expected"])
        self.assertEqual("Clarification Path", payload["triage_actual"])
        self.assertTrue(payload["triage_passed"])
        self.assertTrue(payload["clarification_route_passed"])
        self.assertIn("clarified_spec_readiness", payload)


class InventoryTests(unittest.TestCase):
    def make_skill(self, root: Path, rel: str, name: str, description: str) -> Path:
        path = root / rel / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        return path

    def test_complex_task_uses_15_candidate_limit_and_4_finalists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(20):
                self.make_skill(
                    root,
                    f"skill-{index}",
                    f"skill-{index}",
                    "frontend browser design testing build verify website app",
                )
            report = skill_inventory.build_report(
                inventory_args("Build a frontend browser design and testing workflow.", [str(root)])
            )
            analysis = report["request_analysis"]
            self.assertEqual("complex", analysis["complexity"])
            self.assertEqual(15, analysis["candidate_limit"])
            self.assertLessEqual(len(report["finalists_to_read"]), 4)

    def test_low_signal_request_does_not_expand_to_complex_or_source_only_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(20):
                self.make_skill(
                    root,
                    f"generic-{index}",
                    f"generic-{index}",
                    "General workflow helper without task-specific terms",
                )
            report = skill_inventory.build_report(
                inventory_args("写一个更好的提示词，用来总结会议纪要", [str(root)])
            )
            analysis = report["request_analysis"]
            self.assertEqual("standard", analysis["complexity"])
            self.assertEqual(10, analysis["candidate_limit"])
            self.assertEqual([], report["candidates"])
            self.assertEqual([], report["finalists_to_read"])

    def test_plugin_invocation_name_uses_plugin_prefix(self) -> None:
        old_codex_home = os.environ.get("CODEX_HOME")
        with tempfile.TemporaryDirectory() as temp:
            os.environ["CODEX_HOME"] = str(Path(temp) / ".codex")
            path = (
                Path(os.environ["CODEX_HOME"])
                / "plugins/cache/vendor/sample-plugin/1.2.3/skills/do-thing/SKILL.md"
            )
            self.assertEqual("sample-plugin:do-thing", skill_inventory.invocation_name_for_path(str(path), "do-thing"))
        if old_codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = old_codex_home

    def test_plugin_prefixed_frontmatter_is_not_double_prefixed(self) -> None:
        old_codex_home = os.environ.get("CODEX_HOME")
        with tempfile.TemporaryDirectory() as temp:
            os.environ["CODEX_HOME"] = str(Path(temp) / ".codex")
            path = (
                Path(os.environ["CODEX_HOME"])
                / "plugins/cache/vendor/sample-plugin/1.2.3/skills/do-thing/SKILL.md"
            )
            self.assertEqual(
                "sample-plugin:do-thing",
                skill_inventory.invocation_name_for_path(str(path), "sample-plugin:do-thing"),
            )
        if old_codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = old_codex_home

    def test_duplicate_collapse_by_invocation_name(self) -> None:
        records = [
            {"invocation_name": "demo", "name": "demo", "path": "/b/SKILL.md"},
            {"invocation_name": "demo", "name": "demo", "path": "/a/SKILL.md"},
            {"invocation_name": "other", "name": "other", "path": "/c/SKILL.md"},
        ]
        unique, duplicates = skill_inventory.collapse_duplicates(records)
        self.assertEqual(["/a/SKILL.md", "/c/SKILL.md"], [item["path"] for item in unique])
        self.assertEqual(1, len(duplicates))

    def test_gstack_alias_family_dedupes_candidates(self) -> None:
        candidates = [
            {
                "name": "review",
                "invocation_name": "review",
                "description": "Pre-landing PR review",
                "path": "/tmp/review/SKILL.md",
                "score": 12,
                "score_breakdown": {"query": 12},
                "matched_terms": [],
            },
            {
                "name": "gstack-review",
                "invocation_name": "gstack-review",
                "description": "Pre-landing PR review",
                "path": "/tmp/gstack-review/SKILL.md",
                "score": 10,
                "score_breakdown": {"query": 10},
                "matched_terms": [],
            },
        ]
        collapsed, aliases = skill_inventory.collapse_alias_families(candidates)
        self.assertEqual(1, len(collapsed))
        self.assertEqual(["gstack-review"], collapsed[0]["aliases"])
        self.assertEqual(1, len(aliases))

    def test_frontmatter_parser_stops_at_frontmatter_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text(
                "---\nname: demo\ndescription: frontmatter description\n---\n"
                "name: body-should-not-win\ndescription: body should not be read\n",
                encoding="utf-8",
            )
            data = skill_inventory.parse_frontmatter(path)
            self.assertEqual("demo", data["name"])
            self.assertEqual("frontmatter description", data["description"])

    def test_out_of_scope_capability_is_penalized_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            request = (
                "Build a frontend app.\n"
                "Out of Scope / Non-goals: do not deploy, release, or ship anything."
            )
            report = skill_inventory.build_report(inventory_args(request, [str(root)]))
            analysis = report["request_analysis"]
            self.assertIn("deploy", analysis["out_of_scope_capability_hints"])
            deploy_candidate = next(item for item in report["candidates"] if item["name"] == "deploy-skill")
            self.assertLess(deploy_candidate["score_breakdown"]["out_of_scope_penalty"], 0)
            self.assertIn("out-of-scope-capability:deploy", deploy_candidate["matched_terms"])

    def test_inline_out_of_scope_is_extracted_from_natural_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            report = skill_inventory.build_report(
                inventory_args("Build a frontend app but do not deploy, release, or ship anything.", [str(root)])
            )
            analysis = report["request_analysis"]
            self.assertIn("deploy", analysis["out_of_scope_capability_hints"])
            self.assertNotIn("deploy", analysis["capability_hints"])
            deploy_candidate = next(item for item in report["candidates"] if item["name"] == "deploy-skill")
            self.assertLess(deploy_candidate["score_breakdown"]["out_of_scope_penalty"], 0)

    def test_inventory_cli_markdown_reports_out_of_scope_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            command = [
                sys.executable,
                str(SCRIPT_DIR / "skill_inventory.py"),
                "--request",
                "Build a frontend app.\nOut of Scope / Non-goals: do not deploy, release, or ship anything.",
                "--format",
                "markdown",
                "--roots",
                str(root),
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Skill Inventory Report", result.stdout)
            self.assertIn("Out-of-scope capability hints ignored/penalized: deploy", result.stdout)
            self.assertIn("out-of-scope-capability:deploy", result.stdout)

    def test_repo_doc_readme_does_not_promote_qa_or_diagnose_as_primary_finalists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "qa", "qa", "Systematically QA test a web application and fix bugs found")
            self.make_skill(root, "diagnose", "diagnose", "Disciplined diagnosis loop for hard bugs")
            self.make_skill(root, "devex-review", "devex-review", "Live developer experience audit for docs and setup")
            report = skill_inventory.build_report(
                inventory_args("为 /tmp/project 的 README 增加安装步骤和本地开发命令，保持现有风格。", [str(root)])
            )
            self.assertTrue(report["request_analysis"]["no_special_skill_recommended"])
            self.assertEqual([], report["finalists_to_read"])

    def test_repo_doc_specific_skill_can_be_finalist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "repo-doc", "repo-doc-helper", "Update README markdown repository docs install local development commands")
            self.make_skill(root, "qa", "qa", "Systematically QA test a web application and fix bugs found")
            report = skill_inventory.build_report(
                inventory_args("为 /tmp/project 的 README 增加安装步骤和本地开发命令，保持现有风格。", [str(root)])
            )
            self.assertFalse(report["request_analysis"]["no_special_skill_recommended"])
            self.assertIn("repo-doc-helper", [item["invocation_name"] for item in report["finalists_to_read"]])

    def test_complex_finalists_are_role_diverse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "code-review", "code-review", "code review api breaking change client plan")
            self.make_skill(root, "review", "review", "code review api breaking change client plan")
            self.make_skill(root, "github", "github", "github pull request issue inspect source access")
            self.make_skill(root, "playwright", "playwright", "browser testing validation screenshot")
            self.make_skill(root, "plan", "plan", "plan requirements strategy risk")
            report = skill_inventory.build_report(
                inventory_args("审查这个 PR 里 API 变更是否会破坏现有客户端，并给我一个可执行的修复计划。", [str(root)])
            )
            roles = {item["finalist_role"] for item in report["finalists_to_read"]}
            self.assertIn("primary", roles)
            self.assertIn("source-access", roles)
            self.assertLessEqual(len(report["finalists_to_read"]), 4)

    def test_clarification_path_forces_office_hours_finalist_rank_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "frontend", "frontend-skill", "frontend website app build")
            self.make_skill(root, "playwright", "playwright", "browser testing validation screenshot")
            self.make_skill(root, "office", "office-hours", "YC Office Hours clarify vague product requirements scope")
            args = inventory_args("我想做一个产品但不确定是否值得做，请帮我想清楚方向和范围。", [str(root)])
            args.triage = "clarification"
            report = skill_inventory.build_report(args)
            self.assertEqual("office-hours", report["finalists_to_read"][0]["invocation_name"])
            self.assertIn("clarification-priority", report["request_analysis"]["finalist_selection"])

    def test_clarification_path_gstack_office_hours_alias_rank_1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "frontend", "frontend-skill", "frontend website app build")
            self.make_skill(root, "office", "gstack-office-hours", "YC Office Hours clarify vague product requirements scope")
            args = inventory_args("我想做一个产品但不确定是否值得做，请帮我想清楚方向和范围。", [str(root)])
            args.triage = "clarification"
            report = skill_inventory.build_report(args)
            self.assertEqual("gstack-office-hours", report["finalists_to_read"][0]["invocation_name"])

    def test_inventory_cache_cold_warm_and_invalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            cache_path = Path(temp) / "cache.json"
            self.make_skill(root, "office", "office-hours", "YC Office Hours clarify vague product requirements scope")
            args = inventory_args("我不确定产品方向，请帮我想清楚。", [str(root)])
            args.triage = "clarification"
            args.no_cache = False
            args.cache_path = str(cache_path)
            args.rebuild_cache = True
            cold = skill_inventory.build_report(args)
            self.assertEqual(0, cold["inventory"]["cache"]["hits"])
            self.assertGreaterEqual(cold["inventory"]["cache"]["misses"], 1)
            args.rebuild_cache = False
            warm = skill_inventory.build_report(args)
            self.assertGreaterEqual(warm["inventory"]["cache"]["hits"], 1)
            changed = root / "office" / "SKILL.md"
            changed.write_text(
                "---\nname: office-hours\ndescription: YC Office Hours clarify vague product requirements scope updated\n---\n",
                encoding="utf-8",
            )
            invalidated = skill_inventory.build_report(args)
            self.assertGreaterEqual(invalidated["inventory"]["cache"]["misses"], 1)

    def test_explicit_dollar_invocation_matches_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "frontend", "frontend-skill", "frontend website app build")
            self.make_skill(root, "other", "other", "generic helper")
            report = skill_inventory.build_report(
                inventory_args("Use $frontend-skill to build a frontend app.", [str(root)])
            )
            self.assertEqual("frontend-skill", report["candidates"][0]["invocation_name"])

    def test_markdown_request_penalizes_office_documents_skill(self) -> None:
        old_codex_home = os.environ.get("CODEX_HOME")
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        os.environ["CODEX_HOME"] = str(Path(temp.name) / ".codex")
        self.addCleanup(lambda: os.environ.pop("CODEX_HOME", None) if old_codex_home is None else os.environ.__setitem__("CODEX_HOME", old_codex_home))
        record = {
            "name": "documents",
            "invocation_name": "documents:documents",
            "description": "Create and edit docx Word Google Docs documents",
            "path": str(
                Path(os.environ["CODEX_HOME"])
                / "plugins/cache/openai-primary-runtime/documents/1/skills/documents/SKILL.md"
            ),
            "source_root": "/tmp",
        }
        scored = skill_inventory.score_skill(
            record,
            "Update README markdown install steps.",
            ["readme", "markdown", "install", "steps"],
            ["document", "repo-doc"],
            ["edit"],
            [],
            [],
            [],
            {"markdown_doc": True, "office_doc": False},
        )
        self.assertLess(scored["score_breakdown"]["out_of_scope_penalty"], 0)
        self.assertIn("mismatch:markdown-not-office-doc", scored["matched_terms"])

    def test_default_roots_include_multi_agent_hosts(self) -> None:
        roots = skill_inventory.default_roots()
        self.assertIn(str(Path.home() / ".claude" / "skills"), roots)
        self.assertIn(str(Path.home() / ".openclaw" / "skills"), roots)
        self.assertIn(str(Path.home() / ".hermes" / "skills"), roots)


class ReleaseArtifactTests(unittest.TestCase):
    def test_contract_drift_check_passes(self) -> None:
        failures = validate_contract_drift.validate_contract_drift()
        self.assertEqual([], failures)

    def test_structured_eval_fixtures_are_valid(self) -> None:
        payload = json.loads((REPO_ROOT / "references" / "eval-fixtures.json").read_text(encoding="utf-8"))
        failures = validate_eval_fixtures.validate_fixture_payload(payload)
        self.assertEqual([], failures)

    def test_multi_agent_adapter_notes_exist_without_skill_filename(self) -> None:
        adapters = {
            "claude-code": "Claude Code",
            "openclaw": "OpenClaw",
            "hermes": "Hermes",
        }
        for adapter, host_name in adapters.items():
            with self.subTest(adapter=adapter):
                path = REPO_ROOT / "adapters" / f"{adapter}.md"
                self.assertTrue(path.exists(), f"missing {path}")
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\nname: ceo\n"), f"{path} must expose name: ceo")
                self.assertIn("description:", text)
                self.assertIn(host_name, text)
                self.assertIn("skill_inventory.py", text)
                self.assertIn("CEO_SKILL_HOME", text)
        self.assertEqual([], list((REPO_ROOT / "adapters").rglob("SKILL.md")))

    def test_multi_agent_docs_are_linked_and_cover_hosts(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        guide = (REPO_ROOT / "docs" / "multi-agent-usage.md").read_text(encoding="utf-8")
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")

        for required in [
            "adapters/claude-code.md",
            "adapters/openclaw.md",
            "adapters/hermes.md",
            "docs/multi-agent-usage.md",
            "OPENCLAW_HOME",
            "HERMES_HOME",
        ]:
            self.assertIn(required, readme)

        for required in ["Codex", "Claude Code", "OpenClaw", "Hermes", "CEO_SKILL_HOME"]:
            self.assertIn(required, guide)

        self.assertIn("${OPENCLAW_HOME:-$HOME/.openclaw}/skills", skill)
        self.assertIn("${HERMES_HOME:-$HOME/.hermes}/skills", skill)

    def test_multi_agent_install_verifier_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "verify_multi_agent_install.py")],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Multi-agent install verification: PASS", result.stdout)
        for host in ["codex", "claude-code", "openclaw", "hermes"]:
            self.assertIn(f"- {host}: ok", result.stdout)

    def test_benchmark_script_fast_sample_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "benchmark_skill_inventory_scale.py"), "--sizes", "7", "20", "--format", "json"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(all(item["clarification_priority_rank1"] for item in payload["benchmarks"]))

    def test_host_native_smoke_script_skips_or_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "smoke_host_native_cli.py"), "--format", "json"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])

    def test_live_model_fixture_suite_saves_outputs_and_results(self) -> None:
        timestamp = f"test-{os.getpid()}"
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "run_live_model_samples.py"), "--mode", "fixture", "--timestamp", timestamp],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["passed"], payload["total"])
        generated = REPO_ROOT / "evals" / "live-model" / "generated" / timestamp
        results = REPO_ROOT / "evals" / "live-model" / "results" / timestamp
        self.assertTrue(generated.exists())
        self.assertTrue((results / "evaluator-results.jsonl").exists())
        for path in sorted(generated.glob("*.md")):
            path.unlink()
        for path in sorted(results.glob("*")):
            path.unlink()
        generated.rmdir()
        results.rmdir()


if __name__ == "__main__":
    unittest.main()
