#!/usr/bin/env python3
"""Tests for native package lifecycle driver across all harnesses."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_SCRIPT = ROOT / "scripts" / "package-lifecycle.py"

loader = importlib.util.spec_from_file_location("package_lifecycle", LIFECYCLE_SCRIPT)
assert loader is not None and loader.loader is not None
package_lifecycle = importlib.util.module_from_spec(loader)
sys.modules["package_lifecycle"] = package_lifecycle
loader.loader.exec_module(package_lifecycle)


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity"])
def test_isolated_lifecycle_proof(host: str, tmp_path: Path) -> None:
    host_target = tmp_path / f"target-{host}"
    ok, scenarios = package_lifecycle.prove_lifecycle(host, host_target)
    assert ok is True, f"Lifecycle proof failed for {host}: {scenarios}"
    assert len(scenarios) == 3

    steps = [s["step"] for s in scenarios]
    assert steps == ["install", "update", "uninstall"]
    for s in scenarios:
        assert s["verdict"] == "PASS"

    # User sentinel must remain intact after uninstall
    sentinel = host_target / f".{host}-user-sentinel.json"
    assert sentinel.is_file()
    data = json.loads(sentinel.read_text(encoding="utf-8"))
    assert data["user_config"] == "custom_value"

    # Plugin directory must be gone
    plugin_dir = package_lifecycle.get_plugin_dir(host, host_target)
    assert not plugin_dir.exists()


def test_omp_install_replaces_a_stale_generated_plugin_json(tmp_path: Path) -> None:
    target = tmp_path / "stale-omp"
    plugin_dir = package_lifecycle.get_plugin_dir("omp", target)
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "name": "pstack",
                "version": "0.0.1",
                "skills_root": "./skills/",
                "entrypoint": "skills/poteto-mode/SKILL.md",
            }
        ),
        encoding="utf-8",
    )

    package_lifecycle.install_plugin("omp", target)

    assert not (plugin_dir / "plugin.json").exists()
    assert (plugin_dir / "package.json").is_file()


def test_omp_install_preserves_a_user_authored_plugin_json(tmp_path: Path) -> None:
    target = tmp_path / "user-omp"
    plugin_dir = package_lifecycle.get_plugin_dir("omp", target)
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps({"name": "somebody-elses-plugin"}), encoding="utf-8")

    package_lifecycle.install_plugin("omp", target)

    assert json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8")) == {
        "name": "somebody-elses-plugin"
    }


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity"])
def test_install_and_verify(host: str, tmp_path: Path) -> None:
    target = tmp_path / f"inst-{host}"
    plugin_dir = package_lifecycle.install_plugin(host, target)
    assert plugin_dir.is_dir()

    # Router skill must exist
    router = plugin_dir / "skills" / "poteto-mode" / "SKILL.md"
    assert router.is_file()

    # Hosts that project native subagents must copy agents/*.md
    if host in ("grok", "antigravity", "omp"):
        agents_dir = plugin_dir / "agents"
        assert agents_dir.is_dir(), f"agents/ not projected for {host}"
        assert (agents_dir / "poteto-agent.md").is_file(), f"agents/poteto-agent.md missing for {host}"
        assert len(list(agents_dir.glob("*.md"))) == len(list((ROOT / "agents").glob("*.md")))

    # Manifest must exist and match version 0.15.29
    manifest_name = "package.json" if host in ("opencode", "omp") else "plugin.json"
    manifest_path = plugin_dir / manifest_name
    assert manifest_path.is_file()
    m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert m_data.get("version") == "0.15.29-grokbuild.0"
    if host == "omp":
        assert isinstance(m_data.get("omp"), dict), "OMP enrolls a package only through package.json#omp"

    ok, errors = package_lifecycle.verify_plugin(host, target)
    assert ok is True, f"Verify failed for {host}: {errors}"


def test_verify_detects_corrupt_manifest(tmp_path: Path) -> None:
    target = tmp_path / "corrupt"
    plugin_dir = package_lifecycle.install_plugin("grok", target)
    (plugin_dir / "plugin.json").write_text("invalid json", encoding="utf-8")

    ok, errors = package_lifecycle.verify_plugin("grok", target)
    assert ok is False
    assert any("corrupt" in e.lower() for e in errors)


def test_update_idempotent_convergence(tmp_path: Path) -> None:
    target = tmp_path / "conv"
    ok, errors = package_lifecycle.update_plugin("codex", target)
    assert ok is True
    assert errors == []

    # Corrupt a file to verify update restores it
    plugin_dir = package_lifecycle.get_plugin_dir("codex", target)
    (plugin_dir / "plugin.json").write_text("{}", encoding="utf-8")
    ok2, errors2 = package_lifecycle.update_plugin("codex", target)
    assert ok2 is True
    m_data = json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))
    assert m_data.get("version") == "0.15.29-grokbuild.0"


def test_cli_lifecycle_prove(tmp_path: Path) -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(LIFECYCLE_SCRIPT),
            "prove",
            "--host",
            "omp",
            "--target-dir",
            str(tmp_path / "cli-omp"),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "[omp] PROVE PASS" in res.stdout


def test_freshness_reports_drifted_installed_copy(tmp_path: Path) -> None:
    plugin_dir = package_lifecycle.install_plugin("grok", tmp_path)
    assert package_lifecycle.freshness_errors(plugin_dir) == []

    stale = plugin_dir / "skills" / "deslop" / "SKILL.md"
    stale.write_text("stale\n", encoding="utf-8")
    ghost = plugin_dir / "skills" / "ghost-skill"
    ghost.mkdir()
    (ghost / "SKILL.md").write_text("ghost\n", encoding="utf-8")
    errors = package_lifecycle.freshness_errors(plugin_dir)

    assert any("drifted" in e and "deslop" in e for e in errors)
    assert any("extra" in e and "ghost-skill" in e for e in errors)


def test_owned_deploy_target_excludes_foreign_variant_installs(tmp_path: Path) -> None:
    # Real directory installed by pstack -> owned, freshness applies.
    owned = tmp_path / ".grok" / "plugins" / "pstack"
    owned.mkdir(parents=True)
    assert package_lifecycle.is_owned_deploy_target(owned) is True

    # Claude-variant symlinked tree -> foreign source, excluded.
    foreign = tmp_path / "pstack-claude" / "plugins" / "pstack"
    foreign.mkdir(parents=True)
    bind = tmp_path / ".agents" / "skills"
    bind.parent.mkdir(parents=True, exist_ok=True)
    bind.symlink_to(foreign)
    assert package_lifecycle.is_owned_deploy_target(bind) is False

    # Marketplace bind -> foreign source, excluded.
    market = tmp_path / "marketplaces" / "pstack-claude" / "plugins" / "pstack"
    market.mkdir(parents=True)
    assert package_lifecycle.is_owned_deploy_target(market) is False


def test_verify_plugin_skips_foreign_variant_live_install(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    foreign = tmp_path / "pstack-claude" / "plugins" / "pstack"
    (foreign / "skills").mkdir(parents=True)
    (foreign / "plugin.json").write_text('{"name": "not-pstack"}', encoding="utf-8")
    bind = tmp_path / ".grok" / "plugins" / "pstack"
    bind.parent.mkdir(parents=True)
    bind.symlink_to(foreign)

    ok, errors = package_lifecycle.verify_plugin("grok")
    assert ok is True, errors


def test_uninstall_refuses_foreign_symlinked_install(tmp_path: Path) -> None:
    foreign = tmp_path / "foreign"
    (foreign / "skills" / "poteto-mode").mkdir(parents=True)
    sentinel = foreign / "skills" / "poteto-mode" / "SKILL.md"
    sentinel.write_text("foreign router\n", encoding="utf-8")
    live = tmp_path / ".grok" / "plugins" / "pstack"
    live.parent.mkdir(parents=True)
    live.symlink_to(foreign, target_is_directory=True)
    assert package_lifecycle.is_owned_deploy_target(live) is False

    for force in (False, True):
        ok, errors = package_lifecycle.uninstall_plugin("grok", tmp_path, force=force)
        assert ok is False, errors
        assert any("foreign-source" in e for e in errors)
        assert sentinel.exists()


def _tree_digest(root: Path) -> dict:
    """Path -> sha256 for every real file under root, for byte-unchanged checks."""
    import hashlib
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def _foreign_home(base: Path) -> Path:
    """A foreign harness home shaped like a pstack install, with a sentinel skill."""
    plugin = base / "foreign-home" / ".grok" / "plugins" / "pstack"
    (plugin / "skills" / "poteto-mode").mkdir(parents=True)
    (plugin / "skills" / "poteto-mode" / "SKILL.md").write_text("foreign router\n", encoding="utf-8")
    (plugin / "plugin.json").write_text('{"name": "not-pstack"}\n', encoding="utf-8")
    return plugin


def _symlinked_ancestor_target(base: Path, foreign_plugin: Path) -> Path:
    """A scratch target whose `.grok` is bound to the foreign harness home."""
    target = base / "scratch-ancestor"
    target.mkdir()
    (target / ".grok").symlink_to(foreign_plugin.parents[1], target_is_directory=True)
    return target


@pytest.mark.parametrize("force", [False, True])
def test_uninstall_refuses_foreign_install_behind_symlinked_ancestor(force: bool, tmp_path: Path) -> None:
    foreign_plugin = _foreign_home(tmp_path)
    sentinel = foreign_plugin / "skills" / "poteto-mode" / "SKILL.md"
    before = _tree_digest(foreign_plugin)
    target = _symlinked_ancestor_target(tmp_path, foreign_plugin)
    live = package_lifecycle.get_plugin_dir("grok", target)

    assert live == target / ".grok" / "plugins" / "pstack"
    assert package_lifecycle.is_owned_deploy_target(live) is False

    ok, errors = package_lifecycle.uninstall_plugin("grok", target, force=force)
    assert ok is False, errors
    assert any("foreign-source" in e and str(live) in e for e in errors), errors
    assert sentinel.read_text(encoding="utf-8") == "foreign router\n"
    assert _tree_digest(foreign_plugin) == before


@pytest.mark.parametrize("leaf_symlink", [True, False])
def test_install_refuses_foreign_tree(leaf_symlink: bool, tmp_path: Path) -> None:
    foreign_plugin = _foreign_home(tmp_path)
    before = _tree_digest(foreign_plugin)
    if leaf_symlink:
        target = tmp_path / "scratch-leaf"
        live = package_lifecycle.get_plugin_dir("grok", target)
        live.parent.mkdir(parents=True)
        live.symlink_to(foreign_plugin, target_is_directory=True)
    else:
        target = _symlinked_ancestor_target(tmp_path, foreign_plugin)
        live = package_lifecycle.get_plugin_dir("grok", target)

    with pytest.raises(package_lifecycle.ForeignSourceError) as excinfo:
        package_lifecycle.install_plugin("grok", target)

    assert "foreign-source" in str(excinfo.value)
    assert str(live) in str(excinfo.value)
    assert _tree_digest(foreign_plugin) == before


def test_update_refuses_foreign_tree(tmp_path: Path) -> None:
    foreign_plugin = _foreign_home(tmp_path)
    before = _tree_digest(foreign_plugin)
    target = _symlinked_ancestor_target(tmp_path, foreign_plugin)
    live = package_lifecycle.get_plugin_dir("grok", target)

    ok, errors = package_lifecycle.update_plugin("grok", target)

    assert ok is False, errors
    assert any("refused" in e and str(live) in e for e in errors), errors
    assert _tree_digest(foreign_plugin) == before
