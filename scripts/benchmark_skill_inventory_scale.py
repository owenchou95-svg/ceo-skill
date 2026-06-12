#!/usr/bin/env python3
"""Synthetic scale benchmark for CEO skill inventory scanning."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

import skill_inventory


DEFAULT_SIZES = [700, 2000, 5000]


def write_synthetic_skills(root: Path, count: int) -> None:
    for index in range(count):
        name = "office-hours" if index == 0 else f"synthetic-{index:05d}"
        description = (
            "YC Office Hours clarify vague product direction requirements scope acceptance criteria"
            if index == 0
            else "frontend browser testing build verify planning design app workflow"
        )
        path = root / f"skill-{index:05d}" / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: {description}\n---\n", encoding="utf-8")


def run_report(root: Path, cache_path: Path, *, no_cache: bool, rebuild_cache: bool, request: str) -> tuple[dict[str, Any], float]:
    args = argparse.Namespace(
        request=request,
        format="json",
        candidate_limit=10,
        complex_candidate_limit=15,
        finalist_limit=4,
        roots=[str(root)],
        triage="clarification",
        cache_path=str(cache_path),
        no_cache=no_cache,
        rebuild_cache=rebuild_cache,
    )
    start = time.perf_counter()
    report = skill_inventory.build_report(args)
    return report, round(time.perf_counter() - start, 6)


def benchmark_size(size: int, request: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "skills"
        cache_path = Path(temp) / "inventory-cache.json"
        write_synthetic_skills(root, size)

        cold, cold_seconds = run_report(root, cache_path, no_cache=False, rebuild_cache=True, request=request)
        warm, warm_seconds = run_report(root, cache_path, no_cache=False, rebuild_cache=False, request=request)

        changed_index = 1 if size > 1 else 0
        changed = root / f"skill-{changed_index:05d}" / "SKILL.md"
        changed.write_text(
            "---\nname: synthetic-00001\ndescription: frontend browser testing build verify updated app workflow\n---\n",
            encoding="utf-8",
        )
        invalidated, invalidated_seconds = run_report(root, cache_path, no_cache=False, rebuild_cache=False, request=request)

        return {
            "size": size,
            "cold_seconds": cold_seconds,
            "warm_seconds": warm_seconds,
            "single_file_invalidation_seconds": invalidated_seconds,
            "scanned_files": cold["inventory"]["scanned_files"],
            "unique_skills": cold["inventory"]["unique_skills"],
            "candidate_count": len(cold["candidates"]),
            "finalists": [item["invocation_name"] for item in cold["finalists_to_read"]],
            "warm_cache_hits": warm["inventory"]["cache"]["hits"],
            "invalidation_cache_hits": invalidated["inventory"]["cache"]["hits"],
            "clarification_priority_rank1": bool(
                cold["finalists_to_read"]
                and cold["finalists_to_read"][0]["invocation_name"] == "office-hours"
            ),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="*", type=int, default=DEFAULT_SIZES)
    parser.add_argument("--format", choices=["json", "jsonl", "markdown"], default="json")
    parser.add_argument(
        "--request",
        default="我想做一个产品但不确定是否值得做，请帮我想清楚方向和范围。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [benchmark_size(size, args.request) for size in args.sizes]
    if args.format == "jsonl":
        for result in results:
            print(json.dumps(result, ensure_ascii=False))
    elif args.format == "markdown":
        print("# Skill Inventory Scale Benchmark")
        for result in results:
            print(
                f"- {result['size']} files: cold={result['cold_seconds']}s "
                f"warm={result['warm_seconds']}s invalidation={result['single_file_invalidation_seconds']}s "
                f"rank1={result['clarification_priority_rank1']}"
            )
    else:
        print(json.dumps({"benchmarks": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
