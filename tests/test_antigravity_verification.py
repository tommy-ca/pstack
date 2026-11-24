"""Unit and negative-control checks for Antigravity verification upgrades (Unit 3)."""

from __future__ import annotations

import json
import os
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
