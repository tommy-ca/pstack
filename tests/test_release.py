"""Release tagging is grok plugin tag locally and gh release on v* tags."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_script_tags_without_force() -> None:
    script = (ROOT / "scripts/release.sh").read_text(encoding="utf-8")
    assert "grok plugin validate" in script
    assert "grok plugin tag --push" in script
    assert "--force" not in script


def test_github_release_workflow_on_version_tags() -> None:
    wf = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "v*" in wf
    assert "gh release create" in wf
    assert "grok plugin tag" not in wf
    assert "contents: write" in wf


def test_natives_page_names_plugin_tag() -> None:
    natives = (ROOT / "docs/guide/13-grok-natives.md").read_text(encoding="utf-8")
    assert "grok plugin tag" in natives
    assert "wait-for-release" not in natives
    assert "still waits" not in natives


if __name__ == "__main__":
    test_release_script_tags_without_force()
    test_github_release_workflow_on_version_tags()
    test_natives_page_names_plugin_tag()
    print("PASS tests/test_release.py")
