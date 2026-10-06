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


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity"])
def test_install_and_verify(host: str, tmp_path: Path) -> None:
    target = tmp_path / f"inst-{host}"
    plugin_dir = package_lifecycle.install_plugin(host, target)
    assert plugin_dir.is_dir()

    # Router skill must exist
    router = plugin_dir / "skills" / "poteto-mode" / "SKILL.md"
    assert router.is_file()

    # Manifest must exist and match version 0.16.0
    manifest_name = "package.json" if host == "opencode" else "plugin.json"
    manifest_path = plugin_dir / manifest_name
    assert manifest_path.is_file()
    m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert m_data.get("version") == "0.15.5-grokbuild.0"

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
    assert m_data.get("version") == "0.15.5-grokbuild.0"


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
