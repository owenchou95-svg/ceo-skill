# CEO Prompt Builder Showcase

This is the 30-second demo script used by `assets/showcase.tape` and summarized by `assets/showcase.gif`.

Regenerate the committed GIF without third-party dependencies:

```bash
python3 scripts/render_showcase_gif.py
```

## Scene 1: Rough Request

```text
$ceo 我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么。
```

## Scene 2: CEO Refuses To Guess

```text
Triage: Clarification Path

Reason: style, content, audience, deliverables, and success criteria are not settled.
CEO will not invent an implementation brief.
```

## Scene 3: Skill Inventory Evidence

```text
Skill Inventory Report
- Scanned roots: Codex, plugins/cache, agents, Claude, OpenClaw, Hermes
- Candidate limit: 10
- Finalist limit: 4
- Finalist #1: $office-hours
```

## Scene 4: Executable Handoff

```md
## Final Prompt
Use $office-hours.

## Objective
Clarify the website idea enough for $ceo to produce the final execution prompt.

## Output Format
Return ## Clarified Spec with Goal, Deliverables, In Scope, Out of Scope,
Decision Boundaries, Acceptance Criteria, Risks, Open Questions, and:
Return this Clarified Spec to $ceo for the final execution prompt.
```

## What The Viewer Should Understand

CEO is not a prompt polisher. It is the routing and contract layer before execution.
