from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.evidence_test_helpers import (
    CONFORMANCE_PLANES,
    EVIDENCE_DIR,
    ROOT,
    VerificationReceipt,
    _load_verify_portable_module,
    compute_surface_revisions,
)


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
        ["verify-portable.py", "refresh-static", "--host", "grok", "--evidence-dir", str(evidence_root)],
    )

    monkeypatch.setattr(module.PortableVerifier, "doctor", static_doctor)
    with pytest.raises(SystemExit) as exit_info:
        module.main()
    assert exit_info.value.code == 0

    refreshed = json.loads((evidence_root / "grok-receipt.json").read_text(encoding="utf-8"))
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
    assert receipt.evaluate_plane_staleness(compute_surface_revisions(ROOT, "grok")) == {
        plane: [] for plane in CONFORMANCE_PLANES
    }

    for host in receipt_hosts:
        if host == "grok":
            continue
        assert (evidence_root / f"{host}-receipt.json").read_bytes() == untouched[f"{host}-receipt.json"]
    index_after = json.loads((evidence_root / "index.json").read_text(encoding="utf-8"))
    assert sorted(index_after["hosts"]) == sorted(index_before["hosts"])
    assert index_after["hosts"]["grok"]["run_id"] == refreshed["run_id"]
    assert index_after["hosts"]["grok"]["overall_verdict"] == "UNTESTED"
    for host in receipt_hosts:
        if host == "grok":
            continue
        assert index_after["hosts"][host] == index_before["hosts"][host]

    monkeypatch.setattr(module.PortableVerifier, "doctor", failing_doctor)
    with pytest.raises(SystemExit) as failing_exit:
        module.main()
    assert failing_exit.value.code == 1

    failed = json.loads((evidence_root / "grok-receipt.json").read_text(encoding="utf-8"))
    assert failed["planes"]["package"] == "FAIL"
    assert failed["overall_verdict"] == "FAIL"


def test_refresh_static_refuses_when_prior_live_rows_cannot_be_reobserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_verify_portable_module()
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    for name in ("omp-receipt.json", "index.json"):
        shutil.copy2(EVIDENCE_DIR / name, evidence_root / name)
    durable_before = (evidence_root / "omp-receipt.json").read_bytes()
    live_ids = {
        s["id"]
        for s in json.loads(durable_before)["scenarios"]
        if s.get("evidence_level") == "observed_live"
    }
    assert live_ids, "checked-in omp receipt must carry live rows for this guard"

    def static_doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
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

    monkeypatch.setattr(module, "resolve_openspec_change", lambda change: ("none", None, []))
    monkeypatch.setattr(
        sys,
        "argv",
        ["verify-portable.py", "refresh-static", "--host", "omp", "--evidence-dir", str(evidence_root)],
    )
    monkeypatch.setattr(module.PortableVerifier, "doctor", static_doctor)
    with pytest.raises(SystemExit) as exit_info:
        module.main()
    assert "REFUSING to overwrite the durable receipt" in str(exit_info.value.code)
    assert "runtime-child-spawn-omp" in str(exit_info.value.code)
    assert "PSTACK_RUN_OMP_LIVE=1" in str(exit_info.value.code)
    assert (evidence_root / "omp-receipt.json").read_bytes() == durable_before


def test_refresh_static_host_all_skips_live_holding_hosts_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """#726: refresh-static --host all skips a host with live rows, prints that it kept them, and exits 0."""
    module = _load_verify_portable_module()
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    for name in ("omp-receipt.json", "grok-receipt.json", "index.json"):
        shutil.copy2(EVIDENCE_DIR / name, evidence_root / name)
    durable_omp_before = (evidence_root / "omp-receipt.json").read_bytes()

    def static_doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        for plane in ("canonical", "adapter", "package"):
            self.scenarios.append(
                module.ScenarioResult(
                    id=f"doctor-{plane}-{self.host}-stub",
                    description=f"stub static {plane} plane for {self.host}",
                    plane=plane,
                    command="stub",
                    exit_code=0,
                    stdout_snippet="stub",
                    verdict="PASS",
                    duration_s=0.0,
                )
            )
        return True

    monkeypatch.setattr(module, "resolve_openspec_change", lambda change: ("none", None, []))
    monkeypatch.setattr(module, "get_declared_hosts", lambda root=None: ["grok", "omp"])
    monkeypatch.setattr(
        sys,
        "argv",
        ["verify-portable.py", "refresh-static", "--host", "all", "--evidence-dir", str(evidence_root)],
    )
    monkeypatch.setattr(module.PortableVerifier, "doctor", static_doctor)

    with pytest.raises(SystemExit) as exit_info:
        module.main()
    assert exit_info.value.code == 0

    captured = capsys.readouterr()
    assert "Kept prior observed_live settlement(s) for omp" in captured.out
    assert (evidence_root / "omp-receipt.json").read_bytes() == durable_omp_before
    grok_after = json.loads((evidence_root / "grok-receipt.json").read_text(encoding="utf-8"))
    assert any(s["id"] == "doctor-canonical-grok-stub" for s in grok_after["scenarios"])


def test_refresh_static_refusal_names_host_appropriate_remedy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#726: a single-host refresh refusal names a host-appropriate live command, not hardcoded OMP."""
    module = _load_verify_portable_module()
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    shutil.copy2(EVIDENCE_DIR / "index.json", evidence_root / "index.json")

    # Synthetic grok receipt with an observed_live scenario
    grok_receipt = json.loads((EVIDENCE_DIR / "grok-receipt.json").read_text(encoding="utf-8"))
    live_scenario = {
        "id": "runtime-child-spawn-grok",
        "description": "stub live spawn",
        "plane": "runtime",
        "command": "grok test",
        "exit_code": 0,
        "stdout_snippet": "ok",
        "verdict": "PASS",
        "duration_s": 0.5,
        "evidence_level": "observed_live",
        "settlement": {
            "child_id": "c1",
            "terminal_outcome": "success",
            "model": "grok-beta",
            "transport": "cli",
            "effective_rpc": "v1",
        },
    }
    grok_receipt["scenarios"].append(live_scenario)
    grok_receipt["planes"]["runtime"] = "PASS"
    grok_receipt["overall_verdict"] = "UNTESTED"
    (evidence_root / "grok-receipt.json").write_text(json.dumps(grok_receipt), encoding="utf-8")

    def static_doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        for plane in ("canonical", "adapter", "package"):
            self.scenarios.append(
                module.ScenarioResult(
                    id=f"doctor-{plane}-stub",
                    description=f"stub static {plane}",
                    plane=plane,
                    command="stub",
                    exit_code=0,
                    stdout_snippet="stub",
                    verdict="PASS",
                    duration_s=0.0,
                )
            )
        return True

    monkeypatch.setattr(module, "resolve_openspec_change", lambda change: ("none", None, []))
    monkeypatch.setattr(
        sys,
        "argv",
        ["verify-portable.py", "refresh-static", "--host", "grok", "--evidence-dir", str(evidence_root)],
    )
    monkeypatch.setattr(module.PortableVerifier, "doctor", static_doctor)

    with pytest.raises(SystemExit) as exit_info:
        module.main()
    err_msg = str(exit_info.value.code)
    assert "REFUSING to overwrite the durable receipt" in err_msg
    assert "python3 scripts/verify-portable.py run --host grok" in err_msg
    assert "PSTACK_RUN_OMP_LIVE" not in err_msg
