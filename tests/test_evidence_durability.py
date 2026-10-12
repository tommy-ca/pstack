import importlib.util
import json
import shutil
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
    Evidence,
    HarnessProfile,
    MANDATORY_SUPPORT_FLOOR,
    PLANE_SURFACE_DEPENDENCIES,
    PORTABLE_CAPABILITY_UNIVERSE,
    ScenarioResult,
    SurfaceRevisions,
    ValidationError,
    VerificationReceipt,
    check_evidence_durability,
    compute_surface_revisions,
    derive_support_state,
)

SIX_HARNESSES = ("grok", "codex", "omp", "opencode", "antigravity", "droid")
FIVE_HARNESSES = ("grok", "codex", "omp", "opencode", "antigravity")

RECEIPT_SCHEMA = ROOT / "schemas" / "portability" / "receipt.schema.json"
EVIDENCE_DIR = ROOT / ".audit" / "evidence"


def test_receipt_json_schema_exists_and_valid() -> None:
    assert RECEIPT_SCHEMA.is_file()
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "VerificationReceipt" in schema["title"]
    assert "surface_revisions" in schema["required"]
    assert "scenarios" in schema["required"]


def test_compute_surface_revisions_all_fields_present() -> None:
    revs = compute_surface_revisions(ROOT, "grok")
    assert isinstance(revs, SurfaceRevisions)
    d = revs.to_dict()

    expected_keys = [
        "canonical_pin",
        "upstream_head",
        "spec_hash",
        "skills_tree_hash",
        "profile_hash",
        "package_descriptor_hash",
        "manifest_hash",
        "driver_revision",
        "package_driver_revision",
        "boundary_driver_revision",
    ]
    for k in expected_keys:
        assert k in d
        assert d[k] != "missing", f"Surface revision field {k} is 'missing'"
        assert len(d[k]) > 0

    assert len(revs.canonical_pin) == 40
    assert len(revs.upstream_head) == 40


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
        assert receipt.overall_verdict == "PASS"
        assert receipt.planes["canonical"] == "PASS"
        assert receipt.planes["adapter"] == "PASS"
        assert receipt.planes["package"] == "PASS"
        assert receipt.planes["runtime"] == "PASS"

        assert host in index_data["hosts"]
        assert index_data["hosts"][host]["overall_verdict"] == "PASS"


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
        assert result["claimed_support_state"] in ("verified", "supported", "packaged", "mapped", "candidate")
        # Ensure derived state supports claimed state
        assert result["derived_support_state"] in ("verified", "supported", "packaged", "mapped", "candidate")

        # Also test profile method
        method_result = prof.validate_evidence(ROOT, check_freshness=True)
        assert method_result["valid"] is True


test_all_five_profiles_pass_evidence_durability_and_freshness = test_all_six_profiles_pass_evidence_durability_and_freshness


def test_dangling_evidence_path_fails(tmp_path: Path) -> None:
    # Construct a profile with a non-existent evidence_ref
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


def test_stale_skills_tree_hash_invalidates_runtime() -> None:
    current_revs = compute_surface_revisions(ROOT, "codex")
    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)

    # Mutate receipt surface revisions to simulate older skills tree
    tampered_revs = replace(current_revs, skills_tree_hash="0000000000000000000000000000000000000000000000000000000000000000")
    receipt.surface_revisions = tampered_revs

    stale_map = receipt.evaluate_plane_staleness(current_revs)
    assert len(stale_map["runtime"]) > 0
    assert any("skills_tree_hash mismatch" in r for r in stale_map["runtime"])

    # Other planes should remain unaffected
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
    # PLANE_SURFACE_DEPENDENCIES does not include docs
    for plane, deps in PLANE_SURFACE_DEPENDENCIES.items():
        assert "docs" not in "".join(deps)
        assert "readme" not in "".join(deps)

    receipt_data = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    receipt = VerificationReceipt(**receipt_data)
    stale_map = receipt.evaluate_plane_staleness(current_revs)
    for plane in CONFORMANCE_PLANES:
        assert len(stale_map[plane]) == 0


def test_hand_authored_support_state_cannot_outrun_evidence() -> None:
    # A profile claiming 'supported' with tampered stale surface revisions must be rejected
    profile_data = json.loads((ROOT / "profiles" / "grok.json").read_text(encoding="utf-8"))
    b = [Binding(**x) for x in profile_data["bindings"]]
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


def _disposable_copy(tmp_path: Path) -> Path:
    """Fresh extraction of the repo as an installed/extracted package: no .git,
    no pre-existing dependency or bytecode artifacts."""
    copy_root = tmp_path / "extracted-package"
    shutil.copytree(
        ROOT,
        copy_root,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv"),
    )
    return copy_root


@pytest.mark.parametrize(
    "relative_path",
    [
        "scripts/verify-portable.py",
        "scripts/verify-harness.py",
        "scripts/adapt-harness.py",
        "scripts/scaffold-verification-skill.py",
        "scripts/skill_frontmatter.py",
        "scripts/portability_schema.py",
        "scripts/drivers/base.py",
        "scripts/drivers/codex.py",
    ],
)
def test_driver_source_change_invalidates_adapter_and_runtime(
    tmp_path: Path, relative_path: str
) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")
    receipt = VerificationReceipt(
        run_id="driver-fingerprint-regression",
        host="codex",
        host_version="test",
        timestamp="2026-10-07T00:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
        surface_revisions=fresh,
    )
    assert receipt.evaluate_plane_staleness(fresh) == {
        "canonical": [], "adapter": [], "package": [], "runtime": []
    }

    driver_file = copy_root / relative_path
    original = driver_file.read_bytes()
    driver_file.write_bytes(original + b"\n# Changed verification behavior.\n")
    edited = compute_surface_revisions(copy_root, "codex")

    assert edited.driver_revision != fresh.driver_revision
    assert replace(edited, driver_revision=fresh.driver_revision) == fresh
    stale_map = receipt.evaluate_plane_staleness(edited)
    assert {plane for plane, reasons in stale_map.items() if reasons} == {
        "adapter", "runtime"
    }
    for plane, dependencies in PLANE_SURFACE_DEPENDENCIES.items():
        if "driver_revision" in dependencies:
            assert len(stale_map[plane]) == 1
            assert stale_map[plane][0].startswith("driver_revision mismatch")
        else:
            assert stale_map[plane] == []

    driver_file.write_bytes(original)
    assert compute_surface_revisions(copy_root, "codex") == fresh


@pytest.mark.parametrize("relative_path", ["README.md", "docs/fingerprint-notes.md"])
def test_unrelated_docs_change_does_not_change_driver_revision(
    tmp_path: Path, relative_path: str
) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")
    doc_file = copy_root / relative_path
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    with doc_file.open("a", encoding="utf-8") as doc:
        doc.write("\nUnrelated documentation change.\n")

    edited = compute_surface_revisions(copy_root, "codex")
    assert edited.driver_revision == fresh.driver_revision
    assert edited == fresh


def test_dependency_artifacts_do_not_change_skills_tree_hash(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)

    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash

    # Dependency install artifacts under skills/
    pkg = copy_root / "skills" / "poteto-mode" / "scripts" / "node_modules" / "some-pkg"
    pkg.mkdir(parents=True)
    (pkg / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
    after_deps = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert after_deps == fresh

    # Bytecode artifacts under skills/
    pyc_dir = copy_root / "skills" / "swarm" / "scripts" / "__pycache__"
    pyc_dir.mkdir(parents=True)
    (pyc_dir / "partition.cpython-312.pyc").write_bytes(b"\x00\x01fake-bytecode")
    # Stray bytecode outside a __pycache__ directory too
    (copy_root / "skills" / "swarm" / "scripts" / "partition.cpython-312.pyc").write_bytes(b"\x00\x01")
    after_bytecode = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert after_bytecode == fresh

    assert len(fresh) == 64


def test_genuine_skill_source_change_changes_skills_tree_hash(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    skill_file = copy_root / "skills" / "how" / "SKILL.md"

    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    original = skill_file.read_text(encoding="utf-8")
    skill_file.write_text(original + "\nA genuine source edit.\n", encoding="utf-8")
    edited = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert edited != fresh

    # Reverting the edit restores the original fingerprint.
    skill_file.write_text(original, encoding="utf-8")
    reverted = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert reverted == fresh


def test_harness_verifier_dynamic_import_does_not_self_invalidate(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    partition_script = copy_root / "skills" / "swarm" / "scripts" / "partition.py"
    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash

    # Reproduce verify-harness.py's dynamic import with bytecode caching enabled
    # (i.e. run without PYTHONDONTWRITEBYTECODE), as the bare verifier does.
    saved_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = False
    try:
        spec = importlib.util.spec_from_file_location("swarm_partition", partition_script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = saved_dont_write

    pycache = partition_script.parent / "__pycache__"
    assert pycache.is_dir(), "verifier import should have produced bytecode artifacts"
    assert compute_surface_revisions(copy_root, "grok").skills_tree_hash == fresh


def test_check_staleness_cli_json_output() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-staleness", "--host", "all", "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data) >= 6
    for host in SIX_HARNESSES:
        assert host in data
        assert data[host]["needs_regeneration"] is False
        assert data[host]["stale_planes"] == []
        if host == "droid":
            assert data[host]["support_state"] == "candidate"
        else:
            assert data[host]["overall_verdict"] == "PASS"


def test_check_evidence_cli_output() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-evidence", "--host", "all"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    for host in SIX_HARNESSES:
        assert f"[{host}] PASS: Evidence durable" in res.stdout


def _synthetic_evidence_root(tmp_path: Path, evidence_levels: list, planes: list | None = None, host: str = "omp", snippets: list | None = None, settlements: list | None = None, force_verified: bool = False) -> tuple:
    """Self-consistent minimal root: every OMP binding points at one synthetic receipt
    whose scenario (evidence_level, plane) pairs are exactly zipped `evidence_levels`."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "pstack.package.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / ".omp-plugin" / "package.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")

    revisions = compute_surface_revisions(tmp_path, host)
    ref = ".audit/evidence/synthetic-receipt.json"
    receipt = VerificationReceipt(
        run_id="evidence-level-gate",
        host=host,
        host_version="test",
        timestamp="2026-10-11T00:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
        surface_revisions=revisions,
        scenarios=[
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
        ],
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


def test_bare_live_label_without_settlement_stays_packaged(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(tmp_path, ["offline", "observed_live"], force_verified=True)
    assert derive_support_state(prof, root) == "packaged"


def test_non_runtime_live_does_not_prove_runtime(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(
        tmp_path, ["observed_live", "offline"], planes=["canonical", "runtime"], force_verified=True
    )
    assert derive_support_state(prof, root) == "packaged"


def test_legacy_or_missing_evidence_level_never_proves_live(tmp_path: Path) -> None:
    # 'legacy' stays a valid enum member (no rename) but proves at most 'packaged'
    ScenarioResult(
        id="legacy", description="legacy", plane="runtime", command="true", exit_code=0,
        stdout_snippet="", verdict="PASS", duration_s=0.01, evidence_level="legacy",
    ).validate()

    for levels in (["legacy"], ["observed_live", None], []):
        root, prof = _synthetic_evidence_root(tmp_path / "_".join(str(l) for l in levels), list(levels), force_verified=True)
        assert derive_support_state(prof, root) == "packaged"

def test_driver_settlement_survives_receipt_serialization(tmp_path: Path) -> None:
    from scripts.drivers.base import DriverScenarioResult

    settlement = {
        "child_id": "subagent-9",
        "terminal_outcome": "success",
        "model": "test-model",
        "transport": "rpc",
        "effective_rpc": "rpc-v2:profile=disposable:depth=1",
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
    """Minimal omp root whose durable receipt already carries a live settlement."""
    root = tmp_path / "repo"
    (root / ".omp-plugin").mkdir(parents=True)
    (root / "pstack.package.json").write_text("{}", encoding="utf-8")
    (root / ".omp-plugin" / "package.json").write_text("{}", encoding="utf-8")
    evidence_root = root / ".audit" / "evidence"
    evidence_root.mkdir(parents=True)
    revisions = compute_surface_revisions(root, "omp")
    live = VerificationReceipt(
        run_id="previous-live-run",
        host="omp",
        host_version="18.8.9",
        timestamp="2026-10-11T20:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
        surface_revisions=revisions,
        scenarios=[
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
        ],
    )
    (evidence_root / "omp-receipt.json").write_text(json.dumps(asdict(live)), encoding="utf-8")

    profile_data = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in profile_data["bindings"]:
        binding["evidence_ref"] = ".audit/evidence/omp-receipt.json"
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


def _portable_verifier(evidence_root: Path):
    loader = importlib.util.spec_from_file_location("verify_portable_preserve", ROOT / "scripts" / "verify-portable.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    verifier = module.PortableVerifier(host="omp", evidence_root=evidence_root)
    verifier.launch()
    return verifier


def _static_refresh_receipt(revisions: SurfaceRevisions, *, verdict: str = "PASS") -> VerificationReceipt:
    return VerificationReceipt(
        run_id="refresh-without-a-model-route",
        host="omp",
        host_version="18.8.9",
        timestamp="2026-10-12T00:00:00Z",
        overall_verdict=verdict,
        planes={plane: ("FAIL" if verdict != "PASS" and plane == "runtime" else "PASS") for plane in CONFORMANCE_PLANES},
        surface_revisions=revisions,
        scenarios=[_omp_spawn_scenario("static", verdict=verdict)],
    )


def test_durable_refresh_preserves_an_unchanged_observed_settlement(tmp_path: Path) -> None:
    """A model-route-free refresh must not delete the live proof its own gate reads."""
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)
    verifier = _portable_verifier(evidence_root)
    verifier.evidence(_static_refresh_receipt(revisions), update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["evidence_level"] == "observed_live"
    assert scenario["settlement"]["child_id"] == "subagent-1"
    assert scenario["settlement"]["terminal_outcome"] == "success"
    assert scenario["preserved_from"] == "previous-live-run"
    assert check_evidence_durability(prof, root)["derived_support_state"] == "supported"


def test_durable_refresh_drops_a_settlement_once_the_runtime_surface_moved(tmp_path: Path) -> None:
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)
    moved = replace(revisions, driver_revision="moved-driver-revision")

    verifier = _portable_verifier(evidence_root)
    verifier.evidence(_static_refresh_receipt(moved), update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["evidence_level"] == "static"
    assert scenario["settlement"] is None
    assert scenario["preserved_from"] == ""
    assert derive_support_state(prof, root) == "packaged"


def test_durable_refresh_does_not_paper_over_a_failing_run(tmp_path: Path) -> None:
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)
    verifier = _portable_verifier(evidence_root)
    verifier.evidence(_static_refresh_receipt(revisions, verdict="FAIL"), update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["verdict"] == "FAIL"
    assert scenario["evidence_level"] == "static"
    assert scenario["preserved_from"] == ""
    assert derive_support_state(prof, root) == "packaged"


def test_an_unreadable_durable_receipt_is_not_overwritten(tmp_path: Path) -> None:
    """The one place a prior observation lives must survive a run that cannot read it."""
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    durable.write_text("{ not json at all", encoding="utf-8")

    verifier = _portable_verifier(evidence_root)
    verifier.evidence(_static_refresh_receipt(revisions), update_durable=True)

    assert durable.read_text(encoding="utf-8") == "{ not json at all"
    assert (verifier.run_dir / "receipt.json").is_file()


def test_repeated_refreshes_keep_the_run_that_observed(tmp_path: Path) -> None:
    """A second model-route-free refresh must not rewrite the provenance chain."""
    root, prof, evidence_root, revisions = _omp_live_root(tmp_path)

    first = _portable_verifier(evidence_root)
    first.evidence(_static_refresh_receipt(revisions), update_durable=True)
    second = _portable_verifier(evidence_root)
    second.evidence(_static_refresh_receipt(revisions), update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["preserved_from"] == "previous-live-run"
    assert scenario["settlement"]["child_id"] == "subagent-1"


def test_check_evidence_names_the_omp_live_remedy(tmp_path: Path) -> None:
    """The gate that fails must say how to restore the proof it wants."""
    copy_root = _disposable_copy(tmp_path)
    receipt_path = copy_root / ".audit" / "evidence" / "omp-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for scenario in receipt["scenarios"]:
        if scenario["plane"] == "runtime":
            scenario["evidence_level"] = "static"
            scenario["settlement"] = None
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), "check-evidence", "--host", "omp"],
        capture_output=True,
        text=True,
        cwd=copy_root,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "exceeds evidence-derived support state 'packaged'" in proc.stdout
    assert "PSTACK_RUN_OMP_LIVE=1" in proc.stdout


def test_observed_settlement_requires_a_passing_successful_scenario() -> None:
    """A settlement that records failure must never satisfy the promotion gate."""
    from scripts.portability_schema import _is_observed_settlement

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
