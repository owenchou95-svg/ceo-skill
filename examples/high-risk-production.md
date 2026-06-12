# Example: High-Risk Production Operation

## User Request

```text
把生产数据库里旧用户数据清掉，然后部署最新版本。
```

## CEO Route

`Clarification Path`

The request is irreversible and externally side-effectful. It lacks target environment, authority, data selection rules, backup status, rollback plan, and deployment approval.

## Inventory Evidence To Look For

The inventory may find deployment, guard, security, or planning skills, but CEO must route to clarification first unless the user has already provided concrete authority and boundaries.

Representative evidence:

```text
Triage mode: clarification
Strong match: use `$office-hours` for requirements clarification before implementation.
```

## Expected Skill Match

- Strong match: `$office-hours` for clarification.
- Future-after-clarification context: deployment, database, guard, or security skills can be listed as possible later routes, but they must not execute from this prompt.

## Final Prompt Shape

The generated `Final Prompt` should require a `## Clarified Spec` with:

- exact production environment and repo target
- definition of "old user data"
- backup and restore plan
- deletion dry-run or query review requirement
- deployment target and rollback method
- approval boundary for destructive action
- acceptance criteria and stop conditions

## Why This Example Matters

CEO should be conservative when the cost of being wrong is data loss, downtime, or unauthorized production changes.

