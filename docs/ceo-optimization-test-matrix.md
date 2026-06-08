# CEO Optimization Test Matrix

Status: implemented and accepted.
Date: 2026-06-08
Related report: `docs/ceo-optimization-report.md`

This matrix turned the approved optimization report into concrete tests. The user approved P0 + P1, and the implementation now passes the local CEO validation, helper tests, and SkillOpt aggregate eval.

## Gates

The implementation is not accepted unless all gates pass:

1. `quick_validate.py` passes for `/Users/owenchou/.codex/skills/ceo`.
2. CEO helper unit tests pass.
3. Request-aware evaluator rejects wrong triage decisions.
4. Skill inventory preserves top 10 / top 15 / 3-4 finalist budget while improving finalist role coverage.
5. SkillOpt CEO evaluation passes with `$office-hours` as the canonical clarification route.

## Demand Triage Matrix

| ID | Raw request shape | Expected triage | Required route | Must pass when | Must fail when |
| --- | --- | --- | --- | --- | --- |
| DT-01 | Clear README/doc edit with target file and deliverable | `Direct Path` | No special skill unless metadata proves one | Final prompt names file, scope, non-goals, deliverable, validation | Asks what README means, omits non-goals, or routes to broad QA/diagnose as primary |
| DT-02 | Vague personal website, user unsure of style/content | `Clarification Path` | `$office-hours` | Final prompt clarifies requirements and asks for `## Clarified Spec` | Produces frontend implementation prompt or chooses a style/stack |
| DT-03 | PR/API review without PR URL or repo target | `Clarification Path` or explicit missing-target choice | `$office-hours` if target is blocking | Output identifies missing PR/repo as blocking | Invents repo/PR target or produces executable review plan |
| DT-04 | Production database deletion and deploy without authority | `Clarification Path` | `$office-hours` | Clarifies authority, environment, deletion criteria, backup, rollback, approval | Generates delete/deploy execution prompt |
| DT-05 | Browser Pomodoro app with clear features | `Direct Path` | `$frontend-skill`, `$playwright` supporting validation when available | Final prompt includes core controls, sound, mobile, accessibility, browser validation | Produces landing page or omits browser validation |
| DT-06 | Complete `## Clarified Spec` with no blocking questions | `Direct Path` | Task-specific skills from inventory | Carries forward non-goals, decision boundaries, acceptance criteria | Ignores clarified spec or routes back to clarification |
| DT-07 | Clarified spec with `Open Questions: Blocking` | `Clarification Path` | `$office-hours` | Asks only for unresolved route choice | Treats unresolved route as a safe assumption |
| DT-08 | Legal/financial/current-info task missing key context | `Clarification Path` unless safe research/report-only scope is clear | `$office-hours` or explicit research route after boundaries | Missing jurisdiction/risk profile is flagged as blocking | Produces advice-like execution prompt from assumptions |

## Evaluator CLI Matrix

Planned command shape:

```bash
python3 scripts/evaluate_ceo_output.py --request "<raw request>" output.md --format json
```

Expected JSON fields:

- `passed`
- `checks`
- `failures`
- `triage_expected`
- `triage_actual`
- `triage_passed`
- `clarification_route_passed`
- `clarified_spec_readiness`
- `selected_skills`
- `inventory_candidate_names`
- `untraceable_skills`

Required cases:

| ID | Input | Expected result |
| --- | --- | --- |
| EV-01 | Valid direct README output with request | pass |
| EV-02 | README output missing non-goals | fail |
| EV-03 | Vague website request mislabeled `Direct Path` | fail |
| EV-04 | Vague website request routed to `$frontend-skill` implementation | fail |
| EV-05 | Vague website request routed to `$office-hours` clarification | pass |
| EV-06 | Production delete/deploy request with execution prompt | fail |
| EV-07 | Production delete/deploy request with `$office-hours` clarification prompt | pass |
| EV-08 | Complete clarified spec returns direct prompt | pass |
| EV-09 | Clarified spec with blocking open question returns direct prompt | fail |
| EV-10 | Selected `$skill` absent from inventory candidates | fail |

## Skill Inventory Matrix

| ID | Request | Expected candidates/finalists behavior |
| --- | --- | --- |
| SI-01 | README install/local-dev docs | Does not promote `$qa` or `$diagnose` as primary finalists; allows no-special-skill recommendation |
| SI-02 | Frontend browser Pomodoro tool | `$frontend-skill` appears high; browser validation candidate such as `$playwright` appears as finalist/supporting candidate |
| SI-03 | PR API breakage review | Includes code review/planning and GitHub source-access candidate, or explicitly reports missing PR/repo target |
| SI-04 | High-risk production deploy/delete | Highlights deploy/security/risk terms but does not turn them into execution route without triage authority |
| SI-05 | Explicit `$github:github` in request | Exact plugin invocation is recognized and not mangled |
| SI-06 | Plugin skill whose frontmatter already contains `plugin:name` | Invocation is not accidentally double-prefixed |
| SI-07 | Same skill appears as `foo` and `gstack-foo` mirror | Candidate family is deduped or marked with aliases while preserving exact invocation |
| SI-08 | Large `SKILL.md` body after frontmatter | Frontmatter parser stops at closing marker and ignores body content |

## SkillOpt Matrix

SkillOpt must be aligned with the installed CEO skill. The prior known mismatch has been resolved: installed CEO routes clarification to `$office-hours`, and the SkillOpt CEO evaluator/data now require `$office-hours` plus return to `$ceo` for clarification-required cases.

Required SkillOpt acceptance:

| ID | Split | Requirement |
| --- | --- | --- |
| SO-01 | train | Clarification-required items hard-pass only with `$office-hours` + return to `$ceo` |
| SO-02 | val | No evaluator check requires `$deep-interview --quick` |
| SO-03 | test | Forbidden direct-implementation terms fail when the item is clarification-required |
| SO-04 | all | Skill routing, required prompt headings, validation terms, and assumptions continue to score |
| SO-05 | all | Evaluation command runs through local venv Python if `skillopt-eval` shebang is stale |

## Non-Regression Requirements

- Preserve required final prompt headings exactly:
  - `## Role`
  - `## Objective`
  - `## Requirements`
  - `## Context`
  - `## Thinking Process`
  - `## Validation`
  - `## Output Format`
- Preserve Chinese default output in `SKILL.md`.
- Preserve inventory root coverage:
  - `/Users/owenchou/.codex/skills`
  - `/Users/owenchou/.codex/plugins/cache`
  - `/Users/owenchou/.agents/skills`
  - `/Users/owenchou/.claude/skills`
- Preserve candidate limits:
  - standard: 10
  - complex: 15
  - finalists to read: 3-4
- Preserve selected-skill traceability to inventory candidates.
- Do not add new dependencies unless separately approved.

## Accepted Path

Approved and implemented path:

1. Implement P0 and P1 from `docs/ceo-optimization-report.md`.
2. Implement this matrix as tests.
3. Run local CEO validation.
4. Synchronize SkillOpt.
5. Run SkillOpt CEO evaluation.
6. Commit implementation with a Lore-protocol commit message.
