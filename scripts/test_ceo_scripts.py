#!/usr/bin/env python3
"""Regression tests for CEO helper scripts."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import evaluate_ceo_output as evaluator
import skill_inventory


def inventory_args(request: str, roots: list[str] | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        request=request,
        format="json",
        candidate_limit=10,
        complex_candidate_limit=15,
        finalist_limit=4,
        roots=roots,
    )


def valid_ceo_output() -> str:
    return """## Triage
Direct Path - the user provided a concrete app target and deliverable.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: frontend, browser
- Capability hints: build
- Validation hints: browser-validation

### Candidates
1. `$frontend-skill` (`frontend-skill`) score=20 path=/tmp/frontend/SKILL.md
2. `$playwright` (`playwright`) score=12 path=/tmp/playwright/SKILL.md

### Finalists To Read
1. `$frontend-skill` (`frontend-skill`) - /tmp/frontend/SKILL.md
2. `$playwright` (`playwright`) - /tmp/playwright/SKILL.md

## Skill Match
- Strong match: use `$frontend-skill` for frontend implementation quality.
- Supporting match: use `$playwright` for browser interaction and screenshots.

## Contract Check
- Objective: pass
- Inputs/context: pass
- Scope/non-goals: pass
- Deliverables: pass
- Assumptions/boundaries: pass
- Validation evidence: pass
- Failure conditions: pass
- Output format: pass
- Skill provenance: pass
- Skill Inventory Report: pass

## Final Prompt
Use the following skill(s) if available: $frontend-skill, $playwright

## Role
You are a frontend-focused coding agent.

## Objective
Build a browser-based Pomodoro timer that works on desktop and mobile.

## Requirements
- Inputs: the current workspace and existing app structure.
- In scope: start, pause, reset, long-break mode, short-break mode, sound alert, responsive UI, and accessible controls.
- Out of scope / non-goals: backend persistence, payments, deployment, and authentication.
- Deliverables: code changes for the timer and a short verification report with changed file paths.
- Constraints: reuse existing framework and dependencies; no new dependency unless necessary.
- Assumptions and boundaries:
  - Assumption: an existing frontend app is available.
    Boundary: inspect the app before changing files and keep edits scoped to UI code.
    Risk: if no app exists, implementation cannot proceed safely.
    Reversibility: clean.
- Failure / escalation conditions: stop and report a blocker if no app entrypoint exists or if audio cannot be tested in the browser.

## Context
The skill inventory selected frontend implementation plus Playwright validation because the task requires browser UI behavior, responsive layout, and screenshots.

## Thinking Process
Follow this visible workflow: inspect the app, confirm scope and non-goals, implement in small steps, test interactions, verify responsive states, collect evidence, and report remaining gaps.

## Validation
Run the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.

## Output Format
Return a completion report with sections: Changed files, Implemented behavior, Verification commands, Browser evidence, Known gaps, and Follow-up risks.

## Assumptions
- The workspace contains a frontend app.
  Boundary: inspect before editing.
  Risk: no app means no safe implementation target.
  Reversibility: clean.
"""


def valid_clarification_output() -> str:
    return """## Triage
Clarification Path - the user is missing style, content, deliverables, and success criteria.

## Skill Inventory Report
- Scanned files: 3
- Unique skills: 3
- Duplicates found: 0
- Roots covered:
  - /tmp/skills (yes, 3 files)
- Complexity: standard
- Candidate limit: 10
- Finalist limit: 4
- Task type hints: frontend, ideation
- Capability hints: build
- Validation hints: none

### Candidates
1. `$office-hours` (`office-hours`) score=30 path=/tmp/office-hours/SKILL.md

### Finalists To Read
1. `$office-hours` (`office-hours`) - /tmp/office-hours/SKILL.md

## Skill Match
- Strong match: use `$office-hours` for requirements clarification before implementation.

## Contract Check
- Objective: pass
- Inputs/context: pass
- Scope/non-goals: pass
- Deliverables: pass
- Assumptions/boundaries: pass
- Validation evidence: pass
- Failure conditions: pass
- Output format: pass
- Skill provenance: pass
- Skill Inventory Report: pass

## Final Prompt
Use the following skill(s) if available: $office-hours

## Role
You are a YC office-hours partner clarifying requirements before implementation.

## Objective
Clarify the vague personal website idea enough for `$ceo` to produce an executable build prompt.

## Requirements
- Inputs: the user's vague website idea and any portfolio, audience, content, or style references they provide.
- In scope: clarify goal, target audience, content inventory, style direction, decision boundaries, constraints, and acceptance criteria.
- Out of scope / non-goals: do not choose the final style, write code, scaffold a site, deploy, or fabricate missing content.
- Deliverables: a `## Clarified Spec` handoff with all required CEO fields.
- Constraints: ask focused questions and keep implementation decisions as decision boundaries rather than assumptions.
- Assumptions and boundaries:
  - Assumption: the user is still exploring.
    Boundary: clarify requirements only; do not produce an implementation prompt yet.
    Risk: building now would overfit invented content and style.
    Reversibility: clean.
- Failure / escalation conditions: stop and mark fields `Unknown and blocking` if goal, deliverables, scope, or acceptance criteria remain unresolved.

## Context
The user is unsure about style, content, and what to show, so CEO must route to office-hours and receive a clarified spec before direct execution.

## Thinking Process
Follow this visible workflow: identify missing decisions, ask office-hours questions, separate in-scope work from non-goals, capture decision boundaries, and produce the clarified handoff.

## Validation
Verify the output includes `## Clarified Spec` with Goal, Deliverables, In Scope, Out of Scope / Non-goals, Inputs / Context, Decision Boundaries, Constraints, Acceptance Criteria, Risks and Reversibility, Open Questions, and CEO Handoff Summary. Check each required field is concrete or marked `None blocking` / `Unknown and blocking`, then state whether the spec is ready for `$ceo`.

## Output Format
Return exactly one markdown artifact headed `## Clarified Spec`, followed by the required bullet fields and a short readiness note for `$ceo` execution-prompt generation.

## Assumptions
- The site idea is still vague.
  Boundary: requirements clarification only.
  Risk: premature implementation would invent core choices.
  Reversibility: clean.
"""


class EvaluatorTests(unittest.TestCase):
    def test_valid_output_passes(self) -> None:
        result = evaluator.check_contract(valid_ceo_output())
        self.assertTrue(result["passed"], result["failures"])

    def test_valid_clarification_output_passes(self) -> None:
        result = evaluator.check_contract(valid_clarification_output())
        self.assertTrue(result["passed"], result["failures"])

    def test_missing_top_level_section_fails(self) -> None:
        text = valid_ceo_output().replace("## Assumptions\n", "## Notes\n", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Assumptions", result["missing_sections"])

    def test_out_of_order_final_headings_fail(self) -> None:
        text = valid_ceo_output().replace("## Objective\nBuild", "## Validation\nBuild", 1)
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Objective", result["missing_final_prompt_headings"])

    def test_untraceable_skill_fails(self) -> None:
        text = valid_ceo_output().replace(
            "- Supporting match: use `$playwright`",
            "- Supporting match: use `$not-in-inventory`",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("not-in-inventory", result["untraceable_skills"])

    def test_shell_variables_are_not_selected_skills(self) -> None:
        text = valid_ceo_output().replace(
            "## Context\n",
            "## Context\nUse shell variable `$HOME` only as an example, not as a skill.\n",
            1,
        )
        result = evaluator.check_contract(text)
        self.assertTrue(result["passed"], result["failures"])
        self.assertNotIn("HOME", result["selected_skills"])

    def test_semantically_empty_requirements_and_validation_fail(self) -> None:
        text = valid_ceo_output()
        text = text.replace(
            "## Requirements\n- Inputs: the current workspace and existing app structure.\n- In scope: start, pause, reset, long-break mode, short-break mode, sound alert, responsive UI, and accessible controls.\n- Out of scope / non-goals: backend persistence, payments, deployment, and authentication.\n- Deliverables: code changes for the timer and a short verification report with changed file paths.\n- Constraints: reuse existing framework and dependencies; no new dependency unless necessary.\n- Assumptions and boundaries:\n  - Assumption: an existing frontend app is available.\n    Boundary: inspect the app before changing files and keep edits scoped to UI code.\n    Risk: if no app exists, implementation cannot proceed safely.\n    Reversibility: clean.\n- Failure / escalation conditions: stop and report a blocker if no app entrypoint exists or if audio cannot be tested in the browser.\n",
            "## Requirements\nDo the requested thing.\n",
        )
        text = text.replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\nCheck it.\n",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertTrue(result["semantic_failures"])

    def test_placeholder_requirement_fields_fail(self) -> None:
        text = valid_ceo_output().replace(
            "- Inputs: the current workspace and existing app structure.",
            "- Inputs: TBD.",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("placeholder or too-generic field values", "\n".join(result["semantic_failures"]))

    def test_template_validation_lines_fail(self) -> None:
        text = valid_ceo_output().replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\n- Run checks.\n- Verify output.\n- Capture screenshots.\n",
        )
        result = evaluator.check_contract(text)
        self.assertFalse(result["passed"])
        self.assertIn("Validation lacks concrete evidence", "\n".join(result["semantic_failures"]))

    def test_evaluator_cli_markdown_pass_and_fail(self) -> None:
        command = [sys.executable, str(SCRIPT_DIR / "evaluate_ceo_output.py"), "--format", "markdown"]
        valid = subprocess.run(
            command,
            input=valid_ceo_output(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, valid.returncode, valid.stderr)
        self.assertIn("CEO Output Evaluation: PASS", valid.stdout)

        invalid_text = valid_ceo_output().replace(
            "## Validation\nRun the available project checks such as npm test, npm run lint, npm run build, or their detected equivalents. Open the app in a browser with Playwright, test start, pause, reset, break switching, sound-trigger state, mobile layout, desktop layout, and console/runtime health. Capture screenshots or describe exact browser evidence gathered.\n",
            "## Validation\nCheck it.\n",
        )
        invalid = subprocess.run(
            command,
            input=invalid_text,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, invalid.returncode)
        self.assertIn("CEO Output Evaluation: FAIL", invalid.stdout)
        self.assertIn("Validation lacks concrete evidence", invalid.stdout)


class InventoryTests(unittest.TestCase):
    def make_skill(self, root: Path, rel: str, name: str, description: str) -> Path:
        path = root / rel / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        return path

    def test_complex_task_uses_15_candidate_limit_and_4_finalists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(20):
                self.make_skill(
                    root,
                    f"skill-{index}",
                    f"skill-{index}",
                    "frontend browser design testing build verify website app",
                )
            report = skill_inventory.build_report(
                inventory_args("Build a frontend browser design and testing workflow.", [str(root)])
            )
            analysis = report["request_analysis"]
            self.assertEqual("complex", analysis["complexity"])
            self.assertEqual(15, analysis["candidate_limit"])
            self.assertLessEqual(len(report["finalists_to_read"]), 4)

    def test_plugin_invocation_name_uses_plugin_prefix(self) -> None:
        path = "/Users/owenchou/.codex/plugins/cache/vendor/sample-plugin/1.2.3/skills/do-thing/SKILL.md"
        self.assertEqual("sample-plugin:do-thing", skill_inventory.invocation_name_for_path(path, "do-thing"))

    def test_duplicate_collapse_by_invocation_name(self) -> None:
        records = [
            {"invocation_name": "demo", "name": "demo", "path": "/b/SKILL.md"},
            {"invocation_name": "demo", "name": "demo", "path": "/a/SKILL.md"},
            {"invocation_name": "other", "name": "other", "path": "/c/SKILL.md"},
        ]
        unique, duplicates = skill_inventory.collapse_duplicates(records)
        self.assertEqual(["/a/SKILL.md", "/c/SKILL.md"], [item["path"] for item in unique])
        self.assertEqual(1, len(duplicates))

    def test_out_of_scope_capability_is_penalized_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            request = (
                "Build a frontend app.\n"
                "Out of Scope / Non-goals: do not deploy, release, or ship anything."
            )
            report = skill_inventory.build_report(inventory_args(request, [str(root)]))
            analysis = report["request_analysis"]
            self.assertIn("deploy", analysis["out_of_scope_capability_hints"])
            deploy_candidate = next(item for item in report["candidates"] if item["name"] == "deploy-skill")
            self.assertLess(deploy_candidate["score_breakdown"]["out_of_scope_penalty"], 0)
            self.assertIn("out-of-scope-capability:deploy", deploy_candidate["matched_terms"])

    def test_inline_out_of_scope_is_extracted_from_natural_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            report = skill_inventory.build_report(
                inventory_args("Build a frontend app but do not deploy, release, or ship anything.", [str(root)])
            )
            analysis = report["request_analysis"]
            self.assertIn("deploy", analysis["out_of_scope_capability_hints"])
            self.assertNotIn("deploy", analysis["capability_hints"])
            deploy_candidate = next(item for item in report["candidates"] if item["name"] == "deploy-skill")
            self.assertLess(deploy_candidate["score_breakdown"]["out_of_scope_penalty"], 0)

    def test_inventory_cli_markdown_reports_out_of_scope_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_skill(root, "deploy", "deploy-skill", "build create frontend app deploy release ship")
            self.make_skill(root, "build", "build-skill", "build create frontend app")
            command = [
                sys.executable,
                str(SCRIPT_DIR / "skill_inventory.py"),
                "--request",
                "Build a frontend app.\nOut of Scope / Non-goals: do not deploy, release, or ship anything.",
                "--format",
                "markdown",
                "--roots",
                str(root),
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Skill Inventory Report", result.stdout)
            self.assertIn("Out-of-scope capability hints ignored/penalized: deploy", result.stdout)
            self.assertIn("out-of-scope-capability:deploy", result.stdout)

    def test_markdown_request_penalizes_office_documents_skill(self) -> None:
        record = {
            "name": "documents",
            "invocation_name": "documents:documents",
            "description": "Create and edit docx Word Google Docs documents",
            "path": "/Users/owenchou/.codex/plugins/cache/openai-primary-runtime/documents/1/skills/documents/SKILL.md",
            "source_root": "/tmp",
        }
        scored = skill_inventory.score_skill(
            record,
            "Update README markdown install steps.",
            ["readme", "markdown", "install", "steps"],
            ["document", "repo-doc"],
            ["edit"],
            [],
            [],
            [],
            {"markdown_doc": True, "office_doc": False},
        )
        self.assertLess(scored["score_breakdown"]["out_of_scope_penalty"], 0)
        self.assertIn("mismatch:markdown-not-office-doc", scored["matched_terms"])


if __name__ == "__main__":
    unittest.main()
