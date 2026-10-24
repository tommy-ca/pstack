from __future__ import annotations

from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from scripts.portability_types import (
    Binding,
    ChildSettlement,
    CONFORMANCE_PLANES,
    Evidence,
    HarnessProfile,
    ScenarioResult,
    VerificationReceipt,
    reduce_verdicts,
    settle_planes,
)
from scripts.surface_revisions import compute_surface_revisions

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / ".audit" / "evidence"


def _declared_hosts() -> tuple:
    data = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    return tuple(data["host_targets"])


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


def _load_verify_portable_module():
    loader = importlib.util.spec_from_file_location(
        "verify_portable_refresh", ROOT / "scripts" / "verify-portable.py"
    )
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def _stat_denied_copy(tmp_path: Path, relative: str) -> tuple:
    copy_root = _disposable_copy(tmp_path)
    link = copy_root / relative
    denied = tmp_path / "denied"
    denied.mkdir()
    real = denied / Path(relative).name
    real.write_bytes(link.read_bytes())
    link.unlink()
    link.symlink_to(real)
    denied.chmod(0o000)
    return copy_root, link, denied


def _run_gate(copy_root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(copy_root / "scripts" / "verify-portable.py"), *arguments],
        capture_output=True,
        text=True,
        cwd=copy_root,
    )


def _declared_from(scenarios: list) -> tuple:
    planes = settle_planes(scenarios)
    return planes, reduce_verdicts(planes.values())


def _plane_rows(covered: set, verdict: str = "PASS") -> list:
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


def _synthetic_evidence_root(
    tmp_path: Path,
    evidence_levels: list,
    planes: list | None = None,
    host: str = "omp",
    snippets: list | None = None,
    settlements: list | None = None,
    force_verified: bool = False,
) -> tuple:
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


def _omp_spawn_scenario(
    evidence_level: str, verdict: str = "PASS", settlement=None, live_attempted: bool = False
) -> ScenarioResult:
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
        live_attempted=live_attempted,
    )


def _omp_live_root(tmp_path: Path) -> tuple:
    root = tmp_path / "repo"
    (root / ".omp-plugin").mkdir(parents=True)
    (root / "pstack.package.json").write_text(json.dumps({"version": "0.15.29"}), encoding="utf-8")
    (root / ".omp-plugin" / "package.json").write_text(json.dumps({"version": "0.15.29"}), encoding="utf-8")
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
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    if root is not None:
        module.ROOT = root
    verifier = module.PortableVerifier(host="omp", evidence_root=evidence_root)
    verifier.launch()
    return verifier


def _proof_bar_refresh(
    root: Path,
    evidence_root: Path,
    *,
    verdict: str = "PASS",
    live_attempted: bool = False,
    evidence_level: str = "static",
) -> tuple:
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
    verifier.scenarios.append(
        _omp_spawn_scenario(evidence_level, verdict=verdict, live_attempted=live_attempted)
    )
    return verifier, verifier.proof_bar()


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
