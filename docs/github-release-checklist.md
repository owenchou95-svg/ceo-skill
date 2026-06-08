# GitHub Release Checklist

Status: published.
Date: 2026-06-08

Use this checklist before publishing the CEO skill repository to GitHub.

## Required Before Public Release

### Repository Hygiene

- [x] Confirm `git status --short` is clean.
- [x] Confirm commit history has a clear baseline and review documents.
- [x] Confirm no generated caches or local test artifacts are tracked.
- [x] Confirm `.gitignore` covers Python caches and local temporary files.
- [x] Decide whether to publish optimization report docs with the repository.

### User-Specific Paths

Current runtime paths use environment-variable defaults. Before a broad public release:

- [x] Replace user-specific runtime paths with `${CODEX_HOME:-$HOME/.codex}`.
- [x] Replace configured skill roots with environment-variable defaults.
- [x] Add a portability note for `CODEX_HOME`, `AGENTS_HOME`, and `CLAUDE_HOME`.
- [x] Add a portability note for `OPENCLAW_HOME`, `HERMES_HOME`, and `CEO_SKILL_HOME`.
- [x] Keep only historical local paths in archived optimization/audit docs when they describe the original local implementation record.

Files likely to need path review:

- `SKILL.md`
- `README.md`
- `scripts/skill_inventory.py`
- `docs/ceo-optimization-report.md`
- `docs/ceo-optimization-test-matrix.md`
- `docs/review-packet.md`

### Privacy / Secret Review

- [x] Search for secrets:

```bash
rg -n "sk-|api[_-]?key|token|secret|password|credential|oauth|bearer" .
```

- [x] Search for private machine paths:

```bash
rg -n "/Users/owenchou|/Users/" .
```

- [x] Search for email addresses and private URLs:

```bash
rg -n "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|https?://[^ )>]+" .
```

- [x] Confirm no private repo URLs, tokens, cookies, or personal data are embedded.

### Validation

Run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Expected current result:

- `Skill is valid!`
- `Ran 37 tests ... OK`

### Optimization Approval Gate

Optimization approval status:

- [x] P0 + P1 approved by the user and implemented.
- [x] CEO helper tests pass after implementation.
- [x] SkillOpt aggregate eval passed after implementation.

Review documents:

- `docs/review-packet.md`
- `docs/ceo-optimization-report.md`
- `docs/ceo-optimization-test-matrix.md`

### SkillOpt Gate

The project goal requires final acceptance by SkillOpt after implementation.

Before claiming final optimization completion:

- [x] Synchronize SkillOpt CEO evaluator with `$office-hours`.
- [x] Confirm no old `$deep-interview --quick` hard gate remains if `$office-hours` is canonical.
- [x] Run the local SkillOpt CEO evaluation from the acceptance checkout.
- [x] If `skillopt-eval` has a stale shebang, use the venv Python directly.
- [x] Record the SkillOpt result in the final implementation report.

### License

The repository uses the MIT License.

Before public release:

- [x] Choose a license.
- [x] Add `LICENSE`.
- [x] Mention the license in `README.md`.
- [x] Confirm whether copied or adapted patterns from external projects require attribution.

### README Accuracy

- [x] Confirm README describes current implemented behavior, not only planned behavior.
- [x] Keep known gaps visible until P0/P1 are actually implemented.
- [x] Confirm validation commands still work from a fresh clone or document required path adaptation.
- [x] Confirm README links multi-agent usage docs and adapter files.

### Multi-Agent Adapters

- [x] Add Claude Code adapter: `adapters/claude-code/SKILL.md`.
- [x] Add OpenClaw adapter: `adapters/openclaw/SKILL.md`.
- [x] Add Hermes adapter: `adapters/hermes/SKILL.md`.
- [x] Add multi-agent usage guide: `docs/multi-agent-usage.md`.
- [x] Confirm inventory scans `${OPENCLAW_HOME:-$HOME/.openclaw}/skills`.
- [x] Confirm inventory scans `${HERMES_HOME:-$HOME/.hermes}/skills`.

### GitHub Remote

Before pushing:

```bash
git remote -v
```

Remote:

```bash
origin https://github.com/owenchou95-svg/ceo-skill.git
```

Published:

```bash
git push -u origin main
```

Do not push until repository privacy, path portability, and approval status are correct.

## Current Publication Status

Ready for private review: yes.

Ready for broad public release: yes.

Blocking items for broad release:

- None.
