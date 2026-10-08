from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync-antigravity-plugin.py"


def write(root: Path, name: str, content: bytes = b"canonical\n") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def snapshot(root: Path) -> dict[str, tuple[bytes | None, int]]:
    return {
        str(path.relative_to(root)): (
            path.read_bytes() if path.is_file() else None,
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
    }


@pytest.fixture
def plugin(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("sync_antigravity_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    desc, raw = module.load_package_descriptor()
    repo = tmp_path / "repo"
    write(repo, "skills/example/SKILL.md", b"# Example skill\n")
    write(repo, "skills/example/references/details.md", b"Skill reference\n")
    write(repo, "agents/example.md", b"# Example agent\n")
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "LIVE_PLUGIN_DIR", tmp_path / "missing-parent" / "live")
    monkeypatch.setattr(module, "load_package_descriptor", lambda: (desc, raw))
    monkeypatch.setattr(module._pp_mod, "ROOT", repo)
    monkeypatch.setitem(
        module._pp_mod.TARGET_MAP,
        "antigravity",
        (repo / ".antigravity-plugin/plugin.json", module.generate_antigravity_manifest),
    )
    monkeypatch.setattr(module.shutil, "which", lambda executable: None)
    return module


@pytest.mark.parametrize("existing", [False, True])
def test_dry_run_is_read_only(plugin, tmp_path, existing, capsys, monkeypatch):
    if existing:
        plugin.sync_live_plugin()
        write(plugin.LIVE_PLUGIN_DIR, "skills/removed/SKILL.md")
        write(plugin.LIVE_PLUGIN_DIR, "agents/removed.md")
        write(plugin.LIVE_PLUGIN_DIR, "commands/removed.toml")
        write(plugin.LIVE_PLUGIN_DIR, "hooks/hooks.json")
        write(plugin.LIVE_PLUGIN_DIR, ".claude-plugin/plugin.json")
    before = snapshot(tmp_path)
    capsys.readouterr()

    monkeypatch.setattr(plugin.sys, "argv", [str(SCRIPT), "--sync", "--dry-run"])
    plugin.main()

    assert "Syncing skill example" in capsys.readouterr().out
    assert snapshot(tmp_path) == before
    assert plugin.LIVE_PLUGIN_DIR.exists() is existing


def test_sync_creates_missing_destination_and_is_idempotent(plugin):
    plugin.sync_live_plugin()
    assert (plugin.LIVE_PLUGIN_DIR / "skills/example/SKILL.md").read_bytes() == b"# Example skill\n"
    assert (plugin.LIVE_PLUGIN_DIR / "agents/example.md").read_bytes() == b"# Example agent\n"
    assert plugin.check_live_sync() is True
    before = {
        name: content for name, (content, _) in snapshot(plugin.LIVE_PLUGIN_DIR).items()
    }

    plugin.sync_live_plugin()

    assert plugin.check_live_sync() is True
    assert {
        name: content for name, (content, _) in snapshot(plugin.LIVE_PLUGIN_DIR).items()
    } == before


def test_directory_symlink_contents_match_copied_files(plugin):
    references = plugin.ROOT / "skills/example/references"
    (plugin.ROOT / "skills/example/alias").symlink_to(references, target_is_directory=True)
    plugin.sync_live_plugin()
    copied = plugin.LIVE_PLUGIN_DIR / "skills/example/alias/details.md"
    assert copied.read_bytes() == b"Skill reference\n"
    assert plugin.check_live_sync() is True
    copied.write_bytes(b"changed reference\n")
    assert plugin.check_live_sync() is False


@pytest.mark.parametrize(
    "name",
    ["skills/example/SKILL.md", "skills/example/references/details.md", "agents/example.md"],
)
@pytest.mark.parametrize("change", ["drift", "missing"])
def test_check_detects_skill_and_agent_content_changes(plugin, name, change, capsys):
    plugin.sync_live_plugin()
    assert plugin.check_live_sync() is True
    path = plugin.LIVE_PLUGIN_DIR / name
    if change == "missing":
        path.unlink()
    else:
        path.write_bytes(b"changed content\n")
    capsys.readouterr()

    assert plugin.check_live_sync() is False
    assert "FAIL:" in capsys.readouterr().out
    plugin.sync_live_plugin()
    assert plugin.check_live_sync() is True


@pytest.mark.parametrize(
    "name",
    [
        "skills/removed/SKILL.md",
        "skills/example/references/extra.md",
        "agents/removed.md",
        "commands/removed.toml",
    ],
)
def test_check_detects_and_sync_removes_managed_extras(plugin, name, capsys):
    plugin.sync_live_plugin()
    assert plugin.check_live_sync() is True
    extra = write(plugin.LIVE_PLUGIN_DIR, name)
    capsys.readouterr()

    assert plugin.check_live_sync() is False
    assert "FAIL:" in capsys.readouterr().out
    plugin.sync_live_plugin()
    assert not extra.exists()
    assert plugin.check_live_sync() is True


@pytest.mark.parametrize("change", ["drift", "missing"])
def test_check_detects_command_changes(plugin, change):
    plugin.sync_live_plugin()
    command = next((plugin.LIVE_PLUGIN_DIR / "commands").glob("*.toml"))
    if change == "missing":
        command.unlink()
    else:
        command.write_text("changed command\n", encoding="utf-8")

    assert plugin.check_live_sync() is False
    plugin.sync_live_plugin()
    assert plugin.check_live_sync() is True


@pytest.mark.parametrize("name", ["plugin.json", "models.json"])
@pytest.mark.parametrize("content", [b"{}", b"invalid json"])
def test_check_still_detects_manifest_and_model_changes(plugin, name, content):
    plugin.sync_live_plugin()
    write(plugin.LIVE_PLUGIN_DIR, name, content)
    assert plugin.check_live_sync() is False


def test_generated_dependencies_and_bytecode_are_excluded(plugin):
    generated = [
        "skills/node_modules/package/index.js",
        "skills/__pycache__/cache.pyc",
        "skills/example/scripts/node_modules/package/index.js",
        "skills/example/scripts/__pycache__/cache.pyc",
        "skills/example/scripts/cache.pyc",
        "skills/example/scripts/cache.pyo",
    ]
    for name in generated:
        write(plugin.ROOT, name)
    write(plugin.ROOT, "skills/example/scripts/run.py", b"print('example')\n")
    write(plugin.ROOT, "skills/example/references/archive.pyc/details.md", b"Reference\n")

    plugin.sync_live_plugin()

    assert (plugin.LIVE_PLUGIN_DIR / "skills/example/scripts/run.py").read_bytes() == b"print('example')\n"
    assert (plugin.LIVE_PLUGIN_DIR / "skills/example/references/archive.pyc/details.md").read_bytes() == b"Reference\n"
    assert not any((plugin.LIVE_PLUGIN_DIR / name).exists() for name in generated)
    assert plugin.check_live_sync() is True
    for name in generated:
        write(plugin.LIVE_PLUGIN_DIR, name, b"different generated content\n")
    assert plugin.check_live_sync() is True


def test_unrelated_user_files_survive_sync_and_do_not_fail_check(plugin):
    unrelated = [
        "user-notes.txt",
        "skills/user-notes.txt",
        "agents/user-notes.txt",
        "agents/archive/personal.md",
        "commands/user-notes.txt",
        "commands/archive/personal.toml",
        "hooks/personal.json",
    ]
    for name in unrelated:
        write(plugin.LIVE_PLUGIN_DIR, name, b"personal content\n")

    plugin.sync_live_plugin()

    assert plugin.check_live_sync() is True
    for name in unrelated:
        assert (plugin.LIVE_PLUGIN_DIR / name).read_bytes() == b"personal content\n"


def test_check_missing_destination_is_read_only(plugin, tmp_path):
    before = snapshot(tmp_path)
    assert plugin.check_live_sync() is False
    assert snapshot(tmp_path) == before


def test_stale_projected_commands_are_not_installed(plugin):
    write(plugin.ROOT, ".antigravity-plugin/commands/removed.toml")

    plugin.sync_live_plugin()

    assert not (plugin.LIVE_PLUGIN_DIR / "commands/removed.toml").exists()
    assert plugin.check_live_sync() is True


@pytest.mark.parametrize("drifted", [False, True])
def test_check_cli_exit_status(plugin, monkeypatch, drifted):
    plugin.sync_live_plugin()
    if drifted:
        write(plugin.LIVE_PLUGIN_DIR, "agents/example.md", b"changed agent\n")
    monkeypatch.setattr(plugin.sys, "argv", [str(SCRIPT), "--check"])

    with pytest.raises(SystemExit) as result:
        plugin.main()

    assert result.value.code == (1 if drifted else 0)


def test_skill_files_rejects_symlink_cycles_without_looping(plugin):
    skill_dir = plugin.ROOT / "skills" / "example"
    cycle_dir = skill_dir / "cycle"
    cycle_dir.symlink_to(skill_dir, target_is_directory=True)

    files = plugin.skill_files(skill_dir)

    assert "SKILL.md" in files
    assert "references/details.md" in files
    assert not any(k.startswith("cycle") for k in files)


def test_skill_files_rejects_external_targets_without_reading(plugin, tmp_path):
    skill_dir = plugin.ROOT / "skills" / "example"
    external_file = tmp_path / "secret.txt"
    external_file.write_bytes(b"top-secret")
    external_file.chmod(0o000)

    escape_link = skill_dir / "escape.txt"
    escape_link.symlink_to(external_file)

    external_dir = tmp_path / "outside_dir"
    external_dir.mkdir()
    secret_dir_file = external_dir / "dir_secret.txt"
    secret_dir_file.write_bytes(b"dir-secret")
    secret_dir_file.chmod(0o000)

    escape_dir = skill_dir / "escape_dir"
    escape_dir.symlink_to(external_dir, target_is_directory=True)

    # If any external file is opened or read, chmod 000 will raise PermissionError
    files = plugin.skill_files(skill_dir)

    assert "SKILL.md" in files
    assert "escape.txt" not in files
    assert not any(k.startswith("escape_dir") for k in files)


def test_sync_rejects_symlink_cycles_and_external_targets(plugin, tmp_path):
    skill_dir = plugin.ROOT / "skills" / "example"
    (skill_dir / "cycle").symlink_to(skill_dir, target_is_directory=True)

    external_file = tmp_path / "secret.txt"
    external_file.write_bytes(b"top-secret")
    external_file.chmod(0o000)
    (skill_dir / "escape.txt").symlink_to(external_file)

    plugin.sync_live_plugin()

    live_skill = plugin.LIVE_PLUGIN_DIR / "skills" / "example"
    assert (live_skill / "SKILL.md").exists()
    assert not (live_skill / "cycle").exists()
    assert not (live_skill / "escape.txt").exists()
    assert plugin.check_live_sync() is True


def test_sync_rejects_mutual_symlink_cycles(plugin):
    skill_dir = plugin.ROOT / "skills" / "example"
    dir_a = skill_dir / "dir_a"
    dir_b = skill_dir / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()
    (dir_a / "to_b").symlink_to(dir_b, target_is_directory=True)
    (dir_b / "to_a").symlink_to(dir_a, target_is_directory=True)

    files = plugin.skill_files(skill_dir)
    assert "SKILL.md" in files

    plugin.sync_live_plugin()
    assert plugin.check_live_sync() is True
    live_skill = plugin.LIVE_PLUGIN_DIR / "skills" / "example"
    assert (live_skill / "SKILL.md").exists()



