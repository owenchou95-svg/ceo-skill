# Example: Direct README Edit

## User Request

```text
为 ~/project 的 README 增加安装步骤和本地开发命令，保持现有风格，并运行可用的文档检查。
```

## CEO Route

`Direct Path`

The request names a clear target, deliverable, style constraint, and validation shape. It is a low-risk repository documentation task, so CEO should not force a heavy workflow.

## Inventory Evidence To Look For

A healthy CEO output should include a `Skill Inventory Report`. For this request, weak broad validation skills may appear, but the selected route can explicitly say:

```text
No special skill recommended: clear low-risk repository markdown/docs edit; use ordinary file inspection and available project checks.
```

## Expected Skill Match

- Strong match: none required.
- Supporting match: only include a validation/documentation skill if it materially improves the task.
- Exclude weak matches that do not change the execution route.

## Final Prompt Shape

The generated `Final Prompt` should ask the downstream agent to:

- inspect the existing README style before editing
- add installation and local development commands
- preserve existing conventions
- run available docs checks or explain if none exist
- report changed files and verification evidence

## Why This Example Matters

CEO is not rewarded for always selecting a skill. It is rewarded for proving that it searched, then choosing the smallest safe route.

