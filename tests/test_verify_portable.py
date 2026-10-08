import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-portable.py"

loader = importlib.util.spec_from_file_location("verify_portable", SCRIPT)
assert loader is not None and loader.loader is not None
verify_portable = importlib.util.module_from_spec(loader)
sys.modules["verify_portable"] = verify_portable
loader.loader.exec_module(verify_portable)

PortableVerifier = verify_portable.PortableVerifier
ScenarioResult = verify_portable.ScenarioResult
VerificationReceipt = verify_portable.VerificationReceipt


def test_get_declared_hosts_matches_package_json() -> None:
    hosts = verify_portable.get_declared_hosts()
    data = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    assert hosts == data["host_targets"]
    assert "droid" in hosts


def test_portable_verifier_launch_and_doctor(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    assert verifier.launch()
    assert verifier.run_dir.is_dir()

    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert len(verifier.scenarios) >= 4
    for s in verifier.scenarios:
        assert s.verdict == "PASS"


def test_portable_verifier_codex_doctor(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="codex", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert len(verifier.scenarios) >= 4
    for s in verifier.scenarios:
        assert s.verdict == "PASS"


def test_portable_verifier_antigravity(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="antigravity", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert verifier.drive() is True
    receipt = verifier.proof_bar()
    assert receipt.overall_verdict == "PASS"
    assert receipt.planes["canonical"] == "PASS"
    assert receipt.planes["adapter"] == "PASS"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "PASS"


def test_portable_verifier_droid(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="droid", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert verifier.drive() is True
    receipt = verifier.proof_bar()
    assert receipt.overall_verdict == "PASS"
    assert receipt.planes["canonical"] == "PASS"
    assert receipt.planes["adapter"] == "PASS"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "PASS"


def test_portable_verifier_doctor_allow_stale(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=True, allow_stale=True)
    assert ok is True


def test_portable_verifier_proof_bar_and_receipt(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="codex", evidence_root=tmp_path)
    verifier.launch()

    # Synthetic scenarios
    s1 = ScenarioResult(
        id="test-1",
        description="test",
        plane="canonical",
        command="true",
        exit_code=0,
        stdout_snippet="ok",
        verdict="PASS",
        duration_s=0.1,
    )
    s2 = ScenarioResult(
        id="test-2",
        description="test",
        plane="adapter",
        command="false",
        exit_code=1,
        stdout_snippet="failed",
        verdict="FAIL",
        duration_s=0.2,
    )
    verifier.scenarios = [s1, s2]

    receipt = verifier.proof_bar()
    assert receipt.overall_verdict == "FAIL"
    assert receipt.planes["canonical"] == "PASS"
    assert receipt.planes["adapter"] == "FAIL"
    assert receipt.planes["package"] == "UNTESTED"
    assert receipt.planes["runtime"] == "UNTESTED"

    evidence_file = verifier.evidence(receipt)
    assert evidence_file.is_file()
    data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert data["overall_verdict"] == "FAIL"
    assert data["host"] == "codex"


def test_portable_verifier_drives_verification_skill_scaffolding_across_hosts(tmp_path: Path) -> None:
    for host in verify_portable.get_declared_hosts():
        verifier = PortableVerifier(host=host, evidence_root=tmp_path)
        assert verifier.launch()
        ok_doctor = verifier.doctor(check_durability=False)
        assert ok_doctor is True
        ok_drive = verifier.drive()
        assert ok_drive is True

        # Ensure drive-verification-skill-scaffold and drive-verification-skill-check ran
        scenario_ids = [s.id for s in verifier.scenarios]
        assert "drive-verification-skill-scaffold" in scenario_ids
        assert "drive-verification-skill-check" in scenario_ids

        scaffold_res = next(s for s in verifier.scenarios if s.id == "drive-verification-skill-scaffold")
        check_res = next(s for s in verifier.scenarios if s.id == "drive-verification-skill-check")
        assert scaffold_res.verdict == "PASS"
        assert check_res.verdict == "PASS"


def test_portable_verifier_cli_host_all_doctor(tmp_path: Path) -> None:
    declared = verify_portable.get_declared_hosts()
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "doctor", "--host", "all", "--allow-stale", "--evidence-dir", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert f"{len(declared)}-Harness Matrix Verdict: PASS" in res.stdout
    for host in declared:
        assert f"Host: {host}" in res.stdout


def test_portable_verifier_selected_change_validation(tmp_path: Path) -> None:
    # Default target passes and aligns description
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path, change="pstack-portability-contract")
    verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    openspec_scenario = next(s for s in verifier.scenarios if s.id == "doctor-openspec-validation")
    assert openspec_scenario.description == "Verify pstack-portability-contract openspec change passes schema checks"
    assert "pstack-portability-contract" in openspec_scenario.command
    assert openspec_scenario.verdict == "PASS"

    # Failing target is observable in scenario and fails doctor
    failing_verifier = PortableVerifier(host="grok", evidence_root=tmp_path, change="nonexistent-target-change")
    failing_verifier.launch()
    failing_ok = failing_verifier.doctor(check_durability=False)
    assert failing_ok is False
    failing_scenario = next(s for s in failing_verifier.scenarios if s.id == "doctor-openspec-validation")
    assert failing_scenario.description == "Verify nonexistent-target-change openspec change passes schema checks"
    assert "nonexistent-target-change" in failing_scenario.command
    assert failing_scenario.verdict == "FAIL"


def test_portable_verifier_cli_failing_change_observable(tmp_path: Path) -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify-portable.py"),
            "doctor",
            "--host",
            "grok",
            "--change",
            "nonexistent-target-change",
            "--allow-stale",
            "--evidence-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "Verify nonexistent-target-change openspec change passes schema checks" in res.stdout or res.returncode == 1

