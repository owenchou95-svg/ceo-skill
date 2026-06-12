#!/usr/bin/env python3
"""Shared loader for the CEO executable-spec contract schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_SCHEMA_PATH = REPO_ROOT / "schema" / "ceo-output-contract.schema.json"


def load_contract_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or CONTRACT_SCHEMA_PATH
    return json.loads(schema_path.read_text(encoding="utf-8"))


def required_top_level_sections() -> list[str]:
    return list(load_contract_schema()["required_top_level_sections"])


def required_final_prompt_headings() -> list[str]:
    return list(load_contract_schema()["required_final_prompt_headings"])


def clarified_spec_fields() -> list[str]:
    return list(load_contract_schema()["clarified_spec"]["required_fields"])
