from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        load_script("verify-harness").verify_skills_frontmatter(tmp_path)


def test_verifier_allows_metadata_examples_in_body(tmp_path: Path) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text('---\nname: "demo" # skill name\n---\nExample\n```yaml\nmode: true\n```\n')
    load_script("verify-harness").verify_skills_frontmatter(tmp_path)


def test_adapter_normalizes_metadata_and_preserves_body() -> None:
    text = '---\nname: "Fresh Skill"\nmode: TRUE # Cursor\ndescription: Keep this text.\n---\n```yaml\nname: Poteto Mode\nmode: true\n```\n'
    expected = '---\nname: fresh-skill\ndescription: Keep this text.\n---\n```yaml\nname: Poteto Mode\nmode: true\n```\n'
    adapt = load_script("adapt-harness")
    assert adapt.transform(text, skill_name="fresh-skill") == expected
    assert adapt.transform(expected, skill_name="fresh-skill") == expected


def test_adapter_does_not_rewrite_metadata_in_other_documents() -> None:
    text = "name: Poteto Mode\nmode: true\n"
    assert load_script("adapt-harness").transform(text) == text


@pytest.mark.parametrize("field", ["name: demo", "mode: true"])
def test_adapter_rejects_selected_scalar_continuations(field: str) -> None:
    text = f"---\nname: demo\n{field}\n  suffix\n---\n" if field.startswith("mode") else f"---\n{field}\n  suffix\n---\n"
    with pytest.raises(ValueError, match="multiline"):
        load_script("adapt-harness").transform(text, skill_name="demo")


def test_adapter_preserves_unrelated_nested_metadata() -> None:
    text = "---\nname: demo\ndescription: |\n  Keep this text.\nmetadata:\n  category: tools\n---\n"
    assert load_script("adapt-harness").transform(text, skill_name="demo") == text


@pytest.mark.parametrize("key", ['"mode"', "'mode'", '"mo\\u0064e"'])
def test_adapter_removes_equivalent_quoted_mode_keys(key: str) -> None:
    text = f"---\nname: demo\n{key}: true\n---\nBody\n"
    assert load_script("adapt-harness").transform(text, skill_name="demo") == "---\nname: demo\n---\nBody\n"


def test_adapter_rejects_duplicate_equivalent_keys() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        load_script("adapt-harness").transform('---\nname: demo\n"name": other\n---\n', skill_name="demo")


def test_adapter_normalizes_quoted_name_key() -> None:
    text = '---\n"name": "Demo App"\n---\nBody\n'
    assert load_script("adapt-harness").transform(text, skill_name="demo-app") == "---\nname: demo-app\n---\nBody\n"


@pytest.mark.parametrize("name", ["demo", "'demo'", '"demo" # comment'])
def test_verifier_accepts_supported_name_scalars(tmp_path: Path, name: str) -> None:
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    load_script("verify-harness").verify_skills_frontmatter(tmp_path)


def test_adapter_traversal_checks_metadata_and_preserves_line_endings(tmp_path: Path, monkeypatch) -> None:
    adapt = load_script("adapt-harness")
    monkeypatch.setattr(adapt, "ROOT", tmp_path)
    skill = tmp_path / "skills" / "fresh-skill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_bytes(b"---\r\nname: Fresh Skill\r\nmode: true\r\n---\r\nmode: true\r\n")
    assert adapt.files_transform_would_change() == ["skills/fresh-skill/SKILL.md"]
    adapt.main()
    assert skill.read_bytes() == b"---\r\nname: fresh-skill\r\n---\r\nmode: true\r\n"
    assert adapt.files_transform_would_change() == []


def test_adapter_validates_all_headers_before_writing(tmp_path: Path, monkeypatch) -> None:
    adapt = load_script("adapt-harness")
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
