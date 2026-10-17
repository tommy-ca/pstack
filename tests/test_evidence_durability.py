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
    CONDITIONAL_CAPABILITIES,
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
    check_scenario_pins,
    compute_surface_revisions,
    derive_support_state,
    preserve_observed_settlements,
)

def _declared_hosts() -> tuple:
    data = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    return tuple(data["host_targets"])

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
    """Every receipt host records exactly what a static refresh can prove.

    The durable receipts are written by `refresh-static`: the canonical, adapter and
    package planes are observed, the model-backed runtime plane stays UNTESTED, and the
    overall verdict follows the planes instead of being rounded up to PASS.
    """
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
        assert receipt.overall_verdict == "UNTESTED"
        assert receipt.planes == {
            "canonical": "PASS",
            "adapter": "PASS",
            "package": "PASS",
            "runtime": "UNTESTED",
        }

        # A static refresh drives no host, so no row may claim a runtime observation.
        assert [s for s in receipt.scenarios if s.plane == "runtime"] == []
        assert [s for s in receipt.scenarios if s.evidence_level == "observed_live"] == []

        # The receipt binds the surface it was refreshed against, not the one it replaced.
        assert receipt.evaluate_plane_staleness(compute_surface_revisions(ROOT, host)) == {
            plane: [] for plane in CONFORMANCE_PLANES
        }

        assert host in index_data["hosts"]
        entry = index_data["hosts"][host]
        assert entry["overall_verdict"] == "UNTESTED"
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
        # Exact expectations, not a membership check: the static refresh proves the
        # package/static planes for the five receipt hosts, and nothing more; droid has
        # no durable receipt at all and stays candidate.
        expected_state = "candidate" if host == "droid" else "packaged"
        assert result["claimed_support_state"] == expected_state
        assert result["derived_support_state"] == expected_state

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


def _omp_profile(data: dict | None = None) -> HarnessProfile:
    d = data if data is not None else json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    return HarnessProfile(
        host=d["host"],
        support_state=d["support_state"],
        bindings=[Binding(**x) for x in d["bindings"]],
        skills_dir=d.get("skills_dir"),
        plugins_dir=d.get("plugins_dir"),
        plugin_manifest=d.get("plugin_manifest"),
        evidence_ledger=[Evidence(**x) for x in d.get("evidence_ledger", [])],
        tool_mappings=d.get("tool_mappings"),
        skill_order=d.get("skill_order"),
        runtime_conventions=d.get("runtime_conventions"),
    )


def test_omp_profile_claims_only_what_its_receipt_settles() -> None:
    """#289 + refresh-static: omp claims packaged, every row is static-only, and every
    surviving scenario pin resolves in the refreshed static receipt."""
    prof = _omp_profile()
    assert prof.support_state == "packaged"
    assert check_evidence_durability(prof, ROOT, check_freshness=False)["derived_support_state"] == "packaged"

    receipt = VerificationReceipt(
        **json.loads((EVIDENCE_DIR / "omp-receipt.json").read_text(encoding="utf-8"))
    )
    recorded = {s.id for s in receipt.scenarios}
    assert receipt.planes["runtime"] == "UNTESTED", "a static refresh observes no runtime behavior"
    assert not [s for s in receipt.scenarios if s.evidence_level == "observed_live"]

    # The static refresh demoted the live rows: nothing claims verified, so nothing may
    # pin the settlements the refresh dropped.
    assert not {b.capability for b in prof.bindings if b.verification_status == "verified"}
    assert {b.verification_status for b in prof.bindings} == {"static-only", "unverified"}

    pinned = [b for b in prof.bindings if b.scenario_id]
    assert pinned, "the profile row that does have a static proof must keep its pin"
    assert not [b for b in pinned if b.scenario_id.startswith("runtime-")]
    for b in pinned:
        assert b.scenario_id in recorded, f"{b.capability} pins an unrecorded scenario"


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
    """`verified` is a live-behavior claim; a static pin belongs to static-only."""
    d = json.loads((ROOT / "profiles" / "omp.json").read_text(encoding="utf-8"))
    for binding in d["bindings"]:
        if binding["capability"] in ("agent.spawn", "agent.join"):
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


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity"])
def test_stale_package_driver_rejected_for_packaged_claim(host: str) -> None:
    # #473: five hosts claim packaged; a stale package driver must fail closed.
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
        "scripts/route_resolver.py",
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
        claimed = json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))["support_state"]
        if host == "droid":
            assert data[host]["support_state"] == "candidate"
            assert claimed == "candidate"
        else:
            # The refreshed receipt is current, and it is honest about the plane it
            # never observed: runtime UNTESTED, overall UNTESTED, claimed packaged.
            assert data[host]["overall_verdict"] == "UNTESTED"
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
            # #473: the candidate row evaluates no planes, so it reports
            # NOT_COVERED rather than PASS.
            assert "[droid] NOT_COVERED" in res.stdout
            continue
        assert (
            f"[{host}] PASS: Evidence durable, derived support state: packaged (claimed: packaged)"
            in res.stdout
        )

def test_candidate_row_reports_not_covered_not_pass() -> None:
    # #473: a candidate row evaluates no planes; it must not print PASS.
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-evidence", "--host", "droid"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "[droid] NOT_COVERED" in res.stdout
    assert "[droid] PASS" not in res.stdout


def _load_verify_portable_module():
    loader = importlib.util.spec_from_file_location(
        "verify_portable_refresh", ROOT / "scripts" / "verify-portable.py"
    )
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def test_refresh_static_is_partial_and_never_rounds_a_failure_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """refresh-static is a static, partial refresh of one host.

    It must (1) record only the host it ran for — the other hosts' durable receipts and
    index entries stay byte-identical, (2) write canonical/adapter/package PASS with
    runtime and overall UNTESTED at the current revisions, and (3) take its exit status
    from the doctor result, so a failing static plane stays FAIL instead of riding the
    UNTESTED overall verdict out as a pass.

    The doctor itself (OpenSpec, native package lifecycle) is stubbed here because this
    case measures the action's wiring; the real end-to-end run is pinned by the committed
    durable receipts that the other cases in this module read.
    """
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

    # Partial: only the refreshed host moved.
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

    # A failing static plane stays FAIL, in the receipt and in the exit status.
    monkeypatch.setattr(module.PortableVerifier, "doctor", failing_doctor)
    with pytest.raises(SystemExit) as failing_exit:
        module.main()
    assert failing_exit.value.code == 1

    failed = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    assert failed["planes"]["package"] == "FAIL"
    assert failed["overall_verdict"] == "FAIL"


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


def test_adapter_pass_with_package_fail_is_never_an_accepted_package_pass(tmp_path: Path) -> None:
    """#296 second fixture: adapter PASS does not carry a failed package plane.

    The package check is a separate native projection/lifecycle row, so the receipt tops
    out at `verified` (canonical + adapter + runtime) and never becomes the `supported`
    state that accepts the package plane; `check-evidence` names that gap for a claim.
    """
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
    data["planes"]["package"] = "FAIL"
    receipt_path.write_text(json.dumps(data), encoding="utf-8")

    # The adapter PASS and the settled runtime scenario prove their own planes only.
    assert derive_support_state(prof, root) == "verified"
    with pytest.raises(ValidationError, match="exceeds evidence-derived support state 'verified'"):
        check_evidence_durability(replace(prof, support_state="supported"), root)


def test_bare_live_label_without_settlement_stays_packaged(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(tmp_path, ["offline", "observed_live"], force_verified=True)
    assert derive_support_state(prof, root) == "packaged"


def test_static_isolation_row_cannot_satisfy_the_runtime_plane_on_its_own() -> None:
    """#291 negative direction: the runtime plane reduces on verdicts alone, so a runtime
    `PASS` can contain a static row. A static isolation row must not stand in for observed
    isolation — it is not an observed settlement, so a `verified` pin to it is rejected
    until the live isolation run replaces the row.

    The refreshed durable receipt carries no runtime row at all (a static refresh drives
    nothing), so the row this gate reads is rebuilt here as the static row it was before
    the live isolation run."""
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
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
        surface_revisions=compute_surface_revisions(ROOT, "omp"),
        scenarios=[static_isolation],
    )
    receipt.validate()
    assert receipt.planes["runtime"] == "PASS", "the plane reduces on verdicts alone"

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

    # Positive control (gate mechanics only): the same pin holds once the row carries an
    # observed_live settlement, which is exactly what the live isolation run produces.
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
    live_receipt.validate()
    check_scenario_pins(profile, {ref: live_receipt})


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


def _receipt_evidence_levels() -> set:
    """The closed enum the durable receipt schema serves; the source of truth for the fixtures."""
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"]["scenarios"]["items"]["properties"]["evidence_level"]["enum"])


@pytest.mark.parametrize("evidence_level", ["live", "documented"])
def test_invented_evidence_level_rejects_an_omp_receipt_shaped_scenario(evidence_level: str) -> None:
    """#296: `live` (the pre-serialization draft name) and `documented` (a source-provenance tag,
    not receipt evidence) never became receipt evidence levels. Both must fail validation."""
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
    """The refreshed receipts are static: enum-valid levels, and no live label anywhere."""
    enum = _receipt_evidence_levels()
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        receipt = json.loads((EVIDENCE_DIR / f"{host}-receipt.json").read_text(encoding="utf-8"))
        levels = {s["id"]: s["evidence_level"] for s in receipt["scenarios"]}
        assert set(levels.values()) <= enum, host
        assert "observed_live" not in set(levels.values()), host
        assert levels[f"doctor-profile-{host}"] == "offline"


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
        # The fixture re-asserts verified on every row so the promotion gate itself is
        # measured; the committed profile deliberately underclaims (see #289).
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
    """The gate that fails when a claimed live pin has no live settlement must say how to restore it.

    The committed profile is demoted (static-only rows over a static receipt), so the copy
    re-asserts the live claim the way an unrefreshed edit would and puts the static runtime
    row back in the receipt next to it: the scenario-pin gate then names the omp remedy.
    """
    copy_root = _disposable_copy(tmp_path)

    profile_path = copy_root / "profiles" / "omp.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    spawn = next(b for b in profile["bindings"] if b["capability"] == "agent.spawn")
    spawn["verification_status"] = "verified"
    spawn["evidence_ref"] = {
        "receipt": ".audit/evidence/omp-receipt.json",
        "scenario": "runtime-child-spawn-omp",
    }
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

    receipt_path = copy_root / ".audit" / "evidence" / "omp-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert [s for s in receipt["scenarios"] if s["plane"] == "runtime"] == []
    receipt["scenarios"].append(
        {
            "id": "runtime-child-spawn-omp",
            "description": "bounded omp rpc v2 child spawn and join",
            "plane": "runtime",
            "command": "PSTACK_RUN_OMP_LIVE=1 python -m pytest tests/test_omp_rpc.py",
            "exit_code": 0,
            "stdout_snippet": "static evidence",
            "verdict": "UNTESTED",
            "duration_s": 0.0,
            "evidence_level": "static",
            "settlement": None,
            "preserved_from": "",
        }
    )
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), "check-evidence", "--host", "omp"],
        capture_output=True,
        text=True,
        cwd=copy_root,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "carries no observed_live settlement" in proc.stdout
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


# --- Adversarial negatives: child resume, cancelled settlements, dangling pins ---
#
# The promotion gate reads one typed settlement. These cases attack it with the
# near-misses: an observed_live runtime PASS row that carries no child, a child
# that ended cancelled/timed-out/errored, and a pin naming a scenario the receipt
# never recorded.


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
    receipt = VerificationReceipt(
        run_id="p8-adversarial",
        host="omp",
        host_version="test",
        timestamp="2026-10-12T00:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
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
    """A session pickup carries no spawned child, so an observed_live runtime PASS row
    without a ChildSettlement cannot stand in for a `verified` child-resume binding."""
    assert CONDITIONAL_CAPABILITIES["session.resume"] != CONDITIONAL_CAPABILITIES["agent.resume"]

    ref = ".audit/evidence/omp-receipt.json"
    pickup = _adversarial_receipt(_observed_scenario("session-pickup", settlement=None))
    with pytest.raises(ValidationError, match="carries no observed_live settlement"):
        check_scenario_pins(_profile_pinning(ref, "session-pickup"), {ref: pickup})

    # Control: the same pin holds once the row is a settled child.
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
    """#381: a cancelled child is the settlement `agent.cancel` exists to prove, and it
    proves nothing about any other capability."""
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

    # The promotion is the cancelled outcome alone: a timeout or error settles nothing,
    # not even for the capability that owns cancellation.
    for outcome in ("timeout", "error"):
        failed = _adversarial_receipt(
            _observed_scenario(
                scenario_id, settlement=replace(_success_settlement(), terminal_outcome=outcome)
            )
        )
        with pytest.raises(ValidationError, match="carries no observed_live settlement"):
            check_scenario_pins(_profile_pinning(ref, scenario_id, "agent.cancel"), {ref: failed})


def test_a_settled_cancellation_survives_a_durable_refresh() -> None:
    """A route-free refresh must carry the scenario `agent.cancel` pins, or that pin turns
    into a hard error on the run that could not re-observe it (#322)."""
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

    # A failed outcome is not carryable evidence, so a downgraded timeout stays static.
    timed_out_previous = _adversarial_receipt(
        replace(cancelled, settlement=replace(_success_settlement(), terminal_outcome="timeout"))
    )
    timed_out_current = replace(timed_out_previous, run_id="refresh-run", scenarios=[downgraded])
    timed_out_current.validate()
    assert preserve_observed_settlements(timed_out_previous, timed_out_current) == []


def test_a_cancellation_only_receipt_never_derives_verified(tmp_path: Path) -> None:
    """#381 exclusion: a typed cancellation proves `agent.cancel`, not the spawn/join
    runtime proof that carries a host past `packaged`."""
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, replace(_success_settlement(), terminal_outcome="cancelled")],
        force_verified=True,
    )
    assert derive_support_state(prof, root) == "packaged"


def test_a_verified_pin_naming_an_unrecorded_scenario_is_a_dangling_reference() -> None:
    ref = ".audit/evidence/omp-receipt.json"
    receipt = _adversarial_receipt(
        _observed_scenario("child-resume", settlement=_success_settlement())
    )
    with pytest.raises(ValidationError, match="does not record"):
        check_scenario_pins(_profile_pinning(ref, "child-resume-typo"), {ref: receipt})
