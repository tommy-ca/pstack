import importlib.util
import json
import os
import shutil
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


def _canonical_verdict(host: str) -> str:
    """The canonical plane is UNTESTED once the local upstream cache drifts past the pin."""
    fresh = verify_portable.compute_surface_revisions(ROOT, host).upstream_freshness
    return "UNTESTED" if fresh == "DRIFT" else "PASS"


def runtime_available(host: str) -> bool:
    """Whether this machine has the host CLI the drive phase needs."""
    return verify_portable.get_driver(host, ROOT).is_available()[0]


def stub_cli(directory: Path, name: str, script: str) -> Path:
    path = directory / name
    path.write_text(f"#!{sys.executable}\n{script}", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def bin_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "bin"
    directory.mkdir()
    monkeypatch.setenv("PATH", f"{directory}{os.pathsep}{os.environ['PATH']}")
    return directory


@pytest.fixture(autouse=True)
def host_clis(bin_dir: Path) -> None:
    """Bind the host CLIs this module shells out to.

    The doctor resolves the active OpenSpec change by shelling out, and the
    driven local scenarios call `bun`; without both, results depend on the
    developer's tooling and on whatever their checkout happens to hold. The
    OpenSpec stub answers `list --json` only from the repository root.
    """
    stub_cli(
        bin_dir,
        "openspec",
        "import json, os, sys\n"
        f"root = {str(ROOT)!r}\n"
        "if sys.argv[1:3] == ['list', '--json'] and os.path.realpath(os.getcwd()) == os.path.realpath(root):\n"
        "    print(json.dumps({'changes': []}))\n"
        "    sys.exit(0)\n"
        "sys.exit(1)\n",
    )
    stub_cli(bin_dir, "bun", "import sys\nsys.exit(0)\n")


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
    by_id = {s.id: s for s in verifier.scenarios}
    assert by_id["doctor-canonical-index"].verdict == _canonical_verdict("grok")
    assert all(
        s.verdict == "PASS" for s in verifier.scenarios if s.id != "doctor-canonical-index"
    )


def test_portable_verifier_codex_doctor(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="codex", evidence_root=tmp_path)
    assert verifier.launch()
    ok = verifier.doctor(check_durability=False)
    assert ok is True
    assert len(verifier.scenarios) >= 4
    by_id = {s.id: s for s in verifier.scenarios}
    assert by_id["doctor-canonical-index"].verdict == _canonical_verdict("codex")
    assert all(
        s.verdict == "PASS" for s in verifier.scenarios if s.id != "doctor-canonical-index"
    )


@pytest.mark.skipif(
    not runtime_available("antigravity"), reason="antigravity runtime not installed"
)
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
    assert receipt.planes["canonical"] == _canonical_verdict("antigravity")
    assert receipt.planes["adapter"] == "PASS"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "UNTESTED"


def _host_plugin_rel_paths() -> dict[str, Path]:
    """The canonical host -> plugin-mirror map, read from the script that owns it."""
    spec = importlib.util.spec_from_file_location(
        "package_lifecycle", ROOT / "scripts" / "package-lifecycle.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["package_lifecycle"] = module
    spec.loader.exec_module(module)
    return module.HOST_PLUGIN_REL_PATHS


def test_doctor_is_hermetic_against_ambient_plugin_mirrors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#709: the doctor verdict must not change when the live mirrors change."""
    # The doctor's OpenSpec step shells out to a CLI the offline gate does not
    # install; pin it to "no active change" so this case exercises only the
    # HOME-bound install/verify path (#717 follow-up).
    monkeypatch.setattr(
        verify_portable,
        "resolve_openspec_change",
        lambda *a, **k: verify_portable.ChangeResolution(state="none", name=None, names=[]),
    )
    hosts = ("omp", "antigravity")
    fixture_home = tmp_path / "fixture-home"
    mirrors = _host_plugin_rel_paths()

    def snapshot(home: Path) -> dict[str, bytes]:
        return {p.relative_to(home).as_posix(): p.read_bytes() for p in sorted(home.rglob("*")) if p.is_file()}

    def doctor_records(home: Path) -> dict[str, list[tuple[str, str, str, str]]]:
        monkeypatch.setenv("HOME", str(home))
        records: dict[str, list[tuple[str, str, str, str]]] = {}
        for host in hosts:
            shutil.rmtree(fixture_home, ignore_errors=True)
            verifier = PortableVerifier(
                host=host, evidence_root=tmp_path / "evidence", fixture_home=fixture_home
            )
            assert verifier.launch()
            assert verifier.doctor(check_durability=False) is True
            records[host] = [(s.id, s.verdict, s.command, s.stdout_snippet) for s in verifier.scenarios]
        return records

    clean_home = tmp_path / "clean-home"
    clean_home.mkdir()
    clean = doctor_records(clean_home)

    stale_home = tmp_path / "stale-home"
    for rel in mirrors.values():
        (stale_home / rel / "skills").mkdir(parents=True)
        (stale_home / rel / "plugin.json").write_text('{"stale": true}\n', encoding="utf-8")
        (stale_home / rel / "skills" / "stale-skill.md").write_text("stale\n", encoding="utf-8")
    stale_before = snapshot(stale_home)
    stale = doctor_records(stale_home)

    assert stale == clean
    assert snapshot(stale_home) == stale_before
    for host in hosts:
        ambient = {row[0]: row[1] for row in stale[host]}
        assert ambient[f"doctor-package-lifecycle-{host}"] == "PASS"
        lifecycle = next(row for row in stale[host] if row[0] == f"doctor-package-lifecycle-{host}")
        assert f"[HOME={fixture_home.resolve()}]" in lifecycle[2]
    assert {row[0]: row[1] for row in stale["antigravity"]}["doctor-antigravity-sync"] == "PASS"


def test_doctor_fails_closed_when_fixture_install_fails(tmp_path: Path) -> None:
    """#709 follow-up: a refused fixture install must fail the doctor, not pass vacuously."""
    home = tmp_path / "home"
    (tmp_path / "foreign" / "plugins").mkdir(parents=True)
    home.mkdir()
    (home / ".omp").symlink_to(tmp_path / "foreign")  # symlinked mirror: install refuses

    verifier = PortableVerifier(host="omp", evidence_root=tmp_path / "evidence", fixture_home=home)
    assert verifier.launch()
    assert verifier.doctor(check_durability=False) is False

    seed = [s for s in verifier.scenarios if s.id == "doctor-fixture-install-omp"]
    assert len(seed) == 1
    assert seed[0].verdict == "FAIL"
    assert seed[0].exit_code != 0


@pytest.mark.skipif(not runtime_available("droid"), reason="droid runtime not installed")
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
    assert receipt.planes["canonical"] == _canonical_verdict("droid")
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
        verifier.drive()

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

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["only-active"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: ["only-active"])
    seen: dict[str, list[str]] = {}
    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        seen["argv"] = list(a[0]) if a else []
        return subprocess.CompletedProcess(a, 0, "ok", "")
    monkeypatch.setattr(verify_portable.subprocess, "run", _fake_run)
    assert validate(None) == 0
    assert seen.get("argv", [])[2] == "only-active"

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: [])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: [])
    assert validate(None) == 0

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: None)
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: None)
    assert validate(None) == 1

    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
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
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: None)
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: None)
    assert resolve(None)[0] == "lookup-failed"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: [])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: [])
    assert resolve(None)[0] == "none"
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["one"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: ["one"])
    assert resolve(None)[:2] == ("active", "one")
    monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
    monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, **k: ["a", "b"])
    state, name, names = resolve(None)
    assert (state, name, names) == ("ambiguous", None, ["a", "b"])
    assert resolve("explicit-name")[:2] == ("explicit", "explicit-name")


def test_doctor_labels_each_resolution_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.openspec_change as oc

    def scenarios_for(state_values: list[str] | None, **kwargs: object) -> list:
        monkeypatch.setattr(oc, "_active_openspec_changes", lambda *a, _sv=state_values, **k: _sv)
        monkeypatch.setattr(verify_portable, "_active_openspec_changes", lambda *a, _sv=state_values, **k: _sv)
        verifier = PortableVerifier(host="grok", evidence_root=tmp_path, **kwargs)  # type: ignore[arg-type]
        verifier.launch()
        verifier.doctor(check_durability=False)
        return [s for s in verifier.scenarios if s.id == "doctor-openspec-validation"]

    none_matches = scenarios_for([])
    assert none_matches == []

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


def test_doctor_resolves_openspec_from_repo_root_not_caller_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Doctor must find the OpenSpec root even when invoked from a foreign cwd."""
    monkeypatch.chdir(tmp_path)
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    assert verifier.launch()
    assert verifier.doctor(check_durability=False) is True
    matched = [s for s in verifier.scenarios if s.id == "doctor-openspec-validation"]
    assert all(s.verdict == "PASS" for s in matched)

def test_change_named_like_a_flag_still_validates_as_a_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []
    def _fake_run(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        argv = list(a[0]) if a else []
        seen.append(argv)
        # A failed seed install now fails the doctor closed, so script exactly that
        # step to succeed; every other probe keeps the original fail-everything
        # shape so the openspec scenario still records FAIL.
        seed = len(argv) > 2 and argv[2] == "install"
        return subprocess.CompletedProcess(a, 0 if seed else 1, "", "" if seed else "invalid change")
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


def test_active_changes_all_complete_parses_to_none_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    import json as _json
    completed_payload = {
        "changes": [
            {"name": "change-1", "status": "complete", "completedTasks": 5, "totalTasks": 5},
            {"name": "change-2", "status": "complete", "completedTasks": 3, "totalTasks": 3},
        ],
        "root": {},
    }
    monkeypatch.setattr(
        verify_portable.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, _json.dumps(completed_payload), ""),
    )
    assert verify_portable._active_openspec_changes() == []
    resolution = verify_portable.resolve_openspec_change(None)
    assert resolution.state == "none"
    assert resolution.name is None
    assert resolution.names == []
    assert verify_portable.validate_openspec_change(None) == 0


def test_active_changes_filters_out_completed_when_in_progress_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    import json as _json
    mixed_payload = {
        "changes": [
            {"name": "change-complete", "status": "complete"},
            {"name": "change-active", "status": "in-progress"},
        ],
        "root": {},
    }
    monkeypatch.setattr(
        verify_portable.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, _json.dumps(mixed_payload), ""),
    )
    assert verify_portable._active_openspec_changes() == ["change-active"]
    resolution = verify_portable.resolve_openspec_change(None)
    assert resolution.state == "active"
    assert resolution.name == "change-active"
    assert resolution.names == []


def test_verify_portable_modular_decomposition_and_backwards_compatibility() -> None:
    vp_path = ROOT / "scripts" / "verify-portable.py"
    sc_path = ROOT / "scripts" / "select_checks.py"
    oc_path = ROOT / "scripts" / "openspec_change.py"
    ei_path = ROOT / "scripts" / "evidence_index.py"
    hs_path = ROOT / "scripts" / "harness_scenarios.py"
    assert len(vp_path.read_text(encoding="utf-8").splitlines()) < 750
    assert len(sc_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(oc_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(ei_path.read_text(encoding="utf-8").splitlines()) < 1000
    assert len(hs_path.read_text(encoding="utf-8").splitlines()) < 400

    import scripts.select_checks as sc
    import scripts.openspec_change as oc
    import scripts.evidence_index as ei
    import scripts.harness_scenarios as hs

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
        "check_staleness_action",
        "receipt_payload",
        "write_verification_evidence",
    ):
        assert hasattr(verify_portable, name)
        assert getattr(verify_portable, name) is getattr(ei, name)

    for name in (
        "execute_driver_scenarios",
        "execute_local_scenarios",
    ):
        assert hasattr(verify_portable, name)
        assert getattr(verify_portable, name) is getattr(hs, name)

    cmd = [
        sys.executable,
        "-c",
        "import scripts.select_checks; import scripts.openspec_change; import scripts.evidence_index; import scripts.harness_scenarios; print('ok')",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert proc.stdout.strip() == "ok"


def test_execute_driver_scenarios_in_isolation(tmp_path: Path) -> None:
    import scripts.harness_scenarios as hs
    from scripts.drivers import get_driver

    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()
    driver = get_driver("grok", ROOT)
    scenarios = hs.execute_driver_scenarios(verifier, driver, feature="feature")
    assert len(scenarios) == 5
    for s in scenarios:
        assert s.plane == "runtime"
        assert s.verdict == "PASS"
        assert s.evidence_level in ("offline", "static", "observed_live", "legacy")

    omp_verifier = PortableVerifier(host="omp", evidence_root=tmp_path)
    omp_verifier.launch()
    omp_driver = get_driver("omp", ROOT)
    omp_scenarios = hs.execute_driver_scenarios(omp_verifier, omp_driver, feature="feature")
    assert len(omp_scenarios) == 6
    assert any(s.id == "runtime-child-cancel-omp" for s in omp_scenarios)


def test_execute_local_scenarios_in_isolation(tmp_path: Path) -> None:
    import scripts.harness_scenarios as hs

    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()
    scenarios = hs.execute_local_scenarios(verifier, ROOT)
    assert len(scenarios) >= 5
    # Functional purity: verifier.scenarios is not mutated in-place
    assert len(verifier.scenarios) == 0
    for s in scenarios:
        assert s.verdict == "PASS"


def test_write_verification_evidence_in_isolation(tmp_path: Path) -> None:
    import json
    import scripts.evidence_index as ei
    from scripts.surface_revisions import compute_surface_revisions

    receipt = VerificationReceipt(
        run_id="test-run-isolated",
        host="grok",
        host_version="1.0.0",
        timestamp="2026-10-20T00:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in ("canonical", "adapter", "package", "runtime")},
        surface_revisions=compute_surface_revisions(ROOT, "grok"),
        scenarios=[],
        artifacts=[],
        claim="grok portability conformance verification",
        kind="runtime",
    )
    evidence_root = tmp_path / "evidence"
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)

    # 1. Write with update_durable=True
    receipt_path = ei.write_verification_evidence(
        receipt,
        evidence_root=evidence_root,
        run_dir=run_dir,
        host="grok",
        update_durable=True,
    )
    assert receipt_path == run_dir / "receipt.json"
    assert receipt_path.is_file()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "test-run-isolated"
    assert "adapter_version" not in payload

    durable_path = evidence_root / "grok-receipt.json"
    assert durable_path.is_file()
    durable_data = json.loads(durable_path.read_text(encoding="utf-8"))
    assert durable_data["run_id"] == "test-run-isolated"

    index_path = evidence_root / "index.json"
    assert index_path.is_file()
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_data["hosts"]["grok"]["run_id"] == "test-run-isolated"

    # 2. Write with update_durable=False
    run_dir2 = tmp_path / "run2"
    run_dir2.mkdir(parents=True)
    receipt.run_id = "test-run-transient"
    receipt_path2 = ei.write_verification_evidence(
        receipt,
        evidence_root=evidence_root,
        run_dir=run_dir2,
        host="grok",
        update_durable=False,
    )
    assert receipt_path2 == run_dir2 / "receipt.json"
    assert receipt_path2.is_file()
    # Durable file and index must not be updated to test-run-transient
    durable_data2 = json.loads(durable_path.read_text(encoding="utf-8"))
    assert durable_data2["run_id"] == "test-run-isolated"


def test_cleanup_method_eliminated_from_portable_verifier() -> None:
    """PortableVerifier.cleanup() was a dead no-op method (#615)."""
    assert not hasattr(PortableVerifier, "cleanup")


def test_change_resolution_frozen_dataclass_and_semantics() -> None:
    """ChangeResolution is a frozen dataclass with Literal states and tuple compatibility (#615)."""
    from dataclasses import FrozenInstanceError, is_dataclass
    import scripts.openspec_change as oc

    assert is_dataclass(oc.ChangeResolution)

    res = oc.resolve_openspec_change("explicit-change")
    assert isinstance(res, oc.ChangeResolution)
    assert res.state == "explicit"
    assert res.name == "explicit-change"
    assert res.names == []
    assert res.candidates == []

    # Frozen immutability check
    with pytest.raises(FrozenInstanceError):
        res.state = "none"  # type: ignore[misc]

    # Tuple unpacking and indexing backwards compatibility
    state, name, names = res
    assert (state, name, names) == ("explicit", "explicit-change", [])
    assert res[0] == "explicit"
    assert res[1] == "explicit-change"
    assert res[:2] == ("explicit", "explicit-change")

    # Ambiguous resolution
    ambig = oc.ChangeResolution(state="ambiguous", name=None, names=["ch1", "ch2"])
    assert ambig.state == "ambiguous"
    assert ambig.name is None
    assert ambig.candidates == ["ch1", "ch2"]
    assert ambig[2] == ["ch1", "ch2"]


def test_check_rules_typed_named_tuple_and_typed_dict() -> None:
    """CHECK_SELECTION_TABLE rules are typed CheckRule instances (#615)."""
    import scripts.select_checks as sc

    assert issubclass(sc.CheckRule, tuple)
    assert len(sc.CHECK_SELECTION_TABLE) > 0

    for rule in sc.CHECK_SELECTION_TABLE:
        assert isinstance(rule, sc.CheckRule)
        assert isinstance(rule.pattern, str)
        assert isinstance(rule.module_tokens, tuple)
        assert isinstance(rule.verifier_commands, tuple)
        # Property aliases
        assert rule.tests == rule.module_tokens
        assert rule.commands == rule.verifier_commands
        # Tuple indexing and unpacking
        pat, tests, cmds = rule
        assert pat == rule.pattern
        assert tests == rule.module_tokens
        assert cmds == rule.verifier_commands

    # TypedDict structure validation
    plan = sc.select_checks_plan("main", "HEAD")
    assert "patch_id" in plan
    assert "checks" in plan
    assert "unmapped_paths" in plan
    assert isinstance(plan["checks"], list)
    if plan["checks"]:
        first = plan["checks"][0]
        assert "id" in first
        assert "tier" in first
        assert "command" in first
        assert "paths" in first


def test_proof_bar_fails_closed_on_missing_descriptor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#735: proof_bar fails closed with RuntimeError when package descriptor is missing."""
    fake_root = tmp_path / "fake_root"
    fake_root.mkdir()
    monkeypatch.setattr(verify_portable, "ROOT", fake_root)

    class DummyDriver:
        def is_available(self):
            return (False, "none")
        def get_version(self):
            return ""

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: DummyDriver())
    verifier = PortableVerifier("grok", tmp_path / "evidence")
    with pytest.raises(RuntimeError, match="Package descriptor missing at"):
        verifier.proof_bar()


def test_proof_bar_fails_closed_on_corrupt_descriptor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#735: proof_bar fails closed with RuntimeError when package descriptor is corrupt JSON."""
    fake_root = tmp_path / "fake_root"
    fake_root.mkdir()
    (fake_root / "pstack.package.json").write_text("{corrupt json", encoding="utf-8")
    monkeypatch.setattr(verify_portable, "ROOT", fake_root)

    class DummyDriver:
        def is_available(self):
            return (False, "none")
        def get_version(self):
            return ""

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: DummyDriver())
    verifier = PortableVerifier("grok", tmp_path / "evidence")
    with pytest.raises(RuntimeError, match="Corrupt or unreadable package descriptor"):
        verifier.proof_bar()


def test_proof_bar_fails_closed_on_descriptor_missing_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#735: proof_bar fails closed with RuntimeError when package descriptor lacks version."""
    fake_root = tmp_path / "fake_root"
    fake_root.mkdir()
    (fake_root / "pstack.package.json").write_text(json.dumps({"name": "test-pkg"}), encoding="utf-8")
    monkeypatch.setattr(verify_portable, "ROOT", fake_root)

    class DummyDriver:
        def is_available(self):
            return (False, "none")
        def get_version(self):
            return ""

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: DummyDriver())
    verifier = PortableVerifier("grok", tmp_path / "evidence")
    with pytest.raises(RuntimeError, match="missing required 'version' field"):
        verifier.proof_bar()


def test_resolve_host_version_live_driver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDriver:
        def is_available(self):
            return (True, "available")
        def get_version(self):
            return "2.4.6"

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: MockDriver())
    v = verify_portable.resolve_host_version("grok", tmp_path)
    assert v == "2.4.6"


def test_resolve_host_version_descriptor_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDriver:
        def is_available(self):
            return (False, "none")
        def get_version(self):
            return ""

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: MockDriver())
    (tmp_path / "pstack.package.json").write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")
    v = verify_portable.resolve_host_version("grok", tmp_path)
    assert v == "1.2.3"


def test_resolve_host_version_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class MockDriver:
        def is_available(self):
            return (False, "none")
        def get_version(self):
            return ""

    monkeypatch.setattr(verify_portable, "get_driver", lambda host, root: MockDriver())
    with pytest.raises(RuntimeError, match="Package descriptor missing at"):
        verify_portable.resolve_host_version("grok", tmp_path)


def test_normalize_scenarios_replaces_worktree_paths() -> None:
    root = Path("/tmp/worktree/pstack")
    canon = Path("/home/user/pstack")
    scenarios = [
        ScenarioResult(
            id="s1",
            description="run command",
            plane="command",
            command=f"python3 {root}/scripts/test.py",
            exit_code=0,
            stdout_snippet=f"output at {root}/log.txt",
            verdict="PASS",
            duration_s=0.5,
        ),
        ScenarioResult(
            id="s2",
            description="another command",
            plane="runtime",
            command="echo hello",
            exit_code=0,
            stdout_snippet=None,
            verdict="PASS",
            duration_s=0.1,
        ),
    ]

    normalized = verify_portable.normalize_scenarios(scenarios, root, canon)
    assert len(normalized) == 2
    assert normalized[0].command == f"python3 {canon}/scripts/test.py"
    assert normalized[0].stdout_snippet == f"output at {canon}/log.txt"
    assert normalized[1].command == "echo hello"
    assert normalized[1].stdout_snippet is None

    # When roots match, same instances are returned
    same = verify_portable.normalize_scenarios(scenarios, canon, canon)
    assert same == scenarios


def test_run_verifier_action_doctor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import argparse
    verifier = PortableVerifier("grok", tmp_path / "evidence")
    args = argparse.Namespace(allow_stale=False, feature=None, host="grok")
    receipt, ok = verify_portable.run_verifier_action(verifier, "doctor", args)
    assert isinstance(receipt, VerificationReceipt)
    assert ok is True


def test_run_verifier_action_unknown(tmp_path: Path) -> None:
    import argparse
    verifier = PortableVerifier("grok", tmp_path / "evidence")
    args = argparse.Namespace(allow_stale=False, feature=None, host="grok")
    with pytest.raises(ValueError, match="Unknown verifier action"):
        verify_portable.run_verifier_action(verifier, "invalid-action", args)


def test_render_verification_summary(capsys: pytest.CaptureFixture) -> None:
    receipt = VerificationReceipt(
        run_id="run-1",
        host="grok",
        host_version="1.0",
        timestamp="2026-10-24T00:00:00Z",
        overall_verdict="PASS",
        planes={"canonical": "PASS", "adapter": "PASS", "package": "PASS", "runtime": "PASS"},
        surface_revisions=verify_portable.compute_surface_revisions(ROOT, "grok"),
        scenarios=[],
        artifacts=[],
        claim="claim",
    )
    verify_portable.render_verification_summary("doctor", [receipt], all_pass=True)
    out = capsys.readouterr().out
    assert "Verification Summary" in out
    assert "Host: grok" in out
    assert "1-Harness Matrix Verdict: PASS" in out




