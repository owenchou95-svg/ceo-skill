# Safe Install, Update, and Uninstall

Use these commands to avoid overwriting an existing global skill directory.

## Preflight

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
test ! -e "$target" || { echo "Refusing to overwrite $target"; exit 1; }
```

For other hosts, change the target root:

```bash
target="${CLAUDE_HOME:-$HOME/.claude}/skills/ceo"
target="${OPENCLAW_HOME:-$HOME/.openclaw}/skills/ceo"
target="${HERMES_HOME:-$HOME/.hermes}/skills/ceo"
```

## Safe Install

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
test ! -e "$target" || { echo "Refusing to overwrite $target"; exit 1; }
mkdir -p "$(dirname "$target")"
git clone https://github.com/owenchou95-svg/ceo-skill.git "$target"
python3 "$target/scripts/verify_multi_agent_install.py"
```

## Safe Update

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
test -d "$target/.git" || { echo "Not a git checkout: $target"; exit 1; }
git -C "$target" status --short
git -C "$target" pull --ff-only
python3 "$target/scripts/verify_multi_agent_install.py"
```

If local changes exist, inspect them before updating:

```bash
git -C "$target" diff
git -C "$target" status --short
```

## Safe Uninstall

Prefer a reversible move over deletion:

```bash
target="${CODEX_HOME:-$HOME/.codex}/skills/ceo"
test -e "$target" || { echo "Nothing installed at $target"; exit 0; }
backup="$target.backup.$(date +%Y%m%d%H%M%S)"
mv "$target" "$backup"
echo "Moved to $backup"
```

Delete the backup only after confirming the host no longer needs it.

## What Verification Covers

`scripts/verify_multi_agent_install.py` verifies simulated file layout, adapter naming, inventory root coverage, and helper script execution. It does not prove real Claude Code, OpenClaw, Hermes, or Codex runtime dispatch. Use `scripts/smoke_host_native_cli.py` for non-destructive local CLI availability checks.
