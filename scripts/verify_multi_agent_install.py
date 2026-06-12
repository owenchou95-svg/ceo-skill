#!/usr/bin/env python3
"""Simulate installing CEO Prompt Builder across supported agent hosts.

Limitations:
- Verifies copied file layout, adapter naming, inventory root coverage, and helper execution.
- Does not launch Claude Code, OpenClaw, Hermes, or Codex runtime dispatch.
- Does not verify marketplace/plugin registration, shell profile persistence, live model access, or host runtime permissions.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HOSTS = {
    "codex": ("CODEX_HOME", ".codex"),
    "claude-code": ("CLAUDE_HOME", ".claude"),
    "openclaw": ("OPENCLAW_HOME", ".openclaw"),
    "hermes": ("HERMES_HOME", ".hermes"),
}


def copy_repo(destination: Path) -> None:
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache", ".DS_Store")
    shutil.copytree(REPO_ROOT, destination, ignore=ignore)


def run_inventory(install_root: Path, env: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            str(install_root / "scripts" / "skill_inventory.py"),
            "--request",
            "Create an executable prompt for a frontend app and browser validation.",
            "--format",
            "json",
        ],
        cwd=install_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def verify_host(
    host: str,
    env_name: str,
    home_dir_name: str,
    temp_root: Path,
    *,
    allow_ceo_duplicate_count: int = 1,
) -> dict[str, object]:
    host_home = temp_root / home_dir_name
    install_root = host_home / "skills" / "ceo"
    install_root.parent.mkdir(parents=True, exist_ok=True)
    copy_repo(install_root)

    env = os.environ.copy()
    env["CODEX_HOME"] = str(temp_root / ".codex")
    env["AGENTS_HOME"] = str(temp_root / ".agents")
    env["CLAUDE_HOME"] = str(temp_root / ".claude")
    env["OPENCLAW_HOME"] = str(temp_root / ".openclaw")
    env["HERMES_HOME"] = str(temp_root / ".hermes")
    env["CEO_SKILL_HOME"] = str(install_root)
    env[env_name] = str(host_home)

    report = run_inventory(install_root, env)
    inventory = report["inventory"]
    configured_roots = set(inventory["roots_configured"])
    expected_root = str(host_home / "skills")
    if expected_root not in configured_roots:
        raise AssertionError(f"{host}: expected root missing from inventory: {expected_root}")

    skill_file = install_root / "SKILL.md"
    if not skill_file.exists():
        raise AssertionError(f"{host}: missing root SKILL.md")

    adapter_skill_files = sorted((install_root / "adapters").rglob("SKILL.md"))
    if adapter_skill_files:
        raise AssertionError(f"{host}: adapter files must not be named SKILL.md: {adapter_skill_files}")

    ceo_duplicates = [
        duplicate
        for duplicate in inventory["duplicate_names"]
        if duplicate.get("invocation_name") == "ceo"
    ]
    unexpected_ceo_duplicates = [
        duplicate
        for duplicate in ceo_duplicates
        if int(duplicate.get("count", 0)) > allow_ceo_duplicate_count
    ]
    if unexpected_ceo_duplicates:
        raise AssertionError(f"{host}: duplicate ceo skills found: {ceo_duplicates}")

    return {
        "host": host,
        "install_root": str(install_root),
        "expected_root": expected_root,
        "scanned_files": inventory["scanned_files"],
        "unique_skills": inventory["unique_skills"],
        "ceo_duplicate_count": ceo_duplicates[0]["count"] if ceo_duplicates else 1,
        "status": "ok",
    }


def verify_combined_install(temp_root: Path) -> dict[str, object]:
    results = []
    for host, (env_name, home_dir_name) in HOSTS.items():
        results.append(
            verify_host(
                host,
                env_name,
                home_dir_name,
                temp_root,
                allow_ceo_duplicate_count=len(HOSTS),
            )
        )
    return {
        "host": "combined",
        "status": "ok",
        "ceo_duplicate_count": results[-1]["ceo_duplicate_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    results = []
    for host, (env_name, home_dir_name) in HOSTS.items():
        with tempfile.TemporaryDirectory() as temp:
            results.append(verify_host(host, env_name, home_dir_name, Path(temp)))

    with tempfile.TemporaryDirectory() as temp:
        combined = verify_combined_install(Path(temp))

    if args.format == "json":
        print(json.dumps({"hosts": results, "combined": combined}, indent=2, ensure_ascii=False))
    else:
        print("Multi-agent install verification: PASS")
        for result in results:
            print(
                f"- {result['host']}: {result['status']} "
                f"root={result['expected_root']} scanned={result['scanned_files']} unique={result['unique_skills']}"
            )
        print(f"- combined: {combined['status']} ceo_duplicates={combined['ceo_duplicate_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
