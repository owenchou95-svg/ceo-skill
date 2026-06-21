# CEO Prompt Builder Showcase

This showcase demonstrates the three routes CEO must make visible before any downstream agent executes work.

Regenerate the committed GIF without third-party dependencies:

```bash
python3 scripts/render_showcase_gif.py
```

## Route 1: Task Mode / Direct Path

```text
$ceo 为 ~/project 的 README 增加安装步骤和本地开发命令，保持现有风格，并运行可用的文档检查。
```

```text
Mode Router: Task Mode
Triage: Direct Path
Inventory Decision: Run on raw user request
Output: Final Prompt with validation commands
```

## Route 2: Goal Mode / Incomplete

```text
$ceo 我想把 CEO skill 做得更智能。
```

```text
Mode Router: Goal Mode
Goal Mode: Incomplete
Inventory Decision: No
Output: one Blocking Question, no Final Prompt
```

## Route 3: Goal Mode / Risk Boundary

```text
$ceo 我想清理生产数据库并重新部署系统。
```

```text
Mode Router: Goal Mode
Goal Mode: Routed
Clarification Type: Risk Boundary
Output: Risk-Bounded Clarified Spec, no deletion or deploy commands
```

## What The Viewer Should Understand

CEO is not a prompt polisher. It is the routing, inventory, and contract layer before execution. It can green-light bounded tasks, ask one gap-targeted question for unclear goals, and block high-risk goals until risk boundaries are explicit.
