# Changelog

All notable changes to this repository are recorded here.

Dates use local project context date unless otherwise noted.

## Unreleased

### Added

- Initialized the CEO skill as a standalone git repository.
- Added `README.md` for GitHub-facing project introduction.
- Added review documentation for the planned CEO optimization:
  - `docs/review-packet.md`
  - `docs/ceo-optimization-report.md`
  - `docs/ceo-optimization-test-matrix.md`
- Added release-readiness documentation:
  - `docs/github-release-checklist.md`
  - `docs/github-release-audit.md`

### Verified

- `quick_validate.py` passes for `/Users/owenchou/.codex/skills/ceo`.
- CEO helper tests pass: `python3 -m unittest discover -s scripts -p 'test_*.py'`.

### Pending

- License selection before broad public release.
- Path portability review before broad public release.

### Changed

- Implemented request-aware demand-triage evaluation in `scripts/evaluate_ceo_output.py`.
- Added deterministic checks for vague requests, high-risk operations, single critical missing inputs, and clarified-spec readiness.
- Added coverage-aware finalist selection in `scripts/skill_inventory.py`.
- Added alias-family handling for duplicate/mirrored skill families.
- Changed frontmatter inventory parsing to stop at the closing frontmatter marker.
- Expanded helper tests from 17 to 34 cases.
- Synchronized SkillOpt CEO benchmark/evaluator to `$office-hours` clarification handoff.
- Passed SkillOpt CEO eval on train/val/test aggregate: hard=1.0, soft=0.9799375, n=16.

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
- Broad public release is not ready until license, path portability, and GitHub remote decisions are resolved.
