<sub>🌐 <a href="README.md">中文</a> · <b>English</b></sub>

<div align="center">

# CEO Prompt Builder

> *"Stop making agents guess. Compile rough intent into an executable spec."*

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-ceo-blueviolet)](SKILL.md)
[![skills.sh](https://skills.sh/b/owenchou95-svg/ceo-skill)](https://skills.sh/owenchou95-svg/ceo-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CEO is an executable agent-spec compiler: it turns rough requests into briefs with skill inventory evidence, boundaries, validation, and an output contract.**

[See It Work](#see-it-work) · [Quick Start](#quick-start) · [Triggers](#triggers) · [Safety Boundaries](#safety-boundaries) · [Validation](#validation)

</div>

---

![CEO Prompt Builder showcase](assets/showcase.gif)

<sub>The demo is generated from static fixture replay and does not call a live model. Reproduce it with [assets/showcase.tape](assets/showcase.tape), render the GIF without dependencies via [scripts/render_showcase_gif.py](scripts/render_showcase_gif.py), or read the walkthrough in [assets/showcase.md](assets/showcase.md).</sub>

---

CEO's real trick is not "writing a better prompt". It decides whether execution is allowed yet:

| User input | CEO route | Deliverable |
| --- | --- | --- |
| "Add install steps to the README" | `Task Mode -> Direct Path` | An executable brief with inventory evidence and validation commands |
| "I want to make the CEO skill smarter" | `Goal Mode -> Incomplete` | One gap-targeted `Blocking Question`, no execution prompt |
| "I want to clean production data and redeploy" | `Goal Mode -> Risk Boundary` | A risk-boundary clarification, no delete/deploy commands |

---

## What Problem It Solves

You tell an agent: "build me a better website", "review this PR", or "delete old production data and deploy". A normal agent may start too early, guess missing requirements, or keep choosing the same familiar skills.

CEO does not polish prose. It first decides whether a request can go straight to execution or needs clarification. Then it scans local skills/plugins. Finally it returns a brief another agent can execute: objective, inputs, scope, deliverables, selected skills, assumptions, risks, validation, and output format.

Use it when you have many installed skills, unclear task boundaries, or want the route to be evidence-based instead of memory-based.

## See It Work

| Input Type | CEO Route | Evidence | Example |
| --- | --- | --- | --- |
| Clear docs edit | `Direct Path` | Allows `No special skill recommended` for low-risk README work | [examples/direct-readme.md](examples/direct-readme.md) |
| Vague product/site idea | `Clarification Path` | Ranks `$office-hours` first and requests `## Clarified Spec` | [examples/clarify-website.md](examples/clarify-website.md) |
| High-risk production operation | `Clarification Path` | Blocks irreversible deletion/deploy work until authority and rollback are clear | [examples/high-risk-production.md](examples/high-risk-production.md) |
| Unclear goal | `Goal Mode: Incomplete` | Asks one blocking question when desired state, acceptance, or first slice is missing | [evals/live-model/cases.jsonl](evals/live-model/cases.jsonl) |
| High-risk goal | `Goal Mode: Risk Boundary` | Production, auth, deletion, and deploy goals require authority, rollback, dry-run, and stop conditions | [evals/live-model/cases.jsonl](evals/live-model/cases.jsonl) |

Result card:

- [assets/result-card.md](assets/result-card.md): the current score, Luban birth-check result, and verification evidence.

A CEO response starts with `Mode Router`, which decides whether the input is `Task Mode` or `Goal Mode`. Task Mode still produces an executable brief. Goal Mode first produces a goal contract, local blocking question, discovery clarification, or risk-boundary clarification, and returns to Task Mode only when a first executable slice is ready.

Task Mode responses contain:

1. `Mode Router`
2. `Triage`
3. `Inventory Decision`
4. `Skill Inventory Report`
5. `Skill Match`
6. `Conflicts / Choices` when needed
7. `Contract Check`
8. `Final Prompt`
9. `Assumptions`

Goal Mode responses contain `Goal Mode`, `Goal Contract Check`, `Clarification Type`, `Inventory Decision`, and `Route Decision`, then route by status to `Blocking Question`, `Task Mode Handoff`, `Final Prompt`, or `Clarification Prompt`.

The `Final Prompt` keeps these required headings so the downstream agent can execute it:

- `## Role`
- `## Objective`
- `## Requirements`
- `## Context`
- `## Thinking Process`
- `## Validation`
- `## Output Format`

## Quick Start

One-line install:

```bash
npx skills add owenchou95-svg/ceo-skill
```

If your host does not support `npx skills add` yet, use the overwrite-safe clone path:

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
test ! -e "$target" || { echo "Refusing to overwrite $target"; exit 1; }
mkdir -p "$(dirname "$target")"
git clone https://github.com/owenchou95-svg/ceo-skill.git "$target"
python3 "$target/scripts/verify_multi_agent_install.py"
```

Then ask your agent:

```text
$ceo I want to build a more polished personal website, but I am not sure about style, content, or what to show. Decide whether this needs clarification, inspect local skills/plugins, and produce an executable prompt.
```

Safe install, update, rollback, and uninstall commands live in [docs/safe-install-uninstall.md](docs/safe-install-uninstall.md).

## Triggers

Use CEO for requests like:

- `$ceo turn this rough request into an executable prompt`
- `$ceo evaluate whether this prompt is actually executable`
- `$ceo I have an idea but it is vague; decide whether to clarify first`
- `$ceo choose the right local skills for this frontend prototype task`
- `$ceo this involves deployment and data deletion; write safe boundaries first`
- `$ceo turn this Clarified Spec into the final execution prompt`
- `$ceo search my installed skills/plugins instead of relying on memory`

Do not use CEO to directly implement the feature, perform ordinary code review, run a security audit, deploy, or add process when the user already gave a complete executable spec and only wants execution.

## What It Delivers

CEO delivers an executable brief, not prettier wording:

| Capability | Deliverable | Why It Matters |
| --- | --- | --- |
| Mode routing | `Mode Router` | Separates executable tasks from goals that need refinement first |
| Demand routing | `Direct Path` / `Clarification Path` | Prevents vague or high-risk tasks from being executed too early inside Task Mode |
| Goal refinement | `Goal Mode` / `Goal Contract Check` / `Domain Gate` | Turns goal-shaped input into a blocking question, discovery route, risk boundary, or first executable slice |
| Inventory decision | `Inventory Decision` | States whether inventory ran and whether its input was the raw task, clarification intent, or first slice |
| Skill discovery | `Skill Inventory Report` | Makes skill choice traceable instead of memory-based |
| Skill selection | `Skill Match` + finalist scoring | Keeps only strong matches and useful support skills |
| Spec contract | `Final Prompt` | Gives the downstream agent goals, boundaries, deliverables, and validation |
| Quality gate | `Contract Check` | Blocks outputs missing inventory, validation, or output format |

## How It Differs From Prompt Rewriting

| Dimension | Ordinary Prompt Rewrite | CEO Prompt Builder |
| --- | --- | --- |
| Starting point | Make the prompt clearer | Decide whether execution is safe yet |
| Skill choice | Often model memory | Runs `scripts/skill_inventory.py` against local metadata |
| Vague needs | Fills assumptions and proceeds | Routes to `$office-hours` for `## Clarified Spec` |
| High-risk work | May add a generic warning | Requires authority, boundaries, rollback, and stop conditions |
| Validation | Often says "check the result" | Names concrete tests, screenshots, commands, artifact checks, or citations |
| Regression safety | Hard to test | Includes schema, fixtures, evaluator, and contract drift checks |

## Workflow

```text
Raw request
-> Mode Router
  -> Task Mode
     -> Demand Triage
     -> Inventory Decision
     -> Skill Inventory (frontmatter-only scan + cache)
     -> Candidate Ranking
     -> Finalist Reads (3-4 max)
     -> Skill Match
     -> Contract Check
     -> Final Prompt
     -> Evaluator
  -> Goal Mode
     -> Goal Contract Check
     -> Domain Gate
     -> Clarification Type
     -> Inventory Decision
     -> Route Decision
        -> Incomplete: Blocking Question, no execution Final Prompt
        -> Complete: Task Mode Handoff, inventory on First Executable Slice + Goal Spec
        -> Routed: Discovery or Risk Boundary clarification
```

Default scan roots:

- `${CODEX_HOME:-$HOME/.codex}/skills`
- `${CODEX_HOME:-$HOME/.codex}/plugins/cache`
- `${AGENTS_HOME:-$HOME/.agents}/skills`
- `${CLAUDE_HOME:-$HOME/.claude}/skills`
- `${OPENCLAW_HOME:-$HOME/.openclaw}/skills`
- `${HERMES_HOME:-$HOME/.hermes}/skills`

Default recall is top 10 candidates. Complex tasks expand to top 15. Full `SKILL.md` reads are limited to the final 3-4 finalists.

## Safety Boundaries

CEO will:

- Read skill frontmatter metadata and produce a traceable inventory report.
- Use clarification routing for vague, high-risk, irreversible, or under-authorized work.
- Convert material assumptions into boundaries, risks, and reversibility.
- Require downstream completion evidence through commands, tests, screenshots, artifacts, or citations.

CEO will not:

- Directly implement the target feature or edit the target project.
- Replace `$code-review`, `$security-review`, deployment, or database-operation skills.
- Guess skills when no inventory report was produced.
- Approve production deletion, deployment, payments, legal, financial, or security-sensitive work for the user.
- Force weak-match skills into the final prompt.

## Multi-Agent Installation

The repository is host-light: the canonical protocol is [SKILL.md](SKILL.md), helper scripts use the Python standard library, and host-specific notes live in [adapters/](adapters/).

| Host | Install Root | Adapter |
| --- | --- | --- |
| Codex | `${CODEX_HOME:-$HOME/.codex}/skills/ceo` | root `SKILL.md` |
| Claude Code | `${CLAUDE_HOME:-$HOME/.claude}/skills/ceo` | [adapters/claude-code.md](adapters/claude-code.md) |
| OpenClaw | `${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo` | [adapters/openclaw.md](adapters/openclaw.md) |
| Hermes | `${HERMES_HOME:-$HOME/.hermes}/skills/ceo` | [adapters/hermes.md](adapters/hermes.md) |

See [docs/multi-agent-usage.md](docs/multi-agent-usage.md) for full host notes.

## Validation

From the repository root:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_contract_drift.py
python3 scripts/validate_eval_fixtures.py references/eval-fixtures.json
python3 scripts/verify_multi_agent_install.py
python3 scripts/smoke_host_native_cli.py
python3 scripts/render_showcase_gif.py
```

Validate the skill structure:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
```

Run an inventory sample:

```bash
python3 scripts/skill_inventory.py \
  --request "I have a product idea but I am not sure whether it is worth building. Help me clarify the direction and scope." \
  --triage clarification \
  --format markdown
```

Evaluate a generated CEO output:

```bash
python3 scripts/evaluate_ceo_output.py --request "<raw user request>" path/to/ceo-output.md
```

## Repository Layout

```text
.
├── SKILL.md
├── README.md
├── README.en.md
├── examples/
│   ├── direct-readme.md
│   ├── clarify-website.md
│   └── high-risk-production.md
├── assets/
│   ├── showcase.md
│   ├── showcase.tape
│   ├── showcase.gif
│   └── result-card.md
├── adapters/
│   ├── claude-code.md
│   ├── hermes.md
│   └── openclaw.md
├── docs/
├── references/
├── schema/
└── scripts/
```

## Current Optimization Status

Implemented P0/P1 capabilities:

- request-aware demand-triage evaluation
- executable positive/negative fixture tests
- `$office-hours` synchronization in SkillOpt
- coverage-aware skill finalists
- single-critical-gap clarification rule
- clarified-spec readiness checks
- alias/canonical-family handling for duplicate skill families
- stream-based frontmatter parsing
- public examples and reproducible showcase assets
- release templates, issue templates, and a public result card

Current measured results:

- Core skill score: `90 -> 95 / 100`
- Public release readiness: `76 -> 95 / 100`
- Luban birth check: `8 PASS / 5 WARN / 0 FAIL -> 14 PASS / 0 WARN / 0 FAIL`

Known boundaries:

- `scripts/verify_multi_agent_install.py` verifies simulated layout and helper execution. Real host-native dispatch requires `scripts/smoke_host_native_cli.py` and the host CLI to exist locally.
- `scripts/run_live_model_samples.py` supports fixture/historical output validation. Real live-model generation requires a local `CEO_LIVE_MODEL_COMMAND` and credentials, so it is not a default CI hard gate.

## Acknowledgements

CEO is informed by the Agent Skills ecosystem, Codex skills, SkillOpt-style regression evaluation, and prompt-evaluation workflows. See [docs/ceo-three-hour-review-20260608.md](docs/ceo-three-hour-review-20260608.md) for the review and benchmark record.

## License

[MIT](LICENSE)
