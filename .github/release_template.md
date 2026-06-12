# CEO Prompt Builder vX.Y.Z

## Why this release exists

Explain the user-facing problem this release fixes. Prefer "why" over a list of files.

## Highlights

- 

## Verification

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_contract_drift.py
python3 scripts/validate_eval_fixtures.py references/eval-fixtures.json
python3 scripts/verify_multi_agent_install.py
python3 scripts/smoke_host_native_cli.py
bash /path/to/luban/tools/check-skill-repo.sh /path/to/ceo-skill
```

## Upgrade

```bash
npx skills add owenchou95-svg/ceo-skill
```

For git installs:

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
git -C "$target" pull --ff-only
python3 "$target/scripts/verify_multi_agent_install.py"
```

## Known gaps

- Real live-model generation requires local `CEO_LIVE_MODEL_COMMAND` credentials and is not a default CI hard gate.
