#!/usr/bin/env python3
"""Run or evaluate minimal live-model CEO output samples."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import evaluate_ceo_output as evaluator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = REPO_ROOT / "evals" / "live-model" / "cases.jsonl"
GENERATED_ROOT = REPO_ROOT / "evals" / "live-model" / "generated"
RESULTS_ROOT = REPO_ROOT / "evals" / "live-model" / "results"


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def goal_mode_fixture_output(case: dict[str, Any]) -> str:
    status = case["expected_goal_mode_status"]
    if status == "Incomplete":
        if case.get("expected_return_type") == "Local Goal":
            return f"""## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The generated fixture exercises a not-ready Local Goal Clarified Spec return.
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: define
- Goal Signal: local goal answer remains vague after clarification.
- Task Signal: no task-ready first slice, acceptance criteria, or validation.
- Risk / Strategy Signal: route could change after the desired behavior is clarified.
- Continue To: Goal Contract

## Goal Mode
- Status: Incomplete

## Goal Contract Check
- Ready Fields:
  - Goal: local CEO behavior should improve.
- Missing Fields:
  - Desired End State: no observable behavior is defined.
  - Acceptance Criteria: no pass/fail criteria are defined.
  - First Executable Slice: no bounded task can be handed to Task Mode.
- Vague Fields:
  - Goal: "make CEO better" is not observable.
- Unverifiable Fields:
  - Validation Method: no proof method exists.
- Route-Changing Ambiguities:
  - Motivation: could mean routing, output structure, skill selection, or evaluation coverage.
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
Which one observable CEO behavior should improve first, and how would you know it passed?

## Why This Question Comes First
Without an observable desired end state and pass/fail signal, CEO cannot form a task-ready first executable slice.
"""
        return f"""## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The generated fixture exercises Goal Mode Incomplete.
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: define
- Goal Signal: vague desired future capability.
- Task Signal: no task-ready target, action, deliverable, or validation.
- Risk / Strategy Signal: route could change after the desired behavior is clarified.
- Continue To: Goal Contract

## Goal Mode
- Status: Incomplete

## Goal Contract Check
- Ready Fields:
  - Goal: improve CEO behavior.
- Missing Fields:
  - Desired End State: no observable behavior is defined.
  - Acceptance Criteria: no pass/fail criteria are defined.
  - First Executable Slice: no bounded task can be handed to Task Mode.
- Vague Fields:
  - Goal: "smarter" is not observable.
- Unverifiable Fields:
  - Validation Method: no proof method exists.
- Route-Changing Ambiguities:
  - Motivation: could mean routing, output structure, skill selection, or long-term goal management.
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
What observable CEO behavior should "smarter" mean?

## Why This Question Comes First
Without an observable desired end state, CEO cannot form acceptance criteria or a first executable slice.
"""

    if status == "Complete":
        return_type = case.get("expected_return_type")
        if return_type == "Discovery":
            inventory_input = "First Executable Slice plus Discovery Context from Clarified Spec."
        elif return_type == "Risk Boundary":
            inventory_input = "First Executable Slice plus Risk-Bounded Clarified Spec."
        elif return_type == "Local Goal":
            inventory_input = "First Executable Slice plus Local Goal Clarified Spec."
        else:
            inventory_input = "First Executable Slice plus compact Goal Spec context."
        if case.get("expected_domain_gate") == "Yellow":
            goal = "Identify a safe path to make the system architecture more extensible."
            current_state = "The current architecture has suspected extensibility limits but no reviewed assessment yet."
            desired_end_state = "A reviewed architecture assessment identifies bounded improvement options before any code rewrite."
            in_scope = "architecture assessment report, module boundary map, risk list, and candidate first implementation slices."
            out_of_scope = "direct code rewrite, migration, deployment, broad cross-module refactor, and production changes."
            inputs_context = "Current repository structure, architecture notes, module boundaries, tests, and known pain points."
            risks = "Assessment-only work is cleanly reversible; broad implementation would be higher risk."
            acceptance = "Assessment names current boundaries, top 3 risks, candidate slices, non-goals, and validation evidence."
            validation = "Inspect the architecture assessment report against repository evidence and required checklist fields."
            first_slice = "Produce a bounded, reversible architecture assessment report with no code changes."
            risk_signal = "Yellow architecture/refactor domain; broad implementation is not allowed yet."
            domain_gate = """- Domain: Architecture refactor strategy.
- Category: Yellow
- Decision: May route to Task Mode only for bounded assessment, design, documentation, or test-oriented slices.
- Required Clarification: None for assessment-only slice; required before broad implementation or migration.
- Reason: Architecture goals are conditionally allowed when the first slice is bounded, reversible, and does not choose strategy for the user."""
            route_reason = "Goal Contract is complete and Domain Gate Yellow allows this assessment-only first slice."
            task_input = "Produce a bounded, reversible architecture assessment report with no code changes."
            scope_boundary = "repository inspection and assessment report only; no code changes."
            task_validation = "architecture assessment checklist, evidence-backed module map, and no code diff."
        else:
            goal = "CEO can classify user input as Task Mode or Goal Mode before producing downstream prompts."
            current_state = "CEO has an existing Task Mode path and needs a bounded Goal Mode router contract."
            desired_end_state = "CEO outputs Mode Router, keeps incomplete goals out of Final Prompt, and hands task-ready slices back to Task Mode."
            in_scope = "SKILL.md instructions, evaluator checks, fixtures, and generated sample outputs for the routing contract."
            out_of_scope = "long-term goal management, product discovery ownership, deployment, and unrelated skill rewrites."
            inputs_context = "Current CEO skill files, goal-mode design notes, evaluator fixtures, and test scripts."
            risks = "Contract drift is the main risk; changes are reversible by reverting the skill files."
            acceptance = "Task Mode fixtures still pass, Goal Mode Incomplete forbids Final Prompt, and Goal Complete requires inventory on the first executable slice."
            validation = "Run quick validation, fixture validation, contract drift checks, unit tests, and fixture-mode live samples."
            first_slice = "Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff."
            risk_signal = "low-risk local skill contract change."
            domain_gate = """- Domain: Local CEO skill workflow contract.
- Category: Green
- Decision: May route to Task Mode after the first executable slice is task-ready.
- Required Clarification: None.
- Reason: Low-risk, local, reversible skill/evaluator work with bounded validation."""
            route_reason = "Goal Contract is complete and the first executable slice is bounded, local, reversible, and testable."
            task_input = "Add evaluator and fixture coverage for Goal Mode Complete -> Task Mode handoff."
            scope_boundary = "CEO skill contract files only."
            task_validation = "quick validation, fixture validation, contract drift checks, unit tests, and fixture live samples."
        if return_type == "Local Goal":
            goal = "CEO can re-evaluate local goal clarification answers before Task Mode handoff."
            current_state = "Goal Mode exists, but local goal return answers need dedicated ready/not-ready contract coverage."
            desired_end_state = "Ready local goal returns route through Goal Mode Complete, vague returns stay incomplete, and direct Task Mode skip fails."
            in_scope = "evaluator checks, structured fixtures, live fixture cases, and sample outputs for local goal return handling."
            out_of_scope = "unrelated skill ranking changes, new runtime workflows, broad rewrites, and downstream implementation work."
            inputs_context = "Current CEO evaluator, fixture files, live-model fixture cases, and goal-mode contract notes."
            risks = "Contract drift is the main risk; changes are reversible by reverting the evaluator and fixture edits."
            acceptance = "Ready local return passes with Local Goal context, vague return fails Task Mode readiness, direct skip fails, and focused unit tests pass."
            validation = "Run evaluator unit tests, fixture validation, contract drift validation, and fixture-mode sample checks."
            first_slice = "Add local goal return ready/not-ready evaluator tests and fixture cases."
            risk_signal = "low-risk local contract coverage change."
            domain_gate = """- Domain: Local CEO skill workflow contract.
- Category: Green
- Decision: May route to Task Mode after the first executable slice is task-ready.
- Required Clarification: None.
- Reason: Low-risk, local, reversible evaluator and fixture work with bounded validation."""
            route_reason = "Goal Contract is complete and the returned Local Goal Clarified Spec is ready for Task Mode handoff."
            task_input = "Add local goal return ready/not-ready evaluator tests and fixture cases."
            scope_boundary = "CEO evaluator and fixture surfaces only."
            task_validation = "focused unit tests, fixture validation, contract drift validation, and fixture live samples."
        if case["id"] in {"goal-readme-clarity", "goal-contractcheck-readability"}:
            goal = "Improve a local CEO skill document or output section so external users can understand it more easily."
            current_state = "The current wording is functional but not reader-friendly enough for external users."
            desired_end_state = "A clearer document or output section that preserves behavior while improving readability."
            in_scope = "copy clarity, section structure, examples, and small readability improvements."
            out_of_scope = "behavior changes, router redesign, broad refactors, or unrelated skill rewrites."
            inputs_context = "Current CEO skill files and the existing wording to improve."
            risks = "Over-editing could change behavior; keep changes small and reversible."
            acceptance = "The revised wording is clearer for external users while preserving current behavior."
            validation = "Review the revised wording against the current output contract and confirm no behavior drift."
            first_slice = "Revise the target wording for readability without changing behavior."
            domain_gate = """- Domain: Local CEO skill output/document clarity.
- Category: Green
- Decision: May route to Task Mode after the first executable slice is task-ready.
- Required Clarification: None.
- Reason: Low-risk, local wording improvement with reversible changes."""
            route_reason = "Goal Contract is complete and the first executable slice is bounded, local, reversible, and testable."
            task_input = "Revise the target wording for readability without changing behavior."
            scope_boundary = "target wording only; no behavior changes."
            task_validation = "compare revised wording against existing behavior and confirm no contract drift."
        return f"""## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The generated fixture exercises Goal Mode Complete to Task Mode.
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: define
- Goal Signal: desired future capability or quality bar.
- Task Signal: first executable slice is bounded and testable.
- Risk / Strategy Signal: {risk_signal}
- Continue To: Goal Contract

## Goal Mode
- Status: Complete

## Goal Spec
- Goal: {goal}
- Current State: {current_state}
- Desired End State: {desired_end_state}
- In Scope: {in_scope}
- Out of Scope / Non-goals: {out_of_scope}
- Inputs / Context: {inputs_context}
- Constraints: Preserve existing Task Mode behavior and keep edits scoped to the CEO skill contract.
- Decision Boundaries: CEO may add structural routing checks but must not invent unrelated execution workflows.
- Assumptions: The first slice is local and reversible.
- Risks and Reversibility: {risks}
- Acceptance Criteria: {acceptance}
- Validation Method: {validation}
- First Executable Slice: {first_slice}
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
{domain_gate}

## Clarification Type
- Type: Not Required

## Inventory Decision
- Inventory Run: Yes
- Reason: First Executable Slice is task-ready and CEO must select execution and validation skills.
- Inventory Input: {inventory_input}

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
- Reason: {route_reason}

## Task Mode Handoff
- Ready for Task Mode: Yes
- Task Input: {task_input}
- Scope Boundary: {scope_boundary}
- Validation: {task_validation}

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

    if case.get("expected_clarification_type") == "Discovery":
        discovery_goal = "Identify a worthwhile AI product direction."
        discovery_current = "User has not chosen target users, problem, market wedge, or acceptance criteria."
        discovery_desired = "A clarified product direction with target user, problem, constraints, and first executable slice."
        discovery_scope = "product discovery clarification."
        discovery_gate_domain = "Product direction discovery."
        discovery_gate_reason = "Product direction requires user, demand, market wedge, and strategic boundaries before execution."
        discovery_route_reason = "Product direction requires discovery before CEO can form an executable slice."
        discovery_signal = "product direction outcome."
        discovery_risk = "product discovery and strategy required."
        if case["id"] == "goal-startup-discovery-routed":
            discovery_goal = "Identify a startup direction worth exploring."
            discovery_current = "User has not chosen a market, user segment, pain, wedge, or evidence standard."
            discovery_desired = "A clarified startup direction with target user, demand evidence, wedge, and first validation slice."
            discovery_scope = "startup direction discovery clarification."
            discovery_gate_domain = "Startup direction discovery."
            discovery_gate_reason = "Startup direction requires demand, market, wedge, and strategic boundaries before execution."
            discovery_route_reason = "Startup direction requires discovery before CEO can form an executable slice."
            discovery_signal = "startup direction outcome."
            discovery_risk = "startup strategy and demand discovery required."
        elif case["id"] == "goal-okr-discovery-routed":
            discovery_goal = "Clarify a one-year personal growth OKR direction."
            discovery_current = "User has not clarified priorities, constraints, measurable outcomes, or tradeoffs."
            discovery_desired = "A clarified OKR direction with priorities, measurable criteria, and first planning slice."
            discovery_scope = "long-term OKR discovery clarification."
            discovery_gate_domain = "Long-term OKR strategy."
            discovery_gate_reason = "Long-term OKR goals require priority and strategy clarification before execution."
            discovery_route_reason = "Long-term OKR direction requires discovery before CEO can form an executable slice."
            discovery_signal = "long-term OKR outcome."
            discovery_risk = "long-term strategy and priorities required."
        elif case["id"] == "goal-research-direction-routed":
            discovery_goal = "Identify a worthwhile AI Agent research direction for the next three months."
            discovery_current = "User has not chosen research candidates, evaluation criteria, constraints, or evidence standard."
            discovery_desired = "A clarified research direction with candidate criteria, tradeoffs, and first validation slice."
            discovery_scope = "research direction discovery clarification."
            discovery_gate_domain = "Research direction discovery."
            discovery_gate_reason = "Research direction depends on discovery and strategic judgment before execution."
            discovery_route_reason = "Research direction requires discovery before CEO can form an executable slice."
            discovery_signal = "research direction outcome."
            discovery_risk = "research direction and strategic judgment required."
        return f"""## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The generated fixture exercises Discovery clarification routing.
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: decide direction
- Goal Signal: {discovery_signal}
- Task Signal: no concrete execution target, deliverable, or validation.
- Risk / Strategy Signal: {discovery_risk}
- Continue To: Goal Contract

## Goal Mode
- Status: Routed

## Partial Goal Spec
- Goal: {discovery_goal}
- Current State: {discovery_current}
- Desired End State: {discovery_desired}
- In Scope: {discovery_scope}
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
- Domain: {discovery_gate_domain}
- Category: Red
- Decision: Must route to clarification before Task Mode.
- Required Clarification: Discovery.
- Reason: {discovery_gate_reason}

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
- Reason: {discovery_route_reason}

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

    return f"""## Mode Router
- Mode: Goal Mode
- Confidence: High
- Reason: The generated fixture exercises Risk Boundary clarification routing.
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: clarify risk
- Goal Signal: high-risk production outcome.
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


def fixture_output(case: dict[str, Any]) -> str:
    if case.get("expected_mode") == "Goal Mode":
        return goal_mode_fixture_output(case)

    if case["expected_triage"] == "Clarification Path":
        mode_reason = "The generated fixture exercises the existing Task Mode clarification branch."
        mode_intent = "clarify"
        goal_signal = "Vague or risky desired outcome requires clarification before execution."
        task_signal = "Clarification deliverable can be handled by Demand Triage."
        risk_signal = "Material missing information or risk boundary."
        selected = "$office-hours"
        skill_match = "- Strong match: use `$office-hours` for requirements clarification before implementation."
        prompt_objective = "Clarify the request enough for `$ceo` to produce a safe executable prompt."
        requirements = (
            "- Inputs: the user's raw request and any additional context they provide.\n"
            "- In scope: clarify goal, deliverables, in-scope/out-of-scope boundaries, inputs/context, decision boundaries, constraints, acceptance criteria, risks, and open questions.\n"
            "- Out of scope / non-goals: do not implement, deploy, delete data, choose a final route, or fabricate missing authority.\n"
            "- Deliverables: a `## Clarified Spec` handoff for `$ceo`.\n"
            "- Constraints: keep missing material choices explicit and mark unresolved fields as blocking.\n"
            "- Assumptions and boundaries:\n"
            "  - Assumption: material inputs are missing.\n"
            "    Boundary: clarify only and return to `$ceo` before execution.\n"
            "    Risk: direct execution would invent unsafe requirements.\n"
            "    Reversibility: clean.\n"
            "- Failure / escalation conditions: stop if required fields remain unknown and mark them `Unknown and blocking`."
        )
        output_format = "Return `## Clarified Spec` with Goal, Deliverables, In Scope, Out of Scope / Non-goals, Inputs / Context, Decision Boundaries, Constraints, Acceptance Criteria, Risks and Reversibility, Open Questions, CEO Handoff Summary, and readiness for `$ceo`."
    else:
        mode_reason = "The generated fixture exercises a concrete Task Mode execution brief."
        mode_intent = "execute"
        goal_signal = "None beyond the task outcome."
        task_signal = "Concrete target, action, deliverable, and validation are available."
        risk_signal = "No unresolved high-risk boundary in the fixture."
        selected = "$frontend-skill, $playwright"
        skill_match = "- Strong match: use `$frontend-skill` for implementation when available.\n- Supporting match: use `$playwright` for browser validation when available."
        prompt_objective = "Turn the clarified request into a scoped executable implementation brief."
        requirements = (
            "- Inputs: the current workspace, raw request, and existing project structure.\n"
            "- In scope: inspect context, implement the requested scoped change, preserve non-goals, and verify the main workflow.\n"
            "- Out of scope / non-goals: unrelated refactors, deployments, payments, production data changes, and invented requirements.\n"
            "- Deliverables: code or documentation changes plus a verification report with file paths and command evidence.\n"
            "- Constraints: reuse existing patterns and dependencies unless evidence proves otherwise.\n"
            "- Assumptions and boundaries:\n"
            "  - Assumption: the workspace contains the target artifact.\n"
            "    Boundary: inspect before editing and stop if the target is absent.\n"
            "    Risk: editing the wrong file would create unrelated churn.\n"
            "    Reversibility: clean.\n"
            "- Failure / escalation conditions: stop and report blockers if target files, authority, or validation commands are missing."
        )
        output_format = "Return Changed files, Implemented behavior, Verification commands, Evidence, Known gaps, and Follow-up risks."
    return f"""## Mode Router
- Mode: Task Mode
- Confidence: High
- Reason: {mode_reason}
- Evidence: generated fixture sample for {case['id']}.
- Immediate User Intent: {mode_intent}
- Goal Signal: {goal_signal}
- Task Signal: {task_signal}
- Risk / Strategy Signal: {risk_signal}
- Continue To: Demand Triage

## Triage
{case['expected_triage']} - generated fixture sample for {case['id']}.

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
{skill_match}

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
Use the following skill(s) if available: {selected}

## Role
You are an execution-focused agent using the selected skills only where they improve quality.

## Objective
{prompt_objective}

## Requirements
{requirements}

## Context
The CEO inventory evidence and triage decision determine whether to clarify first or execute directly.

## Thinking Process
Follow this visible workflow: inspect the request, confirm triage, preserve scope and non-goals, use selected skills only when justified, verify the required artifact, and report concrete evidence.

## Validation
Run the relevant evaluator or project checks, inspect generated artifacts, verify required fields and command evidence, and report exact pass/fail output. For clarification, check the `## Clarified Spec` fields and return readiness for `$ceo`; for direct work, run available lint, tests, build, or browser checks as applicable.

## Output Format
{output_format}

## Assumptions
- The sample output is generated for evaluator smoke coverage.
  Boundary: use it as sample evidence, not production proof.
  Risk: fixture mode can pass while a real model regresses.
  Reversibility: clean.
"""


def generate_with_command(command: str, case: dict[str, Any]) -> str:
    result = subprocess.run(
        command,
        input=case["raw_request"],
        shell=True,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    parser.add_argument("--timestamp")
    parser.add_argument("--model-command", default=os.environ.get("CEO_LIVE_MODEL_COMMAND", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_cases(Path(args.cases))
    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    generated_dir = GENERATED_ROOT / timestamp
    results_dir = RESULTS_ROOT / timestamp
    generated_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in cases:
        output = fixture_output(case) if args.mode == "fixture" else generate_with_command(args.model_command, case)
        output_path = generated_dir / f"{case['id']}.md"
        output_path.write_text(output, encoding="utf-8")
        result = evaluator.check_contract(output, case["raw_request"])
        result["case_id"] = case["id"]
        result["expected_triage"] = case.get("expected_triage")
        result["expected_mode"] = case.get("expected_mode", "Task Mode")
        result["output_path"] = str(output_path.relative_to(REPO_ROOT))
        rows.append(result)

    results_path = results_dir / "evaluator-results.jsonl"
    results_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    passed = sum(1 for row in rows if row["passed"])
    summary = [
        "# CEO Live-Model Sample Summary",
        "",
        f"- Mode: {args.mode}",
        f"- Cases: {len(rows)}",
        f"- Passed: {passed}",
        f"- Failed: {len(rows) - passed}",
        "",
    ]
    for row in rows:
        summary.append(
            f"- {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} "
            f"mode={row.get('mode_actual')} triage={row.get('triage_actual')} goal={row.get('goal_mode_status')}"
        )
        for failure in row.get("failures", []):
            summary.append(f"  - {failure}")
    summary_path = results_dir / "summary.md"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps({"generated_dir": str(generated_dir), "results_dir": str(results_dir), "passed": passed, "total": len(rows)}, ensure_ascii=False, indent=2))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
