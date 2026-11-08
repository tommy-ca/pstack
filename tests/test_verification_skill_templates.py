from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.scaffold_verification_skill as scaffolder
import scripts.verification_skill_templates as templates
from skill_frontmatter import split_frontmatter, read_scalar


def test_reexport_parity() -> None:
    assert scaffolder.generate_driver_script is templates.generate_driver_script
    assert scaffolder.generate_skill_content is templates.generate_skill_content
    assert scaffolder.generate_features_readme is templates.generate_features_readme
    assert scaffolder.generate_feature_content is templates.generate_feature_content


def test_generate_driver_script_standard() -> None:
    driver = templates.generate_driver_script("testapp", formal=False)
    assert driver.startswith("#!/usr/bin/env bash")
    assert "Verification driver stub template for testapp" in driver
    assert "uv run python" in driver
    assert "bun" in driver
    assert "TIMEOUT_SECONDS=60" in driver
    assert "doctor)" in driver
    assert "launch)" in driver
    assert "drive)" in driver
    assert "cleanup)" in driver
    assert "all)" in driver


def test_generate_driver_script_formal() -> None:
    driver = templates.generate_driver_script("testapp", formal=True)
    assert driver.startswith("#!/usr/bin/env bash")
    assert "Formal verification driver stub template for testapp" in driver
    assert "uv run python" in driver
    assert "bun" in driver
    assert "TIMEOUT_SECONDS=60" in driver


def test_generate_skill_content_standard() -> None:
    content = templates.generate_skill_content("testapp", "antigravity", formal=False)
    header, body = split_frontmatter(content)
    assert read_scalar(header, "name") == "verify-testapp"
    assert "antigravity" in read_scalar(header, "description")
    assert read_scalar(header, "disable-model-invocation") == "true"
    for sec in scaffolder.REQUIRED_SECTIONS:
        assert f"## {sec}" in body


def test_generate_skill_content_formal() -> None:
    content = templates.generate_skill_content("testapp", "codex", formal=True)
    header, body = split_frontmatter(content)
    assert read_scalar(header, "name") == "verify-testapp"
    assert "codex" in read_scalar(header, "description")
    assert read_scalar(header, "disable-model-invocation") == "true"
    for sec in scaffolder.REQUIRED_SECTIONS:
        assert f"## {sec}" in body


def test_generate_features_readme_and_content() -> None:
    readme_std = templates.generate_features_readme("my-app", formal=False)
    assert "Feature Map for my-app" in readme_std
    assert "core.md" in readme_std

    readme_formal = templates.generate_features_readme("my-app", formal=True)
    assert "Formal Feature Map for my-app" in readme_formal
    assert "formal-model.md" in readme_formal

    content_std = templates.generate_feature_content("my-app", formal=False)
    assert "Core Feature: my-app" in content_std

    content_formal = templates.generate_feature_content("my-app", formal=True)
    assert "Formal Invariant Property: my-app" in content_formal
