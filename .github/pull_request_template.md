## Why

What user-visible failure, confusion, or release gap does this change address?

## What changed

- 

## Contract surface touched

- [ ] `SKILL.md`
- [ ] `schema/ceo-output-contract.schema.json`
- [ ] `references/eval-fixtures.json`
- [ ] `references/prompt-template.md`
- [ ] `scripts/evaluate_ceo_output.py`
- [ ] `scripts/skill_inventory.py`
- [ ] README / examples / showcase only

## Verification

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate_contract_drift.py
python3 scripts/validate_eval_fixtures.py references/eval-fixtures.json
python3 scripts/verify_multi_agent_install.py
python3 scripts/smoke_host_native_cli.py
```

## Known gaps

- 

