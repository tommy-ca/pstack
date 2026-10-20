import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    Binding,
    CONFORMANCE_PLANES,
    Evidence,
    HarnessProfile,
    PLANE_SURFACE_DEPENDENCIES,
    ValidationError,
    VerificationReceipt,
    check_evidence_durability,
    compute_surface_revisions,
)
from tests.evidence_test_helpers import (
    _declared_hosts,
    _disposable_copy,
    _load_verify_portable_module,
    _omp_profile,
)


SIX_HARNESSES = _declared_hosts()

RECEIPT_SCHEMA = ROOT / "schemas" / "portability" / "receipt.schema.json"
EVIDENCE_DIR = ROOT / ".audit" / "evidence"


def test_receipt_json_schema_exists_and_valid() -> None:
    assert RECEIPT_SCHEMA.is_file()
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "VerificationReceipt" in schema["title"]
    assert "surface_revisions" in schema["required"]
    assert "scenarios" in schema["required"]


def test_durable_receipts_exist_for_all_five_hosts() -> None:
    assert EVIDENCE_DIR.is_dir()
    index_file = EVIDENCE_DIR / "index.json"
    assert index_file.is_file(), "index.json should exist in .audit/evidence"
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    assert "hosts" in index_data

    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        receipt_file = EVIDENCE_DIR / f"{host}-receipt.json"
        assert receipt_file.is_file(), f"Durable receipt missing for host {host}"
        data = json.loads(receipt_file.read_text(encoding="utf-8"))

        receipt = VerificationReceipt(**data)
        receipt.validate()
        assert receipt.host == host

        live_rows = [s for s in receipt.scenarios if s.evidence_level == "observed_live"]
        if host == "omp":
            assert receipt.overall_verdict == "PASS"
            assert receipt.planes == {
                "canonical": "PASS",
                "adapter": "PASS",
                "package": "PASS",
                "runtime": "PASS",
            }
            assert {s.id for s in live_rows} == {
                "runtime-child-spawn-omp",
                "runtime-child-cancel-omp",
                "runtime-isolation-omp",
            }
            assert all(
                s.plane == "runtime" and s.verdict == "PASS" and s.settlement is not None
                for s in live_rows
            )
        else:
            assert receipt.overall_verdict == "UNTESTED"
            assert receipt.planes == {
                "canonical": "PASS",
                "adapter": "PASS",
                "package": "PASS",
                "runtime": "UNTESTED",
            }
            assert [s for s in receipt.scenarios if s.plane == "runtime"] == []
            assert live_rows == []

        assert receipt.evaluate_plane_staleness(receipt.surface_revisions) == {
            plane: [] for plane in CONFORMANCE_PLANES
        }
        staleness = receipt.evaluate_plane_staleness(compute_surface_revisions(ROOT, host))
        assert set(staleness.keys()) == set(CONFORMANCE_PLANES)

        assert host in index_data["hosts"]
        entry = index_data["hosts"][host]
        assert entry["overall_verdict"] == receipt.overall_verdict
        assert entry["planes"] == receipt.planes
        assert entry["run_id"] == data["run_id"], f"index run_id stale for {host}"
        assert entry["timestamp"] == data["timestamp"], f"index timestamp stale for {host}"
        assert entry["surface_revisions"] == data["surface_revisions"], f"index revisions stale for {host}"


def test_all_six_profiles_pass_evidence_durability_and_freshness() -> None:
    for host in SIX_HARNESSES:
        profile_file = ROOT / "profiles" / f"{host}.json"
        assert profile_file.is_file()
        d = json.loads(profile_file.read_text(encoding="utf-8"))
        b = [Binding(**x) for x in d.get("bindings", [])]
        e = [Evidence(**x) for x in d.get("evidence_ledger", [])]
        prof = HarnessProfile(
            host=d["host"],
            support_state=d["support_state"],
            bindings=b,
            skills_dir=d.get("skills_dir"),
            plugins_dir=d.get("plugins_dir"),
            plugin_manifest=d.get("plugin_manifest"),
            evidence_ledger=e,
            tool_mappings=d.get("tool_mappings"),
            skill_order=d.get("skill_order"),
            runtime_conventions=d.get("runtime_conventions"),
        )
        prof.validate()

        result = check_evidence_durability(prof, ROOT, check_freshness=True)
        assert result["valid"] is True
        expected_state = "candidate" if host == "droid" else "packaged"
        assert result["claimed_support_state"] == expected_state
        assert result["derived_support_state"] == expected_state

        method_result = prof.validate_evidence(ROOT, check_freshness=True)
        assert method_result["valid"] is True


test_all_five_profiles_pass_evidence_durability_and_freshness = test_all_six_profiles_pass_evidence_durability_and_freshness


def test_dangling_evidence_path_fails(tmp_path: Path) -> None:
    profile_data = json.loads((ROOT / "profiles" / "codex.json").read_text(encoding="utf-8"))
    profile_data["bindings"][0]["evidence_ref"] = ".audit/evidence/non-existent-receipt.json"

    b = [Binding(**x) for x in profile_data["bindings"]]
    e = [Evidence(**x) for x in profile_data.get("evidence_ledger", [])]
    prof = HarnessProfile(
        host=profile_data["host"],
        support_state=profile_data["support_state"],
        bindings=b,
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        evidence_ledger=e,
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )

    with pytest.raises(ValidationError, match="Dangling evidence path"):
        check_evidence_durability(prof, ROOT)


def test_omp_profile_claims_only_what_its_receipt_settles() -> None:
    prof = _omp_profile()
    assert prof.support_state == "packaged"
    assert check_evidence_durability(prof, ROOT, check_freshness=False)["derived_support_state"] == "packaged"

    receipt = VerificationReceipt(
        **json.loads((EVIDENCE_DIR / "omp-receipt.json").read_text(encoding="utf-8"))
    )
    recorded = {s.id for s in receipt.scenarios}
    assert receipt.planes["runtime"] == "PASS", "the supported run path observed the runtime plane"
    live = {s.id: s for s in receipt.scenarios if s.evidence_level == "observed_live"}
    assert set(live) == {
        "runtime-child-spawn-omp",
        "runtime-child-cancel-omp",
        "runtime-isolation-omp",
    }

    assert {
        b.capability: b.scenario_id for b in prof.bindings if b.verification_status == "verified"
    } == {
        "agent.spawn": "runtime-child-spawn-omp",
        "agent.join": "runtime-child-spawn-omp",
        "agent.cancel": "runtime-child-cancel-omp",
        "workspace.isolated": "runtime-isolation-omp",
    }
    assert {b.verification_status for b in prof.bindings} == {"verified", "static-only", "unverified"}

    for b in prof.bindings:
        if not b.scenario_id:
            continue
        assert b.scenario_id in recorded, f"{b.capability} pins an unrecorded scenario"
        assert b.receipt_ref == ".audit/evidence/omp-receipt.json"
        if b.verification_status == "verified":
            assert b.scenario_id in live, f"{b.capability} claims verified off a non-live scenario"

    assert {
        b.capability: b.scenario_id
        for b in prof.bindings
        if b.scenario_id and b.verification_status != "verified"
    } == {"verify": "doctor-profile-omp"}


def test_scenario_pin_naming_an_unrecorded_scenario_fails() -> None:
    """A pin that names no scenario in the cited receipt is a dangling reference."""
    d = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    pinned = [b for b in d["bindings"] if isinstance(b.get("evidence_ref"), dict)]
    assert pinned, "the omp profile must pin scenarios"
    for binding in pinned:
        binding["evidence_ref"] = {
            "receipt": ".audit/evidence/omp-receipt.json",
            "scenario": "invented-scenario",
        }

    with pytest.raises(ValidationError, match="cites scenario 'invented-scenario'"):
        check_evidence_durability(_omp_profile(d), ROOT, check_freshness=False)


def test_verified_binding_cannot_pin_a_non_live_scenario() -> None:
    d = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in d["bindings"]:
        if binding["capability"] == "agent.spawn":
            binding["verification_status"] = "verified"
            binding["evidence_ref"] = {
                "receipt": ".audit/evidence/omp-receipt.json",
                "scenario": "doctor-profile-omp",
            }

    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_evidence_durability(_omp_profile(d), ROOT, check_freshness=False)


def test_stale_skills_tree_hash_invalidates_runtime() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)

    tampered_revs = replace(current_revs, skills_tree_hash="0000000000000000000000000000000000000000000000000000000000000000")
    receipt.surface_revisions = tampered_revs

    stale_map = receipt.evaluate_plane_staleness(current_revs)
    assert len(stale_map["runtime"]) > 0
    assert any("skills_tree_hash mismatch" in r for r in stale_map["runtime"])
    assert len(stale_map["canonical"]) == 0
    assert len(stale_map["adapter"]) == 0
    assert len(stale_map["package"]) == 0


def test_stale_profile_hash_invalidates_adapter_and_runtime() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)

    tampered_revs = replace(current_revs, profile_hash="1111111111111111111111111111111111111111111111111111111111111111")
    receipt.surface_revisions = tampered_revs

    stale_map = receipt.evaluate_plane_staleness(current_revs)
    assert len(stale_map["adapter"]) > 0
    assert len(stale_map["runtime"]) > 0
    assert any("profile_hash mismatch" in r for r in stale_map["adapter"])
    assert any("profile_hash mismatch" in r for r in stale_map["runtime"])
    assert len(stale_map["canonical"]) == 0
    assert len(stale_map["package"]) == 0


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity"])
def test_stale_package_driver_rejected_for_packaged_claim(host: str) -> None:
    profile_data = json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))
    assert profile_data["support_state"] == "packaged"
    b = [Binding(**x) for x in profile_data["bindings"]]
    e = [Evidence(**x) for x in profile_data.get("evidence_ledger", [])]
    prof = HarnessProfile(
        host=profile_data["host"],
        support_state=profile_data["support_state"],
        bindings=b,
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        evidence_ledger=e,
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )
    current_revs = compute_surface_revisions(ROOT, host)
    tampered_revs = replace(current_revs, package_driver_revision="stale-package-driver")
    with pytest.raises(ValidationError, match="evidence is stale"):
        check_evidence_durability(prof, ROOT, check_freshness=True, current_revisions=tampered_revs)


def test_a_verified_claim_evaluates_the_package_plane(tmp_path: Path) -> None:
    from tests.test_evidence_settlement import _synthetic_evidence_root, _success_settlement

    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, _success_settlement()],
        force_verified=True,
    )
    assert prof.support_state == "verified"
    assert check_evidence_durability(prof, root)["derived_support_state"] == "supported"

    tampered = replace(
        compute_surface_revisions(root, "omp"), package_driver_revision="stale-package-driver"
    )
    with pytest.raises(ValidationError, match="evidence is stale for claimed verified") as refused:
        check_evidence_durability(prof, root, current_revisions=tampered)
    assert "package_driver_revision mismatch" in str(refused.value)


def test_stale_package_descriptor_invalidates_package_and_runtime() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)

    tampered_revs = replace(current_revs, package_descriptor_hash="2222222222222222222222222222222222222222222222222222222222222222")
    receipt.surface_revisions = tampered_revs

    stale_map = receipt.evaluate_plane_staleness(current_revs)
    assert len(stale_map["package"]) > 0
    assert len(stale_map["runtime"]) > 0
    assert len(stale_map["canonical"]) == 0
    assert len(stale_map["adapter"]) == 0


def test_stale_spec_invalidates_canonical() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)

    tampered_revs = replace(current_revs, spec_hash="3333333333333333333333333333333333333333333333333333333333333333")
    receipt.surface_revisions = tampered_revs

    stale_map = receipt.evaluate_plane_staleness(current_revs)
    assert len(stale_map["canonical"]) > 0
    assert len(stale_map["adapter"]) == 0
    assert len(stale_map["package"]) == 0
    assert len(stale_map["runtime"]) == 0


def test_docs_changes_do_not_stale_any_plane() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    for plane, deps in PLANE_SURFACE_DEPENDENCIES.items():
        assert "docs" not in "".join(deps)
        assert "readme" not in "".join(deps)

    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)
    receipt.surface_revisions = current_revs
    stale_map = receipt.evaluate_plane_staleness(current_revs)
    for plane in CONFORMANCE_PLANES:
        assert len(stale_map[plane]) == 0


def test_hand_authored_support_state_cannot_outrun_evidence() -> None:
    profile_data = json.loads((ROOT / "profiles" / "grok.json").read_text(encoding="utf-8"))
    b = [Binding(**{**x, "verification_status": "verified"}) for x in profile_data["bindings"]]
    e = [Evidence(**x) for x in profile_data.get("evidence_ledger", [])]
    prof = HarnessProfile(
        host=profile_data["host"],
        support_state="supported",
        bindings=b,
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        evidence_ledger=e,
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )

    current_revs = compute_surface_revisions(ROOT, "grok")
    tampered_revs = replace(current_revs, skills_tree_hash="stale-hash-12345")

    with pytest.raises(ValidationError, match="evidence is stale"):
        check_evidence_durability(prof, ROOT, check_freshness=True, current_revisions=tampered_revs)


def test_check_staleness_cli_json_output() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-staleness", "--host", "all", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode in (0, 1)
    data = json.loads(res.stdout)
    assert len(data) >= 6
    for host in SIX_HARNESSES:
        assert host in data
        assert isinstance(data[host]["needs_regeneration"], bool)
        assert isinstance(data[host]["stale_planes"], list)
        if not data[host]["needs_regeneration"]:
            assert data[host]["stale_planes"] == []
        else:
            assert len(data[host]["stale_planes"]) > 0
        claimed = json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))["support_state"]
        if host == "droid":
            assert data[host]["support_state"] == "candidate"
            assert claimed == "candidate"
        else:
            expected_overall = "PASS" if host == "omp" else "UNTESTED"
            assert data[host]["overall_verdict"] == expected_overall
            assert claimed == "packaged"


def test_check_evidence_cli_output() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-evidence", "--host", "all"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    for host in SIX_HARNESSES:
        if host == "droid":
            assert "[droid] NOT_COVERED" in res.stdout
            continue
        assert (
            f"[{host}] PASS: Evidence durable, derived support state: packaged (claimed: packaged)"
            in res.stdout
        )


def test_candidate_row_reports_not_covered_not_pass() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-evidence", "--host", "droid"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "[droid] NOT_COVERED" in res.stdout
    assert "[droid] PASS" not in res.stdout


def test_check_evidence_fails_when_a_row_disagrees_with_its_receipt(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), "check-evidence", "--host", "grok"]

    clean = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert clean.returncode == 0, clean.stdout + clean.stderr

    index_file = copy_root / ".audit" / "evidence" / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    index["hosts"]["grok"]["run_id"] = "hand-edited-run-id"
    index_file.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    tampered = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert tampered.returncode == 1, tampered.stdout + tampered.stderr
    assert "[grok] FAIL" in tampered.stdout
    assert "run_id" in tampered.stdout and "hand-edited-run-id" in tampered.stdout
    assert "grok-receipt.json" in tampered.stdout


def test_a_row_less_host_with_a_durable_receipt_reports_rebuild_required(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    command = [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), "check-evidence"]

    clean = subprocess.run(command + ["--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert clean.returncode == 0, clean.stdout + clean.stderr

    index_file = copy_root / ".audit" / "evidence" / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    del index["hosts"]["grok"]
    index_file.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    row_less = subprocess.run(command + ["--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert row_less.returncode == 1, row_less.stdout + row_less.stderr
    assert "STALE/REBUILD-REQUIRED" in row_less.stdout
    assert "grok-receipt.json" in row_less.stdout

    droid = subprocess.run(command + ["--host", "droid"], capture_output=True, text=True, cwd=copy_root)
    assert droid.returncode == 0, droid.stdout + droid.stderr

    del index["hosts"]["codex"]
    index_file.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    (copy_root / ".audit" / "evidence" / "codex-receipt.json").write_text("{not json", encoding="utf-8")
    unreadable = subprocess.run(command + ["--host", "codex"], capture_output=True, text=True, cwd=copy_root)
    assert unreadable.returncode == 1, unreadable.stdout + unreadable.stderr
    assert "cannot be read as a usable receipt" in unreadable.stdout
    assert "STALE/REBUILD-REQUIRED" not in unreadable.stdout

    index_file.unlink()
    deleted = subprocess.run(command + ["--host", "grok"], capture_output=True, text=True, cwd=copy_root)
    assert deleted.returncode == 1, deleted.stdout + deleted.stderr
    assert "is missing" in deleted.stdout
    assert "refresh-static --host all" in deleted.stdout


def test_refresh_static_is_partial_and_never_rounds_a_failure_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_verify_portable_module()
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    receipt_hosts = ["grok", "codex", "omp", "opencode", "antigravity"]
    names = [f"{host}-receipt.json" for host in receipt_hosts] + ["index.json"]
    for name in names:
        shutil.copy2(EVIDENCE_DIR / name, evidence_root / name)
    untouched = {name: (evidence_root / name).read_bytes() for name in names}
    index_before = json.loads(untouched["index.json"])

    def static_doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        assert check_durability is False, "a static refresh must not re-read the durable evidence"
        for plane in ("canonical", "adapter", "package"):
            self.scenarios.append(
                module.ScenarioResult(
                    id=f"doctor-{plane}-stub",
                    description=f"stub static {plane} plane",
                    plane=plane,
                    command="stub",
                    exit_code=0,
                    stdout_snippet="stub",
                    verdict="PASS",
                    duration_s=0.0,
                )
            )
        return True

    def failing_doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        self.scenarios.append(
            module.ScenarioResult(
                id="doctor-package-stub",
                description="stub failing package plane",
                plane="package",
                command="stub",
                exit_code=1,
                stdout_snippet="stub failure",
                verdict="FAIL",
                duration_s=0.0,
            )
        )
        return False

    monkeypatch.setattr(module, "resolve_openspec_change", lambda change: ("none", None, []))
    monkeypatch.setattr(
        sys,
        "argv",
        ["verify-portable.py", "refresh-static", "--host", "omp", "--evidence-dir", str(evidence_root)],
    )

    monkeypatch.setattr(module.PortableVerifier, "doctor", static_doctor)
    with pytest.raises(SystemExit) as exit_info:
        module.main()
    assert exit_info.value.code == 0

    refreshed = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**refreshed)
    receipt.validate()
    assert receipt.planes == {
        "canonical": "PASS",
        "adapter": "PASS",
        "package": "PASS",
        "runtime": "UNTESTED",
    }
    assert receipt.overall_verdict == "UNTESTED"
    assert [s for s in receipt.scenarios if s.plane == "runtime"] == []
    assert receipt.evaluate_plane_staleness(compute_surface_revisions(ROOT, "omp")) == {
        plane: [] for plane in CONFORMANCE_PLANES
    }

    for host in receipt_hosts:
        if host == "omp":
            continue
        assert (evidence_root / f"{host}-receipt.json").read_bytes() == untouched[f"{host}-receipt.json"]
    index_after = json.loads((evidence_root / "index.json").read_text(encoding="utf-8"))
    assert sorted(index_after["hosts"]) == sorted(index_before["hosts"])
    assert index_after["hosts"]["omp"]["run_id"] == refreshed["run_id"]
    assert index_after["hosts"]["omp"]["overall_verdict"] == "UNTESTED"
    for host in receipt_hosts:
        if host == "omp":
            continue
        assert index_after["hosts"][host] == index_before["hosts"][host]

    monkeypatch.setattr(module.PortableVerifier, "doctor", failing_doctor)
    with pytest.raises(SystemExit) as failing_exit:
        module.main()
    assert failing_exit.value.code == 1

    failed = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    assert failed["planes"]["package"] == "FAIL"
    assert failed["overall_verdict"] == "FAIL"


