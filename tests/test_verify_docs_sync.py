from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OWNED_MAPS = frozenset(
    {
        "leftover-scanner.md",
        "upstream-pin.md",
        "upstream-recipe.md",
        "refresh-hygiene.md",
        "release-tag.md",
    }
)
EDITH_MAPS = frozenset(
    {
        "plugin-install-enable.md",
        "herdr-workspace.md",
        "live-tool-ids.md",
        "setup-pstack.md",
        "poteto-investigation.md",
        "poteto-feature.md",
        "independent-verifier.md",
        "loop-scheduler.md",
    }
)
PLANES = ("Application plane", "Plugin plane", "Ship plane")


def _h2s(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def _load_scanner():
    path = ROOT / "scripts" / "verify-harness.py"
    spec = importlib.util.spec_from_file_location("verify_harness_docs_sync", path)
    assert spec is not None and spec.loader is not None, path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_live_specs_count_twenty_three_principles() -> None:
    principles = (
        ROOT / "openspec" / "specs" / "pstack-principles" / "spec.md"
    ).read_text(encoding="utf-8")
    port = (
        ROOT / "openspec" / "specs" / "pstack-reference-port" / "spec.md"
    ).read_text(encoding="utf-8")
    assert "Twenty-three principle skills" in principles
    assert "MUST ship 23" in principles
    assert "principles: 23" in principles
    assert "Twenty-one principle skills" not in principles
    assert "principles: 21" not in principles
    assert "steer with 23 principle names" in port
    assert "the page names 23 principles" in port
    assert "steer with 21 principle names" not in port
    assert "the page names 21 principles" not in port


def test_readme_lists_slash_verify_pstack() -> None:
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "[`/verify-pstack`](./.grok/skills/verify-pstack/SKILL.md)" in text


def test_guide_06_is_three_planes() -> None:
    path = ROOT / "docs" / "guide" / "06-verify-and-ship.md"
    text = path.read_text(encoding="utf-8")
    heads = _h2s(text)
    for name in PLANES:
        assert f"## {name}" in text, name
    positions = [heads.index(name) for name in PLANES]
    assert positions == sorted(positions), heads
    assert "three planes" in text
    app, plugin, ship = (text.split(f"## {name}", 1)[1] for name in PLANES)
    app = app.split("## ", 1)[0]
    plugin = plugin.split("## ", 1)[0]
    ship = ship.split("## ", 1)[0]
    assert ".grok/skills/verify-<app>/" in app
    assert "/create-verification-skill" in app
    assert ".grok/skills/verify-pstack/" in plugin
    assert "verify.py doctor" in plugin
    assert "verify.py run" in plugin
    assert "leftover" in plugin.lower()
    assert "Plugin doctor lives at `.grok/skills/verify-pstack/`" in plugin
    assert "Do not ship it under `skills/`." in plugin
    assert "Do not write `~/.grok/skills`" in plugin
    assert "Do not write `.grok/skills/verify-pstack`" not in plugin
    assert "`monitor`" in ship
    assert "bundled watcher" not in text
    assert ".cursor/skills" not in text
    assert ".grok/skills/verify-" in text


def test_guide_01_plugin_versus_app() -> None:
    text = (ROOT / "docs" / "guide" / "01-setup.md").read_text(encoding="utf-8")
    assert ".grok/skills/verify-pstack/" in text
    assert ".grok/skills/verify-<app>/" in text
    assert "Plugin doctor lives at `.grok/skills/verify-pstack/`" in text
    assert "Do not ship it under `skills/`." in text
    assert "Do not write `~/.grok/skills`" in text
    assert "Do not generate `.grok/skills/verify-pstack`" not in text
    assert "writes `.grok/skills/verify-<app>/`" in text
    assert "Do not name an app skill `verify-pstack`" in text
    assert "leftover scanner" in text.lower()
    assert ".cursor/skills" not in text


def test_leftover_gotcha_names_scanner_skip_dirs() -> None:
    path = (
        ROOT
        / ".grok"
        / "skills"
        / "verify-pstack"
        / "features"
        / "leftover-scanner.md"
    )
    text = path.read_text(encoding="utf-8")
    heads = _h2s(text)
    assert heads == [
        "Sub-features",
        "How to get to it (user POV)",
        "Driving it with verify.py",
        "Gotchas",
    ]
    gotchas = text.split("## Gotchas", 1)[1]
    scanner = _load_scanner()
    for name in sorted(scanner.SKIP_DIRS):
        assert name in gotchas, name
    for name in sorted(scanner.SKIP_FILES):
        assert name in gotchas, name
    assert ".grok" not in scanner.SKIP_DIRS
    assert "`.grok` is not a skip dir" in gotchas
    assert ".grok/workflows" in gotchas
    assert "docs/" not in gotchas or "docs/` is walked" in gotchas or "`docs/` is walked" in gotchas


def test_no_eight_edith_feature_maps() -> None:
    folder = ROOT / ".grok" / "skills" / "verify-pstack" / "features"
    names = {p.name for p in folder.glob("*.md") if p.name != "README.md"}
    assert not (names & EDITH_MAPS), names & EDITH_MAPS
    assert names == OWNED_MAPS, names


def test_archive_and_superpowers_still_say_twenty_one() -> None:
    archive = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-31-pstack-atomic-blocks"
        / "specs"
        / "pstack-principles"
        / "spec.md"
    )
    superpowers = (
        ROOT
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-08-30-pstack-atomic-blocks-design.md"
    )
    assert archive.is_file()
    text = archive.read_text(encoding="utf-8")
    assert "Twenty-one principle skills" in text
    assert "principles: 21" in text
    assert superpowers.is_file()
    assert "21 principles" in superpowers.read_text(encoding="utf-8")


def test_porting_table_is_twenty_three() -> None:
    text = (ROOT / "docs" / "guide" / "12-porting.md").read_text(encoding="utf-8")
    assert "23 `principle-*` skills" in text
    assert "21 `principle-*` skills" not in text
    assert "23 principles" in text
    assert "UPSTREAM" in text
