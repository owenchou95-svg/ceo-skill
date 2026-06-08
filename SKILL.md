---
name: ceo
description: Turn rough user ideas, goals, or task descriptions into high-quality executable prompts. Use when the user asks to create, improve, structure, or evaluate a prompt; wants a CEO-level framing of a request; wants requirements plus thinking process plus validation method; or wants Codex to search local installed skills/plugins and incorporate the best-fit ones into the prompt, including comparing multiple applicable skills before choosing. First triage whether the request is clear enough to prompt directly or should route through $office-hours for requirements clarification.
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

## Demand Triage

Before writing the executable prompt, classify the user's request as either `Direct Path` or `Clarification Path`.

Use `Direct Path` when:

- The request names a clear action and target object, context, or workflow.
- The expected deliverable or completion shape is reasonably clear.
- The task is low-risk or the missing details can be safely captured as explicit assumptions.
- The request does not require choosing between materially different product, design, technical, legal, security, deployment, or irreversible routes.

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

For `Clarification Path`, route strongly to `$office-hours`. Do not invent a complete execution prompt for the underlying task. Instead, produce a directly executable clarification prompt that asks `$office-hours` to run the appropriate office-hours mode for the user's situation and return this CEO handoff artifact:

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

When a clarified spec is later supplied, treat it as primary context, rerun `Demand Triage`, and only produce the final execution prompt if all material gaps are resolved. A clarified spec is ready only when the required fields are present, no material field is empty or `TBD`, `Open Questions` says `None blocking` or equivalent, `Decision Boundaries` do not contain unresolved route choices, and acceptance criteria are concrete. If the clarified spec still leaves a material route choice open, stay in `Clarification Path` and ask only for that choice.

## Workflow

1. Capture the user's raw request.
   - Preserve the user's intent and wording when it contains useful nuance.
   - Apply `Demand Triage` before selecting skills or writing the final prompt.
   - Identify missing scope, irreversible decisions, external dependencies, and acceptance criteria.
   - If the request qualifies for `Clarification Path`, route to `$office-hours` instead of asking ad hoc clarification questions or making broad assumptions.
   - For `Direct Path`, ask at most 3 clarifying questions only when the missing information materially changes the prompt. Otherwise make explicit assumptions and convert them into boundaries, risks, and reversibility notes.
   - If the user supplied a `Clarified Spec`, consume it before adding new assumptions.

2. Run full skill inventory before selecting skills. This is a hard gate.
   - Run `scripts/skill_inventory.py` from this skill directory, meaning the directory that contains this `SKILL.md`, with the raw user request:
     ```bash
     cd "${CEO_SKILL_HOME:-${CODEX_HOME:-$HOME/.codex}/skills/ceo}"
     python3 scripts/skill_inventory.py --request "<raw user request>" --format markdown
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
   - It uses deterministic weighted lexical recall, not model intuition, embedding search, or a cached index.
   - Default candidate recall is top 10. Complex tasks use top 15. Full `SKILL.md` reads are limited to the top 3-4 finalists.
   - Finalists are selected with coverage-aware role diversity, not raw score alone. Prefer a compact set that covers primary execution, source/access, validation/evidence, and risk/planning/clarification when those roles are present.
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
   - When plugin skills are selected, use the exact `invocation_name` from `Skill Inventory Report`, such as `$browser:control-in-app-browser`, `$chrome:control-chrome`, `$github:github`, `$documents:documents`, or `$presentations:Presentations`.
   - Keep the prompt directly executable; avoid meta commentary inside the prompt.
   - Before returning, check the prompt against `Executable Spec Contract`. If it fails, revise it or route to `Clarification Path`.

6. When evaluating or changing this skill, run the automated output evaluator against representative CEO outputs:
   ```bash
   cd "${CEO_SKILL_HOME:-${CODEX_HOME:-$HOME/.codex}/skills/ceo}"
   python3 scripts/evaluate_ceo_output.py --request "<raw user request>" path/to/ceo-output.md
   ```
   The evaluator checks for `Triage`, `Skill Inventory Report`, `Contract Check`, required `Final Prompt` headings, traceability between selected `$skill` invocations and inventory candidates, semantic completeness, and request-aware alignment between the raw request and `Direct Path` / `Clarification Path`. If it fails, treat the CEO output as non-executable until the missing contract element is fixed.

## Output Format

Default language: use Chinese for the CEO response and for the body content inside `Final Prompt`, unless the user explicitly asks for another language. Preserve required section headings, skill invocation names, file paths, commands, code identifiers, citations, and quoted source text exactly as needed for execution and validation.

Return:

1. `Triage` - `Direct Path` or `Clarification Path`, plus the reason and any material missing inputs.
2. `Skill Inventory Report` - scanned file count, unique skill count, roots covered, duplicate count, complexity, candidate limit, finalist limit, top candidates with exact `invocation_name`, finalists read, and any out-of-scope hints ignored or penalized.
3. `Skill Match` - selected skills/plugins and brief rationale; include finalist score table when multiple skills materially compete.
4. `Conflicts / Choices` - only if alternatives need user choice.
5. `Contract Check` - concise pass/fail checklist for objective, inputs/context, scope/non-goals, deliverables, assumptions/boundaries, validation evidence, failure/escalation conditions, output format, skill provenance, and `Skill Inventory Report`.
6. `Final Prompt` - the prompt the user can copy into Codex.
7. `Assumptions` - concise list of assumptions made, each tied to a boundary/risk/reversibility note when material.

If user choice is required, return the comparison and a short question instead of inventing the final route.

## Quality Bar

- Do not create a vague "better prompt"; create an executable operating brief.
- Default to Chinese output for explanations, rationale, assumptions, contract checks, and final prompt body content unless the user explicitly requests another language.
- Do not include hidden chain-of-thought instructions. Use observable reasoning steps, checkpoints, and evidence requirements.
- Do not overfit skill selection. Include only skills that change execution quality.
- Do not claim a skill/plugin exists unless found in available metadata or on disk.
- Do not select skills before running `scripts/skill_inventory.py`.
- Do not turn vague requirements into a fabricated implementation brief. If `Clarification Path` applies, the useful output is the `$office-hours` clarification handoff plus the instruction to return to `$ceo` after clarification.
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

For `Clarification Path`, the `Final Prompt` must still use the required headings, but its objective is requirements clarification. Its validation should require a clarified spec with goal, deliverable, in-scope/out-of-scope boundaries, decision boundaries, constraints, and acceptance criteria, followed by a handoff back to `$ceo` for the final execution prompt.

When updating or evaluating this skill, use `references/test-fixtures.md` as the minimum behavior fixture set and run `scripts/evaluate_ceo_output.py` against generated fixture outputs before claiming the CEO prompt is executable.
