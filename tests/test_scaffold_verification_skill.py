from __future__ import annotations

import importlib.util
import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "scaffold-verification-skill.py"

loader = importlib.util.spec_from_file_location("scaffold_verification_skill", SCRIPT_PATH)
assert loader is not None and loader.loader is not None
scaffold_mod = importlib.util.module_from_spec(loader)
loader.loader.exec_module(scaffold_mod)

check_skill = scaffold_mod.check_skill
detect_host = scaffold_mod.detect_host
get_skill_dir = scaffold_mod.get_skill_dir
list_verification_skills = scaffold_mod.list_verification_skills
scaffold_skill = scaffold_mod.scaffold_skill


def test_detect_host_from_workspace_markers(tmp_path: pathlib.Path) -> None:
    # Empty workspace defaults to grok
    assert detect_host(tmp_path) == "grok"

    # Antigravity marker
    (tmp_path / ".agents").mkdir()
    assert detect_host(tmp_path) == "antigravity"

    # Clean and test codex marker
    (tmp_path / ".agents").rmdir()
    (tmp_path / ".codex").mkdir()
    assert detect_host(tmp_path) == "codex"


def test_scaffold_and_check_across_all_five_hosts(tmp_path: pathlib.Path) -> None:
    hosts = ["grok", "codex", "omp", "opencode", "antigravity"]
    for host in hosts:
        target = get_skill_dir(tmp_path, host, "demo-app")
        scaffold_skill(target, "demo-app", host)
        assert target.is_dir()

        errors = check_skill(target)
        assert errors == [], f"Validation failed for host {host}: {errors}"

        # Verify SKILL.md contents
        skill_text = (target / "SKILL.md").read_text(encoding="utf-8")
        assert "name: verify-demo-app" in skill_text
        assert "## Launch" in skill_text
        assert "## Doctor" in skill_text
        assert "## Drive" in skill_text
        assert "## Proof bar" in skill_text
        assert "## Evidence" in skill_text
        assert "## Cleanup" in skill_text

        # Verify features
        features_readme = (target / "features" / "README.md").read_text(encoding="utf-8")
        assert "## Full sweep" in features_readme
        assert (target / "features" / "core.md").is_file()


def test_check_skill_detects_missing_sections(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "verify-bad"
    scaffold_skill(target, "bad", "grok")

    # Corrupt SKILL.md by removing Cleanup
    skill_file = target / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    content = content.replace("## Cleanup", "## RemovedSection")
    skill_file.write_text(content, encoding="utf-8")

    errors = check_skill(target)
    assert any("Cleanup" in err for err in errors)


def test_check_skill_detects_missing_features(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "verify-nofeat"
    scaffold_skill(target, "nofeat", "antigravity")

    # Remove core.md
    (target / "features" / "core.md").unlink()

    errors = check_skill(target)
    assert any("at least one feature markdown file" in err for err in errors)


def test_list_verification_skills(tmp_path: pathlib.Path) -> None:
    s1 = get_skill_dir(tmp_path, "grok", "app-one")
    scaffold_skill(s1, "app-one", "grok")

    s2 = get_skill_dir(tmp_path, "antigravity", "app-two")
    scaffold_skill(s2, "app-two", "antigravity")

    found = list_verification_skills(tmp_path)
    assert len(found) == 2
    assert s1 in found
    assert s2 in found
