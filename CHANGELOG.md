# Changelog

All notable changes to this repository are recorded here.

Dates use local project context date unless otherwise noted.

## Unreleased

### Added

- Added CI workflow coverage for unittest, contract drift, structured fixtures, simulated install verification, host CLI smoke, fast scale benchmark, and fixture live-model samples.
- Added `CONTRIBUTING.md`.
- Added safe install/update/uninstall documentation.
- Added machine-readable contract schema and structured eval fixtures.
- Added inventory scale benchmark, host-native CLI smoke checks, and live-model sample harness.
- Added multi-agent adapter notes for Claude Code, OpenClaw, and Hermes.
- Added `docs/multi-agent-usage.md` with host-specific install and dispatch guidance.
- Added simulated multi-agent installation verification.
- Initialized the CEO skill as a standalone git repository.
- Added `README.md` for GitHub-facing project introduction.
- Added review documentation for the planned CEO optimization:
  - `docs/review-packet.md`
  - `docs/ceo-optimization-report.md`
  - `docs/ceo-optimization-test-matrix.md`
- Added release-readiness documentation:
  - `docs/github-release-checklist.md`
  - `docs/github-release-audit.md`
- Added MIT License for public distribution.
- Published the public GitHub repository at `https://github.com/owenchou95-svg/ceo-skill`.

### Verified

- `quick_validate.py` passes for `${CODEX_HOME:-$HOME/.codex}/skills/ceo`.
- CEO helper tests pass: `python3 -m unittest discover -s scripts -p 'test_*.py'`.
- SkillOpt regression target: unchanged CEO benchmark should keep hard=1.0 and soft >= 0.987; any lower soft score must be explained as an intentional evaluator/data change or treated as a regression.

### Changed

- Implemented request-aware demand-triage evaluation in `scripts/evaluate_ceo_output.py`.
- Loaded evaluator contract constants from `schema/ceo-output-contract.schema.json`.
- Forced clarification finalist priority for `$office-hours` / `gstack-office-hours` when `Clarification Path` applies.
- Added frontmatter-only inventory index/cache with cold, warm, and invalidation benchmark support.
- Added deterministic checks for vague requests, high-risk operations, single critical missing inputs, and clarified-spec readiness.
- Added coverage-aware finalist selection in `scripts/skill_inventory.py`.
- Added alias-family handling for duplicate/mirrored skill families.
- Changed frontmatter inventory parsing to stop at the closing frontmatter marker.
- Expanded helper tests from 17 to 34 cases.
- Synchronized SkillOpt CEO benchmark/evaluator to `$office-hours` clarification handoff.
- Historical SkillOpt CEO eval on train/val/test aggregate passed with hard=1.0, soft=0.976859375, n=16; current release regression target is hard=1.0 and soft >= 0.987.
- Replaced user-specific default paths with `CODEX_HOME`, `AGENTS_HOME`, `CLAUDE_HOME`, and `$HOME` fallbacks.
- Extended default skill inventory roots to include `OPENCLAW_HOME` and `HERMES_HOME`.

## 2026-06-08

### Added

- `be79379 Capture CEO skill baseline`
  - Captured the current installed CEO skill baseline.
- `a5fb61b Document CEO optimization path for review`
  - Added the optimization report before functional changes.
- `45631c8 Define CEO optimization acceptance matrix`
  - Added the concrete test and acceptance matrix.
- `258fa46 Add CEO optimization review packet`
  - Added the review entry point and approval options.
- `1fa2521 Introduce CEO skill README`
  - Added the GitHub-facing README.
- `ca50f95 Add CEO GitHub release checklist`
  - Added pre-release hygiene, validation, license, path, and SkillOpt gates.
- `3e29d9e Record CEO GitHub release audit`
  - Recorded actual release-readiness scan results.

### Notes

- Functional P0/P1 optimization changes are implemented in `bd2f47d`.
- Broad public release is complete at `https://github.com/owenchou95-svg/ceo-skill`.
