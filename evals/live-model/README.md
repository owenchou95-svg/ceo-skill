# Live-Model CEO Sample Suite

This directory stores minimal sample cases plus generated CEO outputs and evaluator results.

- `cases.jsonl` defines the live-model prompts.
- `generated/<timestamp>/<case_id>.md` stores generated CEO outputs.
- `results/<timestamp>/evaluator-results.jsonl` stores `evaluate_ceo_output.py --format json` results.
- `results/<timestamp>/summary.md` stores a compact pass/fail summary.

CI should run fixture or historical-output validation only. Real live-model generation requires a stable model command and credentials, so it is not a hard CI gate by default.
