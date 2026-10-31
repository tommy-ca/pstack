"""Offline negative controls for the staged Cursor PStack 0.15.36 migration.

These tests exercise the real read-only sync recipe and review prompt packer.
They do NOT claim six-host native execution or a TLC model proof.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sync_from_upstream as sync
from skills.interrogate.scripts.pack import PackRequest, assemble_prompt, pack_review

REFS = ROOT / "skills" / "interrogate" / "references"


def test_read_only_recipe_records_candidate_without_promoting_pin(tmp_path: Path) -> None:
    upstream = tmp_path / "UPSTREAM"
    pin = "8" * 40
    upstream.write_text(f"Official upstream\ntree {pin}\n", encoding="utf-8")
    before = upstream.read_bytes()

    assert sync.pin(upstream) == pin
    recipe = sync.recipe(upstream)
    assert pin in recipe
    assert "CHANGELOG.md" in recipe
    assert "scripts/sync_from_upstream.py" in recipe
    assert "scripts/verify_portable.py" in recipe
    assert "ONLY after #850" in recipe
    assert "Do not blindly copy" in recipe
    assert upstream.read_bytes() == before


@pytest.mark.parametrize(
    "bad",
    ["", "tree nope", "tree " + ("0" * 39), "tree " + ("X" * 40)],
)
def test_bad_pin_is_not_accepted(tmp_path: Path, bad: str) -> None:
    path = tmp_path / "UPSTREAM"
    path.write_text(bad, encoding="utf-8")
    with pytest.raises(SystemExit, match="missing"):
        sync.pin(path)


def test_reviewer_prompt_requires_executable_reproduction() -> None:
    request = PackRequest(
        intent_text="Keep ownership scoped to one branch.",
        diff_text="diff --git a/file b/file\n+change\n",
        rubric_text=(REFS / "rubric.md").read_text(encoding="utf-8"),
        code_quality_text=(REFS / "code-quality-review.md").read_text(encoding="utf-8"),
        template_text=(REFS / "reviewer-prompt.md").read_text(encoding="utf-8"),
        out_dir=None,
    )
    prompt = pack_review(request)
    assert "exact command" in prompt.lower()
    assert "observed" in prompt.lower()
    assert "expected" in prompt.lower()
    assert "BLOCKED" in prompt
    assert "Keep ownership scoped to one branch." in prompt
    assert "{INTENT}" not in prompt


def test_missing_placeholder_fails_closed() -> None:
    with pytest.raises(SystemExit, match="missing placeholder"):
        assemble_prompt(
            "No interpolation fields",
            "intent",
            "diff",
            "rubric",
            "quality",
        )


def test_source_contracts_disallow_phantom_independent_review() -> None:
    arena = (ROOT / "skills" / "arena" / "SKILL.md").read_text(encoding="utf-8")
    interrogate = (ROOT / "skills" / "interrogate" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    formal = (
        ROOT / "skills" / "create-formal-verification-skill" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "coordinator's own model family" in arena
    assert "skip Phase C" in arena
    assert "lead reruns its reproduction" in interrogate
    assert "Drop or mark BLOCKED" in interrogate
    assert "statechart" in formal
    assert "When absent, run TLC directly" in formal


def test_applied_and_candidate_release_are_distinct() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    descriptor = (ROOT / "pstack.package.json").read_text(encoding="utf-8")
    assert "0.15.36 candidate" in changelog
    assert "NOT SHIPPED" in changelog
    assert '"upstream_pin": "88d47514b82e7c44f00f2b2a72ff6dd12158038c"' in descriptor
    assert "0.15.29-preview.0" in descriptor


def test_agentic_orchestrate_has_one_owner_and_independent_pr_verification() -> None:
    skill = (
        ROOT / "skills" / "poteto-mode" / "playbooks" / "orchestrate.md"
    ).read_text(encoding="utf-8")
    assert "Only the designated PR owner pushes" in skill
    assert "each PR needs an independent verifier" in skill
    assert "MUST NOT create a playbook-local store" in skill
    assert "native PR/CI event subscriptions" in skill
    assert "Gas City formulas and Beads" in skill
    assert "coordinator lands verified units" not in skill
    assert "global stacker write access" in skill


def test_upstream_goal_and_measurement_workflow_is_present() -> None:
    mode = (ROOT / "skills" / "poteto-mode" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    principle = (
        ROOT / "skills" / "principle-explain-the-number" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "First message and PR rationale" in mode
    assert "Give **new work** to a fresh subagent by default" in mode
    assert "Write the decision before you run" in principle
    assert "run-to-run spread is larger than the effect" in principle
