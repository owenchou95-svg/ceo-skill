# CEO skill 当前上下文交接

生成日期：2026-06-19

这份文件用于让同一项目的新会话快速接上 CEO skill 的当前状态。它不是完整聊天记录，而是决策、文件路径、已完成修改和下一步讨论点的压缩交接。

## 当前定位

CEO skill 的主定位是“可执行 Agent 规格编译器”。它不直接实现功能，而是把粗糙想法、目标或任务描述编译成下游 Agent 可以执行的 brief。

最终输出应包含：

- 需求目标和上下文
- 范围边界和非目标
- 交付物
- skill inventory 证据
- 选用技能和工具路由
- 假设、风险、可逆性
- 验证方法
- 失败或升级条件
- 输出格式

CEO 不替代普通代码审查、安全审计、部署、生产操作，也不在用户已经给出完整可执行规格且只想执行时绕一圈。

## 当前主流程

```text
Raw Request
  -> Demand Triage
  -> Skill Inventory
  -> Candidate Ranking
  -> Finalist Reads
  -> Skill Match
  -> Contract Check
  -> Final Prompt
  -> Evaluator / Regression Checks
```

核心思想：先判断请求能否直接编译，再做全量 skill inventory 证据检索，最后输出可执行规格。

## 当前可见文件位置

当前侧线程中，CEO skill 的可见主副本是：

- `/Users/owenchou/.agents/skills/ceo/SKILL.md`
- `/Users/owenchou/.claude/skills/ceo/SKILL.md`

这两份 `SKILL.md` 已同步，SHA-256 均为：

```text
cfe0b5568f5454b1294b09c6701d7f1898afb7441cfeea05a21b19edcf8acd90
```

注意：当前侧线程里 `/Users/owenchou/.codex/skills/ceo` 不可见，不能假设它仍是活跃副本。新会话如果需要继续修改，应先确认实际使用的是哪个安装根。

## 已完成的关键修改

本轮已修改 `Demand Triage` 中的 Direct Path 判断标准。修改位置：

- `/Users/owenchou/.agents/skills/ceo/SKILL.md`
- `/Users/owenchou/.claude/skills/ceo/SKILL.md`

### Direct Path 新准入条件

`Direct Path` 现在只能在请求足够清楚、无需发明核心路线时使用。必须全部满足：

- Target/object is identifiable：能说清处理的文件、产物、repo 区域、prompt、文档、报告、workflow 或具体对象。
- Action type is identifiable：能说清操作类型，例如 evaluate、summarize、edit docs、compare、generate a report、refine a prompt、produce a checklist。
- Deliverable is identifiable：能说清最终交付物、回答形态、代码/报告/文档改动、决策或命令输出。
- Validation can be stated concretely：验证方式能从请求中明确得到，或能按任务类型安全推导。
- Missing details can be reversible assumptions：缺失信息只能转成可逆假设，并写明边界、风险和可逆性。
- No high-risk gate is triggered。
- No unresolved route choice would materially change ownership, workflow, risk, or final deliverable。

### Direct Path 优先适用范围

低风险、可逆、交付物清楚的文档/报告类任务可以走 Direct Path，例如：

- documentation / README edits
- reports
- summaries
- checklists
- comparisons
- prompt reviews
- non-binding recommendations

### 默认 Clarification 的任务类别

以下类别即使表面看起来能做，也默认不能走 Direct Path，除非用户已经给出完整 clarified spec，且有清晰边界和验收标准：

- product direction, positioning, feature scope, roadmap, or user needs
- architecture, system design, data model, migrations, performance strategy, or cross-module ownership
- security, privacy, auth, permissions, secrets, compliance, or threat modeling
- deployment, release, production operations, deletion, rollback, monitoring, or external side effects
- long-term goals, OKRs, business strategy, career strategy, startup direction, research direction, or broad "make it better" goals

### 0-8 清晰度评分

当请求部分清楚但路线可能漂移时，使用 0-8 评分：

- Target/object clarity: 0-2
- Action clarity: 0-2
- Deliverable clarity: 0-2
- Validation clarity: 0-2

解释：

- 7-8：无高风险 gate 时可用 Direct Path。
- 5-6：进入中间地带裁决。
- 0-4：Clarification Path。

### 5-6 分中间地带裁决

5-6 分请求只有在全部满足以下条件时才可用 Conditional Direct：

- 任务低风险且可逆。
- 交付物是文档、报告、prompt evaluation、README/docs edit、summary、checklist、comparison 或 non-binding recommendation。
- 缺失细节能安全转成明确假设和边界。
- 不需要外部授权、生产访问、用户数据、法律/财务/医疗判断、安全批准、部署批准或架构所有权。

5-6 分请求如果涉及产品、架构、安全、部署、长期目标、创业方向、研究方向或 broad "make it better" goal，则走 Clarification Path。

### 不确定性规则

新增硬规则：

```text
When uncertain, do not ask whether a reasonable assumption can be invented.
Ask whether the assumption would change ownership, route, risk, or final deliverable.
If yes, use Clarification Path.
```

中文理解：不确定时，不要问“能不能猜一个合理假设”，而要问“这个假设会不会改变责任、路线、风险或最终交付物”。如果会，就必须澄清。

## 当前 Clarification Path 机制

当请求缺少关键目标、交付物、成功标准、边界，或涉及高风险/不可逆/多路线选择时，CEO 应走 `Clarification Path`。

当前 Clarification Path 会强路由到 `$office-hours`，要求它产出：

```md
## Clarified Spec
- Goal:
- Deliverables:
- In Scope:
- Out of Scope / Non-goals:
- Inputs / Context:
- Decision Boundaries:
- Constraints:
- Acceptance Criteria:
- Risks and Reversibility:
- Open Questions:
- CEO Handoff Summary: include the exact next step `Return this Clarified Spec to $ceo for the final execution prompt` when no blocking questions remain.
```

Clarified Spec 回到 CEO 后，CEO 需要重新运行 Demand Triage。只有当字段完整、没有 blocking open questions、没有未决路线选择、验收标准具体时，才能进入最终 Final Prompt。

## 当前待讨论主题：Goal Mode

用户提出想扩展 CEO skill，新增对 goal 模式的需求细化和边界框定。

目前讨论出的方向：

- Goal Mode 不应让 CEO 变成长期目标管理顾问。
- Goal Mode 更适合作为 CEO 现有架构中的 `Goal Refinement Layer`。
- 它应位于 `Demand Triage` 和 `Final Prompt` 之间，服务于“把目标编译成可执行规格”。

建议目标：

```text
Raw Request
  -> Demand Triage
  -> Goal Refinement Layer, when request is goal-shaped
  -> Skill Inventory
  -> Skill Match
  -> Contract Check
  -> Final Prompt
```

Goal Refinement Layer 可负责回答：

- 这个 goal 是不是太大？
- 它能不能转成执行目标？
- 这个 goal 的边界在哪里？
- 什么不是这个 goal？
- 成功标准是什么？
- 哪些假设会改变路线、风险或交付物？
- 什么时候应该停、问、升级到 `$office-hours`？

## 建议下一步

新会话如果继续打磨 CEO skill，建议从这里开始：

1. 读取 `/Users/owenchou/.agents/skills/ceo/SKILL.md`。
2. 读取本交接文件。
3. 先不要直接实现 Goal Mode。
4. 先和用户确认 Goal Mode 的边界：
   - 是 Goal-to-Spec 编译器？
   - 是 Goal Clarification 前置模式？
   - 是 Goal Boundary Risk Gate？
   - 还是 OKR/长期目标模式？
5. 推荐默认方案：Goal-to-Spec 编译器，吸收轻量边界 gate，不替代 `$office-hours`。

## 新会话推荐开场指令

用户可以在新会话中这样说：

```text
请先读取 `/Users/owenchou/.agents/skills/ceo/docs/CEO skill 当前上下文交接.md` 和 `/Users/owenchou/.agents/skills/ceo/SKILL.md`，然后继续和我讨论 CEO skill 的 Goal Mode 设计，不要直接实现，先细化边界和方案。
```

## 注意事项

- 这是侧线程中创建的交接文件，不代表 git 已提交或发布。
- 当前只确认 `.agents` 与 `.claude` 两份 `SKILL.md` 同步。
- 如果要让 GitHub 仓库、release 或其他安装根也包含这些变更，需要在主工作流中另行同步、测试、提交和推送。
- 不要把这份交接当作完整聊天原文；它是可执行上下文摘要。
