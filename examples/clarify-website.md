# Example: Clarify A Vague Website Idea

## User Request

```text
我想做一个更高级的个人网站，但还不确定风格、内容和要展示什么，你帮我想清楚。
```

## CEO Route

`Clarification Path`

The user is explicitly unsure about style, content, and what to show. Multiple product/design routes are plausible, so CEO should not invent a complete implementation prompt.

## Inventory Evidence To Look For

The inventory should scan all configured roots and place `$office-hours` / `gstack-office-hours` as the first finalist when present.

Representative evidence:

```text
Triage mode: clarification
Candidate limit: 10
Finalist limit: 4
1. `$office-hours` (`office-hours`) ... Role: risk-planning
```

Frontend or product-design skills may appear as future execution context, but they must not displace the clarification route.

## Expected Skill Match

- Strong match: `$office-hours`
- Future-after-clarification context: frontend/design skills may be mentioned only after a concrete `## Clarified Spec` exists.

## Final Prompt Shape

The generated `Final Prompt` should ask `$office-hours` to return:

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
- CEO Handoff Summary:
```

The handoff summary must include:

```text
Return this Clarified Spec to $ceo for the final execution prompt.
```

## Why This Example Matters

This is the failure mode CEO was built to prevent: a vague request becoming a fabricated implementation brief.

