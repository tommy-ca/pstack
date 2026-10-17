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
    _row_level,
    check_evidence_durability,
    check_scenario_pins,
    compute_surface_revisions,
    derive_support_state,
    preserve_observed_settlements,
    reduce_verdicts,
    settle_planes,
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
    # `check-evidence` now runs the profile domain rules before the staleness gate (#473),
    # so the fixture has to be a profile that *may* claim `supported`: every row verified.
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

    # A comment is not behaviour: it must not cost a re-proof. Asserted here in
    # the opposite direction, because the whole-file recipe this test used to
    # pin moved on comment bytes (#444).
    driver_file.write_bytes(original + b"\n# Changed verification behavior.\n")
    assert compute_surface_revisions(copy_root, "codex") == fresh

    # A statement is behaviour: it must stale exactly the planes that depend on
    # the driver revision.
    driver_file.write_bytes(original + b"\nBEHAVIOR_PROBE = 'changed verification behavior'\n")
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


def test_published_module_docstring_moves_the_driver_revision(tmp_path: Path) -> None:
    """`--help` text is the module docstring, so a consumed one stays in the fingerprint.

    A driver that publishes its own docstring at runtime contributes it raw; a
    docstring nobody publishes is commentary and must not cost a re-proof (#444).
    """
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")

    published = copy_root / "scripts" / "verify-portable.py"
    src = published.read_text(encoding="utf-8")
    anchor = '"""Portable lever verification engine for pstack across agent harnesses.'
    assert src.count(anchor) == 1
    published.write_text(src.replace(anchor, anchor + " Published at --help."), encoding="utf-8")
    assert compute_surface_revisions(copy_root, "codex").driver_revision != fresh.driver_revision

    published.write_text(src, encoding="utf-8")
    commentary = copy_root / "scripts" / "drivers" / "base.py"
    base_src = commentary.read_text(encoding="utf-8")
    base_anchor = '"""Base classes and scenario contracts for host-native harness drivers."""'
    assert base_src.count(base_anchor) == 1
    commentary.write_text(
        base_src.replace(base_anchor, '"""Base classes for host-native harness drivers."""'),
        encoding="utf-8",
    )
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


def test_skills_script_comment_does_not_stale_runtime(tmp_path: Path) -> None:
    """A comment under `skills/` is not a skill change; a statement still is (#444).

    `skills_tree_hash` sits in the runtime plane, so the byte-wise recipe used to
    cost every host a live re-proof for a comment inside a skill script.
    """
    copy_root = _disposable_copy(tmp_path)
    script = copy_root / "skills" / "swarm" / "scripts" / "partition.py"
    original = script.read_bytes()
    fresh = compute_surface_revisions(copy_root, "grok")
    receipt = VerificationReceipt(
        run_id="skills-tree-hash-regression",
        host="grok",
        host_version="test",
        timestamp="2026-10-17T00:00:00Z",
        overall_verdict="PASS",
        planes={plane: "PASS" for plane in CONFORMANCE_PLANES},
        surface_revisions=fresh,
    )
    assert receipt.evaluate_plane_staleness(fresh) == {
        "canonical": [], "adapter": [], "package": [], "runtime": []
    }

    script.write_bytes(original + b"\n# comment only: no behaviour changed\n")
    assert compute_surface_revisions(copy_root, "grok") == fresh

    script.write_bytes(original + b"\nBEHAVIOR_PROBE = 'changed skill behaviour'\n")
    edited = compute_surface_revisions(copy_root, "grok")
    assert edited.skills_tree_hash != fresh.skills_tree_hash
    assert replace(edited, skills_tree_hash=fresh.skills_tree_hash) == fresh
    stale_map = receipt.evaluate_plane_staleness(edited)
    assert {plane for plane, reasons in stale_map.items() if reasons} == {"runtime"}
    assert stale_map["runtime"][0].startswith("skills_tree_hash mismatch")

    script.write_bytes(original)
    assert compute_surface_revisions(copy_root, "grok") == fresh


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


def test_check_evidence_fails_when_a_row_disagrees_with_its_receipt(tmp_path: Path) -> None:
    """The reader is the only closure for the window between the durable write and the row.

    No writer-side guard can cover a crash in between (ENOSPC, SIGINT, a read-only index),
    so `check-evidence` has to compare the inventory to the bytes it names (#495). The same
    command on the untouched copy is the positive control: it exits 0.
    """
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


def _declared_from(scenarios: list) -> tuple[dict, str]:
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
    # The failed package plane is a FAIL scenario, not a hand-written declared plane:
    # the receipt's own rows are what the gate reads (#473).
    for row in data["scenarios"]:
        if row["plane"] == "package":
            row["verdict"], row["exit_code"] = "FAIL", 1
    data["planes"], data["overall_verdict"] = _declared_from(
        [ScenarioResult(**row) for row in data["scenarios"]]
    )
    receipt_path.write_text(json.dumps(data), encoding="utf-8")

    # The adapter PASS and the settled runtime scenario prove their own planes only.
    assert derive_support_state(prof, root) == "verified"
    with pytest.raises(ValidationError, match="exceeds evidence-derived support state 'verified'"):
        check_evidence_durability(replace(prof, support_state="supported"), root)


def test_bare_live_label_without_settlement_stays_packaged(tmp_path: Path) -> None:
    root, prof = _synthetic_evidence_root(tmp_path, ["offline", "observed_live"], force_verified=True)
    assert derive_support_state(prof, root) == "packaged"


def test_static_isolation_row_cannot_satisfy_the_runtime_plane_on_its_own() -> None:
    """#291 negative direction: a static runtime row proves no live runtime.

    A static isolation row must not stand in for observed isolation — it is not an
    observed settlement, so the runtime plane it would claim reduces to UNTESTED
    (#473), and a `verified` pin to it is rejected until the live isolation run
    replaces the row.

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
    """Minimal omp root whose durable receipt already carries a live settlement.

    The receipt is the whole-receipt shape a driver writes: one row per plane, planes
    declared from that reduction, so the durable bytes stay evidence-shaped (#473)."""
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


def _portable_verifier(evidence_root: Path, root: Path | None = None):
    loader = importlib.util.spec_from_file_location("verify_portable_preserve", ROOT / "scripts" / "verify-portable.py")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    if root is not None:
        # proof_bar reads the surface revisions off the module root. Point it at the
        # fixture root so the receipt it assembles is comparable to the durable one there.
        module.ROOT = root
    verifier = module.PortableVerifier(host="omp", evidence_root=evidence_root)
    verifier.launch()
    return verifier


def _proof_bar_refresh(root: Path, evidence_root: Path, *, verdict: str = "PASS") -> tuple:
    """Assemble the route-free refresh receipt the way `verify-portable.py run` does.

    The fixture used to hand-write `planes={plane: "PASS"}`, so the preservation path and
    the settlement gate could disagree with no test noticing: the durable receipt carried
    a live settlement row under a runtime UNTESTED plane and demoted the host (#322, #444).
    Reduce the planes from the scenarios instead, exactly like the CLI does.
    """
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
    """A model-route-free refresh must not delete the live proof its own gate reads."""
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)
    # The refresh itself observed no child, so its own planes claim no live runtime.
    assert receipt.planes["runtime"] == "UNTESTED"
    assert receipt.overall_verdict == "UNTESTED"

    verifier.evidence(receipt, update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["evidence_level"] == "observed_live"
    assert scenario["settlement"]["child_id"] == "subagent-1"
    assert scenario["settlement"]["terminal_outcome"] == "success"
    assert scenario["preserved_from"] == "previous-live-run"
    # The preserved settlement is what the runtime gate reads, so the planes land with
    # the live row instead of demoting the host for a reason unrelated to the refresh.
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
    # Nothing was preserved, so the settlement-free plane stays UNTESTED.
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
    """The one place a prior observation lives must survive a run that cannot read it.

    The index row follows the durable bytes it names (#495): a refused overwrite leaves the
    row on the run whose receipt is actually on disk, not on the run that was refused.
    """
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


@pytest.mark.parametrize("shape", ["[]", '{"version": 1, "hosts": []}'])
def test_a_wrong_shaped_evidence_index_is_refused_not_crashed(tmp_path: Path, shape: str) -> None:
    """A parseable index of the wrong shape refuses the whole update, like an unreadable one.

    `[]` reached `index_data.setdefault` and died with AttributeError; `{"hosts": []}` with
    TypeError. Both *after* `omp-receipt.json` had been rewritten, so the refusal left the
    index naming a run whose durable bytes were gone (#495). Nothing durable may move, and
    the run that was refused still keeps its own run receipt.
    """
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_file.write_text(shape, encoding="utf-8")

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    with pytest.raises(SystemExit) as exit_info:
        second.evidence(second_receipt, update_durable=True)

    assert "REFUSING to rewrite the unreadable evidence index" in str(exit_info.value.code)
    assert str(index_file) in str(exit_info.value.code)
    assert durable.read_bytes() == durable_before
    assert index_file.read_text(encoding="utf-8") == shape
    run_receipt = json.loads((second.run_dir / "receipt.json").read_text(encoding="utf-8"))
    assert run_receipt["run_id"] == second_receipt.run_id != first_receipt.run_id


def test_a_corrupt_evidence_index_is_refused_not_reset(tmp_path: Path) -> None:
    """index.json is the inventory of every host's durable receipt.

    A run that cannot read it used to fall back to a fresh {"hosts": {}} and write its
    own host alone, silently un-listing the other hosts (#429, #444). It must fail
    loudly, name the file, and leave the bytes on disk for the operator to recover.
    """
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    index_file = evidence_root / "index.json"
    index_file.write_text(
        json.dumps({"version": 1, "hosts": {"grok": {"run_id": "grok-run"}}}), encoding="utf-8"
    )
    corrupt_bytes = b'{ "version": 1, "hosts": { "grok": { "run_id": "grok-run"'
    index_file.write_bytes(corrupt_bytes)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)

    with pytest.raises(SystemExit) as exit_info:
        verifier.evidence(receipt, update_durable=True)

    assert str(index_file) in str(exit_info.value.code)
    # No silent reset and no backup-and-continue: the corrupt bytes are untouched.
    assert index_file.read_bytes() == corrupt_bytes
    assert (verifier.run_dir / "receipt.json").is_file()


def test_a_stat_denied_evidence_index_is_refused_not_crashed(tmp_path: Path) -> None:
    """A stat denial above index.json is a refusal, not a traceback (#495).

    The guard stats through the link, so a parent directory this run cannot search
    raised PermissionError *before* the read that already knows how to refuse. A
    denied stat must route into that same refusal: name the file, leave both durable
    byte sets alone, and keep the run's own receipt.
    """
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_before = index_file.read_bytes()

    denied = tmp_path / "denied"
    denied.mkdir()
    real_index = denied / "index.json"
    real_index.write_bytes(index_before)
    index_file.unlink()
    index_file.symlink_to(real_index)
    denied.chmod(0o000)

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    try:
        with pytest.raises(SystemExit) as exit_info:
            second.evidence(second_receipt, update_durable=True)
        assert "REFUSING to rewrite the unreadable evidence index" in str(exit_info.value.code)
        assert str(index_file) in str(exit_info.value.code)
        assert durable.read_bytes() == durable_before
        assert (second.run_dir / "receipt.json").is_file()
    finally:
        denied.chmod(0o755)

    assert real_index.read_bytes() == index_before


def test_a_stat_denied_durable_receipt_is_refused_not_crashed(tmp_path: Path) -> None:
    """The durable guard refuses the same denial instead of crashing on the stat (#495)."""
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    durable = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    durable_before = durable.read_bytes()
    index_before = index_file.read_bytes()

    denied = tmp_path / "denied"
    denied.mkdir()
    real_durable = denied / "omp-receipt.json"
    real_durable.write_bytes(durable_before)
    durable.unlink()
    durable.symlink_to(real_durable)
    denied.chmod(0o000)

    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    try:
        second.evidence(second_receipt, update_durable=True)
    finally:
        denied.chmod(0o755)

    # The refused overwrite leaves the durable bytes and the row that names them alone.
    assert durable.read_bytes() == durable_before
    assert index_file.read_bytes() == index_before
    assert (second.run_dir / "receipt.json").is_file()


def test_a_missing_evidence_index_is_initialized_for_this_host(tmp_path: Path) -> None:
    """A fresh evidence root has no inventory to protect, so the first host creates it."""
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    index_file = evidence_root / "index.json"
    assert not index_file.is_file()
    verifier, receipt = _proof_bar_refresh(root, evidence_root)

    verifier.evidence(receipt, update_durable=True)

    index = json.loads(index_file.read_text(encoding="utf-8"))
    assert sorted(index["hosts"]) == ["omp"]
    assert index["hosts"]["omp"]["run_id"] == receipt.run_id


def test_repeated_refreshes_keep_the_run_that_observed(tmp_path: Path) -> None:
    """A second model-route-free refresh must not rewrite the provenance chain."""
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)

    first, first_receipt = _proof_bar_refresh(root, evidence_root)
    first.evidence(first_receipt, update_durable=True)
    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    second.evidence(second_receipt, update_durable=True)

    durable = json.loads((evidence_root / "omp-receipt.json").read_text(encoding="utf-8"))
    scenario = next(s for s in durable["scenarios"] if s["id"] == "runtime-child-spawn-omp")
    assert scenario["preserved_from"] == "previous-live-run"
    assert scenario["settlement"]["child_id"] == "subagent-1"
    assert durable["planes"]["runtime"] == "PASS"


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


def test_a_corrupt_index_refusal_leaves_the_durable_receipt_untouched(tmp_path: Path) -> None:
    """A corrupt index refuses the whole durable update, receipt included (#495).

    The receipt used to be rewritten before the index was parsed, so the abort left
    a new run_id in omp-receipt.json and the previous one in the repaired index row.
    """
    root, prof, evidence_root, _ = _omp_live_root(tmp_path)
    verifier, receipt = _proof_bar_refresh(root, evidence_root)
    verifier.evidence(receipt, update_durable=True)

    durable_file = evidence_root / "omp-receipt.json"
    index_file = evidence_root / "index.json"
    durable_before = durable_file.read_bytes()
    assert json.loads(index_file.read_text(encoding="utf-8"))["hosts"]["omp"]["run_id"] == json.loads(
        durable_before
    )["run_id"]

    corrupt = b'{ "version": 1, "hosts": { BAD'
    index_file.write_bytes(corrupt)
    second, second_receipt = _proof_bar_refresh(root, evidence_root)
    with pytest.raises(SystemExit):
        second.evidence(second_receipt, update_durable=True)

    assert durable_file.read_bytes() == durable_before
    assert index_file.read_bytes() == corrupt
    # The refused run still keeps its own run receipt, so the abort names real evidence.
    assert json.loads((second.run_dir / "receipt.json").read_text(encoding="utf-8"))["run_id"] == second_receipt.run_id


def test_supported_needs_a_behavioral_pass_on_every_row(tmp_path: Path) -> None:
    """A non-floor row citing a package-only PASS receipt proves `verified`, not `supported` (#473).

    The supported loop read the package plane alone, so a receipt with FAIL
    canonical/adapter/runtime still derived `supported` and outvoted the floor.
    The lane-A probe set (behavioral FAILs, foreign host, settlement-free omp
    receipt) must all stop at `verified` and fail the supported claim.

    Every probe is expressed as scenarios (a `FAIL` row, a foreign host, static
    settlement-free rows) and declares the planes that reduction yields — the
    declaration is no longer free to disagree with the rows (#473).
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
    assert derive_support_state(prof, root) == "supported"

    floor_ref = ".audit/evidence/synthetic-receipt.json"
    rest_ref = ".audit/evidence/rest.json"
    base = json.loads((root / floor_ref).read_text(encoding="utf-8"))
    # Claimed supported, with every conditional row citing a second receipt: only the
    # nine floor rows keep the settled receipt that does prove `verified`.
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
        # Package PASS beside FAIL canonical/adapter/runtime rows: the receipt says so in
        # its own scenarios, which is the only way it may say it.
        "package-only-PASS": (
            {"scenarios": [behavioral_fail(row) for row in base["scenarios"]]},
            "exceeds evidence-derived support state 'verified'",
        ),
        # A foreign-host receipt is already refused earlier by the durability check,
        # so this probe pins the derivation half only.
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
    """#473: the runtime plane is gated once, and a FAIL row cannot slip under it.

    Before the dedupe the runtime clause existed in two loops, so deleting it from
    either one left the suite green — the other copy still read the plane, and no test
    noticed. This pins the one evaluator instead: the row's only non-PASS plane is
    runtime (declared and evidenced FAIL by a second runtime row, per #473's rules),
    while the settled observed_live row that would satisfy the settlement clause stays
    in the receipt. Both bars must refuse it.
    """
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

    # Positive control: the same evaluator on the same row shape clears both bars as
    # soon as the runtime plane really passes, so the refusals above are the plane.
    clean = VerificationReceipt(**data_before)
    clean.validate()
    assert _row_level(clean, prof, revisions, require_package=False) == "verified"
    assert _row_level(clean, prof, revisions, require_package=True) == "supported"


def test_a_package_only_pass_never_clears_a_bar(tmp_path: Path) -> None:
    """#473: one evaluator — `supported` is the floor bar plus `package` and nothing else.

    Both directions of the act-on's `package-only-PASS` shape are pinned against the
    single evaluator: a package PASS whose behavioral planes FAIL clears neither bar,
    and a row that clears the floor on behavior alone stops at `verified` because the
    same evaluator asks one plane more. Delete the package clause from the one bar and
    the second direction is what reddens (the pre-dedupe suite had a second copy of the
    package check in the `supported` loop that this test would not have reached).
    """
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

    # package-only PASS: the behavioral planes FAIL, so neither bar may be cleared.
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

    # The converse: the floor bar clears on the behavioral planes alone, and the
    # package plane is the only thing `supported` adds.
    package_fail = row_with({"package": "FAIL"})
    assert _row_level(package_fail, prof, revisions, require_package=False) == "verified"
    assert _row_level(package_fail, prof, revisions, require_package=True) == ""
    assert derive_support_state(prof, root) == "verified"


def test_a_receipt_cannot_declare_a_plane_it_never_observed(tmp_path: Path) -> None:
    """Act-on probe A (#473): zero scenarios under four declared PASS planes.

    The hand-written declaration was a `supported` receipt: no scenario proved anything,
    and every row that cited these bytes read the declared plane. Both readers now refuse
    the bytes instead, and the host the rows belong to derives at `packaged`.
    """
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
    """Act-on probe B (#473): declared runtime PASS beside a FAIL runtime row.

    The declaration used to win: the runtime row failed, the plane said PASS, and the
    receipt derived `supported`.
    """
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
    """Explicit `evidence_level: null` is not evidence, at either level (#473)."""
    scenario = _omp_spawn_scenario("offline")
    scenario.evidence_level = None
    with pytest.raises(ValidationError, match="records no evidence_level"):
        scenario.validate()

    durable = json.loads((EVIDENCE_DIR / "codex-receipt.json").read_text(encoding="utf-8"))
    durable["scenarios"][0]["evidence_level"] = None
    with pytest.raises(ValidationError, match="records no evidence_level"):
        VerificationReceipt(**durable).validate()


def test_driver_shaped_receipts_still_validate() -> None:
    """Positive control: the tightening rejects nothing a run actually produced.

    The five durable receipts are already evidence-shaped (§0), and a receipt assembled
    the way the driver assembles one — planes from the scenario reduction — validates.
    """
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
    """#473: two rows for one capability collapse last-wins, so the dropped row's
    evidence stops being read and nine duplicate floor rows could hide a `FAIL` receipt
    behind a `supported` baseline. One predicate in `HarnessProfile.validate()` refuses
    the shape on both readers instead.
    """
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

    # The act-on's reproduction shape: nine duplicate floor rows citing a FAIL-plane
    # receipt, prepended to the supported baseline. Last-wins read the baseline's good
    # receipt and derived `supported`; the shape is refused before any row is read.
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


def test_check_evidence_validates_the_profile_it_reads(tmp_path: Path) -> None:
    """#473: the check-evidence path skipped the domain rules doctor already ran.

    A profile claiming `supported` with a `gap` on a mandatory floor capability used to
    pass `check-evidence`; the same predicate now runs on both readers, so the claim is
    refused by name instead of being derived.
    """
    root, prof = _synthetic_evidence_root(
        tmp_path,
        ["offline", "observed_live"],
        settlements=[None, _success_settlement()],
        force_verified=True,
    )
    gap_row = replace(
        next(b for b in prof.bindings if b.capability == "workspace.shared"),
        implementation_status="gap",
    )
    bad = replace(
        prof,
        support_state="supported",
        bindings=[gap_row if b.capability == "workspace.shared" else b for b in prof.bindings],
    )
    message = r"cannot have gap on mandatory capability workspace\.shared"
    with pytest.raises(ValidationError, match=message):
        derive_support_state(bad, root)
    with pytest.raises(ValidationError, match=message):
        check_evidence_durability(bad, root)


def test_check_evidence_cli_refuses_a_profile_that_violates_a_domain_rule(tmp_path: Path) -> None:
    """The CLI path is the reachability half of the same rule (#473)."""
    copy_root = _disposable_copy(tmp_path)
    command = [
        sys.executable,
        str(copy_root / "scripts" / "verify-portable.py"),
        "check-evidence",
        "--host",
        "grok",
    ]
    clean = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert clean.returncode == 0, clean.stdout + clean.stderr

    profile_file = copy_root / "profiles" / "grok.json"
    d = json.loads(profile_file.read_text(encoding="utf-8"))
    d["support_state"] = "supported"
    # Every row verified, so the *gap* rule is the one that fires rather than the
    # unverified-row rule that precedes it in the mandatory-floor scan.
    for binding in d["bindings"]:
        binding["verification_status"] = "verified"
        if binding["capability"] == "workspace.shared":
            binding["implementation_status"] = "gap"
    profile_file.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")

    res = subprocess.run(command, capture_output=True, text=True, cwd=copy_root)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "[grok] FAIL" in res.stdout
    assert "cannot have gap on mandatory capability workspace.shared" in res.stdout
