#!/usr/bin/env python3
"""Tests for host-native harness drivers and runtime plane conformance."""

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import (
    AntigravityDriver,
    ClaudeDriver,
    CodexDriver,
    CopilotDriver,
    GrokDriver,
    HarnessDriver,
    OMPDriver,
    OpenCodeDriver,
    get_driver,
)
from scripts.drivers.omp import ISOLATION_CHILD_FILE, ISOLATION_TOKEN
from scripts.drivers.omp_rpc import negotiated_descriptor
loader = importlib.util.spec_from_file_location("verify_portable", ROOT / "scripts" / "verify-portable.py")
assert loader is not None and loader.loader is not None
verify_portable = importlib.util.module_from_spec(loader)
loader.loader.exec_module(verify_portable)
PortableVerifier = verify_portable.PortableVerifier

# These tests interrogate locally installed host CLIs; they do not prove
# real model-backed child spawn/join. Keep them opt-in in generic CI.
HOST_DEPENDENT = os.environ.get("PSTACK_RUN_HOST_DEPENDENT_TESTS") == "1"


def test_get_driver_factory() -> None:
    assert isinstance(get_driver("grok", ROOT), GrokDriver)
    assert isinstance(get_driver("antigravity", ROOT), AntigravityDriver)
    assert isinstance(get_driver("codex", ROOT), CodexDriver)
    assert isinstance(get_driver("omp", ROOT), OMPDriver)
    assert isinstance(get_driver("opencode", ROOT), OpenCodeDriver)
    assert isinstance(get_driver("claude", ROOT), ClaudeDriver)
    assert isinstance(get_driver("github:copilot", ROOT), CopilotDriver)

    with pytest.raises(ValueError, match="No native driver registered"):
        get_driver("unsupported_host", ROOT)


@pytest.mark.skipif(not HOST_DEPENDENT, reason="Opt-in host CLI smoke: set PSTACK_RUN_HOST_DEPENDENT_TESTS=1")
@pytest.mark.parametrize("host", ["grok", "antigravity", "codex", "omp", "opencode"])
def test_driver_scenarios(host: str, tmp_path: Path) -> None:
    driver = get_driver(host, ROOT)
    avail, reason = driver.is_available()
    assert avail is True, f"Host {host} should be available: {reason}"

    version = driver.get_version()
    assert version is not None, f"Host {host} should return a version string"
    assert len(version) > 0

    # Discover scenario
    sc_disc = driver.discover(tmp_path)
    assert sc_disc.verdict == "PASS", f"Discover failed for {host}: {sc_disc.stdout} {sc_disc.stderr}"
    assert sc_disc.exit_code == 0

    # Route scenario
    sc_route = driver.route_playbook("feature", tmp_path)
    assert sc_route.verdict == "PASS"

    # Child spawn scenario
    sc_spawn = driver.child_spawn(tmp_path)
    assert sc_spawn.verdict == "PASS"

    # Isolation scenario
    sc_iso = driver.isolation(tmp_path)
    assert sc_iso.verdict == "PASS"

    # Evidence capture scenario
    sc_ev = driver.evidence_capture(tmp_path)
    assert sc_ev.verdict == "PASS"

    # In-flight child cancellation is an OMP-only drive surface. verify-portable.py
    # dispatches the same arm for omp alone because the other hosts declare no cancel
    # primitive. Without PSTACK_RUN_OMP_LIVE this resolves at the static contract level,
    # so the arm never needs a live model.
    if isinstance(driver, OMPDriver):
        sc_cancel = driver.child_cancel(tmp_path)
        assert sc_cancel.verdict == "PASS", f"Cancel failed for {host}: {sc_cancel.stdout} {sc_cancel.stderr}"
        assert sc_cancel.evidence_level == "static"
        assert sc_cancel.settlement is None


def test_blocked_driver_fallback(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    # Isolate unavailable-native-driver behavior: the other drive scenarios
    # invoke Bun, shell, and project packaging, none of which is relevant to
    # determining whether an absent host CLI reports BLOCKED.
    def fake_contract_check(scenario_id, desc, plane, cmd, cwd=None, **kwargs):
        result = verify_portable.ScenarioResult(
            id=scenario_id, description=desc, plane=plane,
            command="mock-offline-contract", exit_code=0,
            stdout_snippet="simulated contract PASS",
            verdict="PASS", duration_s=0.0,
        )
        if kwargs.get("record", True):
            verifier.scenarios.append(result)
        return result

    with (
        patch.object(verifier, "run_command", side_effect=fake_contract_check),
        patch.object(GrokDriver, "is_available", return_value=(False, "simulated missing grok binary")),
    ):
        ok = verifier.drive()
        assert ok is False

        # Verify a scenario with BLOCKED was recorded
        blocked_scenarios = [s for s in verifier.scenarios if s.verdict == "BLOCKED"]
        assert len(blocked_scenarios) >= 1
        assert blocked_scenarios[0].plane == "runtime"
        assert "BLOCKED" in blocked_scenarios[0].stdout_snippet

        receipt = verifier.proof_bar()
        assert receipt.planes["runtime"] == "BLOCKED"
        assert receipt.overall_verdict == "BLOCKED"


@pytest.mark.skipif(not HOST_DEPENDENT, reason="Opt-in host CLI smoke: set PSTACK_RUN_HOST_DEPENDENT_TESTS=1")
def test_reclassified_smoke_tests_planes(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()
    ok = verifier.drive()
    assert ok is True

    scenarios_by_id = {s.id: s for s in verifier.scenarios}

    # Verify planes for reclassified tests
    assert scenarios_by_id["drive-principles-load"].plane == "canonical"
    assert scenarios_by_id["drive-check-plan"].plane == "adapter"
    assert scenarios_by_id["drive-worktree-audit"].plane == "adapter"
    assert scenarios_by_id["drive-verification-skill-scaffold"].plane == "package"
    assert scenarios_by_id["drive-verification-skill-check"].plane == "package"

    # Verify native driver scenarios are in runtime plane
    assert scenarios_by_id["runtime-discover-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-route-playbook-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-child-spawn-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-isolation-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-evidence-capture-grok"].plane == "runtime"


@pytest.mark.skipif(not HOST_DEPENDENT, reason="Opt-in host CLI smoke: set PSTACK_RUN_HOST_DEPENDENT_TESTS=1")
def test_omp_proxy_scenarios_report_static_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PSTACK_RUN_OMP_LIVE", raising=False)
    driver = get_driver("omp", ROOT)
    sc_spawn = driver.child_spawn(tmp_path)
    assert sc_spawn.evidence_level == "static", "profile-string spawn check must not claim live evidence"
    assert "static" in sc_spawn.description
    assert sc_spawn.settlement is None
    sc_iso = driver.isolation(tmp_path)
    assert sc_iso.evidence_level == "static", "help-grep isolation check must not claim live evidence"
    assert "static" in sc_iso.description
    # The CLI probe wording is gone: the row now points at the live gate instead of
    # denying that observed isolation exists.
    assert "CLI probe" not in sc_iso.description
    assert "PSTACK_RUN_OMP_LIVE=1" in sc_iso.description


# --- #291: the isolation row must be observable, and only when it really is ---------

_OMP_READY = {
    "type": "ready",
    "protocolVersion": 1,
    "supportedProtocolVersions": [1, 2],
    "maxFrameBytes": 1048576,
    "maxReassembledFrameBytes": 67108864,
}
_OMP_NEGOTIATED = {
    "id": "p1",
    "type": "response",
    "command": "negotiate_protocol",
    "success": True,
    "data": {"protocolVersion": 2},
}


def _isolation_frames(session_file: str, reply: str = "PARENT_DONE", child: str = "IsoChild") -> list:
    """A settled isolated child: lifecycle, model identity, parent literal, quiescence."""
    lifecycle = {
        "type": "subagent_lifecycle",
        "payload": {"id": child, "agent": "task", "status": "started", "sessionFile": session_file},
    }
    terminal = {
        "type": "subagent_lifecycle",
        "payload": {"id": child, "agent": "task", "status": "completed", "sessionFile": session_file},
    }
    return [
        _OMP_READY,
        _OMP_NEGOTIATED,
        lifecycle,
        {
            "type": "subagent_progress",
            "payload": {"id": child, "progress": {"id": child, "resolvedModelIdentity": "model-a"}},
        },
        terminal,
        {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "completed", "sessionSettled": True},
        {
            "type": "message_end",
            "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]},
        },
        {"type": "session_settled"},
    ]


def _stub_isolation_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    patch_text: str | None = "diff --git a/ISO_CHILD.txt b/ISO_CHILD.txt\n+CHILD_ISO_OK\n",
    lifecycle_session: bool = True,
    child_writes_parent: bool = False,
    worktree_leftover: bool = False,
    settled: bool = True,
    exit_code: int = 0,
) -> None:
    """Replace the RPC session so the live isolation verdict path runs offline."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    patch_file = artifacts / "IsoChild.patch"
    if patch_text is not None:
        patch_file.write_text(patch_text, encoding="utf-8")
    session_file = str(artifacts / "IsoChild.jsonl") if lifecycle_session else ""
    frames = _isolation_frames(session_file)

    class _StubSession:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self._cwd = Path(str(kwargs.get("cwd")))
            self._env = dict(kwargs.get("env") or {})  # type: ignore[arg-type]

        def start(self, timeout: float = 30.0) -> dict:
            return {}

        def negotiate(self, protocol_version: int = 2, timeout: float = 30.0) -> dict:
            return negotiated_descriptor(frames)

        def subscribe_subagents(self, level: str = "events", timeout: float = 30.0) -> dict:
            return {}

        def prompt(self, message: str, timeout: float = 30.0) -> dict:
            return {"id": "q1"}

        def wait_settled(self, prompt_id: str | None = None, timeout: float | None = None) -> bool:
            return settled

        @property
        def frames(self) -> list:
            return list(frames)

        def close(self, grace: float = 10.0) -> int:
            if child_writes_parent:
                (self._cwd / ISOLATION_CHILD_FILE).write_text(ISOLATION_TOKEN, encoding="utf-8")
            if worktree_leftover:
                base = Path(self._env.get("OMP_WORKTREE_DIR") or str(self._cwd))
                (base / "leftover-workspace").mkdir(parents=True, exist_ok=True)
            return exit_code

    monkeypatch.setattr("scripts.drivers.omp.OmpRpcSession", lambda *a, **k: _StubSession(*a, **k))


def _live_isolation_driver(monkeypatch: pytest.MonkeyPatch) -> object:
    monkeypatch.setenv("PSTACK_RUN_OMP_LIVE", "1")
    driver = get_driver("omp", ROOT)
    available, reason = driver.is_available()
    if not available:
        pytest.skip(reason)
    return driver


def test_omp_isolation_live_pass_carries_a_settlement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_isolation_session(monkeypatch, tmp_path)
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "PASS", f"{result.stdout}\n{result.stderr}"
    assert result.evidence_level == "observed_live"
    assert result.settlement is not None
    assert result.settlement["terminal_outcome"] == "success"
    assert result.settlement["transport"] == "rpc"
    # The observation is the whole boundary: captured delta, untouched sentinel, clean parent.
    assert "token_in_patch=True" in result.stdout
    assert "sentinel_intact=True" in result.stdout
    assert "child_file_absent=True" in result.stdout
    assert "worktrees=1" in result.stdout
    assert result.duration_s >= 0


def test_omp_isolation_live_fails_when_the_child_write_lands_in_the_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_isolation_session(monkeypatch, tmp_path, child_writes_parent=True)
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "FAIL"
    assert result.evidence_level == "offline"
    assert result.settlement is None
    assert "isolated delta reached the parent checkout" in result.stderr


def test_omp_isolation_live_fails_without_a_captured_delta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_isolation_session(monkeypatch, tmp_path, lifecycle_session=False)
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "FAIL"
    assert "no captured isolation patch" in result.stderr


def test_omp_isolation_live_fails_when_the_write_is_missing_from_the_patch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_isolation_session(monkeypatch, tmp_path, patch_text="diff --git a/other.txt\n+something else\n")
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "FAIL"
    assert "did not hold the CHILD_ISO_OK write" in result.stderr


def test_omp_isolation_live_fails_on_worktree_residue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_isolation_session(monkeypatch, tmp_path, worktree_leftover=True)
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "FAIL"
    assert "worktree residue left behind" in result.stderr


def test_omp_isolation_live_fails_when_the_session_does_not_settle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_isolation_session(monkeypatch, tmp_path, settled=False)
    result = _live_isolation_driver(monkeypatch).isolation(tmp_path)

    assert result.verdict == "FAIL"
    assert "session did not settle after the prompt" in result.stderr


def test_omp_isolation_live_requires_the_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the gate the probe never spawns a model-backed child."""
    monkeypatch.delenv("PSTACK_RUN_OMP_LIVE", raising=False)
    driver = get_driver("omp", ROOT)
    available, reason = driver.is_available()
    if not available:
        pytest.skip(reason)
    result = driver.isolation(tmp_path)
    assert result.evidence_level == "static"
    assert result.settlement is None


def test_omp_isolation_residue_detects_untracked_files_with_show_untracked_files_no(tmp_path: Path) -> None:
    import subprocess
    from scripts.drivers.omp import _isolation_residue

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    (repo / "initial.txt").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    # Set status.showUntrackedFiles = no
    subprocess.run(["git", "config", "status.showUntrackedFiles", "no"], cwd=repo, check=True, capture_output=True)
    # Child drops an untracked file into parent repo
    (repo / "child_scratch.txt").write_text("leaked scratch\n", encoding="utf-8")

    residue = _isolation_residue(repo, tmp_path / "worktrees")
    assert residue["tree_clean"] is False, "Untracked child file must prevent tree_clean even when showUntrackedFiles=no"


def test_driver_scenario_result_to_scenario_result_mapping() -> None:
    from scripts.drivers.base import DriverScenarioResult, to_scenario_result

    driver_res = DriverScenarioResult(
        scenario_id="runtime-child-spawn-omp",
        description="Prove native child spawn",
        command="omp spawn",
        exit_code=0,
        stdout="child spawned successfully",
        stderr="",
        verdict="PASS",
        duration_s=1.23,
        evidence_level="observed_live",
        settlement={"child_id": "c-123", "terminal_outcome": "success"},
        live_attempted=True,
    )

    sc = driver_res.to_scenario_result(plane="runtime")
    assert sc.id == "runtime-child-spawn-omp"
    assert sc.description == "Prove native child spawn"
    assert sc.plane == "runtime"
    assert sc.command == "omp spawn"
    assert sc.exit_code == 0
    assert sc.stdout_snippet == "child spawned successfully"
    assert sc.verdict == "PASS"
    assert sc.duration_s == 1.23
    assert sc.evidence_level == "observed_live"
    assert sc.settlement == {"child_id": "c-123", "terminal_outcome": "success"}
    assert sc.live_attempted is True

    sc2 = to_scenario_result(driver_res, plane="runtime")
    assert sc2 == sc


