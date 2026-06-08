# GitHub Release Checklist

Status: pre-release checklist.
Date: 2026-06-08

Use this checklist before publishing the CEO skill repository to GitHub.

## Required Before Public Release

### Repository Hygiene

- [ ] Confirm `git status --short` is clean.
- [ ] Confirm commit history has a clear baseline and review documents.
- [ ] Confirm no generated caches or local test artifacts are tracked.
- [ ] Confirm `.gitignore` covers Python caches and local temporary files.
- [ ] Decide whether to publish optimization report docs with the repository.

### User-Specific Paths

Current files intentionally document local paths because this is the active installed skill. Before a broad public release, decide whether to:

- [ ] Keep local paths as examples and document that users must adapt them.
- [ ] Replace `/Users/owenchou/.codex` with `$CODEX_HOME`.
- [ ] Replace configured skill roots with environment-variable defaults.
- [ ] Add a short portability note for macOS/Linux path differences.

Files likely to need path review:

- `SKILL.md`
- `README.md`
- `scripts/skill_inventory.py`
- `docs/ceo-optimization-report.md`
- `docs/ceo-optimization-test-matrix.md`
- `docs/review-packet.md`

### Privacy / Secret Review

- [ ] Search for secrets:

```bash
rg -n "sk-|api[_-]?key|token|secret|password|credential|oauth|bearer" .
```

- [ ] Search for private machine paths:

```bash
rg -n "/Users/owenchou|/Users/" .
```

- [ ] Search for email addresses and private URLs:

```bash
rg -n "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|https?://[^ )>]+" .
```

- [ ] Confirm no private repo URLs, tokens, cookies, or personal data are embedded.

### Validation

Run:

```bash
python3 /Users/owenchou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/owenchou/.codex/skills/ceo
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Expected current result:

- `Skill is valid!`
- `Ran 34 tests ... OK`

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
- [x] Run the local SkillOpt CEO evaluation from `/Users/owenchou/SkillOpt`.
- [ ] If `/Users/owenchou/SkillOpt/.venv/bin/skillopt-eval` has a stale shebang, use the venv Python directly.
- [x] Record the SkillOpt result in the final implementation report.

### License

No license has been selected in this repository yet.

Before public release:

- [ ] Choose a license.
- [ ] Add `LICENSE`.
- [ ] Mention the license in `README.md`.
- [ ] Confirm whether copied or adapted patterns from external projects require attribution.

### README Accuracy

- [ ] Confirm README describes current implemented behavior, not only planned behavior.
- [ ] Keep known gaps visible until P0/P1 are actually implemented.
- [ ] Confirm validation commands still work from a fresh clone or document required path adaptation.

### GitHub Remote

Before pushing:

```bash
git remote -v
```

If no remote exists:

```bash
git remote add origin <github-repo-url>
```

Then push:

```bash
git push -u origin main
```

Do not push until repository privacy, license, path portability, and approval status are correct.

## Current Publication Status

Ready for private review: yes.

Ready for broad public release: not yet.

Blocking items for broad release:

- License is not selected.
- Local paths are still embedded.
- No GitHub remote is configured.
