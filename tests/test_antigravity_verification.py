"""Unit and negative-control checks for Antigravity verification upgrades."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import AntigravityDriver
from scripts.harness_scenarios import execute_local_scenarios
from scripts.portability_schema import ScenarioResult
from scripts.scaffold_verification_skill import check_skill


def test_verify_antigravity_skill_passes_feature_map_and_script_audit() -> None:
    skill_dir = ROOT / ".agents" / "skills" / "verify-antigravity-pstack"
    errors = check_skill(skill_dir)
    assert errors == [], f"Unexpected skill audit errors: {errors}"

    driver_sh = skill_dir / "scripts" / "driver.sh"
    assert driver_sh.is_file()
    assert os.access(driver_sh, os.X_OK), "driver.sh must be executable"

    features_json = json.loads(
        (skill_dir / "features" / "features.json").read_text(encoding="utf-8")
    )
    feature_ids = {f["id"] for f in features_json["features"]}
    assert feature_ids == {"core", "swarm-and-workflows", "cli-models-and-plugin"}


def test_antigravity_driver_discover_fails_closed_on_findings(tmp_path: Path) -> None:
    driver = AntigravityDriver(ROOT)
    bin_fake = tmp_path / "agy"
    bin_fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    bin_fake.chmod(0o755)

    clean_report = {
        "components": {"skills": 68, "agents": 22, "rules": 1},
        "findings": [],
    }
    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch("scripts.drivers.antigravity.stage_antigravity_package", return_value=tmp_path / "staged"),
        patch("scripts.drivers.antigravity.run_antigravity_validation", return_value=(True, clean_report)),
    ):
        ok = driver.discover(tmp_path)
        assert ok.verdict == "PASS"
        assert ok.exit_code == 0

    warning_report = {
        "components": {"skills": 68, "agents": 22, "rules": 1},
        "findings": [{"code": "AGY-TEST", "severity": "warning"}],
    }
    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch("scripts.drivers.antigravity.stage_antigravity_package", return_value=tmp_path / "staged"),
        patch("scripts.drivers.antigravity.run_antigravity_validation", return_value=(True, warning_report)),
    ):
        bad = driver.discover(tmp_path)
        assert bad.verdict == "FAIL"
        assert bad.exit_code == 1


def test_antigravity_driver_child_spawn_checks_conventions_and_fails_closed(tmp_path: Path) -> None:
    driver = AntigravityDriver(ROOT)
    bin_fake = tmp_path / "agy"
    bin_fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    bin_fake.chmod(0o755)

    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch.object(driver, "run_command", return_value=(0, "Available agents:\nfeature\n", "", 0.01)),
    ):
        ok = driver.child_spawn(tmp_path)
        assert ok.verdict == "PASS"

    mutated = json.loads(json.dumps(driver.profile_data))
    mutated["runtime_conventions"]["forbidden_spawn_fields"] = ["readonly", "environment"]
    driver._profile_data = mutated
    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch.object(driver, "run_command", return_value=(0, "Available agents:\nfeature\n", "", 0.01)),
    ):
        bad = driver.child_spawn(tmp_path)
        assert bad.verdict == "FAIL"


def test_antigravity_driver_isolation_contract(tmp_path: Path) -> None:
    driver = AntigravityDriver(ROOT)
    bin_fake = tmp_path / "agy"
    bin_fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    bin_fake.chmod(0o755)

    # 1. Blocks when binary is unavailable
    with patch.object(driver, "is_available", return_value=(False, "agy not found")):
        blocked = driver.isolation(tmp_path)
        assert blocked.verdict == "BLOCKED"
        assert "agy not found" in blocked.stdout

    # 2. Passes when available and conventions satisfied
    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch.object(driver, "is_available", return_value=(True, "")),
        patch.object(driver, "run_command", return_value=(0, "Usage: agy [options]", "", 0.01)),
    ):
        ok = driver.isolation(tmp_path)
        assert ok.verdict == "PASS"

    # 3. Fails when isolation modes are incomplete
    mutated = json.loads(json.dumps(driver.profile_data))
    mutated["runtime_conventions"]["supported_isolation_modes"] = ["inherit"]
    driver._profile_data = mutated
    with (
        patch.object(driver, "get_binary_path", return_value=bin_fake),
        patch.object(driver, "is_available", return_value=(True, "")),
        patch.object(driver, "run_command", return_value=(0, "Usage: agy [options]", "", 0.01)),
    ):
        bad = driver.isolation(tmp_path)
        assert bad.verdict == "FAIL"



def test_harness_local_scenarios_cover_1_5_16_antigravity_contracts(tmp_path: Path) -> None:
    import subprocess

    class _StubVerifier:
        host = "antigravity"
        run_dir = tmp_path

        def run_command(self, sid, desc, plane, cmd, cwd=None, record=True):
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
            return ScenarioResult(
                id=sid,
                description=desc,
                plane=plane,
                command=" ".join(cmd),
                exit_code=proc.returncode,
                stdout_snippet=proc.stdout[:200],
                verdict="PASS" if proc.returncode == 0 else "FAIL",
                duration_s=0.01,
            )

    results = execute_local_scenarios(_StubVerifier(), ROOT)
    agy_results = [r for r in results if r.id in ("drive-antigravity-models", "drive-antigravity-tools-ref")]
    assert len(agy_results) == 2
    assert all(r.verdict == "PASS" for r in agy_results)


def test_stage_antigravity_package_is_strict_valid_with_zero_warnings(tmp_path: Path) -> None:
    from scripts.package_install_staging import stage_antigravity_package
    from scripts.prove_antigravity_native_package import run_antigravity_validation

    staged = stage_antigravity_package(tmp_path / "stage", source_root=ROOT)
    assert (staged / "plugin.json").is_file()
    assert (staged / "models.json").is_file()
    # Native plugins expose commands as skills; commands/ directory is never loaded
    # and causes agy plugin validate --strict to emit warnings.
    assert not (staged / "commands").exists()

    val_pass, report = run_antigravity_validation(staged)
    if report.get("verdict") != "BLOCKED":
        assert val_pass is True, f"Validation failed: {report}"
        assert report.get("findings") == [], f"Unexpected findings: {report.get('findings')}"



def test_antigravity_driver_sh_all_works_from_subdirectories() -> None:
    driver_sh = ROOT / ".agents" / "skills" / "verify-antigravity-pstack" / "scripts" / "driver.sh"
    if os.environ.get("_PSTACK_DRIVER_RUNNING") == "1":
        # Within driver.sh doctor run, verify driver execution from subfolder without recursion
        proc = subprocess.run(
            [str(driver_sh), "launch"],
            cwd=ROOT / "tests",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"driver.sh launch failed from subfolder:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        assert "Launch: Antigravity environment ready." in proc.stdout
        return

    env = dict(os.environ, _PSTACK_DRIVER_RUNNING="1")
    proc = subprocess.run(
        [str(driver_sh), "all"],
        cwd=ROOT / "tests",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"driver.sh all failed from subfolder:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Launch: Antigravity environment ready." in proc.stdout


def test_stage_antigravity_native_install_restore_guard_and_stray_exclusion(tmp_path: Path) -> None:
    from scripts.package_install_staging import stage_antigravity_native_install
    from scripts.package_projection import load_package_descriptor

    plugin_dir = tmp_path / "live"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    unmanaged_file = plugin_dir / "custom_user_file.txt"
    unmanaged_file.write_text("keep me", encoding="utf-8")
    stray_file = plugin_dir / ".codex-plugin" / "legacy.json"
    stray_file.parent.mkdir(parents=True, exist_ok=True)
    stray_file.write_text("purge me", encoding="utf-8")

    desc, _ = load_package_descriptor()
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_agy.chmod(0o755)

    def _simulated_install(cmd, env=None, capture_output=True, text=True, check=False, **kwargs):
        # Simulate installer wiping the directory before failing
        shutil.rmtree(plugin_dir)
        plugin_dir.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="simulated install error")

    with patch("shutil.which", return_value=str(fake_agy)):
        with patch("subprocess.run", side_effect=_simulated_install):
            import pytest
            with pytest.raises(RuntimeError, match="agy plugin install failed"):
                stage_antigravity_native_install(
                    plugin_dir=plugin_dir,
                    standard_dir=plugin_dir,
                    host="antigravity",
                    desc=desc,
                    src_root=ROOT,
                    target_base=tmp_path,
                )

    assert unmanaged_file.is_file()
    assert unmanaged_file.read_text(encoding="utf-8") == "keep me"
    assert not (plugin_dir / ".codex-plugin").exists()


