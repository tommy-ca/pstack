from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skill_frontmatter import split_frontmatter, read_scalar, validate_skill_name
from scripts.sync_antigravity_plugin import skill_names


def test_thermo_nuclear_review_skill_frontmatter() -> None:
    skill_file = ROOT / "skills" / "thermo-nuclear-review" / "SKILL.md"
    assert skill_file.is_file()
    text = skill_file.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 24000

    # Ensure style rules: no long-dash, no mid-sentence colon
    assert "—" not in text
    assert "–" not in text

    header, body = split_frontmatter(text)
    name = validate_skill_name(read_scalar(header, "name"), expected="thermo-nuclear-review")
    assert name == "thermo-nuclear-review"
    desc = read_scalar(header, "description")
    assert desc
    assert "security and correctness" in desc.lower()
    assert read_scalar(header, "disable-model-invocation") == "true"

    assert "## Core Prompt" in body
    assert "## Scope and Boundaries" in body
    assert "## Core Review Guidelines" in body
    assert "## Execution Protocol" in body
    assert "## Report Structure" in body


def test_thermos_skill_frontmatter() -> None:
    skill_file = ROOT / "skills" / "thermos" / "SKILL.md"
    assert skill_file.is_file()
    text = skill_file.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 24000

    # Ensure style rules: no long-dash, no mid-sentence colon
    assert "—" not in text
    assert "–" not in text

    header, body = split_frontmatter(text)
    name = validate_skill_name(read_scalar(header, "name"), expected="thermos")
    assert name == "thermos"
    desc = read_scalar(header, "description")
    assert desc
    assert "parallel" in desc.lower()
    assert read_scalar(header, "disable-model-invocation") == "true"

    assert "## Workflow Overview" in body
    assert "## Step 1. Scope Determination" in body
    assert "## Step 2. Context Gathering" in body
    assert "## Step 3. Launch Parallel Review Passes" in body
    assert "## Step 4. Synthesis and Deduplication" in body
    assert "## Output Format" in body


def test_thermo_nuclear_code_quality_review_skill_frontmatter() -> None:
    skill_file = ROOT / "skills" / "thermo-nuclear-code-quality-review" / "SKILL.md"
    assert skill_file.is_file()
    text = skill_file.read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 24000

    # Ensure style rules: no long-dash, no mid-sentence colon
    assert "—" not in text
    assert "–" not in text

    header, body = split_frontmatter(text)
    name = validate_skill_name(read_scalar(header, "name"), expected="thermo-nuclear-code-quality-review")
    assert name == "thermo-nuclear-code-quality-review"
    desc = read_scalar(header, "description")
    assert desc
    assert "maintainability review" in desc.lower()
    assert read_scalar(header, "disable-model-invocation") == "true"

    assert "## Core Prompt" in body
    assert "## Non-Negotiable Additional Standards" in body
    assert "## Reachability, Behavior Pin and Evidence Standards" in body
    assert "## Primary Review Questions" in body
    assert "## What to Flag Aggressively" in body
    assert "## Preferred Remedies" in body
    assert "## Review Tone" in body
    assert "## Output Expectations" in body
    assert "## Report Format" in body
    assert "## Approval Bar" in body


def test_thermos_skills_discovered_in_sync_inventory() -> None:
    discovered = skill_names(ROOT / "skills")
    assert "thermos" in discovered
    assert "thermo-nuclear-review" in discovered
    assert "thermo-nuclear-code-quality-review" in discovered
