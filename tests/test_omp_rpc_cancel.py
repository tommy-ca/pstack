#!/usr/bin/env python3
"""Offline tests for the bounded OMP RPC v2 child cancel path (#297).

Reducer negatives, bounded waits, live verdict path, and verifier dispatch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import get_driver
from scripts.drivers.omp_rpc import (
    OmpRpcSession,
    reduce_child_settlement,
)
from tests.test_omp_rpc import (
    NEGOTIATED,
    READY,
    _StubSession,
    _expected,
    _lifecycle,
    _progress,
    _session,
)


def test_reduce_cancelled_status_is_cancelled() -> None:
    frames = [
        READY,
        NEGOTIATED,
        _lifecycle("ProbeChild", "started"),
        _progress("ProbeChild", "model-a"),
        _lifecycle("ProbeChild", "cancelled"),
    ]
    assert reduce_child_settlement(frames) == _expected(outcome="cancelled")


def test_reduce_cancel_acknowledgement_is_not_a_settlement() -> None:
    """An accepted cancel request says the host was asked, never that the child stopped."""
    frames = [
        READY,
        NEGOTIATED,
        _lifecycle("ProbeChild", "started"),
        _progress("ProbeChild", "model-a"),
        {"type": "response", "id": "c1", "command": "cancel_subagent", "success": True, "data": {}},
    ]
    assert reduce_child_settlement(frames) is None
    assert reduce_child_settlement(frames, timed_out=True) == _expected(outcome="timeout")


def test_reduce_dropped_terminal_frame_never_settles_as_cancelled(tmp_path: Path) -> None:
    """A terminal frame lost in the stream must not be read as an observed cancellation."""
    session = _session(tmp_path)
    dropped = '{"type": "subagent_lifecycle", "payload": {"id": "ProbeChild", "status": "cancelled"'
    for line in [
        json.dumps(READY),
        json.dumps(NEGOTIATED),
        json.dumps(_lifecycle("ProbeChild", "started")),
        json.dumps(_progress("ProbeChild", "model-a")),
        dropped,
    ]:
        session._ingest(line + "\n")

    assert session.raw_lines == [dropped]
    assert reduce_child_settlement(session.frames) is None
    assert reduce_child_settlement(session.frames, timed_out=True) == _expected(outcome="timeout")


def test_wait_child_started_is_bounded_and_returns_the_child_id(tmp_path: Path) -> None:
    session = _session(tmp_path)
    assert session.wait_child_started(timeout=0.2) is None

    session._ingest(json.dumps(_lifecycle("ChildX", "started")) + "\n")

    assert session.wait_child_started(timeout=0.2) == "ChildX"


def test_wait_child_terminal_requires_that_child_and_a_terminal_status(tmp_path: Path) -> None:
    session = _session(tmp_path, [_lifecycle("ChildA", "started"), _lifecycle("ChildB", "cancelled")])

    assert session.wait_child_terminal("ChildA", timeout=0.2) is None
    assert session.wait_child_terminal("Missing", timeout=0.2) is None

    session._ingest(json.dumps(_lifecycle("ChildA", "aborted")) + "\n")
    terminal = session.wait_child_terminal("ChildA", timeout=0.2)

    assert terminal is not None and terminal["payload"]["status"] == "aborted"


def _cancel_frames(
    child: str = "ChildX", terminal: str | None = "aborted", protocol_version: int = 2
) -> list[dict]:
    negotiation = dict(NEGOTIATED)
    negotiation["data"] = {"protocolVersion": protocol_version}
    frames: list[dict] = [
        READY,
        negotiation,
        {"type": "subagent_lifecycle", "payload": {"id": child, "agent": "task", "status": "started"}},
        {
            "type": "subagent_progress",
            "payload": {"id": child, "progress": {"id": child, "resolvedModelIdentity": "model-a"}},
        },
    ]
    if terminal is None:
        # The terminal lifecycle frame is dropped; only the cancel acknowledgement arrives.
        frames.append({"type": "response", "id": "c1", "command": "cancel_subagent", "success": True, "data": {}})
    else:
        frames.append({"type": "subagent_lifecycle", "payload": {"id": child, "agent": "task", "status": terminal}})
    frames.append({"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "aborted"})
    return frames


def _cancel_result(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **stub_kwargs: object):
    """Run the live cancel path against a stub session, returning the result and the stub."""
    from scripts.drivers import omp as omp_driver

    monkeypatch.setenv(omp_driver.LIVE_GATE_ENV, "1")
    session = _StubSession(stub_kwargs.pop("frames", _cancel_frames()), **stub_kwargs)
    monkeypatch.setattr(omp_driver, "OmpRpcSession", lambda *args, **_kw: session)
    driver = get_driver("omp", ROOT)
    monkeypatch.setattr(type(driver), "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py")
    return driver.child_cancel(tmp_path), session


def test_live_cancel_records_a_typed_cancelled_settlement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The full cancellation path: in flight, cancelled through RPC, terminal cancelled."""
    result, session = _cancel_result(monkeypatch, tmp_path)

    assert result.verdict == "PASS"
    assert result.evidence_level == "observed_live"
    assert result.settlement == _expected(model="model-a", child_id="ChildX", outcome="cancelled")
    assert session.cancelled == ["ChildX"] and session.listed == 1
    assert "killed=True" in result.stdout and "in_flight=True" in result.stdout
    assert "latency=" in result.stdout


def test_live_cancel_requires_an_accepted_cancel_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A rejected cancel request is a failure, and the host's reason must survive."""
    result, _ = _cancel_result(monkeypatch, tmp_path, cancel_ack=False)

    assert result.verdict == "FAIL"
    assert "cancel_subagent was rejected" in result.stderr
    assert "no such subagent" in result.stderr, "the host's own rejection text must survive"


def test_live_cancel_rejects_an_idempotent_no_op(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Upstream answers success with `cancelled: false` for a child that was not running."""
    result, _ = _cancel_result(monkeypatch, tmp_path, cancel_killed=False)

    assert result.verdict == "FAIL"
    assert "found no running subagent to cancel" in result.stderr
    assert "killed=False" in result.stdout


def test_live_cancel_records_a_timeout_settlement_when_the_terminal_frame_is_dropped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The negative receipt: a bounded cancel that never lands is recorded as a timeout."""
    result, _ = _cancel_result(monkeypatch, tmp_path, frames=_cancel_frames(terminal=None), terminal=False)

    assert result.verdict == "FAIL"
    assert result.settlement is not None and result.settlement["terminal_outcome"] == "timeout"
    assert "outcome=timeout" in result.stdout
    assert "no terminal child lifecycle" in result.stderr


def test_live_cancel_without_an_in_flight_child_is_a_bounded_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, session = _cancel_result(monkeypatch, tmp_path, child_id=None, frames=[READY, NEGOTIATED])

    assert result.verdict == "FAIL"
    assert result.settlement is None
    assert session.cancelled == []
    assert "no child lifecycle within" in result.stderr


def test_live_cancel_route_error_is_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A missing model route is an unavailable host, not a cancellation defect."""
    frames = [
        READY,
        NEGOTIATED,
        {
            "type": "prompt_result",
            "id": "q1",
            "status": "error",
            "error": {"message": "no route to provider for model x"},
        },
    ]
    result, _ = _cancel_result(monkeypatch, tmp_path, child_id=None, frames=frames)

    assert result.verdict == "BLOCKED"
    assert "no route to provider" in result.stderr


def test_live_cancel_reports_blocked_when_the_session_cannot_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.drivers import omp as omp_driver

    monkeypatch.setenv(omp_driver.LIVE_GATE_ENV, "1")

    class _Unstartable:
        def __init__(self, *args: object, **_kwargs: object) -> None:
            pass

        def start(self, timeout: float = 30.0) -> dict:
            raise OSError("omp binary vanished")

        @property
        def frames(self) -> list[dict]:
            return []

        def close(self, grace: float = 10.0) -> int:
            return 1

    monkeypatch.setattr(omp_driver, "OmpRpcSession", _Unstartable)
    driver = get_driver("omp", ROOT)
    monkeypatch.setattr(type(driver), "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py")

    result = driver.child_cancel(tmp_path)

    assert result.verdict == "BLOCKED"
    assert "omp binary vanished" in result.stderr


def test_static_child_cancel_path_unchanged_without_live_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("PSTACK_RUN_OMP_LIVE", raising=False)
    driver = get_driver("omp", ROOT)
    available, reason = driver.is_available()
    if not available:
        pytest.skip(reason)
    result = driver.child_cancel(tmp_path)

    assert result.evidence_level == "static"
    assert result.settlement is None
    assert result.verdict == "PASS"
    assert "static" in result.description


def test_verifier_dispatch_records_the_cancel_scenario_for_omp_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The cancel scenario reaches a receipt only because drive() dispatches it."""
    from scripts.drivers import omp as omp_driver
    import scripts.portable_verifier as verify_portable

    monkeypatch.delenv(omp_driver.LIVE_GATE_ENV, raising=False)
    monkeypatch.setattr(omp_driver.OMPDriver, "is_available", lambda self: (True, "stubbed host"))
    monkeypatch.setattr(
        omp_driver.OMPDriver, "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py"
    )
    # The non-driver contracts are irrelevant here, and some of them drive a host CLI.
    monkeypatch.setattr(verify_portable.PortableVerifier, "run_command", lambda *args, **kwargs: None)

    def drive(host: str) -> dict:
        verifier = verify_portable.PortableVerifier(host=host, evidence_root=tmp_path / host)
        verifier.launch()
        verifier.drive()
        return {s.id: s for s in verifier.scenarios}

    cancel = drive("omp")["runtime-child-cancel-omp"]
    assert cancel.verdict == "PASS"
    assert cancel.evidence_level == "static"
    assert cancel.plane == "runtime"

    assert "runtime-child-cancel-omp" not in drive("codex")
