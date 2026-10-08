from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "scaffold-verification-skill.py"
loader = importlib.util.spec_from_file_location("scaffold_verification_skill", SCRIPT_PATH)
assert loader is not None and loader.loader is not None
scaffold_mod = importlib.util.module_from_spec(loader)
loader.loader.exec_module(scaffold_mod)

HOST_CASES = [
    ("grok", ".grok/skills/verify-demo-app"),
    ("codex", ".codex/skills/verify-demo-app"),
    ("omp", ".omp/skills/verify-demo-app"),
    ("opencode", ".opencode/skills/verify-demo-app"),
    ("antigravity", ".agents/skills/verify-demo-app"),
    ("droid", ".factory/skills/verify-demo-app"),
]
FEATURE = """# Core behavior

## Sub-features
Start and exit.

## How to get to it (user POV)
Run the CLI.

## Driving it with CLI
Run `demo --help` and observe usage and exit code 0.

## Gotchas
Use the built executable.
"""
NUMBERED_MAP = """# Map

## Full sweep
1. `./core.md`
2. `search.md`

## Features
- [Core](core.md)
- [Search](./search.md)
"""
LINK_MAP = """# Map

## Full sweep
Walk Features top to bottom, first core, then search.

## Features
- [Core](./core.md)
- [Search](search.md)
"""


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


@pytest.mark.parametrize(("host", "relative"), HOST_CASES)
def test_scaffold_check_and_list_across_all_six_hosts(tmp_path, host, relative):
    assert {h for h, _ in HOST_CASES} == set(scaffold_mod.DEFAULT_SKILLS_DIRS)
    result = cli(tmp_path, "--host", host, "--app", "demo-app", "--write")
    assert result.returncode == 0, result.stderr
    assert "Draft scaffold" in result.stdout
    assert "requires tailoring and runtime proof" in result.stdout
    target = tmp_path / relative
    assert set(file_bytes(target)) == {"SKILL.md", "features/README.md", "features/core.md", "scripts/driver.sh"}
    assert (target / "scripts/driver.sh").stat().st_mode & 0o111
    assert "name: verify-demo-app\n" in (target / "SKILL.md").read_text()
    result = cli(tmp_path, "--host", host, "--app", "demo-app", "--check")
    assert result.returncode == 0, result.stdout
    assert "PASS: Structural validation" in result.stdout
    assert "runtime proof unassessed" in result.stdout
    result = cli(tmp_path, "--list")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["Found 1 verification skill(s):", f"  {relative}"]


@pytest.mark.parametrize(("host", "relative"), HOST_CASES)
def test_detect_host_from_each_marker(tmp_path, host, relative):
    assert scaffold_mod.detect_host(tmp_path) == "grok"
    (tmp_path / pathlib.Path(relative).parts[0]).mkdir()
    assert scaffold_mod.detect_host(tmp_path) == host


def test_droid_detection_and_explicit_host_precedence(tmp_path):
    (tmp_path / ".factory").mkdir()
    result = cli(tmp_path, "--app", "demo-app", "--write")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".factory/skills/verify-demo-app/SKILL.md").is_file()
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".codex").mkdir()
    assert scaffold_mod.detect_host(tmp_path) == "antigravity"
    result = cli(tmp_path, "--host", "codex", "--app", "demo-app", "--write")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".codex/skills/verify-demo-app/SKILL.md").is_file()
    assert not (tmp_path / ".agents/skills").exists()
    result = cli(tmp_path, "--list")
    assert result.returncode == 0
    assert set(result.stdout.splitlines()[1:]) == {
        "  .factory/skills/verify-demo-app", "  .codex/skills/verify-demo-app",
    }


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


@pytest.mark.parametrize("readme", [NUMBERED_MAP, LINK_MAP])
def test_both_documented_ordered_map_forms(draft, readme):
    (draft / "features/README.md").write_text(readme)
    (draft / "features/core.md").write_text(FEATURE)
    (draft / "features/search.md").write_text(FEATURE.replace("Core", "Search"))
    assert scaffold_mod.check_skill(draft) == []
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 0
    assert "PASS: Structural validation" in result.stdout


@pytest.mark.parametrize(("readme", "error"), [
    ("## Full sweep\n\n", "nonempty ordered"),
    ("## Full sweep\n\n## Features\n- [Core](core.md)\n", "prose directing"),
    ("## Features\n- [Core](core.md)\n", "missing '## Full sweep'"),
    ("## Full sweep\n1. `missing.md`\n", "Missing regular feature"),
    ("## Full sweep\n1. `core.md`\n2. `./core.md`\n", "Duplicate Full sweep"),
    ("## Full sweep\nSee Features.\n## Features\n- [Core](core.md)\n- [Again](./core.md)\n", "Duplicate Features"),
    ("## Full sweep\n1. `core.md`\n## Features\n- [Other](missing.md)\n", "references disagree"),
    ("## Full sweep\n1. `../core.md`\n", "must stay inside features/"),
    ("## Full sweep\n1. `sub/core.md`\n", "must stay inside features/"),
    ("## Full sweep\n1. `/tmp/core.md`\n", "must stay inside features/"),
    ("## Full sweep\n1. `README.md`\n", "must stay inside features/"),
    ("## Full sweep\n1. `core.md`\n## Features\n- [Other](../core.md)\n", "must stay inside features/"),
    ("## Full sweep\n1. `core.md`\n## Full sweep\n1. `core.md`\n", "duplicate sections"),
])
def test_invalid_maps_report_structural_failure(draft, readme, error):
    (draft / "features/README.md").write_text(readme)
    assert any(error in message for message in scaffold_mod.check_skill(draft))
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 1
    assert error in result.stdout


def test_unlisted_sibling_feature_rejected(draft):
    (draft / "features/extra.md").write_text(FEATURE)
    assert "Unlisted feature in Full sweep: extra.md" in scaffold_mod.check_skill(draft)


@pytest.mark.parametrize("kind", ["missing", "directory", "outside-symlink", "inside-symlink", "dangling-symlink"])
def test_feature_reference_requires_actual_regular_sibling(draft, kind):
    core = draft / "features/core.md"
    core.unlink()
    if kind == "directory":
        core.mkdir()
    elif kind == "outside-symlink":
        outside = draft / "outside.md"
        outside.write_text(FEATURE)
        core.symlink_to(outside)
    elif kind == "inside-symlink":
        other = draft / "features/other.md"
        other.write_text(FEATURE)
        core.symlink_to(other)
    elif kind == "dangling-symlink":
        core.symlink_to(draft / "absent.md")
    assert any("Missing regular feature" in message for message in scaffold_mod.check_skill(draft))


@pytest.mark.parametrize("relative", ["features", "features/README.md"])
def test_feature_map_symlinks_rejected(draft, relative):
    path = draft / relative
    original = path.with_name(path.name + "-original")
    path.rename(original)
    path.symlink_to(original, target_is_directory=original.is_dir())
    result = cli(draft.parent, "--check", "--target-dir", str(draft))
    assert result.returncode == 1
    assert "Missing regular features/" in result.stdout


@pytest.mark.parametrize("feature", [
    "# Core\n",
    FEATURE.replace("## Driving it with CLI", "## Driving it with"),
    FEATURE.replace("## Driving it with CLI", "## Driving it with   "),
    FEATURE.replace("## Sub-features", "## Gotchas").replace("## Gotchas\nUse", "## Sub-features\nUse"),
    FEATURE.replace("## Gotchas", "## Unknown"),
    FEATURE + "\n## Extra\n",
])
def test_feature_requires_exactly_four_ordered_sections(draft, feature):
    (draft / "features/core.md").write_text(feature)
    assert any("four feature sections in order" in message for message in scaffold_mod.check_skill(draft))


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


def test_scaffold_audit_mode(tmp_path):
    result = cli(tmp_path, "--audit")
    assert result.returncode == 0
    assert "No verification skills found" in result.stdout

    cli(tmp_path, "--host", "grok", "--app", "app1", "--write")
    cli(tmp_path, "--host", "droid", "--app", "app2", "--write")
    result = cli(tmp_path, "--audit")
    assert result.returncode == 0
    assert "PASS: .grok/skills/verify-app1" in result.stdout
    assert "PASS: .factory/skills/verify-app2" in result.stdout

    (tmp_path / ".grok/skills/verify-app1/SKILL.md").unlink()
    result = cli(tmp_path, "--audit")
    assert result.returncode == 1
    assert "FAIL: .grok/skills/verify-app1" in result.stdout
