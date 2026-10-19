import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    Binding,
    ChildSettlement,
    CONFORMANCE_PLANES,
    CONDITIONAL_CAPABILITIES,
    Evidence,
    HarnessProfile,
    MANDATORY_SUPPORT_FLOOR,
    ScenarioResult,
    SurfaceRevisions,
    ValidationError,
    VerificationReceipt,
    _is_observed_settlement,
    _row_level,
    check_evidence_durability,
    check_scenario_pins,
    compute_surface_revisions,
    derive_support_state,
    preserve_observed_settlements,
    reduce_verdicts,
    settle_planes,
)

RECEIPT_SCHEMA = ROOT / "schemas" / "portability" / "receipt.schema.json"
EVIDENCE_DIR = ROOT / ".audit" / "evidence"


def _declared_from(scenarios: list) -> tuple:
    """The planes and overall verdict a run's own scenarios reduce to.

    Fixtures declare planes the way a driver writes them — from the reduction — because
    `VerificationReceipt.validate` refuses a declaration that floats free of its scenarios
    (#473). A receipt that observed nothing declares UNTESTED, not PASS.
    """
    planes = settle_planes(scenarios)
    return planes, reduce_verdicts(planes.values())


def _plane_rows(covered: set, verdict: str = "PASS") -> list:
    """One `verdict` scenario per conformance plane not already covered by a fixture row,
    so a fixture that claims a whole-receipt shape proves each plane it declares."""
    return [
        ScenarioResult(
            id=f"synthetic-{plane}-plane-row",
            description=f"synthetic {plane} plane row",
            plane=plane,
            command="true",
            exit_code=0 if verdict == "PASS" else 1,
            stdout_snippet=f"{plane} fixture row",
            verdict=verdict,
            duration_s=0.01,
            evidence_level="offline",
        )
        for plane in CONFORMANCE_PLANES
        if plane not in covered
    ]


def _synthetic_evidence_root(tmp_path: Path, evidence_levels: list, planes: list | None = None, host: str = "omp", snippets: list | None = None, settlements: list | None = None, force_verified: bool = False) -> tuple:
    """Self-consistent minimal root: every OMP binding points at one synthetic receipt
    whose scenario (evidence_level, plane) pairs are exactly zipped `evidence_levels`,
    plus one row per remaining plane so the receipt's declared planes are its own
    reduction instead of a hand-written PASS (#473)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "pstack.package.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / ".omp-plugin" / "package.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")

    revisions = compute_surface_revisions(tmp_path, host)
    ref = ".audit/evidence/synthetic-receipt.json"
    scenarios = [
        ScenarioResult(
            id=f"synthetic-{i}",
            description="synthetic scenario",
            plane=(planes[i] if planes else "runtime"),
            command="true",
            exit_code=0,
            stdout_snippet=(snippets[i] if snippets else ""),
            verdict="PASS",
            duration_s=0.01,
            evidence_level=level,
            settlement=(settlements[i] if settlements else None),
        )
        for i, level in enumerate(evidence_levels)
    ]
    scenarios += _plane_rows({s.plane for s in scenarios})
    declared, overall = _declared_from(scenarios)
    receipt = VerificationReceipt(
        run_id="evidence-level-gate",
        host=host,
        host_version="test",
        timestamp="2026-10-11T00:00:00Z",
        overall_verdict=overall,
        planes=declared,
        surface_revisions=revisions,
        scenarios=scenarios,
    )
    receipt_path = tmp_path / ref
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(asdict(receipt)), encoding="utf-8")

    d = json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))
    for binding in d["bindings"]:
        binding["evidence_ref"] = ref
        if force_verified:
            binding["verification_status"] = "verified"
    prof = HarnessProfile(
        host=d["host"],
        support_state="verified",
        bindings=[Binding(**x) for x in d["bindings"]],
        skills_dir=d.get("skills_dir"),
        plugins_dir=d.get("plugins_dir"),
        plugin_manifest=d.get("plugin_manifest"),
        tool_mappings=d.get("tool_mappings"),
        skill_order=d.get("skill_order"),
        runtime_conventions=d.get("runtime_conventions"),
    )
    return tmp_path, prof


def test_offline_only_receipt_derives_packaged_not_verified(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(tmp_path, ["offline", "offline"], force_verified=True)
    assert prof.support_state == "verified"
    assert derive_support_state(prof, root) == "packaged"
    with pytest.raises(ValidationError, match="exceeds evidence-derived support state 'packaged'"):
        check_evidence_durability(prof, root)


def test_observed_live_scenario_still_derives_verified(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[
            None,
            ChildSettlement(
                child_id="subagent-7",
                terminal_outcome="success",
                model="test-model",
                transport="rpc",
                effective_rpc="rpc-v2:profile=disposable:depth=1",
            ),
        ],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "supported"
    assert check_evidence_durability(prof, root)["derived_support_state"] == "supported"


def test_adapter_pass_with_package_fail_is_never_an_accepted_package_pass(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[
            None,
            ChildSettlement(
                child_id="subagent-7",
                terminal_outcome="success",
                model="test-model",
                transport="rpc",
                effective_rpc="rpc-v2:profile=disposable:depth=1",
            ),
        ],
        force_verified=True,
    )

    receipt_path = root / ".audit" / "evidence" / "synthetic-receipt.json"
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["planes"] == {
        "canonical": "PASS",
        "adapter": "PASS",
        "package": "PASS",
        "runtime": "PASS",
    }
    for row in data["scenarios"]:
        if row["plane"] == "package":
            row["verdict"], row["exit_code"] = "FAIL", 1
    data["planes"], data["overall_verdict"] = _declared_from(
        [ScenarioResult(**row) for row in data["scenarios"]]
    )
    receipt_path.write_text(json.dumps(data), encoding="utf-8")

    assert derive_support_state(prof, root) == "verified"
    with pytest.raises(ValidationError, match="exceeds evidence-derived support state 'verified'"):
        check_evidence_durability(replace(prof, support_state="supported"), root)


def test_bare_live_label_without_settlement_stays_packaged(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(tmp_path, ["offline", "observed_live"], force_verified=True)
    assert derive_support_state(prof, root) == "packaged"


def test_static_isolation_row_cannot_satisfy_the_runtime_plane_on_its_own() -> None:
    static_isolation = ScenarioResult(
        id="runtime-isolation-omp",
        description="static isolation surface probe",
        plane="runtime",
        command="omp task --isolation git-worktree --help",
        exit_code=0,
        stdout_snippet="isolation surface present",
        verdict="PASS",
        duration_s=0.01,
        evidence_level="static",
    )
    receipt = VerificationReceipt(
        run_id="static-isolation-probe",
        host="omp",
        host_version="test",
        timestamp="2026-10-17T00:00:00Z",
        overall_verdict="UNTESTED",
        planes={plane: "UNTESTED" for plane in CONFORMANCE_PLANES},
        surface_revisions=compute_surface_revisions(ROOT, "omp"),
        scenarios=[static_isolation],
    )
    receipt.planes, receipt.overall_verdict = _declared_from(receipt.scenarios)
    receipt.validate()
    assert receipt.planes["runtime"] == "UNTESTED", "a static row never claims a live plane"

    ref = ".audit/evidence/omp-receipt.json"
    profile_data = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in profile_data["bindings"]:
        binding["evidence_ref"] = ref
        if binding["capability"] == "workspace.isolated":
            binding["verification_status"] = "verified"
            binding["evidence_ref"] = {"receipt": ref, "scenario": "runtime-isolation-omp"}
    profile = HarnessProfile(
        host=profile_data["host"],
        support_state="packaged",
        bindings=[Binding(**x) for x in profile_data["bindings"]],
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(profile, {ref: receipt})

    live_receipt = replace(
        receipt,
        scenarios=[
            replace(
                static_isolation,
                evidence_level="observed_live",
                settlement=ChildSettlement(
                    child_id="IsoChild",
                    terminal_outcome="success",
                    model="test-model",
                    transport="rpc",
                    effective_rpc="rpc-v2",
                ),
            )
        ],
    )
    live_receipt.planes, live_receipt.overall_verdict = _declared_from(live_receipt.scenarios)
    assert live_receipt.planes["runtime"] == "PASS", "the settled row is what promotes the plane"
    live_receipt.validate()
    check_scenario_pins(profile, {ref: live_receipt})


def test_non_runtime_live_does_not_prove_runtime(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path, ["observed_live", "offline"], planes=["canonical", "runtime"], force_verified=True
    )
    assert derive_support_state(prof, root) == "packaged"


def test_legacy_or_missing_evidence_level_never_proves_live(tmp_path: Path) -> None:
    ScenarioResult(
        id="legacy", description="legacy", plane="runtime", command="true", exit_code=0,
        stdout_snippet="", verdict="PASS", duration_s=0.01, evidence_level="legacy",
    ).validate()

    for levels in (["legacy"], ["observed_live", None], []):
        root, prof = _synthetic_evidence_root(tmp_path / "_".join(str(l) for l in levels), list(levels), force_verified=True)
        assert derive_support_state(prof, root) == "packaged"


def _receipt_evidence_levels() -> set:
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"]["scenarios"]["items"]["properties"]["evidence_level"]["enum"])


@pytest.mark.parametrize("evidence_level", ["live", "documented"])
def test_invented_evidence_level_rejects_an_omp_receipt_shaped_scenario(evidence_level: str) -> None:
    enum = _receipt_evidence_levels()
    assert enum == {"static", "offline", "observed_live", "legacy"}
    assert evidence_level not in enum

    durable_receipt = json.loads((EVIDENCE_DIR / "omp-receipt.json").read_text(encoding="utf-8"))
    tampered = json.loads(json.dumps(durable_receipt))
    target = next(s for s in tampered["scenarios"] if s["id"] == "doctor-profile-omp")
    assert target["evidence_level"] == "offline"
    target["evidence_level"] = evidence_level

    with pytest.raises(ValidationError):
        ScenarioResult(**target).validate()
    with pytest.raises(ValidationError):
        VerificationReceipt(**tampered).validate()


def test_durable_receipts_keep_only_recorded_evidence_levels() -> None:
    enum = _receipt_evidence_levels()
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        receipt = json.loads((EVIDENCE_DIR / f"{host}-receipt.json").read_text(encoding="utf-8"))
        levels = {s["id"]: s["evidence_level"] for s in receipt["scenarios"]}
        assert set(levels.values()) <= enum, host
        if host == "omp":
            assert "observed_live" in set(levels.values()), host
        else:
            assert "observed_live" not in set(levels.values()), host
        assert levels[f"doctor-profile-{host}"] == "offline"


def test_driver_settlement_survives_receipt_serialization(tmp_path: Path) -> None:
    from scripts.drivers.base import DriverScenarioResult

    settlement = {
        "child_id": "subagent-9",
        "terminal_outcome": "success",
        "model": "test-model",
        "transport": "rpc",
        "effective_rpc": "rpc-v2:profile=disposable",
    }
    driver_result = DriverScenarioResult(
        scenario_id="runtime-child-spawn-omp",
        description="driver settlement propagation",
        command="omp task spawn",
        exit_code=0,
        stdout="child joined",
        stderr="",
        verdict="PASS",
        duration_s=0.05,
        evidence_level="observed_live",
        settlement=settlement,
    )
    scenario = ScenarioResult(
        id=driver_result.scenario_id,
        description=driver_result.description,
        plane="runtime",
        command=driver_result.command,
        exit_code=driver_result.exit_code,
        stdout_snippet=driver_result.stdout_snippet,
        verdict=driver_result.verdict,
        duration_s=driver_result.duration_s,
        evidence_level=driver_result.evidence_level,
        settlement=driver_result.settlement,
    )
    scenario.validate()
    blob = json.dumps(asdict(scenario))
    assert '"effective_rpc"' in blob
    assert "credential" not in blob.lower() and "api_key" not in blob.lower()
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]["scenarios"]["items"]["properties"]["settlement"]
    assert set(props["required"]) == {"child_id", "terminal_outcome", "model", "transport", "effective_rpc"}
    parsed = json.loads(blob)
    for key in props["required"]:
        assert parsed["settlement"][key]


def _omp_spawn_scenario(evidence_level: str, verdict: str = "PASS", settlement=None) -> ScenarioResult:
    return ScenarioResult(
        id="runtime-child-spawn-omp",
        description="bounded omp rpc v2 child spawn and join",
        plane="runtime",
        command="PSTACK_RUN_OMP_LIVE=1 python -m pytest tests/test_omp_rpc.py",
        exit_code=0 if verdict == "PASS" else 1,
        stdout_snippet="child=subagent-1 outcome=success" if settlement else "static evidence",
        verdict=verdict,
        duration_s=19.1,
        evidence_level=evidence_level,
        settlement=settlement,
    )


def _omp_live_root(tmp_path: Path) -> tuple:
    root = tmp_path / "repo"
    (root / ".omp-plugin").mkdir(parents=True)
    (root / "pstack.package.json").write_text("{}", encoding="utf-8")
    (root / ".omp-plugin" / "package.json").write_text("{}", encoding="utf-8")
    evidence_root = root / ".audit" / "evidence"
    evidence_root.mkdir(parents=True)
    revisions = compute_surface_revisions(root, "omp")
    scenarios = [
        _omp_spawn_scenario(
            "observed_live",
            settlement=ChildSettlement(
                child_id="subagent-1",
                terminal_outcome="success",
                model="deepseek-v4-pro",
                transport="rpc",
                effective_rpc="rpc-v2:profile=disposable:depth=1",
            ),
        )
    ] + _plane_rows({"runtime"})
    declared, overall = _declared_from(scenarios)
    live = VerificationReceipt(
        run_id="previous-live-run",
        host="omp",
        host_version="18.8.9",
        timestamp="2026-10-11T20:00:00Z",
        overall_verdict=overall,
        planes=declared,
        surface_revisions=revisions,
        scenarios=scenarios,
    )
    (evidence_root / "omp-receipt.json").write_text(json.dumps(asdict(live)), encoding="utf-8")

    profile_data = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in profile_data["bindings"]:
        binding["evidence_ref"] = ".audit/evidence/omp-receipt.json"
        binding["verification_status"] = "verified"
    prof = HarnessProfile(
        host="omp",
        support_state="verified",
        bindings=[Binding(**x) for x in profile_data["bindings"]],
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )
    return root, prof, evidence_root, revisions


def _portable_verifier(evidence_root: Path, root: Path | None = None):
    loader = importlib.util.spec_from_file_location("verify_portable_preserve", ROOT / "scripts" / "verify-portable.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    if root is not None:
        module.ROOT = root
    verifier = module.PortableVerifier(host="omp", evidence_root=evidence_root)
    verifier.launch()
    return verifier


def _proof_bar_refresh(root: Path, evidence_root: Path, *, verdict: str = "PASS") -> tuple:
    verifier = _portable_verifier(evidence_root, root=root)
    verifier.scenarios = [
        ScenarioResult(
            id=f"doctor-{plane}-stub",
            description=f"static {plane} plane",
            plane=plane,
            command="stub",
            exit_code=0,
            stdout_snippet="stub",
            verdict="PASS",
            duration_s=0.0,
        )
        for plane in ("canonical", "adapter", "package")
    ]
    verifier.scenarios.append(_omp_spawn_scenario("static", verdict=verdict))
    return verifier, verifier.proof_bar()


def test_durable_refresh_preserves_an_unchanged_observed_settlement(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)
    assert receipt.planes["runtime"] == "UNTESTED"
    assert receipt.overall_verdict == "UNTESTED"

    verifier.evidence(receipt, update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["evidence_level"] == "observed_live"
    assert scenario["settlement"]["child_id"] == "subagent-1"
    assert scenario["settlement"]["terminal_outcome"] == "success"
    assert scenario["preserved_from"] == "previous-live-run"
    assert durable["planes"]["runtime"] == "PASS"
    assert durable["overall_verdict"] == "PASS"
    assert receipt.planes["runtime"] == "PASS"
    assert receipt.overall_verdict == "PASS"
    assert check_evidence_durability(prof, root)["derived_support_state"] == "supported"


def test_durable_refresh_drops_a_settlement_once_the_runtime_surface_moved(tmp_path: Path) -> None:
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)
    moved = replace(revisions, driver_revision="moved-driver-revision")
    durable_file = evidence_root / "omp-receipt.json"
    previous = json.loads(durable_file.read_text(encoding="utf-8"))
    previous["surface_revisions"] = asdict(moved)
    durable_file.write_text(json.dumps(previous), encoding="utf-8")

    verifier, receipt = _proof_bar_refresh(root, evidence_root)
    verifier.evidence(receipt, update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["evidence_level"] == "static"
    assert scenario["settlement"] is None
    assert scenario["preserved_from"] == ""
    assert durable["planes"]["runtime"] == "UNTESTED"
    assert derive_support_state(prof, root) == "packaged"


def test_durable_refresh_does_not_paper_over_a_failing_run(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    verifier, receipt = _proof_bar_refresh(root, evidence_root, verdict="FAIL")
    verifier.evidence(receipt, update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["verdict"] == "FAIL"
    assert scenario["evidence_level"] == "static"
    assert scenario["preserved_from"] == ""
    assert durable["planes"]["runtime"] == "FAIL"
    assert derive_support_state(prof, root) == "packaged"


def test_an_unreadable_durable_receipt_is_not_overwritten(tmp_path: Path) -> None:
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"

    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    row_before = json.loads(index_file.read_text(encoding="utf-8"))["hosts"]["omp"]
    assert row_before["run_id"] == json.loads(durable.read_text(encoding="utf-8"))["run_id"]

    durable.write_text("{ not json at all", encoding="utf-8")
    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    second.evidence(second_receipt, update_durable=True)

    assert durable.read_text(encoding="utf-8") == "{ not json at all"
    assert (second.run_dir / "receipt.json").is_file()
    assert json.loads(index_file.read_text(encoding="utf-8"))["hosts"]["omp"] == row_before
    assert row_before["run_id"] != second_receipt.run_id


def test_observed_settlement_requires_a_passing_successful_scenario() -> None:
    success = ChildSettlement(
        child_id="child-1",
        terminal_outcome="success",
        model="test-model",
        transport="rpc",
        effective_rpc="rpc-v2:maxFrameBytes=1048576",
    )
    live = ScenarioResult(
        id="runtime-child-spawn-omp",
        description="observed live spawn",
        plane="runtime",
        command="omp --mode rpc",
        exit_code=0,
        stdout_snippet="child=child-1 outcome=success",
        verdict="PASS",
        duration_s=1.0,
        evidence_level="observed_live",
        settlement=success,
    )

    assert _is_observed_settlement(live) is True
    assert _is_observed_settlement(replace(live, verdict="FAIL")) is False
    assert _is_observed_settlement(replace(live, evidence_level="static")) is False
    assert (
        _is_observed_settlement(
            replace(live, settlement=replace(success, terminal_outcome="timeout"))
        )
        is False
    )
    assert (
        _is_observed_settlement(
            replace(live, settlement=replace(success, terminal_outcome="cancelled"))
        )
        is False
    )


def _observed_scenario(
    scenario_id: str, settlement: ChildSettlement | None = None
) -> ScenarioResult:
    return ScenarioResult(
        id=scenario_id,
        description="adversarial observed_live runtime row",
        plane="runtime",
        command="omp --mode rpc",
        exit_code=0,
        stdout_snippet="observed_live row",
        verdict="PASS",
        duration_s=0.01,
        evidence_level="observed_live",
        settlement=settlement,
    )


def _success_settlement() -> ChildSettlement:
    return ChildSettlement(
        child_id="subagent-7",
        terminal_outcome="success",
        model="test-model",
        transport="rpc",
        effective_rpc="rpc-v2:profile=disposable:depth=1",
    )


def _adversarial_receipt(scenario: ScenarioResult) -> VerificationReceipt:
    planes, overall = _declared_from([scenario])
    receipt = VerificationReceipt(
        run_id="p8-adversarial",
        host="omp",
        host_version="test",
        timestamp="2026-10-12T00:00:00Z",
        overall_verdict=overall,
        planes=planes,
        surface_revisions=compute_surface_revisions(ROOT, "omp"),
        scenarios=[scenario],
    )
    receipt.validate()
    return receipt


def _profile_pinning(
    receipt_ref: str, scenario_id: str, capability: str = "agent.resume"
) -> HarnessProfile:
    d = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in d["bindings"]:
        binding["evidence_ref"] = receipt_ref
        if binding["capability"] == capability:
            binding["verification_status"] = "verified"
            binding["evidence_ref"] = {"receipt": receipt_ref, "scenario": scenario_id}
    return HarnessProfile(
        host=d["host"],
        support_state=d["support_state"],
        bindings=[Binding(**x) for x in d["bindings"]],
        skills_dir=d.get("skills_dir"),
        plugins_dir=d.get("plugins_dir"),
        plugin_manifest=d.get("plugin_manifest"),
        tool_mappings=d.get("tool_mappings"),
        skill_order=d.get("skill_order"),
        runtime_conventions=d.get("runtime_conventions"),
    )


def test_a_session_pickup_never_satisfies_a_child_resume_pin() -> None:
    assert CONDITIONAL_CAPABILITIES["session.resume"] != CONDITIONAL_CAPABILITIES["agent.resume"]

    ref = ".audit/evidence/omp-receipt.json"
    pickup = _adversarial_receipt(_observed_scenario("session-pickup", settlement=None))
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(_profile_pinning(ref, "session-pickup"), {ref: pickup})

    child = _adversarial_receipt(
        _observed_scenario("child-resume", settlement=_success_settlement())
    )
    check_scenario_pins(_profile_pinning(ref, "child-resume"), {ref: child})


@pytest.mark.parametrize("outcome", ["cancelled", "timeout", "error"])
def test_a_non_success_child_settlement_never_satisfies_a_verified_pin(outcome: str) -> None:
    ref = ".audit/evidence/omp-receipt.json"
    scenario_id = f"child-{outcome}"
    failed = _adversarial_receipt(
        _observed_scenario(
            scenario_id, settlement=replace(_success_settlement(), terminal_outcome=outcome)
        )
    )
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(_profile_pinning(ref, scenario_id), {ref: failed})


def test_a_typed_cancellation_settles_only_the_cancel_capability() -> None:
    ref = ".audit/evidence/omp-receipt.json"
    scenario_id = "runtime-child-cancel-omp"
    cancelled = _adversarial_receipt(
        _observed_scenario(
            scenario_id, settlement=replace(_success_settlement(), terminal_outcome="cancelled")
        )
    )
    check_scenario_pins(_profile_pinning(ref, scenario_id, "agent.cancel"), {ref: cancelled})
    for capability in ("agent.spawn", "agent.join", "agent.resume"):
        with pytest.raises(ValidationError, match="carries no observed_live settlement"):
            check_scenario_pins(_profile_pinning(ref, scenario_id, capability), {ref: cancelled})

    for outcome in ("timeout", "error"):
        failed = _adversarial_receipt(
            _observed_scenario(
                scenario_id, settlement=replace(_success_settlement(), terminal_outcome=outcome)
            )
        )
        with pytest.raises(ValidationError, match="carries no observed_live settlement"):
            check_scenario_pins(_profile_pinning(ref, scenario_id, "agent.cancel"), {ref: failed})


def test_a_settled_cancellation_survives_a_durable_refresh() -> None:
    scenario_id = "runtime-child-cancel-omp"
    cancelled = _observed_scenario(
        scenario_id, settlement=replace(_success_settlement(), terminal_outcome="cancelled")
    )
    previous = _adversarial_receipt(cancelled)
    downgraded = replace(cancelled, evidence_level="static", settlement=None)
    current = replace(previous, run_id="refresh-run", scenarios=[downgraded])
    current.validate()

    assert preserve_observed_settlements(previous, current) == [scenario_id]
    assert current.scenarios[0].evidence_level == "observed_live"
    assert current.scenarios[0].preserved_from == previous.run_id

    timed_out_previous = _adversarial_receipt(
        replace(cancelled, settlement=replace(_success_settlement(), terminal_outcome="timeout"))
    )
    timed_out_current = replace(timed_out_previous, run_id="refresh-run", scenarios=[downgraded])
    timed_out_current.validate()
    assert preserve_observed_settlements(timed_out_previous, timed_out_current) == []


def test_a_cancellation_only_receipt_never_derives_verified(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, replace(_success_settlement(), terminal_outcome="cancelled")],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "packaged"


def test_supported_needs_a_behavioral_pass_on_every_row(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[
            None,
            ChildSettlement(
                child_id="subagent-7",
                terminal_outcome="success",
                model="test-model",
                transport="rpc",
                effective_rpc="rpc-v2:profile=disposable:depth=1",
            ),
        ],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "supported"

    floor_ref = ".audit/evidence/synthetic-receipt.json"
    rest_ref = ".audit/evidence/rest.json"
    base = json.loads((root / floor_ref).read_text(encoding="utf-8"))
    split = replace(
        prof,
        support_state="supported",
        bindings=[
            replace(b, evidence_ref=floor_ref if b.capability in MANDATORY_SUPPORT_FLOOR else rest_ref)
            for b in prof.bindings
        ],
    )

    def behavioral_fail(row: dict) -> dict:
        return (
            {**row, "verdict": "FAIL", "exit_code": 1}
            if row["plane"] in ("canonical", "adapter", "runtime")
            else row
        )

    probes = {
        "package-only-PASS": (
            {"scenarios": [behavioral_fail(row) for row in base["scenarios"]]},
            "exceeds evidence-derived support state 'verified'",
        ),
        "foreign-host": ({"host": "codex"}, "host mismatch"),
        "settlement-free-omp": (
            {
                "scenarios": [
                    {**s, "evidence_level": "static", "settlement": None} for s in base["scenarios"]
                ]
            },
            "exceeds evidence-derived support state 'verified'",
        ),
    }
    for name, (patch, match) in probes.items():
        rest = {**base, "run_id": f"rest-{name}", **patch}
        rest["planes"], rest["overall_verdict"] = _declared_from(
            [ScenarioResult(**row) for row in rest["scenarios"]]
        )
        (root / ".audit" / "evidence" / "rest.json").write_text(
            json.dumps(rest), encoding="utf-8"
        )
        assert derive_support_state(split, root) == "verified", name
        with pytest.raises(ValidationError, match=match):
            check_evidence_durability(split, root)


def test_a_runtime_fail_row_clears_neither_bar(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, _success_settlement()],
        force_verified=True,
    )
    receipt_path = root / ".audit" / "evidence" / "synthetic-receipt.json"
    data_before = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data_before["planes"]["runtime"] == "PASS"

    data = json.loads(json.dumps(data_before))
    data["scenarios"] = [
        *data["scenarios"],
        asdict(
            ScenarioResult(
                id="synthetic-runtime-fail",
                description="runtime row that failed",
                plane="runtime",
                command="false",
                exit_code=1,
                stdout_snippet="",
                verdict="FAIL",
                duration_s=0.01,
                evidence_level="offline",
            )
        ),
    ]
    data["planes"], data["overall_verdict"] = _declared_from(
        [ScenarioResult(**row) for row in data["scenarios"]]
    )
    receipt_path.write_text(json.dumps(data), encoding="utf-8")
    assert data["planes"]["runtime"] == "FAIL"

    revisions = compute_surface_revisions(root, "omp")
    runtime_fail = VerificationReceipt(**data)
    runtime_fail.validate()
    assert _row_level(runtime_fail, prof, revisions, require_package=False) == ""
    assert _row_level(runtime_fail, prof, revisions, require_package=True) == ""
    assert derive_support_state(prof, root) == "packaged"

    clean = VerificationReceipt(**data_before)
    clean.validate()
    assert _row_level(clean, prof, revisions, require_package=False) == "verified"
    assert _row_level(clean, prof, revisions, require_package=True) == "supported"


def test_a_package_only_pass_never_clears_a_bar(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, _success_settlement()],
        force_verified=True,
    )
    receipt_path = root / ".audit" / "evidence" / "synthetic-receipt.json"
    base = json.loads(receipt_path.read_text(encoding="utf-8"))
    revisions = compute_surface_revisions(root, "omp")

    def row_with(plane_verdicts: dict) -> VerificationReceipt:
        data = json.loads(json.dumps(base))
        for row in data["scenarios"]:
            if row["plane"] in plane_verdicts:
                row["verdict"], row["exit_code"] = plane_verdicts[row["plane"]], 1
        data["planes"], data["overall_verdict"] = _declared_from(
            [ScenarioResult(**row) for row in data["scenarios"]]
        )
        receipt_path.write_text(json.dumps(data), encoding="utf-8")
        receipt = VerificationReceipt(**data)
        receipt.validate()
        return receipt

    package_only = row_with({p: "FAIL" for p in ("canonical", "adapter", "runtime")})
    assert package_only.planes == {
        "canonical": "FAIL",
        "adapter": "FAIL",
        "package": "PASS",
        "runtime": "FAIL",
    }
    assert _row_level(package_only, prof, revisions, require_package=False) == ""
    assert _row_level(package_only, prof, revisions, require_package=True) == ""
    assert derive_support_state(prof, root) == "packaged"

    package_fail = row_with({"package": "FAIL"})
    assert _row_level(package_fail, prof, revisions, require_package=False) == "verified"
    assert _row_level(package_fail, prof, revisions, require_package=True) == ""
    assert derive_support_state(prof, root) == "verified"


def test_a_receipt_cannot_declare_a_plane_it_never_observed(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["observed_live"],
        settlements=[_success_settlement()],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "supported"

    receipt_path = root / ".audit" / "evidence" / "synthetic-receipt.json"
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["planes"] == {plane: "PASS" for plane in CONFORMANCE_PLANES}
    data["scenarios"] = []
    receipt_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValidationError, match="not the scenario reduction"):
        VerificationReceipt(**data).validate()
    assert derive_support_state(prof, root) == "packaged"
    with pytest.raises(ValidationError, match="is not a valid VerificationReceipt"):
        check_evidence_durability(prof, root)


def test_a_declared_plane_cannot_outlive_a_failing_scenario(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["observed_live"],
        settlements=[_success_settlement()],
        force_verified=True,
    )
    receipt_path = root / ".audit" / "evidence" / "synthetic-receipt.json"
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    runtime_row = next(row for row in data["scenarios"] if row["plane"] == "runtime")
    runtime_row["verdict"], runtime_row["exit_code"] = "FAIL", 1
    receipt_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValidationError, match="not the scenario reduction"):
        VerificationReceipt(**data).validate()
    assert derive_support_state(prof, root) == "packaged"
    with pytest.raises(ValidationError, match="is not a valid VerificationReceipt"):
        check_evidence_durability(prof, root)


def test_a_scenario_records_how_it_was_observed() -> None:
    scenario = _omp_spawn_scenario("offline")
    scenario.evidence_level = None
    with pytest.raises(ValidationError, match="records no evidence_level"):
        scenario.validate()

    durable = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    durable["scenarios"][0]["evidence_level"] = None
    with pytest.raises(ValidationError, match="records no evidence_level"):
        VerificationReceipt(**durable).validate()


def test_driver_shaped_receipts_still_validate() -> None:
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        VerificationReceipt(
            **json.loads((EVIDENCE_DIR / f"{host}-receipt.json").read_text(encoding="utf-8"))
        ).validate()

    scenario = _omp_spawn_scenario("observed_live", settlement=_success_settlement())
    scenarios = [scenario] + _plane_rows({"runtime"})
    planes, overall = _declared_from(scenarios)
    receipt = VerificationReceipt(
        run_id="driver-shaped-control",
        host="omp",
        host_version="test",
        timestamp="2026-10-17T00:00:00Z",
        overall_verdict=overall,
        planes=planes,
        surface_revisions=compute_surface_revisions(ROOT, "omp"),
        scenarios=scenarios,
    )
    receipt.validate()
    assert receipt.planes == {plane: "PASS" for plane in CONFORMANCE_PLANES}
    assert settle_planes(receipt.scenarios) == receipt.planes


def test_a_verified_pin_naming_an_unrecorded_scenario_is_a_dangling_reference() -> None:
    ref = ".audit/evidence/omp-receipt.json"
    receipt = _adversarial_receipt(
        _observed_scenario("child-resume", settlement=_success_settlement())
    )
    with pytest.raises(ValidationError, match="does not record"):
        check_scenario_pins(_profile_pinning(ref, "child-resume-typo"), {ref: receipt})


def test_a_profile_that_binds_one_capability_twice_is_refused(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, _success_settlement()],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "supported"

    floor_row = next(b for b in prof.bindings if b.capability == "agent.spawn")
    duplicated = replace(prof, bindings=[floor_row] * 9 + list(prof.bindings))

    with pytest.raises(ValidationError, match=r"binds a capability more than once.*agent\.spawn"):
        derive_support_state(duplicated, root)
    with pytest.raises(ValidationError, match=r"binds a capability more than once.*agent\.spawn"):
        check_evidence_durability(duplicated, root)

    fail_ref = ".audit/evidence/fail-receipt.json"
    data = json.loads((root / ".audit" / "evidence" / "synthetic-receipt.json").read_text(encoding="utf-8"))
    for row in data["scenarios"]:
        if row["plane"] == "runtime":
            row["verdict"], row["exit_code"] = "FAIL", 1
    data["planes"], data["overall_verdict"] = _declared_from(
        [ScenarioResult(**row) for row in data["scenarios"]]
    )
    (root / fail_ref).write_text(json.dumps(data), encoding="utf-8")

    act_on = replace(
        prof,
        bindings=[replace(floor_row, evidence_ref=fail_ref)] * 9 + list(prof.bindings),
    )
    with pytest.raises(ValidationError, match=r"binds a capability more than once.*agent\.spawn"):
        derive_support_state(act_on, root)
