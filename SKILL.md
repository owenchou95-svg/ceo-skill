---
name: ceo
description: "将粗略想法、目标或任务说明转成高质量可执行提示，并选择合适技能。"
---

# CEO Prompt Builder

## Purpose

Transform the user's rough input into a stronger prompt that another AI agent can execute as a lightweight specification, not as polished wording alone. The prompt must include:

1. Requirements: what the user wants, constraints, scope, deliverables, and success criteria.
2. Thinking process: the reasoning workflow the agent should follow, without exposing hidden chain-of-thought.
3. Validation method: how the agent should prove the result is correct or useful.
4. Skill/plugin routing: which locally installed skills or plugin skills should be used, and why.

## Executable Spec Contract

A `Final Prompt` is executable only when it gives the downstream agent enough information to act without guessing the core route. It must include:

- Objective: the desired outcome in one concrete sentence.
- Inputs and context: files, URLs, artifacts, constraints, audience, environment, or source material the agent should use.
- Scope boundaries: what is in scope, what is out of scope, and any non-goals that prevent overreach.
- Deliverables: the exact artifact, code change, report, design, command output, or decision the user expects.
- Skill inventory evidence: a `Skill Inventory Report` produced by `scripts/skill_inventory.py` before selecting skills.
- Skill/tool routing: selected skills/plugins from the inventory candidates, or an explicit statement that no special skill is needed after inventory evidence.
- Assumptions as boundaries: each material assumption must become an execution boundary, with risk and reversibility noted.
- Validation evidence: concrete checks that prove completion for the deliverable and task type.
- Failure or escalation conditions: when the downstream agent should stop, ask, avoid destructive action, or report a blocker.
- Output format: the exact structure expected in the final answer or artifact.

Treat a prompt as not executable when any of these are true:

- The deliverable or output format is undefined.
- The task route depends on an unresolved material choice.
- The prompt asks for irreversible, destructive, legal, financial, security, deployment, or external side-effect work without authority or boundaries.
- Validation is generic, subjective, or unrelated to the deliverable.
- Selected skills/plugins are guessed instead of found in available metadata or on disk.
- No `Skill Inventory Report` was produced before selecting skills.
- The agent would need to invent missing inputs, acceptance criteria, or non-goals to proceed.

## Mode Router

Before `Demand Triage`, classify the user's input as `Task Mode` or `Goal Mode`.

Use `Task Mode` when the user already knows what they want done. A Task Mode input has an identifiable target/object, action, deliverable, and validation method that can be stated directly or safely inferred. Task Mode continues through the existing CEO path: `Demand Triage`, skill inventory, skill matching, contract check, and `Final Prompt`.

Use `Goal Mode` when the user describes a desired future state, capability, quality bar, or outcome that still needs boundary framing before execution. Goal Mode applies when the first executable task is not yet clear, or when the goal needs current state, desired end state, scope, non-goals, success criteria, and a first executable slice before Task Mode can safely continue.

For mixed inputs, classify by immediate user intent:

```text
execute now -> Task Mode
define, refine, discuss, decompose, or decide path -> Goal Mode
```

When uncertain, prefer `Goal Mode` with `Status: Incomplete` over premature Task Mode. Do not force vague goals into executable prompts.

Every CEO output must start with:

```md
## Mode Router
- Mode: Task Mode / Goal Mode
- Confidence: High / Medium / Low
- Reason:
- Evidence:
- Immediate User Intent:
- Goal Signal:
- Task Signal:
- Risk / Strategy Signal:
- Continue To:
```

For `Task Mode`, `Continue To` must be `Demand Triage`.

## Inventory Decision

Every CEO output must include `Inventory Decision`, even when skill inventory is intentionally skipped.

Use this shape:

```md
## Inventory Decision
- Inventory Run: Yes / No
- Reason:
- Inventory Input:
```

Mode Router always runs before inventory. `Inventory Decision` always appears before `Skill Inventory Report`. `Skill Inventory Report` appears only when `Inventory Run: Yes`.

Use these timing rules:

- Task Mode: `Inventory Run: Yes`; use `Inventory Input: Raw user request.`
- Goal Mode Incomplete / Local Goal: `Inventory Run: No`; use `Inventory Input: Not applicable.`
- Goal Mode Complete -> Task Mode: `Inventory Run: Yes`; use `Inventory Input: First Executable Slice plus compact Goal Spec context.`
- Goal Mode -> Discovery Clarification: `Inventory Run: Yes` when recommending `$office-hours` or another discovery skill; use the raw goal with clarification intent.
- Goal Mode -> Risk Boundary Clarification: use `Inventory Run: Yes` only when recommending a specific safety, security, deployment, or review skill; otherwise use `Inventory Run: No`.

Do not run inventory on an incomplete goal just to appear complete. If the Goal Contract is incomplete and CEO is asking one local blocking question without selecting a skill, skip inventory and say so in `Inventory Decision`.

## Goal Mode

Goal Mode is a goal-refinement layer. It is not implementation, long-term goal management, or a replacement for `$office-hours`.

Goal Mode has exactly three status families:

- `Incomplete`: the goal contract is not complete enough to form a first executable slice.
- `Complete -> Task Mode`: the goal contract is complete and the first executable slice is task-ready.
- `Routed -> Clarification`: discovery, strategy, risk, authority, reversibility, or safety boundaries must be clarified before Task Mode can continue.

Goal Mode must not produce an execution `Final Prompt`. If the goal is incomplete, output a gap report and exactly one blocking question. If the goal routes to clarification, output a clarification prompt only, not an implementation prompt. If the goal is complete, produce a `Goal Spec` and hand off the first executable slice to Task Mode before any execution prompt is produced.

A clear goal must satisfy these required fields:

```md
- Goal:
- Current State:
- Desired End State:
- In Scope:
- Out of Scope / Non-goals:
- Acceptance Criteria:
- Validation Method:
- First Executable Slice:
- Stop / Ask / Escalate Conditions:
```

Also require these fields when they would change route, ownership, risk, scope, validation, deliverable, or the first executable slice:

```md
- Motivation / Why:
- Inputs / Context:
- Constraints:
- Decision Boundaries:
- Assumptions:
- Risks and Reversibility:
```

Classify goal fields as `PASS`, `MISSING`, `VAGUE`, `UNVERIFIABLE`, `ROUTE-CHANGING`, or `HIGH-RISK`. Goal Mode can route to Task Mode only when all required fields are `PASS`, the domain is allowed or safely bounded, and the first executable slice is task-ready.

After the clarity check, run `Domain Gate` before `Route Decision` for every `Goal Mode` output that is `Complete` or `Routed`. Use this shape:

```md
## Domain Gate
- Domain:
- Category: Green / Yellow / Red
- Decision:
- Required Clarification:
- Reason:
```

Domain Gate categories:

- `Green`: low-risk artifact, design, report, prompt, doc, test, evaluator, workflow, or local reversible skill/workflow goals. May route to Task Mode when the first executable slice is task-ready.
- `Yellow`: architecture, product feature scope, performance strategy, cross-module refactor, or research goals. May route to Task Mode only when the first slice is bounded, reversible, and limited to analysis, design, documentation, tests, reports, specs, or otherwise low-risk implementation. Do not route Yellow directly to broad implementation, migration, or cross-module rewrite unless ownership, migration plan, tests, rollback, and acceptance criteria are explicit.
- `Red`: startup, business, career, long-term strategy, OKR, product discovery, user needs, market positioning, security, privacy, auth, compliance, legal, financial, medical, production, deployment, deletion, migration, rollback, monitoring, external side effects, or irreversible goals without authority. Red may include a `Goal Spec`, but must route to `Clarification` before Task Mode.

For Red domains, choose clarification by risk priority: `Risk Boundary` for production, deletion, deployment, security, privacy, auth, compliance, legal, financial, medical, irreversible, or externally side-effectful work; otherwise `Discovery` for product, startup, career, OKR, long-term strategy, market, demand, user, or research-direction discovery. Red domains must not produce an execution `Final Prompt`.

For Yellow domains, include the domain gate explicitly and keep the first executable slice assessment-first when the user has not yet committed to a bounded implementation target. If the slice is broad implementation, migration, or cross-module rewrite, keep Goal Mode routed or incomplete until the boundary is narrowed.

For `Goal Mode` with `Status: Incomplete`, return:

```md
## Mode Router
...

## Goal Mode
- Status: Incomplete

## Goal Contract Check
- Ready Fields:
- Missing Fields:
- Vague Fields:
- Unverifiable Fields:
- Route-Changing Ambiguities:
- High-Risk Boundaries:

## Clarification Type
- Type: Local Goal

## Inventory Decision
- Inventory Run: No
- Reason: Goal Contract is incomplete and CEO is asking one local blocking question without selecting a skill.
- Inventory Input: Not applicable.

## Route Decision
- Next Route: Stay in Goal Mode

## Blocking Question
[one question only]

## Why This Question Comes First
[short explanation]
```

Do not include `Skill Inventory Report`, `Skill Match`, `Contract Check`, or `Final Prompt` for `Goal Mode` with `Status: Incomplete`.

The blocking question must target the first missing or vague field that prevents safe decomposition into a first executable slice. Priority:

1. High-risk authority or route-changing ambiguity.
2. Desired End State.
3. Current State.
4. Acceptance Criteria.
5. First Executable Slice.
6. Scope / Non-goals.
7. Decision Boundaries.
8. Validation Method.

The blocking question must target a gap reported in `Goal Contract Check`. Do not ask about unrelated preferences, implementation details, files, tools, or style choices unless that item is explicitly listed as the blocking gap.

`First Executable Slice` is the exit gate from Goal Mode to Task Mode. It must include a concrete target/object, action, deliverable, scope boundary, non-goals, required context, validation method, risk/reversibility assessment, no unresolved strategic choice, and no missing authority or context.

For `Goal Mode` with `Status: Complete`, produce a `Goal Spec`, then route the first executable slice to Task Mode. Inventory must run on the first executable slice plus compact Goal Spec context, not on the raw goal alone. If the first slice is route-sensitive or high-risk, do not produce an execution `Final Prompt`; route to clarification instead.

For `Goal Mode` with `Status: Routed`, produce a clarification prompt only. Use `Discovery` when product, strategy, demand, market, user, career, OKR, or research direction discovery is needed. Use `Risk Boundary` when authority, reversibility, safety, production, security, privacy, compliance, deployment, or destructive-action boundaries are unresolved. Routed Goal Mode must not produce an execution prompt.

## Demand Triage

In `Task Mode`, before writing the executable prompt, classify the user's request as either `Direct Path` or `Clarification Path`.

Do not run `Demand Triage` before `Mode Router`. Do not use `Demand Triage` to bypass Goal Mode when the user's immediate intent is to define, refine, discuss, decompose, or decide a goal.

Use `Direct Path` only when the request is clear enough to produce an executable prompt without inventing the core route. All of these must be true:

- Target/object is identifiable: the agent can name the file, artifact, repo area, prompt, document, report, workflow, or concrete thing being handled.
- Action type is identifiable: the agent can name the requested operation, such as evaluate, summarize, edit docs, compare, generate a report, refine a prompt, or produce a checklist.
- Deliverable is identifiable: the agent can name the expected artifact, answer shape, code/report/document change, decision, or command output.
- Validation can be stated concretely from the request or safely inferred from the task type.
- Missing details, if any, can be converted into reversible assumptions with explicit boundaries, risks, and reversibility.
- No high-risk gate is triggered.
- No unresolved route choice would materially change ownership, workflow, risk, or final deliverable.

Prefer `Direct Path` for low-risk, reversible documentation, report, summary, checklist, comparison, prompt-review, README/docs edit, or non-binding recommendation tasks when the required clarity conditions above are met.

Do not use `Direct Path` for product direction, architecture, security, deployment, production operations, long-term goals, business/career strategy, startup direction, or broad "make it better" requests unless the user has already supplied a complete clarified spec with concrete boundaries and acceptance criteria.

Use this 0-8 clarity score when the request is partly clear but the route could drift:

- Target/object clarity: 0-2 points.
- Action clarity: 0-2 points.
- Deliverable clarity: 0-2 points.
- Validation clarity: 0-2 points.

Score interpretation:

- 7-8 points: use `Direct Path` when no high-risk gate is triggered.
- 5-6 points: use the mid-clarity tie-breaker below.
- 0-4 points: use `Clarification Path`.

For 5-6 point requests, use `Conditional Direct` only when all of these are true:

- The task is low-risk and reversible.
- The expected deliverable is a document, report, prompt evaluation, README/docs edit, summary, checklist, comparison, or non-binding recommendation.
- Missing details can be safely converted into explicit assumptions and boundaries.
- The work does not require external authority, production access, user data, legal/financial/medical judgment, security approval, deployment approval, or architecture ownership.

Use `Clarification Path` for 5-6 point requests when the task involves any of these categories:

- Product direction, positioning, feature scope, roadmap, or user needs.
- Architecture, system design, data model, migrations, performance strategy, or cross-module ownership.
- Security, privacy, auth, permissions, secrets, compliance, or threat modeling.
- Deployment, release, production operations, deletion, rollback, monitoring, or external side effects.
- Long-term goals, OKRs, business strategy, career strategy, startup direction, research direction, or broad "make it better" goals.

Uncertainty rule: when uncertain, do not ask whether a reasonable assumption can be invented. Ask whether the assumption would change ownership, route, risk, or final deliverable. If yes, use `Clarification Path`.

For `Direct Path`, do not leave assumptions as passive notes. Convert each material assumption into a boundary the downstream agent must respect:

```md
- Assumption: [what is being assumed]
  Boundary: [what the agent may and may not do because of this assumption]
  Risk: [what could go wrong if the assumption is false]
  Reversibility: [clean, messy, or irreversible]
```

Use `Clarification Path` when any of these are true:

- The request is missing two or more of: goal, deliverable, success criteria, scope boundary.
- The request is missing one critical execution input whose absence would force the agent to invent the target, authority, or safe boundary, such as a PR/repo target, production approval/environment/rollback, legal jurisdiction, or financial risk profile.
- The user says they are unsure, asks to figure something out, says not to assume, or signals that the requirements are still vague.
- Multiple materially different routes are plausible and choosing one would shape the final prompt.
- The task involves high-risk or irreversible work and the user has not supplied the boundary or authority needed to proceed.

For `Clarification Path`, route strongly to `$office-hours`. Do not invent a complete execution prompt for the underlying task. Instead, produce a directly executable clarification prompt that asks `$office-hours` to run the appropriate office-hours mode for the user's situation, return this CEO handoff artifact, and explicitly pass the finished `## Clarified Spec` back to `$ceo` for the final execution prompt:

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
- CEO Handoff Summary: include the exact next step `Return this Clarified Spec to $ceo for the final execution prompt` when no blocking questions remain.
```

When a clarified spec is later supplied, treat it as primary context, rerun `Demand Triage`, and only produce the final execution prompt if all material gaps are resolved. A clarified spec is ready only when the required fields are present, no material field is empty or `TBD`, `Open Questions` says `None blocking` or equivalent, `Decision Boundaries` do not contain unresolved route choices, and acceptance criteria are concrete. If the clarified spec still leaves a material route choice open, stay in `Clarification Path` and ask only for that choice.

When a Goal Mode clarification return is supplied, rerun `Mode Router`, `Goal Contract Check`, `Clarification Type`, and `Inventory Decision`; do not skip directly to plain Task Mode.

For a Discovery `Clarified Spec` return:

- Route to `Goal Mode Complete -> Task Mode` only when target user/audience, problem/need, current status quo, desired end state, scope/non-goals, decision boundaries, measurable acceptance criteria, validation method, first executable slice, and `Open Questions: None blocking` are all specific.
- For product or startup direction returns, also require demand evidence, status quo workaround, narrowest wedge, and why-now/future-fit.
- If ready, run inventory on `First Executable Slice plus Discovery Context from Clarified Spec`.
- If still vague, stay in Goal Mode or route to Discovery clarification instead of producing a final execution prompt.

For a `Risk-Bounded Clarified Spec` return:

- Route to `Goal Mode Complete -> Task Mode` only when authority/approval, target environment, affected systems/data, backup/recovery, rollback plan, dry-run/simulation, verification method, audit trail, stop conditions, forbidden actions, and readiness are explicit.
- Readiness must be `Ready for CEO Re-evaluation`, not `Ready for Execution`.
- If ready, run inventory on `First Executable Slice plus Risk-Bounded Clarified Spec`.
- If not ready, stay in Goal Mode or route to Risk Boundary clarification; do not produce execution commands or a final execution prompt.

## Workflow

1. Capture the user's raw request.
   - Preserve the user's intent and wording when it contains useful nuance.
   - Apply `Mode Router` before `Demand Triage`, skill inventory, or writing the final prompt.
   - If `Mode Router` selects `Goal Mode`, run `Goal Mode` first. If `Goal Mode` is incomplete, return the Goal Mode incomplete output and do not produce `Final Prompt`. If `Goal Mode` is complete and the first executable slice is task-ready, continue into Task Mode using the first executable slice plus compact Goal Spec context.
   - For `Goal Mode` `Complete` or `Routed` outputs, run `Domain Gate` after `Goal Contract Check` and before `Route Decision`; do not route Red domains to Task Mode.
   - If `Mode Router` selects `Task Mode`, continue to `Demand Triage`.
   - Apply `Demand Triage` before selecting skills or writing the final prompt only inside Task Mode.
   - Identify missing scope, irreversible decisions, external dependencies, and acceptance criteria.
   - If the request qualifies for `Clarification Path`, route to `$office-hours` instead of asking ad hoc clarification questions or making broad assumptions.
   - For `Direct Path`, ask at most 3 clarifying questions only when the missing information materially changes the prompt. Otherwise make explicit assumptions and convert them into boundaries, risks, and reversibility notes.
   - If the user supplied a `Clarified Spec`, consume it before adding new assumptions.

2. Decide whether to run full skill inventory before selecting skills. This is a hard gate when CEO is about to select a skill, prove a route, or generate a Task Mode executable specification.
   - Always emit `Inventory Decision`.
   - For Task Mode, run inventory on the raw user request.
   - For Goal Mode Incomplete / Local Goal, do not run inventory and do not include `Skill Inventory Report`.
   - For Goal Mode Complete -> Task Mode, run inventory on the first executable slice plus compact Goal Spec context, not on the raw goal alone.
   - For Discovery clarified-spec returns that are ready for Task Mode, run inventory on the first executable slice plus Discovery context.
   - For Risk-Bounded clarified-spec returns that are ready for Task Mode, run inventory on the first executable slice plus the Risk-Bounded Clarified Spec.
   - For Discovery Clarification, run inventory before recommending `$office-hours` or another clarification skill.
   - For Risk Boundary Clarification, run inventory only when recommending a specific safety, security, deployment, or review skill.
   - When inventory runs, run `scripts/skill_inventory.py` from this skill directory, meaning the directory that contains this `SKILL.md`, with the selected inventory input:
     ```bash
     cd "${CEO_SKILL_HOME:-${CODEX_HOME:-$HOME/.codex}/skills/ceo}"
     python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
     ```
     If `Demand Triage` already determined `Clarification Path`, pass that decision through so `$office-hours` / `gstack-office-hours` can become finalist rank 1:
     ```bash
     python3 scripts/skill_inventory.py --request "<raw user request>" --triage clarification --format markdown
     ```
   - If `CEO_SKILL_HOME` is not set and this skill is installed outside Codex, resolve the equivalent install root first, such as `${CLAUDE_HOME:-$HOME/.claude}/skills/ceo`, `${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo`, or `${HERMES_HOME:-$HOME/.hermes}/skills/ceo`.
   - The script must scan all configured roots:
     - `${CODEX_HOME:-$HOME/.codex}/skills`
     - `${CODEX_HOME:-$HOME/.codex}/plugins/cache`
     - `${AGENTS_HOME:-$HOME/.agents}/skills`
     - `${CLAUDE_HOME:-$HOME/.claude}/skills`
     - `${OPENCLAW_HOME:-$HOME/.openclaw}/skills`
     - `${HERMES_HOME:-$HOME/.hermes}/skills`
   - It reads only frontmatter `name`, `description`, and path for all `SKILL.md` files; the parser stops at the closing frontmatter marker and does not read full skill bodies during inventory.
   - It uses deterministic weighted lexical recall, not model intuition or embedding search. A frontmatter-only index/cache may be used to avoid reparsing unchanged `SKILL.md` files, but routing must remain deterministic and cache entries must invalidate on path, mtime, or size changes.
   - Default candidate recall is top 10. Complex tasks use top 15. Full `SKILL.md` reads are limited to the top 3-4 finalists.
   - Finalists are selected with coverage-aware role diversity, not raw score alone. Prefer a compact set that covers primary execution, source/access, validation/evidence, and risk/planning/clarification when those roles are present.
   - For `Clarification Path`, the `$office-hours` / `gstack-office-hours` canonical family must be finalist rank 1 when present. Implementation-focused skills may appear only as future-after-clarification context and must not displace the clarification route.
   - Alias families may be collapsed for ranking so mirrored skills or cached plugin versions do not crowd out other roles. Final prompts must still use the exact inventory-provided `invocation_name`.
   - For clear, low-risk repository Markdown/README edits where inventory finds only broad QA/diagnosis/CI-adjacent skills, the report may state `No special skill recommended` and skip full skill reads. This is preferable to forcing weak matches into the final prompt.
   - Include the resulting `Skill Inventory Report` in the response, including each candidate's exact `invocation_name` and any `Out-of-scope task hints ignored/penalized` line when present. If the script cannot run or scans zero files, do not produce a final execution prompt; report the blocker or route to clarification.
   - If the user explicitly says no special skill is needed, still run inventory and state that no special skill was selected after evidence.

3. Classify candidate skills.
   - Use only candidates returned by `Skill Inventory Report` unless the report proves no candidate exists and you explain that gap.
   - Read the full `SKILL.md` only for the top 3-4 `finalists_to_read` from the report.
   - Strong match: directly supports the requested task and should be included.
   - Supporting match: useful for a subtask, verification step, or output format.
   - Weak match: related vocabulary but not necessary.
   - Exclude weak matches from the final prompt unless the user asks for alternatives.

4. Resolve multiple applicable skills.
   - If multiple skills can solve the same part of the task, compare their roles, strengths, costs, and risks.
   - Score finalist skills on a 0-2 scale. All dimensions are positive-fit scores where `2` means best fit / safest fit, `1` means usable with caveats, and `0` means poor fit or unacceptable risk:
     - Task fit: `2` directly performs the requested work; `1` supports part of it; `0` is only loosely related.
     - Output fit: `2` naturally produces the expected artifact or verification surface; `1` needs adaptation; `0` produces the wrong kind of output.
     - Overhead fit: `2` adds little necessary process/context; `1` adds tolerable overhead; `0` adds disproportionate overhead.
     - Risk control: `2` materially reduces irreversible, external, security, legal, deployment, or data-loss risk; `1` is risk-neutral; `0` increases risk or weakens control.
     - Evidence strength: `2` materially improves proof through tests, citations, screenshots, renders, CI, or file inspection; `1` gives partial evidence; `0` gives no useful evidence.
     - Side-effect safety: `2` has no external side effects or clearly bounded safe effects; `1` needs browser/network/repo writes with manageable boundaries; `0` needs deployments, payments, destructive writes, production changes, or unclear external authority.
   - Prefer the skill with the strongest task fit and evidence strength after excluding candidates with `0` in risk control or side-effect safety unless the user explicitly authorized that route.
   - When a conflict is non-trivial, include a compact score table in `Conflicts / Choices` or `Skill Match` so the route is auditable.
   - If the best choice is obvious and low-risk, choose it and state why.
   - If the choice changes the workflow materially, stop and ask the user to choose before producing the final prompt.

5. Produce the final prompt.
   - Use the structure in `references/prompt-template.md`.
   - Include explicit `$skill-name` invocations when a skill should be used.
   - For `Clarification Path`, include `$office-hours` as the strong skill invocation and make the prompt about requirements clarification, not implementation.
   - For `Clarification Path`, the `## Output Format` section must include `## Clarified Spec` and an explicit `$ceo` return handoff. Do not rely on generic "CEO handoff" wording alone.
   - When plugin skills are selected, use the exact `invocation_name` from `Skill Inventory Report`, such as `$browser:control-in-app-browser`, `$chrome:control-chrome`, `$github:github`, `$documents:documents`, or `$presentations:Presentations`.
   - Keep the prompt directly executable; avoid meta commentary inside the prompt.
   - Before returning, check the prompt against `Executable Spec Contract`. If it fails, revise it or route to `Clarification Path`.

6. When evaluating or changing this skill, run the automated output evaluator against representative CEO outputs:
   ```bash
   cd "${CEO_SKILL_HOME:-${CODEX_HOME:-$HOME/.codex}/skills/ceo}"
   python3 scripts/evaluate_ceo_output.py --request "<raw user request>" path/to/ceo-output.md
   ```
   The evaluator checks for `Mode Router`, `Inventory Decision`, `Triage`, `Skill Inventory Report`, `Contract Check`, required `Final Prompt` headings, traceability between selected `$skill` invocations and inventory candidates, semantic completeness, request-aware alignment between the raw request and `Direct Path` / `Clarification Path`, and the `Goal Mode` incomplete rule that requires `Inventory Run: No` while forbidding `Skill Inventory Report` and `Final Prompt`. If it fails, treat the CEO output as non-executable until the missing contract element is fixed.

## Output Format

Default language: use Chinese for the CEO response and for the body content inside `Final Prompt`, unless the user explicitly asks for another language. Preserve required section headings, skill invocation names, file paths, commands, code identifiers, citations, and quoted source text exactly as needed for execution and validation.

Every response must start with `Mode Router`. Every response must include `Inventory Decision`. `Inventory Decision` must appear before `Skill Inventory Report` whenever a skill inventory report exists.

For `Goal Mode` with `Status: Incomplete`, return only:

1. `Mode Router` - `Goal Mode`, confidence, reason, evidence, immediate intent, signals, and `Continue To: Goal Contract`.
2. `Goal Mode` - `Status: Incomplete`.
3. `Goal Contract Check` - ready, missing, vague, unverifiable, route-changing, and high-risk fields.
4. `Clarification Type` - `Type: Local Goal`.
5. `Inventory Decision` - `Inventory Run: No`, with the skip reason and `Inventory Input: Not applicable`.
6. `Route Decision` - `Stay in Goal Mode`.
7. `Blocking Question` - exactly one blocking question.
8. `Why This Question Comes First` - short rationale.

For `Goal Mode` with `Status: Incomplete`, do not include `Skill Inventory Report`, `Skill Match`, `Contract Check`, or `Final Prompt`.

For `Goal Mode` with `Status: Complete -> Task Mode`, return:

1. `Mode Router` - `Goal Mode`, confidence, reason, evidence, immediate intent, signals, and `Continue To: Goal Contract`.
2. `Goal Mode` - `Status: Complete`.
3. `Goal Spec` - required goal contract fields, including first executable slice and stop/ask/escalate conditions.
4. `Goal Contract Check` - pass/fail statuses for required and conditional fields.
5. `Domain Gate` - `Category: Green` or safely bounded `Yellow`; never `Red`.
6. `Clarification Type` - `Type: Not Required`.
7. `Inventory Decision` - `Inventory Run: Yes`, reason, and `Inventory Input: First Executable Slice plus compact Goal Spec context`.
8. `Skill Inventory Report` - produced from the first executable slice plus compact Goal Spec context.
9. `Route Decision` - `Next Route: Task Mode`.
10. `Task Mode Handoff` - task-ready slice with target, action, deliverable, scope, validation, and `Ready for Task Mode: Yes`.
11. `Skill Match` - selected skills/plugins and rationale from inventory.
12. `Contract Check` - executable-spec checklist.
13. `Final Prompt` - Task Mode execution prompt for the first executable slice.
14. `Assumptions` - bounded assumptions, risks, and reversibility.

For `Goal Mode` with `Status: Routed -> Clarification`, return:

1. `Mode Router` - `Goal Mode`, confidence, reason, evidence, immediate intent, signals, and `Continue To: Goal Contract`.
2. `Goal Mode` - `Status: Routed`.
3. `Goal Spec` or `Partial Goal Spec` - known fields and explicit gaps.
4. `Goal Contract Check` - missing, vague, route-changing, or high-risk fields.
5. `Domain Gate` - usually `Category: Red`; use `Yellow` only when the first slice is not bounded enough for Task Mode yet.
6. `Clarification Type` - `Type: Discovery` or `Type: Risk Boundary`.
7. `Inventory Decision` - `Inventory Run: Yes / No` according to the clarification route.
8. `Skill Inventory Report` - only when `Inventory Run: Yes`.
9. `Route Decision` - `Next Route: Clarification`, with recommended skill if one is selected.
10. `Final Prompt` for Discovery clarification, or `Clarification Prompt` for Risk Boundary clarification.

Discovery clarification must require a `## Clarified Spec` and the literal handoff: `Return this Clarified Spec to $ceo for the final execution prompt`.

Risk Boundary clarification must output a `## Risk-Bounded Clarified Spec` shape with authority, affected systems/data, target environment, backup/recovery, rollback, dry-run/simulation, verification, audit trail, stop conditions, forbidden actions until approved, readiness, and CEO handoff summary. Allowed readiness values are `Ready for CEO Re-evaluation` or `Not Ready for Execution`; never say `Ready for Execution`.

Risk Boundary clarification must not include execution commands, operational steps, deletion commands, deployment commands, permission-bypass instructions, or approval language. It may list forbidden actions only under an explicitly forbidden/non-goal/stop-condition field.

For `Task Mode`, return:

1. `Mode Router` - `Task Mode`, confidence, reason, evidence, immediate intent, signals, and `Continue To: Demand Triage`.
2. `Triage` - `Direct Path` or `Clarification Path`, plus the reason and any material missing inputs.
3. `Inventory Decision` - `Inventory Run: Yes`, reason, and `Inventory Input: Raw user request`.
4. `Skill Inventory Report` - scanned file count, unique skill count, roots covered, duplicate count, complexity, candidate limit, finalist limit, top candidates with exact `invocation_name`, finalists read, and any out-of-scope hints ignored or penalized.
5. `Skill Match` - selected skills/plugins and brief rationale; include finalist score table when multiple skills materially compete.
6. `Conflicts / Choices` - only if alternatives need user choice.
7. `Contract Check` - concise pass/fail checklist for objective, inputs/context, scope/non-goals, deliverables, assumptions/boundaries, validation evidence, failure/escalation conditions, output format, skill provenance, and `Skill Inventory Report`.
8. `Final Prompt` - the prompt the user can copy into Codex.
9. `Assumptions` - concise list of assumptions made, each tied to a boundary/risk/reversibility note when material.

If user choice is required, return the comparison and a short question instead of inventing the final route.

## Quality Bar

- Do not create a vague "better prompt"; create an executable operating brief.
- Default to Chinese output for explanations, rationale, assumptions, contract checks, and final prompt body content unless the user explicitly requests another language.
- Do not include hidden chain-of-thought instructions. Use observable reasoning steps, checkpoints, and evidence requirements.
- Do not overfit skill selection. Include only skills that change execution quality.
- Do not claim a skill/plugin exists unless found in available metadata or on disk.
- Do not select skills before running `scripts/skill_inventory.py`.
- Do not include `Skill Inventory Report` unless `Inventory Decision` says `Inventory Run: Yes`.
- Do not turn vague requirements into a fabricated implementation brief. If `Clarification Path` applies, the useful output is the `$office-hours` clarification handoff plus the instruction to return to `$ceo` after clarification.
- Do not output `Hard Stop`, terminate the request, or refuse to continue when risk, authority, reversibility, or permission boundaries are unclear. Route to `Risk Boundary` or `Discovery` clarification instead.
- Do not ship a `Final Prompt` that fails the `Executable Spec Contract`.
- Do not ship a `Final Prompt` if `Skill Inventory Report` is absent, scans zero files, omits a configured root without explanation, or selected skills are not traceable to inventory candidates.
- For Direct Path prompts, assumptions must appear as actionable boundaries with risk and reversibility, not only as a trailing list.
- For plugin skills, use the inventory-provided `invocation_name`; do not invent or shorten plugin prefixes.

## Final Prompt Guardrails

Inside `Final Prompt`, always emit these exact headings in this order: `## Role`, `## Objective`, `## Requirements`, `## Context`, `## Thinking Process`, `## Validation`, and `## Output Format`. Do not rename, omit, reorder, translate, or replace them with informal labels such as `Requirements`, `Execution workflow`, or `Completion report`. Write the content under these headings in Chinese by default unless the user explicitly asks for another language.

Invoke only strong matches and truly useful supporting matches in the executable prompt. Do not include weak-match `$skill-name` invocations unless the user explicitly asked for alternatives or the weak match creates a material routing choice. Excluding weak matches is usually silent; mention them only when explaining a conflict or preventing a likely mistaken route.

Tie validation to the selected skills and deliverable. Name the concrete commands, checks, screenshots, file renders, CI statuses, artifact inspections, or manual browser flows that would prove the prompt was executed successfully.

Select a validation pattern by task type:

- Code/build tasks: run the relevant lint, typecheck, unit/integration tests, and inspect changed files or diagnostics.
- Debugging tasks: reproduce the failure, identify root cause evidence, verify the fix against the failing case, and check likely regressions.
- Prompt-only tasks: check contract completeness, scope clarity, skill routing, validation specificity, and absence of hidden chain-of-thought requests.
- Research/legal/medical/financial/current-information tasks: use authoritative or primary sources, include citations/links, verify dates, and separate facts from inference.
- Document/spreadsheet/presentation tasks: render or inspect the generated artifact, verify formatting/content requirements, and check export/open behavior.
- Browser/frontend/app/game tasks: run the app in a browser, test core interactions, inspect responsive states, collect screenshots or visual evidence, and verify console/runtime health.
- Deployment/external-side-effect tasks: confirm authority, dry-run or plan first when possible, verify target environment, and report exact deployed URLs/statuses/logs.

For browser app, frontend build, prototype, demo, landing page, website, or game UI requests, route strongly to `$frontend-skill` when available. Route `$playwright` as supporting validation when browser behavior, visuals, keyboard shortcuts, export flows, responsiveness, or UI interaction must be verified. Include concrete requirements for the working surface, core interactions, export behavior when relevant, keyboard shortcuts when relevant, responsive layout, accessibility basics, and polished visual treatment. Validation should require running the app in a browser, checking screenshots or visual state, testing key interactions and shortcuts, testing export output when relevant, and reporting exact evidence gathered.

In `## Thinking Process`, instruct only observable work: inspect context, choose the route, implement in scoped steps, verify each workflow, and report evidence. Do not ask for hidden reasoning or chain-of-thought.

For `Clarification Path`, the `Final Prompt` must still use the required headings, but its objective is requirements clarification. Its validation should require a clarified spec with goal, deliverable, in-scope/out-of-scope boundaries, decision boundaries, constraints, and acceptance criteria, followed by an explicit handoff back to `$ceo` for the final execution prompt. The `## Output Format` section should name the required `## Clarified Spec` fields and include the literal `$ceo` next-step handoff.

When updating or evaluating this skill, use `references/eval-fixtures.json` as the machine-readable behavior fixture set and `references/test-fixtures.md` as the human-readable explanation. Run `scripts/validate_eval_fixtures.py`, `scripts/validate_contract_drift.py`, and `scripts/evaluate_ceo_output.py` against generated fixture outputs before claiming the CEO prompt is executable.
