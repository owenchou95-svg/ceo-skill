# CEO Prompt Template

Use this structure for final prompts.

```md
Use the following skill(s) if available: $skill-a, $skill-b

## Role
You are [role/persona appropriate to the task].

## Objective
[One clear sentence describing the desired outcome and completion state.]

## Requirements
- Inputs: [files, URLs, artifacts, user-provided material, data sources, or environment to use]
- In scope: [work the agent should perform]
- Out of scope / non-goals: [work the agent should not perform]
- Deliverables: [exact artifact, answer, code change, report, design, or decision expected]
- Constraints: [technical, product, style, safety, legal, privacy, time, dependency, or environment limits]
- Assumptions and boundaries:
  - Assumption: [what is being assumed]
    Boundary: [what the agent may and may not do because of the assumption]
    Risk: [what could go wrong if the assumption is false]
    Reversibility: [clean, messy, or irreversible]
- Failure / escalation conditions: [when to stop, ask, avoid destructive action, or report a blocker]

## Context
[Relevant background, prior decisions, target audience, repo/app context, available skills/tools, and selected skill-routing rationale.]

## Thinking Process
Follow this visible reasoning workflow:
1. Restate the task in concrete terms.
2. Confirm the inputs, scope boundaries, non-goals, and deliverables before acting.
3. Resolve assumptions as explicit boundaries with risk and reversibility.
4. Choose the selected skills/tools only where they improve execution quality or evidence.
5. Compare alternatives when they materially affect the route, output, cost, or side effects.
6. Execute in scoped steps and verify each important workflow before reporting completion.
7. Produce the final artifact and include evidence gathered.

## Validation
Use the validation pattern that matches the task type:

- Code/build: run [lint/typecheck/tests/build command], inspect changed files, and report failures or passing evidence.
- Debugging: reproduce [failure], identify root-cause evidence, verify the fix against the failing case, and check likely regressions.
- Prompt-only: verify the prompt includes objective, inputs, scope, non-goals, deliverables, assumptions as boundaries, skill routing, validation evidence, failure conditions, and output format.
- Research/current information: use authoritative sources, verify dates, cite links, and separate sourced facts from inference.
- Document/spreadsheet/presentation: render or open the artifact, check content and formatting requirements, and verify export/open behavior.
- Browser/frontend/app/game: run in a browser, test core interactions and responsive states, capture screenshots or visual evidence, and check console/runtime health.
- Deployment/external side effect: confirm authority, prefer dry-run or plan first, verify target environment, then report exact URLs/statuses/logs.

Definition of done:
- [Concrete evidence that proves the deliverable is complete]
- [Edge cases, regressions, or failure modes checked]
- [Known gaps or not-tested items, if any]

## Output Format
[Exact structure expected in the final answer or artifact, including any required file paths, commands, citations, screenshots, tables, JSON, or completion report fields.]
```

For prompt-only tasks, the validation section should evaluate whether the prompt is:

- Complete enough to execute.
- Clear about scope and deliverables.
- Explicit about inputs, non-goals, assumptions, risks, reversibility, and failure conditions.
- Explicit about evidence and verification.
- Free of unnecessary skills or tools.
