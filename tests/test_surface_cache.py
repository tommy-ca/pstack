import ast
import importlib.util
import json
import os
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
    CONFORMANCE_PLANES,
    Evidence,
    HarnessProfile,
    PLANE_SURFACE_DEPENDENCIES,
    SurfaceRevisions,
    ValidationError,
    VerificationReceipt,
    _driver_core,
    check_evidence_durability,
    compute_surface_revisions,
)


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


def _package_ignored_paths() -> frozenset:
    listed = subprocess.run(
        [
            "git", "-C", str(ROOT), "ls-files",
            "--others", "--ignored", "--exclude-standard", "--directory", "-z",
        ],
        capture_output=True,
        check=True,
    ).stdout
    return frozenset(os.fsdecode(path.rstrip(b"/")) for path in listed.split(b"\0") if path)


_PACKAGE_IGNORED = _package_ignored_paths()


def _disposable_copy(tmp_path: Path) -> Path:
    """Fresh extraction of the repo as an installed/extracted package: no .git,
    no pre-existing dependency or bytecode artifacts."""
    copy_root = tmp_path / "extracted-package"
    dropped_by_name = shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".venv")

    def ignore(src: str, names: list) -> set:
        skipped = set(dropped_by_name(src, names))
        skipped.update(
            name for name in names
            if Path(src, name).relative_to(ROOT).as_posix() in _PACKAGE_IGNORED
        )
        return skipped

    shutil.copytree(ROOT, copy_root, ignore=ignore)
    return copy_root


@pytest.mark.skipif(sys.platform == "win32", reason="requires POSIX byte-path semantics")
def test_the_disposable_copy_drops_only_git_ignored_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "-C", str(source), "init", "--quiet"], check=True)
    (source / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
    evidence = source / ".audit" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "index.json").write_text("tracked receipt index", encoding="utf-8")
    (evidence / "keep.txt").write_text("unignored input", encoding="utf-8")
    carriage_return_name = "ignored\rname.tmp"
    non_utf8_name = os.fsdecode(b"ignored-\xff.tmp")
    (evidence / carriage_return_name).write_text("ignored", encoding="utf-8")
    (evidence / non_utf8_name).write_text("ignored", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(source), "add", "--", ".gitignore", ".audit/evidence/index.json"],
        check=True,
    )

    monkeypatch.setitem(globals(), "ROOT", source)
    monkeypatch.setitem(globals(), "_PACKAGE_IGNORED", _package_ignored_paths())
    copied = _disposable_copy(tmp_path) / ".audit" / "evidence"

    assert (copied / "index.json").read_text(encoding="utf-8") == "tracked receipt index"
    assert (copied / "keep.txt").read_text(encoding="utf-8") == "unignored input"
    assert not (copied / carriage_return_name).exists()
    assert not (copied / non_utf8_name).exists()


def test_package_ignored_path_query_propagates_git_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "not-a-git-repository"
    source.mkdir()
    monkeypatch.setitem(globals(), "ROOT", source)

    with pytest.raises(subprocess.CalledProcessError):
        _package_ignored_paths()


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
    assert compute_surface_revisions(copy_root, "codex") == fresh

    driver_file.write_bytes(original + b"\nBEHAVIOR_PROBE = 'changed verification behavior'\n")
    edited = compute_surface_revisions(copy_root, "codex")

    assert edited.driver_revision != fresh.driver_revision
    expected_planes = {"adapter", "runtime"}
    if relative_path == "scripts/portability_schema.py":
        assert edited.package_driver_revision != fresh.package_driver_revision
        expected_planes.add("package")
    else:
        assert replace(edited, driver_revision=fresh.driver_revision) == fresh
    stale_map = receipt.evaluate_plane_staleness(edited)
    assert {plane for plane, reasons in stale_map.items() if reasons} == expected_planes
    for plane, dependencies in PLANE_SURFACE_DEPENDENCIES.items():
        if plane in expected_planes:
            assert len(stale_map[plane]) == 1
        else:
            assert stale_map[plane] == []

    driver_file.write_bytes(original)
    assert compute_surface_revisions(copy_root, "codex") == fresh


def test_mutated_model_role_policy_stales_the_package_plane(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    profile_data = json.loads((copy_root / "profiles" / "grok.json").read_text(encoding="utf-8"))
    prof = HarnessProfile(
        host=profile_data["host"],
        support_state=profile_data["support_state"],
        bindings=[Binding(**x) for x in profile_data["bindings"]],
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        evidence_ledger=[Evidence(**x) for x in profile_data.get("evidence_ledger", [])],
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )
    assert prof.support_state == "packaged"

    fresh = compute_surface_revisions(copy_root, "grok")
    receipt_data = json.loads(
        (copy_root / ".audit" / "evidence" / "grok-receipt.json").read_text(encoding="utf-8")
    )
    receipt_data["surface_revisions"] = asdict(fresh)
    (copy_root / ".audit" / "evidence" / "grok-receipt.json").write_text(
        json.dumps(receipt_data, indent=2), encoding="utf-8"
    )
    assert VerificationReceipt(**receipt_data).evaluate_plane_staleness(fresh) == {
        plane: [] for plane in CONFORMANCE_PLANES
    }
    assert check_evidence_durability(prof, copy_root)["derived_support_state"] == "packaged"

    policy_file = copy_root / "examples" / "portability" / "model-role-policy.example.json"
    original = policy_file.read_bytes()
    mutated = original.replace(b'"cursor/plugins"', b'"cursor/pluginx"')
    assert len(mutated) == len(original) and mutated != original
    policy_file.write_bytes(mutated)

    edited = compute_surface_revisions(copy_root, "grok")
    assert edited.package_driver_revision != fresh.package_driver_revision
    assert replace(edited, package_driver_revision=fresh.package_driver_revision) == fresh
    stale_map = VerificationReceipt(**receipt_data).evaluate_plane_staleness(edited)
    assert {plane for plane, reasons in stale_map.items() if reasons} == {"package"}
    assert stale_map["package"][0].startswith("package_driver_revision mismatch")

    with pytest.raises(ValidationError, match="evidence is stale for claimed packaged") as refused:
        check_evidence_durability(prof, copy_root)
    assert "(package)" in str(refused.value)
    assert "package_driver_revision mismatch" in str(refused.value)

    policy_file.unlink()
    assert compute_surface_revisions(copy_root, "grok").package_driver_revision != fresh.package_driver_revision
    with pytest.raises(ValidationError, match="evidence is stale for claimed packaged"):
        check_evidence_durability(prof, copy_root)

    schema_file = copy_root / "schemas" / "portability" / "model-role-policy.schema.json"
    schema_file.unlink()
    assert compute_surface_revisions(copy_root, "grok").package_driver_revision != fresh.package_driver_revision
    with pytest.raises(ValidationError, match="evidence is stale for claimed packaged"):
        check_evidence_durability(prof, copy_root)


def test_mutated_planner_module_stales_the_package_plane(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    profile_data = json.loads((copy_root / "profiles" / "grok.json").read_text(encoding="utf-8"))
    prof = HarnessProfile(
        host=profile_data["host"],
        support_state=profile_data["support_state"],
        bindings=[Binding(**x) for x in profile_data["bindings"]],
        skills_dir=profile_data.get("skills_dir"),
        plugins_dir=profile_data.get("plugins_dir"),
        plugin_manifest=profile_data.get("plugin_manifest"),
        evidence_ledger=[Evidence(**x) for x in profile_data.get("evidence_ledger", [])],
        tool_mappings=profile_data.get("tool_mappings"),
        skill_order=profile_data.get("skill_order"),
        runtime_conventions=profile_data.get("runtime_conventions"),
    )
    fresh = compute_surface_revisions(copy_root, "grok")
    receipt_data = json.loads(
        (copy_root / ".audit" / "evidence" / "grok-receipt.json").read_text(encoding="utf-8")
    )
    receipt_data["surface_revisions"] = asdict(fresh)
    (copy_root / ".audit" / "evidence" / "grok-receipt.json").write_text(
        json.dumps(receipt_data, indent=2), encoding="utf-8"
    )
    assert VerificationReceipt(**receipt_data).evaluate_plane_staleness(fresh) == {
        plane: [] for plane in CONFORMANCE_PLANES
    }

    resolver = copy_root / "scripts" / "model_role_resolver.py"
    src = resolver.read_text(encoding="utf-8")
    anchor = "unproven = unproven_catalog_reason(config)"
    assert src.count(anchor) == 1
    resolver.write_text(src.replace(anchor, "unproven = None  # probe mutation"), encoding="utf-8")

    edited = compute_surface_revisions(copy_root, "grok")
    assert edited.package_driver_revision != fresh.package_driver_revision
    assert replace(edited, package_driver_revision=fresh.package_driver_revision) == fresh
    stale_map = VerificationReceipt(**receipt_data).evaluate_plane_staleness(edited)
    assert {plane for plane, reasons in stale_map.items() if reasons} == {"package"}
    with pytest.raises(ValidationError, match="evidence is stale for claimed packaged"):
        check_evidence_durability(prof, copy_root)


def test_mutated_vocabulary_module_stales_the_package_plane(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "grok")

    vocab = copy_root / "scripts" / "portability_types.py"
    src = vocab.read_text(encoding="utf-8")
    anchor = 'VERIFICATION_STATUSES = ("verified", "static-only", "unverified", "stale")'
    assert src.count(anchor) == 1
    vocab.write_text(src.replace(anchor, anchor + "  # probe mutation"), encoding="utf-8")

    assert compute_surface_revisions(copy_root, "grok").package_driver_revision == fresh.package_driver_revision

    vocab.write_text(src.replace('"stale"', '"stale-renamed"'), encoding="utf-8")
    edited = compute_surface_revisions(copy_root, "grok")
    assert edited.package_driver_revision != fresh.package_driver_revision
    assert replace(edited, package_driver_revision=fresh.package_driver_revision) == fresh
    receipt_data = json.loads(
        (copy_root / ".audit" / "evidence" / "grok-receipt.json").read_text(encoding="utf-8")
    )
    stale_map = VerificationReceipt(**receipt_data).evaluate_plane_staleness(edited)
    assert "package" in {plane for plane, reasons in stale_map.items() if reasons}


def test_mutated_portability_schema_stales_both_driver_and_package_revisions(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "grok")

    schema_file = copy_root / "scripts" / "portability_schema.py"
    original = schema_file.read_bytes()
    schema_file.write_bytes(original + b"\n# AST inert comment\n")
    assert compute_surface_revisions(copy_root, "grok") == fresh

    schema_file.write_bytes(original + b"\nSCHEMA_PROBE = 'probe mutation'\n")
    edited = compute_surface_revisions(copy_root, "grok")
    assert edited.package_driver_revision != fresh.package_driver_revision
    assert edited.driver_revision != fresh.driver_revision
    assert replace(edited, package_driver_revision=fresh.package_driver_revision,
                    driver_revision=fresh.driver_revision) == fresh


def test_published_module_docstring_moves_the_driver_revision(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")

    published = copy_root / "scripts" / "verify-portable.py"
    src = published.read_text(encoding="utf-8")
    anchor = '"""Portable lever verification engine for pstack across agent harnesses.'
    assert src.count(anchor) == 1
    published.write_text(
        src.replace(anchor, '"""Portable lever engine for pstack across agent harnesses.'),
        encoding="utf-8",
    )
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


@pytest.mark.parametrize(
    "relative_path",
    [
        "skills/interrogate/scripts/pack.py",
        "skills/swarm/scripts/partition.py",
        "skills/swarm/scripts/apply.py",
        "skills/swarm/scripts/refresh-hygiene.py",
    ],
)
def test_published_skill_docstring_moves_skills_tree_hash(tmp_path: Path, relative_path: str) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    script = copy_root / relative_path
    src = script.read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)
    anchor = tree.body[0].value.value
    script.write_text(src.replace(anchor, anchor + " Published at --help.", 1), encoding="utf-8")
    assert compute_surface_revisions(copy_root, "grok").skills_tree_hash != fresh


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

    pkg = copy_root / "skills" / "poteto-mode" / "scripts" / "node_modules" / "some-pkg"
    pkg.mkdir(parents=True)
    (pkg / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
    after_deps = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert after_deps == fresh

    pyc_dir = copy_root / "skills" / "swarm" / "scripts" / "__pycache__"
    pyc_dir.mkdir(parents=True)
    (pyc_dir / "partition.cpython-312.pyc").write_bytes(b"\x00\x01fake-bytecode")
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

    skill_file.write_text(original, encoding="utf-8")
    reverted = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    assert reverted == fresh


def test_skills_script_comment_does_not_stale_runtime(tmp_path: Path) -> None:
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


def test_unparseable_skills_script_names_its_file_without_aborting(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash
    bad = copy_root / "skills" / "legacy-pack" / "scripts" / "legacy.py"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b'print "py2"\n')
    named = compute_surface_revisions(copy_root, "grok")
    assert named.skills_tree_hash != fresh
    assert compute_surface_revisions(copy_root, "grok").skills_tree_hash == named.skills_tree_hash
    bad.write_bytes(b'print "py2 with more bytes"\n')
    changed = compute_surface_revisions(copy_root, "grok")
    assert changed.skills_tree_hash != named.skills_tree_hash
    second_root = tmp_path / "extracted-package-2"
    shutil.copytree(copy_root, second_root)
    assert (
        compute_surface_revisions(second_root, "grok").skills_tree_hash
        == changed.skills_tree_hash
    )
    bad.unlink()
    assert compute_surface_revisions(copy_root, "grok").skills_tree_hash == fresh


def test_driver_core_is_memoised_by_content_not_by_location(tmp_path: Path) -> None:
    src = b"def probe():\n    return 1\n"
    one = tmp_path / "one" / "probe.py"
    two = tmp_path / "two" / "probe.py"
    assert _driver_core(one, src) is _driver_core(one, src)
    assert _driver_core(one, src) == _driver_core(two, src)
    assert _driver_core(one, b'"""published docs"""\n' + src) == _driver_core(one, src)
    assert _driver_core(one, b"def probe():\n    return 2\n") != _driver_core(one, src)
    publishing = tmp_path / "pack.py"
    assert _driver_core(publishing, b'"""docs"""\n' + src) != _driver_core(publishing, src)


@pytest.mark.skipif(
    os.name != "posix", reason="disk cache requires POSIX permission checks"
)
def test_driver_core_disk_cache_persists_and_tracks_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy_root = _disposable_copy(tmp_path)
    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    driver = copy_root / "scripts" / "drivers" / "base.py"
    program = (
        "import sys; from pathlib import Path; "
        "from scripts.portability_schema import compute_surface_revisions; "
        "print(compute_surface_revisions(Path(sys.argv[1]), 'grok').driver_revision)"
    )

    def run_revision() -> str:
        proc = subprocess.run(
            [sys.executable, "-c", program, str(copy_root)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()

    first = run_revision()
    cache_dir = cache_home / "pstack" / "driver-core"
    assert list(cache_dir.glob("*.json"))
    assert run_revision() == first
    corrupt = next(cache_dir.glob("*.json"))
    corrupt.write_text("{", encoding="utf-8")
    assert run_revision() == first

    driver.write_bytes(driver.read_bytes() + b"\nCACHE_PROBE = 'changed'\n")
    assert run_revision() != first


@pytest.mark.skipif(
    os.name != "posix", reason="disk cache requires POSIX permission checks"
)
def test_driver_core_disk_cache_keeps_published_docs_basename_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = tmp_path / "same-source.py"
    source.write_bytes(b'"""published docs"""\ndef probe():\n    return 1\n')
    program = (
        "import json, sys; from pathlib import Path; "
        "from scripts.portability_schema import _driver_core; "
        "src = Path(sys.argv[1]).read_bytes(); "
        "print(json.dumps([_driver_core(Path('verify-portable.py'), src).decode(), "
        "_driver_core(Path('ordinary.py'), src).decode()]))"
    )

    def run_cores() -> list[str]:
        proc = subprocess.run(
            [sys.executable, "-c", program, str(source)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    first = run_cores()
    assert "published docs" in first[0]
    assert "published docs" not in first[1]
    assert first[0] != first[1]
    cache_dir = cache_home / "pstack" / "driver-core"
    assert len(list(cache_dir.glob("*.json"))) >= 2
    assert run_cores() == first


def test_driver_core_cache_unavailable_path_preserves_core(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_home = tmp_path / "not-a-directory"
    cache_home.write_text("blocked", encoding="utf-8")
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = b"def cache_offline_probe():\n    return 7\n"
    assert _driver_core(
        tmp_path / "cache_offline_probe.py", source
    ) == b"def cache_offline_probe():\n    return 7"


@pytest.mark.skipif(
    os.name != "posix", reason="simulates non-POSIX cache behavior on POSIX"
)
def test_driver_core_cache_is_disabled_without_posix_permission_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.portability_schema as schema
    from pathlib import PosixPath

    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    monkeypatch.setattr(schema, "Path", PosixPath)
    monkeypatch.setattr(schema.os, "name", "nt")

    assert schema._driver_core_cache_dir() is None
    assert not cache_home.exists()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX symlink semantics")
@pytest.mark.parametrize("symlink_component", ("cache-home", "pstack"))
def test_driver_core_cache_rejects_symlink_directory_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, symlink_component: str
) -> None:
    target = tmp_path / "symlink-target"
    target.mkdir()
    cache_home = tmp_path / "cache-home"
    if symlink_component == "cache-home":
        cache_home.symlink_to(target, target_is_directory=True)
        untouched = target / "pstack"
    else:
        cache_home.mkdir()
        (cache_home / "pstack").symlink_to(target, target_is_directory=True)
        untouched = target / "driver-core"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = f"def symlink_probe_{symlink_component.replace('-', '_')}():\n    return 1\n".encode()

    core = _driver_core(tmp_path / f"{symlink_component}.py", source)

    expected_name = symlink_component.replace("-", "_")
    assert core == f"def symlink_probe_{expected_name}():\n    return 1".encode()
    assert not untouched.exists()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX symlink semantics")
def test_driver_core_cache_rejects_symlinked_ancestor_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "symlink-target"
    target.mkdir()
    cache_link = tmp_path / "cache-link"
    cache_link.symlink_to(target, target_is_directory=True)
    cache_home = cache_link / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = b"def symlink_ancestor_probe():\n    return 1\n"

    core = _driver_core(tmp_path / "symlink-ancestor-probe.py", source)

    assert core == b"def symlink_ancestor_probe():\n    return 1"
    assert not (target / "cache-home").exists()


@pytest.mark.skipif(
    os.name != "posix", reason="requires POSIX directory mode semantics"
)
def test_driver_core_cache_rejects_world_writable_ancestor_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unsafe_parent = tmp_path / "world-writable-parent"
    unsafe_parent.mkdir()
    unsafe_parent.chmod(0o777)
    cache_home = unsafe_parent / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = b"def writable_ancestor_probe():\n    return 1\n"

    core = _driver_core(tmp_path / "writable-ancestor-probe.py", source)

    assert core == b"def writable_ancestor_probe():\n    return 1"
    assert not cache_home.exists()


@pytest.mark.skipif(
    os.name != "posix", reason="disk cache requires POSIX permission checks"
)
def test_driver_core_disk_cache_prunes_to_record_and_byte_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.surface_revisions as surface_revisions

    monkeypatch.setattr(surface_revisions, "_DRIVER_CORE_CACHE_MAX_RECORDS", 2)
    record_home = tmp_path / "record-bound"
    monkeypatch.setenv("XDG_CACHE_HOME", str(record_home))
    for index in range(3):
        _driver_core(
            tmp_path / f"record-bound-{index}.py",
            f"VALUE_{index} = {index}\n".encode(),
        )
    record_files = list((record_home / "pstack" / "driver-core").glob("*.json"))
    assert len(record_files) == 2

    byte_home = tmp_path / "byte-bound"
    monkeypatch.setenv("XDG_CACHE_HOME", str(byte_home))
    monkeypatch.setattr(surface_revisions, "_DRIVER_CORE_CACHE_MAX_RECORDS", 256)
    monkeypatch.setattr(surface_revisions, "_DRIVER_CORE_CACHE_MAX_BYTES", 2500)
    for index in range(3):
        source = f"VALUE_{index} = {'x' * 1024!r}\n".encode()
        _driver_core(tmp_path / f"byte-bound-{index}.py", source)
    byte_files = list((byte_home / "pstack" / "driver-core").glob("*.json"))
    byte_sizes = [path.stat().st_size for path in byte_files]
    assert len(byte_files) == 1
    assert 1250 < byte_sizes[0] <= 2500


def test_harness_verifier_dynamic_import_does_not_self_invalidate(tmp_path: Path) -> None:
    copy_root = _disposable_copy(tmp_path)
    partition_script = copy_root / "skills" / "swarm" / "scripts" / "partition.py"
    fresh = compute_surface_revisions(copy_root, "grok").skills_tree_hash

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
