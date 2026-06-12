#!/usr/bin/env python3
"""Non-destructive host-native CLI smoke checks for CEO supported hosts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


HOST_COMMANDS = {
    "codex": "codex",
    "claude-code": "claude",
    "openclaw": "openclaw",
    "hermes": "hermes",
}


def smoke_command(host: str, command: str, timeout: float) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {
            "host": host,
            "command": command,
            "status": "skipped",
            "reason": "command not found",
        }
    result = subprocess.run(
        [executable, "--help"],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "host": host,
        "command": executable,
        "status": "ok" if result.returncode in {0, 1, 2} and (result.stdout or result.stderr) else "fail",
        "returncode": result.returncode,
        "stdout_preview": result.stdout[:200],
        "stderr_preview": result.stderr[:200],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument(
        "--host",
        action="append",
        default=[],
        help="Extra or override host check in host=command form.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    commands = dict(HOST_COMMANDS)
    for item in args.host:
        if "=" not in item:
            raise SystemExit(f"--host must be host=command, got {item!r}")
        host, command = item.split("=", 1)
        commands[host] = command
    results = [smoke_command(host, command, args.timeout) for host, command in commands.items()]
    failed = [result for result in results if result["status"] == "fail"]
    if args.format == "json":
        print(json.dumps({"hosts": results, "passed": not failed}, ensure_ascii=False, indent=2))
    else:
        print("Host-native CLI smoke checks: " + ("PASS" if not failed else "FAIL"))
        for result in results:
            detail = result.get("reason") or f"returncode={result.get('returncode')}"
            print(f"- {result['host']}: {result['status']} ({detail})")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
