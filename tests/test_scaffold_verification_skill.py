from __future__ import annotations

import importlib.util
import pathlib
import sys
import subprocess
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


def cli(workspace: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--workspace", str(workspace), *args],
        cwd=workspace, capture_output=True, text=True, check=False,
    )


def file_bytes(target: pathlib.Path) -> dict[str, bytes]:
    return {str(p.relative_to(target)): p.read_bytes() for p in target.rglob("*") if p.is_file()}


@pytest.fixture
def draft(tmp_path: pathlib.Path) -> pathlib.Path:
    target = tmp_path / ".codex/skills/verify-demo"
    scaffold_mod.scaffold_skill(target, "demo", "codex")
    return target


@pytest.mark.parametrize("app", ["", "foo/bar", "../escape", "../../../../../escape", "Demo", "demo_app", "-demo", "demo-", "demo--app", "pstack", "demo\nname: injected"])
def test_invalid_app_rejected_before_writes(tmp_path, app):
    target = tmp_path / "scratch"
    with pytest.raises(ValueError):
        scaffold_mod.scaffold_skill(target, app, "codex")
    assert not target.exists()
    result = cli(tmp_path, "--host", "codex", "--app", app, "--write", "--target-dir", str(target))
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert not target.exists()
    result = cli(tmp_path, "--host", "codex", "--app", app, "--write")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("app", ["0", "notes2", "demo-app-2"])
def test_valid_kebab_names(tmp_path, app):
    target = tmp_path / "scratch"
    scaffold_mod.scaffold_skill(target, app, "grok")
    assert f"name: verify-{app}\n" in (target / "SKILL.md").read_text()
    assert scaffold_mod.check_skill(target) == []


@pytest.mark.parametrize("scratch_name", ["scratch", "verify-scratch", "Some explicit scratch_2"])
def test_arbitrary_explicit_scratch_directory_names(tmp_path, scratch_name):
    target = tmp_path / scratch_name
    target.mkdir()
    result = cli(tmp_path, "--app", "demo", "--write", "--target-dir", str(target))
    assert result.returncode == 0, result.stderr
    result = cli(tmp_path, "--check", "--target-dir", str(target))
    assert result.returncode == 0, result.stdout
    assert "runtime proof unassessed" in result.stdout


@pytest.mark.parametrize("conflict", ["rerun", "authored", "partial", "skill-symlink", "features-symlink", "target-file"])
def test_conflicting_target_preserves_all_bytes(tmp_path, conflict):
    target = tmp_path / "draft"
    outside = tmp_path / "authored.txt"
    outside.write_bytes(b"authored outside\x00\n")
    if conflict == "target-file":
        target.write_bytes(b"authored target\n")
    else:
        target.mkdir()
        if conflict == "rerun":
            scaffold_mod.scaffold_skill(target, "demo", "codex")
            (target / "SKILL.md").write_bytes(b"authored skill\n")
            (target / "features/README.md").write_bytes(b"authored map\n")
            (target / "features/core.md").write_bytes(b"authored recipe\n")
        elif conflict == "authored":
            (target / "notes.txt").write_bytes(b"authored notes\n")
        elif conflict == "partial":
            (target / "features").mkdir()
        elif conflict == "skill-symlink":
            (target / "SKILL.md").symlink_to(outside)
        else:
            (target / "features").symlink_to(tmp_path, target_is_directory=True)
    before = {str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")}
    originals = file_bytes(tmp_path)
    result = cli(tmp_path, "--app", "demo", "--write", "--target-dir", str(target))
    assert result.returncode == 2
    assert "Refusing" in result.stderr
    assert "Traceback" not in result.stderr
    assert {str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*")} == before
    assert file_bytes(tmp_path) == originals
    assert outside.read_bytes() == b"authored outside\x00\n"
    with pytest.raises(FileExistsError):
        scaffold_mod.scaffold_skill(target, "demo", "codex")


@pytest.mark.parametrize("kind", ["target", "dangling", "ancestor"])
def test_symlink_destinations_refused_without_following(tmp_path, kind):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "absent" if kind == "dangling" else real, target_is_directory=True)
    target = link / "new-draft" if kind == "ancestor" else link
    result = cli(tmp_path, "--app", "demo", "--write", "--target-dir", str(target))
    assert result.returncode == 2
    assert "symlink" in result.stderr
    assert "Traceback" not in result.stderr
    assert list(real.iterdir()) == []
    assert not (tmp_path / "absent").exists()
    assert link.is_symlink()


@pytest.mark.parametrize(("old", "new", "error"), [
    ("---\nname:", "--- name:", "frontmatter opening"),
    ("true\n---", "true\n--", "frontmatter closing"),
    ("name: verify-demo\n", "", "not kebab-case"),
    ("name: verify-demo\n", "name: Verify_demo\n", "not kebab-case"),
    ("name: verify-demo\n", "name: ordinary\n", "does not match directory"),
    ("name: verify-demo\n", "name: verify-other\n", "does not match directory"),
    ("name: verify-demo\n", "name: verify-demo\nname: verify-demo\n", "duplicate frontmatter"),
    ("name: verify-demo\n", "name: \"verify-demo'\n", "invalid quoted"),
    ("name: verify-demo\n", "name: verify-demo\n  continued\n", "multiline frontmatter"),
    ("description:", "unused-description:", "nonempty description"),
    ("description:", "description: 'other'\ndescription:", "duplicate frontmatter"),
    ("disable-model-invocation: true\n", "", "disable-model-invocation"),
    ("disable-model-invocation: true", "disable-model-invocation: false", "disable-model-invocation"),
    ("disable-model-invocation: true", "disable-model-invocation: true\ndisable-model-invocation: true", "duplicate frontmatter"),
    ("disable-model-invocation: true", "disable-model-invocation: true\n  continued", "multiline frontmatter"),
    ("## Cleanup", "## Removed", "Cleanup"),
])
def test_metadata_and_sections_are_structural_errors(draft, old, new, error):
    skill = draft / "SKILL.md"
    skill.write_text(skill.read_text().replace(old, new) + "\ndisable-model-invocation: true\n")
    assert any(error in message for message in scaffold_mod.check_skill(draft))
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 1
    assert error in result.stdout
    assert "Traceback" not in result.stderr


def test_existing_plugin_doctor_can_be_checked_and_listed(tmp_path):
    target = tmp_path / ".factory/skills/verify-pstack"
    scaffold_mod.scaffold_skill(target, "demo", "droid")
    skill = target / "SKILL.md"
    skill.write_text(skill.read_text().replace("verify-demo", "verify-pstack"))
    result = cli(tmp_path, "--host", "droid", "--app", "pstack", "--check")
    assert result.returncode == 0, result.stdout
    assert "runtime proof unassessed" in result.stdout
    assert cli(tmp_path, "--list").stdout.splitlines() == [
        "Found 1 verification skill(s):", "  .factory/skills/verify-pstack",
    ]


def test_unrelated_nested_metadata_allowed(draft):
    skill = draft / "SKILL.md"
    skill.write_text(skill.read_text().replace(
        "disable-model-invocation: true\n",
        "disable-model-invocation: true\nmetadata:\n  category: verification\n",
    ))
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 0, result.stdout
    assert "PASS: Structural validation" in result.stdout


def test_cli_read_value_error_exits_two_without_traceback(draft):
    (draft / "SKILL.md").write_bytes(b"\xff")
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("args", [["--write"], ["--check"]])
def test_cli_missing_required_arguments(tmp_path, args):
    result = cli(tmp_path, *args)
    assert result.returncode == 2
    assert "required" in result.stderr
    assert "Traceback" not in result.stderr
    assert list(tmp_path.iterdir()) == []
