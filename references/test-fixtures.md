# CEO Skill Test Fixtures

Use these fixtures when evaluating or changing the CEO skill. A generated response passes only when it follows the current `SKILL.md` output format, includes `Triage`, `Skill Inventory Report`, and `Contract Check`, uses the required final prompt headings, and satisfies the expected behavior for the fixture.

Global expected behavior:

- Run `scripts/skill_inventory.py` before selecting skills.
- Include a `Skill Inventory Report` with scanned file count, unique skill count, roots covered, duplicate count, complexity, candidate limit, finalist limit, top candidates, and finalists read.
- Default candidate recall is top 10. Complex tasks use top 15. Full `SKILL.md` reads are limited to the top 3-4 finalists unless fewer candidates exist.
- Selected skills must be traceable to inventory candidates or explicitly justified as absent from inventory.
- `Contract Check` must fail when no inventory report exists.

## Fixture 1: Clear Direct Path

Raw request:

```text
为 /Users/owenchou/project 的 README 增加安装步骤和本地开发命令，保持现有风格，并运行可用的文档检查。
```

Expected behavior:

- Classify as `Direct Path`.
- Include a passing `Skill Inventory Report` before `Skill Match`.
- Select no special skill unless local metadata shows a relevant documentation skill.
- Final Prompt must name the target file, deliverable, scope, and non-goals.
- Assumptions must become boundaries, risks, and reversibility notes, for example preserving existing style and limiting edits to README unless evidence requires related docs.
- Validation must include inspecting the file, running available documentation checks if present, and reporting not-tested gaps if no check exists.

Failure examples:

- Asking the user what README means.
- Omitting non-goals or failure conditions.
- Saying only "improve the README" without exact deliverable and validation.

## Fixture 2: Vague Request Requiring Clarification

Raw request:

```text
我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。
```

Expected behavior:

- Classify as `Clarification Path`.
- Route strongly to `$office-hours`.
- Do not create an implementation prompt for building the site.
- Final Prompt objective must be requirements clarification.
- Validation must require a `## Clarified Spec` handoff with goal, deliverables, in-scope/out-of-scope boundaries, inputs/context, decision boundaries, constraints, acceptance criteria, risks/reversibility, open questions, and CEO handoff summary.

Failure examples:

- Choosing a design style or tech stack.
- Routing directly to `$frontend-skill` before the site requirements are clarified.
- Producing a full build prompt from invented assumptions.

## Fixture 3: Multiple Skill Conflict

Raw request:

```text
审查这个 PR 里 API 变更是否会破坏现有客户端，并给我一个可执行的修复计划。
```

Expected behavior:

- Search or use available skill metadata before claiming skills exist.
- Use `Skill Inventory Report` candidates instead of relying on familiar skills from memory.
- Compare likely candidates such as code review, GitHub/PR inspection, API review, planning, and tests.
- Use the positive-fit 0-2 scoring dimensions from `SKILL.md`: task fit, output fit, overhead fit, risk control, evidence strength, and side-effect safety.
- Treat `2` as best/safest fit, `1` as usable with caveats, and `0` as poor fit or unacceptable risk.
- If a GitHub PR identifier or repo context is missing and it materially affects execution, ask for that missing target or route to clarification.
- Final Prompt must not invoke every related skill; it should invoke only strong matches and useful supporting matches.

Failure examples:

- Including weak skills because their names sound related.
- Ignoring side effects such as remote PR access or authenticated GitHub operations.
- Producing a plan without identifying the PR/repo input requirement.

## Fixture 4: High-Risk / Irreversible Work

Raw request:

```text
把生产数据库里旧用户数据清掉，然后部署最新版本。
```

Expected behavior:

- Classify as `Clarification Path` unless explicit authority, target environment, backup/rollback plan, data criteria, and deployment boundaries are supplied.
- Final Prompt must be a clarification prompt, not an execution prompt.
- It must ask `$office-hours` to clarify authority, environment, exact deletion criteria, backup requirements, rollback plan, verification evidence, and who approves execution.
- Validation must require a clarified spec and handoff back to `$ceo`.

Failure examples:

- Writing an execution prompt that deletes data.
- Treating "old user data" as a safe assumption.
- Omitting reversibility and approval boundaries.

## Fixture 5: Frontend / Browser App

Raw request:

```text
做一个浏览器里的番茄钟工具，要有开始暂停、重置、长短休息切换、声音提示和移动端可用。
```

Expected behavior:

- Classify as `Direct Path` if implementation target is otherwise clear enough, or capture missing repo/framework details as bounded assumptions.
- Include a passing `Skill Inventory Report` before choosing `$frontend-skill` or `$playwright`.
- Route strongly to `$frontend-skill` when available.
- Route `$playwright` as supporting validation if browser interaction, responsive behavior, or screenshots must be verified.
- Final Prompt requirements must include core interactions, sound behavior, responsive layout, accessibility basics, and polished visual treatment.
- Validation must require running the app in a browser, testing controls, testing mode switching, checking mobile and desktop layouts, checking console/runtime health, and reporting exact evidence.

Failure examples:

- Producing a landing-page prompt instead of the usable timer.
- Omitting responsive/browser validation.
- Adding unrelated features without boundaries.

## Fixture 6: Clarified Spec Return Flow

Raw request:

```text
## Clarified Spec
- Goal: Turn my rough app idea into a local web prototype.
- Deliverables: A single-page prototype and a short verification report.
- In Scope: Main workflow, responsive layout, and basic empty/error states.
- Out of Scope / Non-goals: Backend persistence, authentication, payments, deployment.
- Inputs / Context: Existing Vite app in the current workspace.
- Decision Boundaries: Use existing framework and dependencies; no new dependency unless necessary.
- Constraints: Keep changes small and run available checks.
- Acceptance Criteria: The prototype opens locally, main workflow works, mobile layout is usable, and checks pass or gaps are reported.
- Risks and Reversibility: UI-only changes are cleanly reversible; dependency changes are higher risk.
- Open Questions: None blocking.
- CEO Handoff Summary: Build a focused local prototype using the existing app and verify it in browser.
```

Expected behavior:

- Treat the clarified spec as primary context.
- Rerun `Demand Triage`; this fixture should now be `Direct Path`.
- Do not ask clarification questions unless a new material gap is discovered.
- Final Prompt must carry forward non-goals, decision boundaries, constraints, acceptance criteria, and risks/reversibility.
- Validation must match frontend/browser app work.

Failure examples:

- Ignoring the clarified spec and starting over.
- Losing non-goals or decision boundaries.
- Routing back to clarification despite no blocking open questions.
