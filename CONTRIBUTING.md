# Contributing

This repository is a skill contract plus deterministic helper scripts. Treat `SKILL.md`, `schema/ceo-output-contract.schema.json`, `references/prompt-template.md`, `references/eval-fixtures.json`, `scripts/evaluate_ceo_output.py`, and `scripts/skill_inventory.py` as one coupled surface.

## Local Setup

No runtime dependency beyond Python 3 standard library is required for the helper scripts.

Run the standard checks before opening a PR:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_contract_drift.py
python3 scripts/validate_eval_fixtures.py references/eval-fixtures.json
python3 scripts/verify_multi_agent_install.py
python3 scripts/smoke_host_native_cli.py
python3 scripts/benchmark_skill_inventory_scale.py --sizes 700 2000 5000 --format markdown
python3 scripts/run_live_model_samples.py --mode fixture
```

Optional local Codex validation, when the bundled validator exists:

```bash
test ! -f "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" || \
  python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/ceo"
```

## Contract Drift Rules

If you change the response contract, update all affected files in the same change:

- `SKILL.md`
- `schema/ceo-output-contract.schema.json`
- `references/prompt-template.md`
- `references/eval-fixtures.json`
- `scripts/evaluate_ceo_output.py`
- `scripts/test_ceo_scripts.py`
- SkillOpt benchmark/evaluator notes when the acceptance target changes

`$office-hours` is the canonical `Clarification Path` route. `$deep-interview --quick` must not return as a hard clarification route.

## PR Checklist

- The change keeps inventory scanning deterministic and frontmatter-only.
- New behavior has a positive fixture and, when regression-prone, a negative fixture.
- `Clarification Path` keeps `$office-hours` / `gstack-office-hours` as finalist priority when available.
- Public docs do not overclaim host-native runtime validation.
- SkillOpt hard score remains `1.0`; soft score must stay `>= 0.987` unless the change intentionally updates evaluator/data and explains the regression.
