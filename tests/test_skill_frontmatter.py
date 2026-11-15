from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.adapt_harness as ah
import scripts.verify_harness as vh


@pytest.mark.parametrize("text", [
    "---garbage\nname: demo\n---\n",
    "---\nname: demo\n# no closing delimiter\n",
    "---\nname: wrong\nname: demo\n---\n",
    "---\nname: demo\nmode: true # Cursor metadata\n---\n",
    "---\nname: demo\nmode: TRUE\n---\n",
    "---\nname: demo\n  suffix\n---\n",
    '---\nname: demo\n"mode": true\n---\n',
    '---\nname: demo\n"name": other\n---\n',
    '---\nname: demo\n"mo\\u0064e": true\n---\n',
])
def test_verifier_rejects_invalid_frontmatter(tmp_path: Path, text: str) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text(text)
    with pytest.raises(SystemExit):
        vh.verify_skills_frontmatter(tmp_path)


def test_verifier_allows_metadata_examples_in_body(tmp_path: Path) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text('---\nname: "demo" # skill name\ndescription: Sample verification skill.\n---\nExample\n```yaml\nmode: true\n```\n')
    vh.verify_skills_frontmatter(tmp_path)


def test_adapter_normalizes_metadata_and_preserves_body() -> None:
    text = '---\nname: "Fresh Skill"\nmode: TRUE # Cursor\ndescription: Keep this text.\n---\n```yaml\nname: Poteto Mode\nmode: true\n```\n'
    expected = '---\nname: fresh-skill\ndescription: Keep this text.\n---\n```yaml\nname: Poteto Mode\nmode: true\n```\n'
    adapt = ah
    assert adapt.transform(text, skill_name="fresh-skill") == expected
    assert adapt.transform(expected, skill_name="fresh-skill") == expected


def test_adapter_does_not_rewrite_metadata_in_other_documents() -> None:
    text = "name: Poteto Mode\nmode: true\n"
    assert ah.transform(text) == text


@pytest.mark.parametrize("field", ["name: demo", "mode: true"])
def test_adapter_rejects_selected_scalar_continuations(field: str) -> None:
    text = f"---\nname: demo\n{field}\n  suffix\n---\n" if field.startswith("mode") else f"---\n{field}\n  suffix\n---\n"
    with pytest.raises(ValueError, match="multiline"):
        ah.transform(text, skill_name="demo")


def test_adapter_preserves_unrelated_nested_metadata() -> None:
    text = "---\nname: demo\ndescription: |\n  Keep this text.\nmetadata:\n  category: tools\n---\n"
    assert ah.transform(text, skill_name="demo") == text


@pytest.mark.parametrize("key", ['"mode"', "'mode'", '"mo\\u0064e"'])
def test_adapter_removes_equivalent_quoted_mode_keys(key: str) -> None:
    text = f"---\nname: demo\n{key}: true\n---\nBody\n"
    assert ah.transform(text, skill_name="demo") == "---\nname: demo\n---\nBody\n"


def test_adapter_rejects_duplicate_equivalent_keys() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        ah.transform('---\nname: demo\n"name": other\n---\n', skill_name="demo")


def test_adapter_normalizes_quoted_name_key() -> None:
    text = '---\n"name": "Demo App"\n---\nBody\n'
    assert ah.transform(text, skill_name="demo-app") == "---\nname: demo-app\n---\nBody\n"


@pytest.mark.parametrize("name", ["demo", "'demo'", '"demo" # comment'])
def test_verifier_accepts_supported_name_scalars(tmp_path: Path, name: str) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Sample verification skill.\n---\n")
    vh.verify_skills_frontmatter(tmp_path)


def test_adapter_traversal_checks_metadata_and_preserves_line_endings(tmp_path: Path, monkeypatch) -> None:
    adapt = ah
    monkeypatch.setattr(adapt, "ROOT", tmp_path)
    skill = tmp_path / "skills" / "fresh-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_bytes(b"---\r\nname: Fresh Skill\r\nmode: true\r\n---\r\nmode: true\r\n")
    assert adapt.files_transform_would_change() == ["skills/fresh-skill/SKILL.md"]
    adapt.main()
    assert skill.read_bytes() == b"---\r\nname: fresh-skill\r\n---\r\nmode: true\r\n"
    assert adapt.files_transform_would_change() == []


def test_adapter_validates_all_headers_before_writing(tmp_path: Path, monkeypatch) -> None:
    adapt = ah
    monkeypatch.setattr(adapt, "ROOT", tmp_path)
    valid = tmp_path / "skills" / "fresh-skill" / "SKILL.md"
    valid.parent.mkdir(parents=True)
    original = "---\nname: Fresh Skill\n---\n"
    valid.write_text(original)
    invalid = tmp_path / "skills" / "bad" / "SKILL.md"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("---\nname: bad\n")
    with pytest.raises(ValueError):
        adapt.main()
    assert valid.read_text() == original


def test_openspec_git_discipline_and_template_configurations() -> None:
    import json

    opencode_json = ROOT / "opencode.json"
    assert opencode_json.is_file(), "opencode.json must exist at repo root"
    config = json.loads(opencode_json.read_text(encoding="utf-8"))
    assert config.get("$schema") == "https://opencode.ai/config.json"

    agents_md = ROOT / "AGENTS.md"
    assert agents_md.is_file(), "AGENTS.md must exist at repo root"
    content = agents_md.read_text(encoding="utf-8")
    assert "openspec-git-discipline" in content

    for skill_path in [
        ROOT / ".agents" / "skills" / "openspec-git-discipline" / "SKILL.md",
        ROOT / ".opencode" / "skills" / "openspec-git-discipline" / "SKILL.md",
    ]:
        assert skill_path.is_file(), f"{skill_path} must exist"
        text = skill_path.read_text(encoding="utf-8")
        assert text.startswith("---\nname: openspec-git-discipline\n")


@pytest.mark.parametrize("description", ["", " ", "x" * 1025])
def test_verifier_rejects_invalid_description(tmp_path: Path, description: str) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        f"---\nname: demo\ndescription: {description}\n---\n"
    )
    with pytest.raises(SystemExit):
        vh.verify_skills_frontmatter(tmp_path)


def test_verifier_rejects_missing_description(tmp_path: Path) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: demo\n---\n")
    with pytest.raises(SystemExit):
        vh.verify_skills_frontmatter(tmp_path)


def test_name_validator_rejects_overlong_name() -> None:
    from scripts.skill_frontmatter import validate_skill_name

    with pytest.raises(ValueError, match="64"):
        validate_skill_name("a" * 65)


def test_discover_all_84_skills() -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    records = discover_skills_inventory(ROOT)
    assert len(records) == 84

    canonical = [r for r in records if r.root_rel == "skills"]
    assert len(canonical) == 67

    automations = [r for r in records if r.root_rel.startswith("automations/")]
    assert len(automations) == 5

    host_specific = [r for r in records if r.root_rel.startswith(".")]
    assert len(host_specific) == 12


def test_all_84_skills_conform_to_frontmatter_contract() -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    records = discover_skills_inventory(ROOT)
    assert len(records) == 84

    for record in records:
        assert record.frontmatter["name"] == record.directory.name
        desc = record.frontmatter["description"]
        assert isinstance(desc, str)
        assert 1 <= len(desc.strip()) <= 1024


def test_inventory_detects_directory_missing_skill_md(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    sdir = tmp_path / "skills" / "empty-skill"
    sdir.mkdir(parents=True)
    with pytest.raises(ValueError, match="missing SKILL.md"):
        discover_skills_inventory(tmp_path)


def test_inventory_detects_duplicate_skill_in_same_scope(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    s1 = tmp_path / "skills" / "alpha"
    s1.mkdir(parents=True)
    (s1 / "SKILL.md").write_text("---\nname: alpha\ndescription: First alpha skill.\n---\n")

    s2 = tmp_path / "skills" / "alpha-clone"
    s2.mkdir(parents=True)
    (s2 / "SKILL.md").write_text("---\nname: alpha\ndescription: Duplicate alpha skill.\n---\n")

    with pytest.raises(ValueError, match="does not match directory name"):
        discover_skills_inventory(tmp_path)


@pytest.mark.parametrize("payload,error_match", [
    ("---\nname: \"unclosed quote\n---\n", "invalid YAML"),
    ("---\nname: NotKebab\ndescription: Valid description.\n---\n", "not kebab-case"),
    ("---\nname: wrong-name\ndescription: Valid description.\n---\n", "does not match directory"),
    ("---\nname: demo\ndescription: Valid description.\nmode: true\n---\n", "Cursor-only"),
    ("---\nname: demo\ndescription: Valid description.\ncompatibility: 123\n---\n", "compatibility must be a string"),
    ("---\nname: demo\ndescription: Valid description.\nlicense: 456\n---\n", "license must be a string"),
    ("---\nname: demo\ndescription: Valid description.\nallowed-tools: {bad: true}\n---\n", "allowed-tools must be a string"),
    ("---\nname: demo\ndescription: Valid description.\nmetadata: [not, a, dict]\n---\n", "metadata must be a mapping"),
    ("---\nname: demo\ndescription: Valid description.\ndisable-model-invocation: 'yes'\n---\n", "disable-model-invocation must be a boolean"),
    ("---\nname: demo\ndescription: Valid description.\nunknown-field: true\n---\n", "unexpected frontmatter fields"),
])
def test_validate_skill_frontmatter_negative_controls(payload: str, error_match: str) -> None:
    from scripts.skill_frontmatter import validate_skill_frontmatter

    with pytest.raises(ValueError, match=error_match):
        validate_skill_frontmatter(payload, expected_dir="demo")


def test_project_spec_frontmatter_and_reference_validation(tmp_path: Path) -> None:
    import shutil
    import subprocess
    import yaml
    from scripts.skill_frontmatter import project_spec_frontmatter, validate_skill_frontmatter

    native_frontmatter = {
        "name": "projected-demo",
        "description": "Projected demo skill description.",
        "compatibility": "All POSIX platforms",
        "license": "MIT",
        "disable-model-invocation": True,
        "color": "#123456",
        "reminder": "Always verify proofs.",
    }
    projected = project_spec_frontmatter(native_frontmatter)
    assert projected["name"] == "projected-demo"
    assert projected["description"] == "Projected demo skill description."
    assert projected["compatibility"] == "All POSIX platforms"
    assert projected["license"] == "MIT"
    assert projected["metadata"]["disable-model-invocation"] == "true"
    assert projected["metadata"]["color"] == "#123456"
    assert projected["metadata"]["reminder"] == "Always verify proofs."

    validated = validate_skill_frontmatter(
        f"---\n{yaml.dump(projected)}---\n",
        expected_dir="projected-demo",
        strict_spec=True,
    )
    assert validated["name"] == "projected-demo"

    npx_bin = shutil.which("npx")
    if npx_bin:
        sdir = tmp_path / "projected-demo"
        sdir.mkdir()
        (sdir / "SKILL.md").write_text(f"---\n{yaml.dump(projected)}---\n# Projected Demo Body\n")
        proc = subprocess.run([npx_bin, "--yes", "skills-ref@0.1.5", "validate", str(sdir)], capture_output=True, text=True)
        assert proc.returncode == 0, f"skills-ref validation failed: {proc.stderr}"


def test_host_package_projections_skill_drift() -> None:
    import json
    from scripts.skill_frontmatter import discover_skills_inventory

    records = discover_skills_inventory(ROOT)
    known_skill_names = {r.name for r in records}

    pstack_package_file = ROOT / "pstack.package.json"
    assert pstack_package_file.is_file()
    pkg_data = json.loads(pstack_package_file.read_text(encoding="utf-8"))
    skills_root = pkg_data.get("skills_root", "skills")
    assert (ROOT / skills_root).is_dir()

    antigravity_plugin = ROOT / ".antigravity-plugin" / "plugin.json"
    if antigravity_plugin.is_file():
        ag_data = json.loads(antigravity_plugin.read_text(encoding="utf-8"))
        assert ag_data.get("skills") in ["./skills/", "./skills", "skills", ["./skills/"], ["./skills"]]

