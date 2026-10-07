import importlib.util
import json
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


def test_all_five_profiles_pass_evidence_durability_and_freshness() -> None:
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
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
        assert result["claimed_support_state"] in ("verified", "supported")
        # Ensure derived state supports claimed state
        assert result["derived_support_state"] in ("verified", "supported")

        # Also test profile method
        method_result = prof.validate_evidence(ROOT, check_freshness=True)
        assert method_result["valid"] is True


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
    assert len(data) == 5
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        assert host in data
        assert data[host]["needs_regeneration"] is False
        assert data[host]["stale_planes"] == []
        assert data[host]["overall_verdict"] == "PASS"


def test_check_evidence_cli_output() -> None:
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify-portable.py"), "check-evidence", "--host", "all"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        assert f"[{host}] PASS: Evidence durable" in res.stdout
