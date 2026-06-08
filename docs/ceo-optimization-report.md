# CEO Skill Optimization Report

Status: pending user review before implementation.
Date: 2026-06-08
Scope: demand triage and skill retrieval/routing.

## Executive Summary

The current CEO skill is directionally strong: it converts rough user requests into executable agent specifications, requires a `Direct Path` vs `Clarification Path` decision, runs local skill inventory before selecting skills, and validates the output structure with helper scripts.

The main gap is enforcement. The skill instructions describe the intended behavior, but the evaluator cannot yet prove whether the demand-triage decision is correct because it does not inspect the original request. Skill retrieval also works, but the top 3-4 finalists are currently selected by raw score only, which can crowd out important role coverage on complex tasks.

Recommended plan: implement P0 changes first, then P1 refinements. Do not modify behavior until this report is reviewed and accepted by the user.

## Current Baseline

- Repository: `/Users/owenchou/.codex/skills/ceo`
- Baseline commit: `be79379 Capture CEO skill baseline`
- Current validation:
  - `python3 /Users/owenchou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/owenchou/.codex/skills/ceo` passes.
  - `python3 -m unittest discover -s /Users/owenchou/.codex/skills/ceo/scripts -p 'test_*.py'` passes 17 tests.

## Current Strengths

1. The `SKILL.md` contract positions CEO as an executable-spec generator, not a prompt-polishing helper.
2. `Demand Triage` already separates `Direct Path` from `Clarification Path`.
3. `Clarification Path` currently routes to `$office-hours`, matching the latest user decision to replace the previous clarification skill.
4. Direct-path assumptions must become boundaries with risk and reversibility.
5. `skill_inventory.py` scans all configured roots and produces traceable `invocation_name` values.
6. `evaluate_ceo_output.py` enforces required sections, final prompt headings, semantic completeness, validation specificity, and selected-skill traceability.

## Key Findings

### 1. Demand Triage Is Specified But Not Enforced

`evaluate_ceo_output.py` checks that a `Triage` section exists, but it does not accept or analyze the raw user request. Therefore it cannot know whether `Direct Path` or `Clarification Path` is correct.

Observed risk: a vague or high-risk request can be mislabeled as `Direct Path`; if the output still includes all required sections, inventory evidence, and validation phrasing, the evaluator can pass it.

### 2. SkillOpt Is Out Of Sync With The Latest Clarification Route

The active CEO skill uses `$office-hours` for clarification. The local SkillOpt CEO evaluator still contains legacy checks for `$deep-interview --quick`.

This must be synchronized before final acceptance, because the user's acceptance gate requires SkillOpt testing to pass.

### 3. Fixtures Are Behavioral Documentation, Not A Full Executable Suite

`references/test-fixtures.md` defines six important scenarios:

- clear direct path
- vague clarification
- multiple skill conflict
- high-risk irreversible work
- frontend/browser app
- clarified spec return flow

The current test suite covers helper behaviors but does not yet convert each fixture into positive and negative executable tests.

### 4. Finalist Selection Needs Role Coverage

`skill_inventory.py` currently shows top 10 candidates by default, top 15 for complex tasks, and limits full `SKILL.md` reads to 3-4 finalists. This matches the requested candidate budget.

The issue is that finalists are selected by raw score only. On complex tasks, similar high-scoring skills can occupy all finalist slots, leaving out a source-access, validation, risk-control, or planning skill that the downstream prompt needs.

### 5. Skill Inventory Reads More Than The Contract Implies

The skill contract says inventory reads only frontmatter metadata. The parser currently reads full `SKILL.md` files before extracting frontmatter. Current scale is still acceptable, but this is unnecessary I/O and should be corrected.

## External Patterns To Borrow

These projects are useful design references because they solve similar routing and delegation problems:

- OpenAI Agents SDK handoffs: make handoff targets, descriptions, and input handling explicit and auditable.
- AutoGen SelectorGroupChat: select the next agent from a constrained candidate set rather than relying on freeform recall.
- LangGraph / DeepAgents skills: represent sub-capabilities as discrete skills and route by task shape.
- Semantic Kernel function choice behavior: use structured tool/function metadata to constrain model choice.

Applied to CEO, the pattern is:

1. Determine whether the user request is executable.
2. If not executable, route to a structured clarification handoff.
3. If executable, generate a broad but bounded candidate set.
4. Select finalists by role coverage, not raw score alone.
5. Require selected skills to be traceable to inventory evidence.
6. Validate the route against the original request and expected risk level.

## Proposed Changes

## P0 - Required Before Implementation Acceptance

### P0.1 Add Request-Aware Triage Evaluation

Update `scripts/evaluate_ceo_output.py`:

- Add `--request`.
- Report `triage_expected`, `triage_actual`, and `triage_passed`.
- Add deterministic heuristics for:
  - vague intent
  - missing goal/deliverable/scope/success criteria
  - material route choice
  - high-risk or irreversible work
  - missing authority/environment/rollback/approval
  - missing single critical input, such as PR URL, repository, jurisdiction, or risk profile
- Hard-fail when clarification-required requests are labeled as direct execution prompts.

Acceptance examples:

- Vague personal website request must require `Clarification Path`.
- Production database deletion/deploy request must require `Clarification Path`.
- Clear README update request must allow `Direct Path`.
- Complete `Clarified Spec` with no blocking questions must allow `Direct Path`.

### P0.2 Synchronize SkillOpt With `$office-hours`

Update `/Users/owenchou/SkillOpt` CEO evaluator/data as needed:

- Replace legacy `$deep-interview --quick` hard gate with `$office-hours`.
- Preserve the requirement to hand off back to `$ceo`.
- Preserve forbidden direct-implementation checks for clarification-required items.
- Keep SkillOpt split aliases and local Python environment behavior in mind.

Acceptance:

- SkillOpt CEO eval passes after implementation.
- Clarification cases require `$office-hours` plus return-to-`$ceo`.

### P0.3 Convert Fixtures Into Executable Positive/Negative Tests

Update `scripts/test_ceo_scripts.py`:

- Add positive and negative samples for all six fixtures.
- Negative cases must fail for the right reason, not only because of missing formatting.
- Include CLI tests for `evaluate_ceo_output.py --request ... --format json`.

Acceptance:

- Fixture 2 direct frontend build prompt fails.
- Fixture 4 destructive execution prompt fails.
- Fixture 6 incomplete clarified spec stays in clarification.
- Existing 17 tests continue to pass.

### P0.4 Improve Finalist Selection Without Increasing Candidate Budget

Update `scripts/skill_inventory.py`:

- Preserve default top 10 candidate recall.
- Preserve complex top 15 candidate recall.
- Preserve final 3-4 full-read limit.
- Change finalist selection from raw top-N to coverage-aware selection.

Suggested finalist roles:

- primary executor
- source/access skill
- validation/evidence skill
- risk/planning/clarification skill

Acceptance:

- PR review conflict includes a GitHub source/access candidate or explicitly reports missing PR/repo input.
- Frontend/browser app keeps `$frontend-skill` and browser validation available.
- README/repo-doc tasks do not promote QA/diagnose as primary implementation routes.

## P1 - Recommended Quality Improvements

### P1.1 Single Critical Gap Rule

Clarification should trigger when one critical missing input prevents safe execution, even if only one field is missing.

Examples:

- PR review missing PR/repo target.
- Production operation missing approval, environment, or rollback.
- Legal task missing jurisdiction.
- Financial task missing risk profile or investment boundary.

### P1.2 Clarified Spec Readiness Checker

Add readiness checks for `## Clarified Spec`:

- required fields are present
- no required field is empty, `TBD`, or blocking-unknown
- `Open Questions` is `None blocking` or equivalent
- `Decision Boundaries` do not contain unresolved core route choices
- acceptance criteria are concrete

### P1.3 Alias / Canonical Family Layer

Keep exact `invocation_name` for final calls, but add a `canonical_family` or similar grouping for sorting and deduplication.

Initial safe grouping:

- `gstack-*` mirror aliases
- same basename plus same description hash
- same plugin skill across multiple cached versions

Avoid merging legitimately different skills such as `review` and `code-review` unless evidence proves they are aliases.

### P1.4 Stream Frontmatter Parsing

Make `parse_frontmatter()` stop reading at the closing frontmatter marker.

Acceptance:

- No body content is needed for inventory.
- Current inventory speed remains the same or improves.

## Files Expected To Change After Approval

CEO skill repository:

- `/Users/owenchou/.codex/skills/ceo/SKILL.md`
- `/Users/owenchou/.codex/skills/ceo/scripts/evaluate_ceo_output.py`
- `/Users/owenchou/.codex/skills/ceo/scripts/skill_inventory.py`
- `/Users/owenchou/.codex/skills/ceo/scripts/test_ceo_scripts.py`
- `/Users/owenchou/.codex/skills/ceo/references/test-fixtures.md`

SkillOpt repository:

- `/Users/owenchou/SkillOpt/skillopt/envs/ceo/evaluator.py`
- `/Users/owenchou/SkillOpt/data/ceo_prompt_builder/train/items.json`
- `/Users/owenchou/SkillOpt/data/ceo_prompt_builder/val/items.json`
- `/Users/owenchou/SkillOpt/data/ceo_prompt_builder/test/items.json`
- Additional SkillOpt config or fixture files only if required by the local evaluator.

## Verification Plan

Run after implementation:

```bash
python3 /Users/owenchou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/owenchou/.codex/skills/ceo
python3 -m unittest discover -s /Users/owenchou/.codex/skills/ceo/scripts -p 'test_*.py'
python3 /Users/owenchou/.codex/skills/ceo/scripts/skill_inventory.py --request "做一个浏览器里的番茄钟工具，要有开始暂停、重置、长短休息切换、声音提示和移动端可用。" --format markdown
python3 /Users/owenchou/.codex/skills/ceo/scripts/evaluate_ceo_output.py --request "我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。" path/to/generated-output.md --format json
```

SkillOpt verification must be run from `/Users/owenchou/SkillOpt` using the local venv Python because the `skillopt-eval` shebang may point at an old path:

```bash
/Users/owenchou/SkillOpt/.venv/bin/python --version
```

Then run the local SkillOpt CEO eval command appropriate to the current repository state. If the `skillopt-eval` entrypoint remains broken, use the venv Python module/script path rather than the stale shebang wrapper.

## Decision Required

Approve one of these paths:

1. Implement P0 only, then run local tests and SkillOpt.
2. Implement P0 + P1, then run local tests and SkillOpt.
3. Revise this report before implementation.

Recommended: option 2. It addresses both core goals: better demand judgment and better skill retrieval, while keeping candidate/read limits under control.
