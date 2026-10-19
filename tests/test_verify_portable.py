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
    # #444: every driven runtime scenario here is an offline contract check, so the
    # plane reads UNTESTED instead of a PASS claiming an unobserved child spawn/join.
    assert receipt.overall_verdict == "UNTESTED"
    assert receipt.planes["canonical"] == "PASS"
    assert receipt.planes["adapter"] == "PASS"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "UNTESTED"


def test_portable_verifier_droid(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="droid", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert verifier.drive() is True
    receipt = verifier.proof_bar()
    # #444: every driven runtime scenario here is an offline contract check, so the
    # plane reads UNTESTED instead of a PASS claiming an unobserved child spawn/join.
    assert receipt.overall_verdict == "UNTESTED"
    assert receipt.planes["canonical"] == "PASS"
    assert receipt.planes["adapter"] == "PASS"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "UNTESTED"


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
    # Explicit archived name validates exactly that name and fails honestly
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path, change="pstack-portability-contract")
    verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is False
    openspec_scenario = next(s for s in verifier.scenarios if s.id == "doctor-openspec-validation")
    assert openspec_scenario.description == "Verify pstack-portability-contract openspec change passes schema checks"
    assert "pstack-portability-contract" in openspec_scenario.command
    assert openspec_scenario.verdict == "FAIL"

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

def test_validate_default_change_fallback_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.openspec_change as oc

    validate = verify_portable.validate_openspec_change

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: ["only-active"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: ["only-active"])
    seen: dict[str, list[str]] = {}
    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "ok", "")
    monkeypatch.setattr(verify_portable.subprocess, "run", _fake_run)
    assert validate(None) == 0
    assert seen.get("argv", [])[2] == "only-active"

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: [])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: [])
    assert validate(None) == 0

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: None)
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: None)
    assert validate(None) == 1

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: ["a", "b"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: ["a", "b"])
    assert validate(None) == 1


def test_validate_explicit_default_name_validates_that_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate = verify_portable.validate_openspec_change
    name = "pstack-portability-contract"
    seen: dict[str, list[str]] = {}
    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "ok", "")
    monkeypatch.setattr(verify_portable.subprocess, "run", _fake_run)
    assert validate(name) == 0
    assert seen.get("argv", [])[2] == name


def test_resolution_states_are_distinct(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.openspec_change as oc

    resolve = verify_portable.resolve_openspec_change
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: None)
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: None)
    assert resolve(None)[0] == "lookup-failed"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: [])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: [])
    assert resolve(None)[0] == "none"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: ["one"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: ["one"])
    assert resolve(None)[:2] == ("active", "one")
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda: ["a", "b"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: ["a", "b"])
    state, name, names = resolve(None)
    assert (state, name, names) == ("ambiguous", None, ["a", "b"])
    assert resolve("explicit-name")[:2] == ("explicit", "explicit-name")


def test_doctor_labels_each_resolution_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.openspec_change as oc

    def scenarios_for(state_values: list[str] | None, **kwargs: object) -> list:
        monkeypatch.setattr(oc, "_active_openspec_changes", lambda: state_values)
        monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda: state_values)
        verifier = PortableVerifier(host="grok", evidence_root=tmp_path, **kwargs)  # type: ignore[arg-type]
        verifier.launch()
        verifier.doctor(check_durability=False)
        return [s for s in verifier.scenarios if s.id == "doctor-openspec-validation"]

    none_matches = scenarios_for([])
    assert len(none_matches) == 1
    assert none_matches[0].verdict == "PASS"
    assert "No active OpenSpec change" in none_matches[0].description

    failed_matches = scenarios_for(None)
    assert len(failed_matches) == 1
    assert failed_matches[0].verdict == "FAIL"
    assert "lookup failed" in failed_matches[0].description

    ambiguous_matches = scenarios_for(["a", "b"])
    assert len(ambiguous_matches) == 1
    assert ambiguous_matches[0].verdict == "FAIL"
    assert "2 active OpenSpec changes" in ambiguous_matches[0].description

    active_matches = scenarios_for(["only-active"])
    assert len(active_matches) == 1
    assert "only-active" in active_matches[0].description


def test_change_named_like_a_flag_still_validates_as_a_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []
    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen.append(list(a[0]) if a else [])
        return subprocess.CompletedProcess(a, 1, "", "invalid change")
    monkeypatch.setattr(verify_portable.subprocess, "run", _fake_run)
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path, change="--no-active-change")
    verifier.launch()
    verifier.doctor(check_durability=False)
    scenario = next(s for s in verifier.scenarios if s.id == "doctor-openspec-validation")
    assert any(argv and argv[-1] == "--no-active-change" for argv in seen)
    assert scenario.verdict == "FAIL"


@pytest.mark.parametrize("stdout", [
    '{"changes": ["junk"]}',
    '{"changes": [{}]}',
    '{"changes": [{"name": ""}]}',
    '{"changes": [{"name": 42}]}',
    '{"changes": "junk"}',
    'not json',
])
def test_active_changes_malformed_payload_is_lookup_failure(
    monkeypatch: pytest.MonkeyPatch, stdout: str
) -> None:
    monkeypatch.setattr(
        verify_portable.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout, ""),
    )
    assert verify_portable._active_openspec_changes() is None
    assert verify_portable.validate_openspec_change(None) == 1

def test_active_changes_lookup_failure_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    def _rc1(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(a, 1, "", "boom")
    monkeypatch.setattr(verify_portable.subprocess, "run", _rc1)
    assert verify_portable._active_openspec_changes() is None
    assert verify_portable.validate_openspec_change(None) == 1

    def _missing(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("no openspec binary")
    monkeypatch.setattr(verify_portable.subprocess, "run", _missing)
    assert verify_portable._active_openspec_changes() is None
    assert verify_portable.validate_openspec_change(None) == 1


def test_active_changes_empty_list_parses_to_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    import json as _json
    monkeypatch.setattr(
        verify_portable.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, _json.dumps({"changes": [], "root": {}}), ""),
    )
    assert verify_portable._active_openspec_changes() == []
    assert verify_portable.validate_openspec_change(None) == 0


def test_verify_portable_modular_decomposition_and_backwards_compatibility() -> None:
    vp_path = ROOT / "scripts" / "verify-portable.py"
    sc_path = ROOT / "scripts" / "select_checks.py"
    oc_path = ROOT / "scripts" / "openspec_change.py"
    ei_path = ROOT / "scripts" / "evidence_index.py"
    assert len(vp_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(sc_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(oc_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(ei_path.read_text(encoding="utf-8").splitlines()) < 1000

    import scripts.select_checks as sc
    import scripts.openspec_change as oc
    import scripts.evidence_index as ei

    for name in (
        "CHECK_SELECTION_TABLE",
        "offline_contract_tests",
        "select_checks",
        "changed_paths",
        "select_checks_plan",
        "select_checks_action",
    ):
        assert hasattr(verify_portable, name)
        assert getattr(verify_portable, name) is getattr(sc, name)

    for name in (
        "ChangeResolution",
        "_active_openspec_changes",
        "_validate_named_change",
        "resolve_openspec_change",
        "validate_openspec_change",
    ):
        assert hasattr(verify_portable, name)
        assert getattr(verify_portable, name) is getattr(oc, name)

    for name in (
        "_file_or_denied",
        "get_declared_hosts",
        "evidence_index_row",
        "rows_from_receipts",
        "index_row_mismatch",
        "check_evidence_action",
    ):
        assert hasattr(verify_portable, name)
        assert getattr(verify_portable, name) is getattr(ei, name)

    cmd = [
        sys.executable,
        "-c",
        "import scripts.select_checks; import scripts.openspec_change; import scripts.evidence_index; print('ok')",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert proc.stdout.strip() == "ok"


