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


def test_discover_all_86_skills() -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    records = discover_skills_inventory(ROOT)
    assert len(records) == 86

    canonical = [r for r in records if r.root_rel == "skills"]
    assert len(canonical) == 67

    automations = [r for r in records if r.root_rel.startswith("automations/")]
    assert len(automations) == 5

    host_specific = [r for r in records if r.root_rel.startswith(".")]
    assert len(host_specific) == 14


def test_all_86_skills_conform_to_frontmatter_contract() -> None:
    from scripts.skill_frontmatter import discover_skills_inventory

    records = discover_skills_inventory(ROOT)
    assert len(records) == 86

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
    from scripts.skill_frontmatter import dump_frontmatter_yaml, project_spec_frontmatter, validate_skill_frontmatter

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

    yaml_text = dump_frontmatter_yaml(projected)
    validated = validate_skill_frontmatter(
        yaml_text,
        expected_dir="projected-demo",
        strict_spec=True,
    )
    assert validated["name"] == "projected-demo"

    npx_bin = shutil.which("npx")
    if npx_bin:
        sdir = tmp_path / "projected-demo"
        sdir.mkdir()
        (sdir / "SKILL.md").write_text(f"{yaml_text}# Projected Demo Body\n")
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


def test_validate_skill_script_layout_valid(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_script_layout

    skill_dir = tmp_path / "sample-skill"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "runner.py").write_text("print('hello')\n")
    (scripts_dir / "helper.sh").write_text("#!/bin/sh\nexit 0\n")
    (skill_dir / "SKILL.md").write_text("---\nname: sample-skill\ndescription: Test.\n---\n")

    violations = validate_skill_script_layout(skill_dir)
    assert violations == []


def test_validate_skill_script_layout_misplaced_script(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_script_layout

    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "loose_helper.py").write_text("print('bad')\n")
    (skill_dir / "SKILL.md").write_text("---\nname: bad-skill\ndescription: Test.\n---\n")

    with pytest.raises(ValueError, match="executable helpers must reside under scripts/"):
        validate_skill_script_layout(skill_dir)


def test_validate_skill_script_layout_misplaced_subfolder(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_script_layout

    skill_dir = tmp_path / "bad-subfolder"
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True)
    (ref_dir / "script.sh").write_text("#!/bin/sh\n")

    with pytest.raises(ValueError, match="executable helpers must reside under scripts/"):
        validate_skill_script_layout(skill_dir)


def test_validate_skill_script_layout_executable_binary(tmp_path: Path) -> None:
    import os
    import stat
    from scripts.skill_frontmatter import validate_skill_script_layout

    skill_dir = tmp_path / "binary-skill"
    skill_dir.mkdir(parents=True)
    loose_bin = skill_dir / "custom-tool"
    loose_bin.write_text("#!/bin/sh\necho hi\n")
    os.chmod(loose_bin, loose_bin.stat().st_mode | stat.S_IXUSR)

    with pytest.raises(ValueError, match="executable helpers must reside under scripts/"):
        validate_skill_script_layout(skill_dir)


def test_validate_skill_script_layout_ignores_vendor(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_script_layout

    skill_dir = tmp_path / "vendor-skill"
    vendor_dir = skill_dir / "scripts" / "node_modules" / "some-lib"
    vendor_dir.mkdir(parents=True)
    (vendor_dir / "index.js").write_text("module.exports = {};\n")

    violations = validate_skill_script_layout(skill_dir)
    assert violations == []


def test_validate_skill_links_valid(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_links

    repo_root = tmp_path
    skill_dir = repo_root / "skills" / "demo-skill"
    scripts_dir = skill_dir / "scripts"
    refs_dir = skill_dir / "references"
    scripts_dir.mkdir(parents=True)
    refs_dir.mkdir(parents=True)

    (scripts_dir / "driver.sh").write_text("#!/bin/sh\n")
    (refs_dir / "guide.md").write_text("# Guide\n")

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: demo-skill\ndescription: Test.\n---\n"
        "# Demo\n\n"
        "See [Guide](references/guide.md) and [Driver](scripts/driver.sh).\n"
        "Anchor link: [Section](#demo).\n"
        "External link: [Site](https://example.com).\n"
    )

    verified = validate_skill_links(skill_dir, repo_root=repo_root)
    assert len(verified) == 2


def test_validate_skill_links_broken_relative(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_links

    repo_root = tmp_path
    skill_dir = repo_root / "skills" / "broken-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: broken-skill\ndescription: Test.\n---\n"
        "Check [Missing](scripts/missing.py).\n"
    )

    with pytest.raises(ValueError, match="broken relative link"):
        validate_skill_links(skill_dir, repo_root=repo_root)


def test_validate_skill_links_cross_skill(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_links

    repo_root = tmp_path
    skill_a = repo_root / "skills" / "skill-a"
    skill_b = repo_root / "skills" / "skill-b"
    skill_a.mkdir(parents=True)
    skill_b.mkdir(parents=True)

    (skill_b / "SKILL.md").write_text("---\nname: skill-b\ndescription: Skill B.\n---\n")
    (skill_a / "SKILL.md").write_text(
        "---\nname: skill-a\ndescription: Skill A.\n---\n"
        "Check [B](../skill-b/SKILL.md).\n"
    )

    verified = validate_skill_links(skill_a, repo_root=repo_root)
    assert len(verified) == 1

    (skill_a / "SKILL.md").write_text(
        "---\nname: skill-a\ndescription: Skill A.\n---\n"
        "Check [C](../skill-c/SKILL.md).\n"
    )
    with pytest.raises(ValueError, match="broken relative link"):
        validate_skill_links(skill_a, repo_root=repo_root)


def test_validate_skill_links_symlink_escape(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_links

    repo_root = tmp_path / "repo"
    skill_dir = repo_root / "skills" / "escape-skill"
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(
        "---\nname: escape-skill\ndescription: Escape.\n---\n"
        "Escape link: [Outside](../../../../etc/passwd).\n"
    )

    with pytest.raises(ValueError, match="escapes repository boundary"):
        validate_skill_links(skill_dir, repo_root=repo_root)


def test_validate_skill_links_code_blocks_and_allowlist(tmp_path: Path) -> None:
    from scripts.skill_frontmatter import validate_skill_links

    repo_root = tmp_path
    skill_dir = repo_root / "skills" / "template-skill"
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(
        "---\nname: template-skill\ndescription: Template.\n---\n"
        "Example citation: [PR #123](url).\n"
        "Template param: [Field]({param_name}).\n"
        "```markdown\n[Fake Link](nonexistent/fake.md)\n```\n"
    )

    verified = validate_skill_links(skill_dir, repo_root=repo_root)
    assert verified == []


def test_verify_all_skills_policy_live_repo() -> None:
    from scripts.skill_frontmatter import verify_all_skills_policy

    verify_all_skills_policy(ROOT)


def test_verify_skills_policy_harness_integration() -> None:
    from scripts.verify_harness import verify_skills_policy

    verify_skills_policy(ROOT)

@pytest.mark.parametrize(
    ("optional_fields", "reason"),
    [
        ("compatibility:", "1-500"),
        ("compatibility: " + "x" * 501, "1-500"),
        ("allowed-tools: [Read, Bash(git:*)]", "space-separated string"),
        ("metadata:\n  enabled: true", "string values"),
        ("metadata: {enabled: true}", "string values"),
        ("metadata:\n  author: first\n  author: second", "duplicate"),
        ("metadata: {author: first, author: second}", "duplicate"),
    ],
)
def test_reference_rejects_invalid_optional_fields(optional_fields: str, reason: str) -> None:
    from scripts.skill_frontmatter import validate_skill_frontmatter

    header = f"---\nname: demo\ndescription: Example skill.\n{optional_fields}\n---\n"
    with pytest.raises(ValueError, match=reason):
        validate_skill_frontmatter(header, expected_dir="demo", strict_spec=True)


def test_reference_accepts_valid_optional_fields_and_native_list_remains_supported() -> None:
    from scripts.skill_frontmatter import validate_skill_frontmatter

    header = (
        "---\nname: demo\ndescription: Example skill.\n"
        "compatibility: POSIX tools required\n"
        "allowed-tools: Bash(git:*) Read\n"
        "metadata:\n  author: pstack\n"
        "---\n"
    )
    strict = validate_skill_frontmatter(header, expected_dir="demo", strict_spec=True)
    assert strict["metadata"] == {"author": "pstack"}
    assert strict["allowed-tools"] == "Bash(git:*) Read"

    native = (
        "---\nname: demo\ndescription: Example skill.\n"
        "allowed-tools: [Read, Bash]\n---\n"
    )
    assert validate_skill_frontmatter(native, expected_dir="demo")["allowed-tools"] == ["Read", "Bash"]
