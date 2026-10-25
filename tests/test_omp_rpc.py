#!/usr/bin/env python3
"""Offline tests for the bounded OMP RPC v2 child spawn/join reduction.

The live test is opt-in (PSTACK_RUN_OMP_LIVE=1): the offline path must never
need a model route.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import get_driver
from scripts.drivers.omp_rpc import (
    OmpRpcSession,
    negotiated_descriptor,
    reduce_child_settlement,
)

FIXTURE = ROOT / "tests" / "fixtures" / "omp-rpc-live-frames.jsonl"
READY = {
    "type": "ready",
    "protocolVersion": 1,
    "supportedProtocolVersions": [1, 2],
    "maxFrameBytes": 1048576,
    "maxReassembledFrameBytes": 67108864,
}
NEGOTIATED = {
    "id": "p1",
    "type": "response",
    "command": "negotiate_protocol",
    "success": True,
    "data": {"protocolVersion": 2},
}
EFFECTIVE_RPC = "rpc-v2:maxFrameBytes=1048576:maxReassembledFrameBytes=67108864"


def _expected(model: str = "model-a", child_id: str = "ProbeChild", outcome: str = "success") -> dict:
    return {
        "child_id": child_id,
        "terminal_outcome": outcome,
        "model": model,
        "transport": "rpc",
        "effective_rpc": EFFECTIVE_RPC,
    }


EXPECTED_SETTLEMENT = _expected(model="opencode-go/deepseek-v4.1-flash")


def _load_fixture() -> tuple[list[dict], int]:
    frames: list[dict] = []
    malformed = 0
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            frames.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    return frames, malformed


def _lifecycle(child_id: str, status: str) -> dict:
    return {"type": "subagent_lifecycle", "payload": {"id": child_id, "status": status}}


def _progress(child_id: str, identity: str | None = None, key: str = "resolvedModelIdentity") -> dict:
    progress: dict = {"id": child_id, "status": "running"}
    if identity is not None:
        progress[key] = identity
    return {"type": "subagent_progress", "payload": {"id": child_id, "progress": progress}}


class _StubProc:
    """Minimal stdin/stdout stand-in that answers requests by command type."""

    def __init__(self, session: OmpRpcSession, replies: dict[str, dict]):
        self.session = session
        self.replies = replies
        self.writes: list[dict] = []
        self.stdin = self
        self.stdout = None

    def write(self, data: bytes) -> int:
        request = json.loads(data.decode("utf-8"))
        self.writes.append(request)
        reply = self.replies.get(request.get("type"))
        if reply is not None:
            self.session._ingest(
                json.dumps(
                    {
                        "type": "response",
                        "id": request["id"],
                        "command": request["type"],
                        "success": True,
                        "data": reply,
                    }
                )
            )
        return len(data)

    def flush(self) -> None:
        pass

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def kill(self) -> None:
        pass

    def close(self) -> None:
        pass


def _session(tmp_path: Path, frames: list[dict] | None = None) -> OmpRpcSession:
    session = OmpRpcSession("/nonexistent/omp", cwd=tmp_path)
    for frame in frames or []:
        session._ingest(json.dumps(frame))
    return session


def test_fixture_reduces_to_literal_settlement() -> None:
    frames, malformed = _load_fixture()
    assert malformed == 1, "fixture must carry exactly one non-JSON diagnostics line"
    assert len(frames) == 11
    assert reduce_child_settlement(frames) == EXPECTED_SETTLEMENT


def test_reduce_returns_none_without_any_lifecycle() -> None:
    frames = [READY, NEGOTIATED, _progress("ProbeChild", "model-a")]
    assert reduce_child_settlement(frames) is None


def test_reduce_returns_none_when_started_without_terminal() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "started"), _progress("ProbeChild", "model-a")]
    assert reduce_child_settlement(frames) is None


def test_reduce_aborted_child_is_cancelled() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "started"), _progress("ProbeChild", "model-a"), _lifecycle("ProbeChild", "aborted")]
    assert reduce_child_settlement(frames) == _expected(outcome="cancelled")


def test_reduce_error_status_is_error() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "started"), _progress("ProbeChild", "model-a"), _lifecycle("ProbeChild", "error")]
    assert reduce_child_settlement(frames) == _expected(outcome="error")


def test_reduce_returns_none_when_model_missing() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "started"), _progress("ProbeChild"), _lifecycle("ProbeChild", "completed")]
    assert reduce_child_settlement(frames) is None


def test_reduce_timeout_requires_caller_deadline() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "started"), _progress("ProbeChild", "model-a")]
    assert reduce_child_settlement(frames, timed_out=False) is None
    assert reduce_child_settlement(frames, timed_out=True) == _expected(outcome="timeout")


def test_reduce_falls_back_to_resolved_model() -> None:
    frames = [READY, NEGOTIATED, _lifecycle("ProbeChild", "completed"), _progress("ProbeChild", "model-b", key="resolvedModel")]
    assert reduce_child_settlement(frames) == _expected(model="model-b")


def test_reduce_refuses_ambiguous_children() -> None:
    """With more than one child the settlement cannot be attributed, so it is refused."""
    frames = [
        READY,
        NEGOTIATED,
        _lifecycle("ChildA", "completed"),
        _progress("ChildA", "model-a"),
        _lifecycle("ChildB", "error"),
        _progress("ChildB", "model-b"),
    ]
    assert reduce_child_settlement(frames) is None
    assert reduce_child_settlement(frames, timed_out=True) is None
    assert reduce_child_settlement(frames, child_id="ChildA") == _expected(child_id="ChildA")
    assert reduce_child_settlement(frames, child_id="ChildB") == _expected(
        child_id="ChildB", model="model-b", outcome="error"
    )
    assert reduce_child_settlement(frames, child_id="Missing") is None


def test_reduce_uses_v1_when_negotiation_is_absent() -> None:
    frames = [READY, _lifecycle("ProbeChild", "completed"), _progress("ProbeChild", "model-a")]
    assert reduce_child_settlement(frames)["effective_rpc"] == (
        "rpc-v1:maxFrameBytes=1048576:maxReassembledFrameBytes=67108864"
    )


def test_negotiated_descriptor_ignores_failed_negotiation() -> None:
    frames = [
        READY,
        {"type": "response", "command": "negotiate_protocol", "success": False, "id": "p1"},
        NEGOTIATED,
    ]
    assert negotiated_descriptor(frames) == {
        "protocol_version": 2,
        "supported_protocol_versions": [1, 2],
        "max_frame_bytes": 1048576,
        "max_reassembled_frame_bytes": 67108864,
        "effective_rpc": EFFECTIVE_RPC,
    }


def test_ingest_tolerates_and_logs_malformed_lines(tmp_path: Path) -> None:
    session = _session(tmp_path)
    session._ingest("omp: warming model catalog\n")
    session._ingest(json.dumps(READY) + "\n")
    session._ingest("[not, a, frame]\n")
    assert session.raw_lines == ["omp: warming model catalog", "[not, a, frame]"]
    assert session.frames == [READY]


def test_requests_correlate_by_id(tmp_path: Path) -> None:
    session = _session(tmp_path)
    # A decoy response with a foreign id must never satisfy a pending request.
    session._ingest(json.dumps({"type": "response", "id": "p9", "success": True, "data": {"protocolVersion": 1}}))
    session._proc = _StubProc(
        session,
        {
            "negotiate_protocol": {"protocolVersion": 2},
            "set_subagent_subscription": {"level": "events"},
        },
    )
    first = session._request({"type": "negotiate_protocol", "protocolVersion": 2}, "p")
    second = session._request({"type": "set_subagent_subscription", "level": "events"}, "s")
    assert first["id"] == "p1" and first["data"] == {"protocolVersion": 2}
    assert second["id"] == "s2" and second["data"] == {"level": "events"}
    assert [w["type"] for w in session._proc.writes] == [
        "negotiate_protocol",
        "set_subagent_subscription",
    ]


def test_negotiate_returns_descriptor_from_ready_and_response(tmp_path: Path) -> None:
    session = _session(tmp_path)
    session._ready = dict(READY)
    session._proc = _StubProc(session, {"negotiate_protocol": {"protocolVersion": 2}})
    assert session.negotiate()["effective_rpc"] == EFFECTIVE_RPC


def test_wait_settled_expires_on_deadline(tmp_path: Path) -> None:
    session = _session(tmp_path)
    session._proc = _StubProc(session, {})
    assert session.wait_settled(timeout=0.2) is False
    assert session.wait_settled(prompt_id="q1", timeout=0.2) is False


def test_static_child_spawn_path_unchanged_without_live_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PSTACK_RUN_OMP_LIVE", raising=False)
    driver = get_driver("omp", ROOT)
    available, reason = driver.is_available()
    if not available:
        pytest.skip(reason)
    result = driver.child_spawn(tmp_path)
    assert result.evidence_level == "static"
    assert result.settlement is None
    assert result.verdict == "PASS"


@pytest.mark.skipif(
    os.environ.get("PSTACK_RUN_OMP_LIVE") != "1",
    reason="Live model-backed proof: set PSTACK_RUN_OMP_LIVE=1",
)
def test_live_child_spawn_observes_rpc_settlement(tmp_path: Path) -> None:
    driver = get_driver("omp", ROOT)
    available, reason = driver.is_available()
    assert available, reason
    result = driver.child_spawn(tmp_path)
    assert result.verdict == "PASS", f"{result.stdout}\n{result.stderr}"
    assert result.evidence_level == "observed_live"
    assert result.settlement is not None
    assert result.settlement["transport"] == "rpc"
    assert result.settlement["terminal_outcome"] == "success"
    assert result.settlement["child_id"]
    assert result.settlement["model"]
    assert result.settlement["effective_rpc"].startswith("rpc-v2")


class _StubSession:
    """Stands in for OmpRpcSession so the live verdict path is testable offline."""

    def __init__(
        self,
        frames: list[dict],
        settled: bool = True,
        exit_code: int = 0,
        child_id: str | None = "ChildX",
        cancel_ack: bool = True,
        cancel_killed: bool = True,
        terminal: bool = True,
        **_kwargs: object,
    ):
        self._frames = frames
        self._settled = settled
        self._exit_code = exit_code
        self._child_id = child_id
        self._cancel_ack = cancel_ack
        self._cancel_killed = cancel_killed
        self._terminal = terminal
        self.cancelled: list[str] = []
        self.listed = 0

    def start(self, timeout: float = 30.0) -> dict:
        return {}

    def negotiate(self, protocol_version: int = 2, timeout: float = 30.0) -> dict:
        return negotiated_descriptor(self._frames)

    def subscribe_subagents(self, level: str = "events", timeout: float = 30.0) -> dict:
        return {}

    def prompt(self, message: str, timeout: float = 30.0) -> dict:
        return {"id": "q1"}

    def wait_settled(self, prompt_id: str | None = None, timeout: float | None = None) -> bool:
        return self._settled

    def wait_child_started(self, timeout: float = 60.0) -> str | None:
        return self._child_id

    def subagents(self, timeout: float = 30.0) -> list[dict]:
        self.listed += 1
        return [{"id": self._child_id, "agent": "task"}] if self._child_id else []

    def cancel_subagent(self, subagent_id: str, timeout: float = 30.0) -> dict:
        self.cancelled.append(subagent_id)
        return {
            "id": "c1",
            "type": "response",
            "command": "cancel_subagent",
            "success": self._cancel_ack,
            # Upstream: data.cancelled is false for an id that is not a running subagent.
            "data": {"cancelled": self._cancel_ack and self._cancel_killed},
            **({} if self._cancel_ack else {"error": {"message": "no such subagent"}}),
        }

    def wait_child_terminal(self, child_id: str, timeout: float = 30.0) -> dict | None:
        if not self._terminal:
            return None
        return {"type": "subagent_lifecycle", "payload": {"id": child_id, "status": "aborted"}}

    @property
    def frames(self) -> list[dict]:
        return list(self._frames)

    def close(self, grace: float = 10.0) -> int:
        return self._exit_code


def _assistant_reply(text: str) -> dict:
    return {
        "type": "message_end",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _successful_child_frames(
    children: tuple[str, ...] = ("ChildX",),
    protocol_version: int = 2,
    reply: str = "PARENT_DONE",
    status: str = "completed",
) -> list[dict]:
    negotiation = dict(NEGOTIATED)
    negotiation["data"] = {"protocolVersion": protocol_version}
    frames: list[dict] = [READY, negotiation]
    for child in children:
        frames += [
            {"type": "subagent_lifecycle", "payload": {"id": child, "agent": "task", "status": "started"}},
            {
                "type": "subagent_progress",
                "payload": {"id": child, "progress": {"id": child, "resolvedModelIdentity": "model-a"}},
            },
            {"type": "subagent_lifecycle", "payload": {"id": child, "agent": "task", "status": "completed"}},
        ]
    frames += [
        {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": status, "sessionSettled": True},
        _assistant_reply(reply),
        {"type": "session_settled"},
    ]
    return frames


@pytest.mark.parametrize(
    ("settled", "exit_code", "expected"),
    [(True, 0, "PASS"), (False, 0, "FAIL"), (True, 2, "FAIL")],
)
def test_live_verdict_requires_session_settlement_and_clean_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, settled: bool, exit_code: int, expected: str
) -> None:
    """A completed child alone is not a PASS: the session must settle and exit cleanly."""
    from scripts.drivers import omp as omp_driver

    monkeypatch.setenv(omp_driver.LIVE_GATE_ENV, "1")
    frames = _successful_child_frames()
    monkeypatch.setattr(
        omp_driver,
        "OmpRpcSession",
        lambda *args, **kwargs: _StubSession(frames, settled=settled, exit_code=exit_code),
    )
    driver = get_driver("omp", ROOT)
    monkeypatch.setattr(type(driver), "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py")

    result = driver.child_spawn(tmp_path)

    assert result.verdict == expected
    if expected == "PASS":
        assert result.evidence_level == "observed_live"
        assert result.settlement == _expected(model="model-a", child_id="ChildX")
    else:
        assert result.evidence_level == "offline"
        assert "settled=" in result.stdout


def _live_result(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **kwargs: object):
    """Run the live driver path against a stub session built from the given frame shape."""
    from scripts.drivers import omp as omp_driver

    monkeypatch.setenv(omp_driver.LIVE_GATE_ENV, "1")
    frames = _successful_child_frames(**kwargs)
    monkeypatch.setattr(
        omp_driver,
        "OmpRpcSession",
        lambda *args, **_kw: _StubSession(frames, settled=True, exit_code=0),
    )
    driver = get_driver("omp", ROOT)
    monkeypatch.setattr(type(driver), "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py")
    return driver.child_spawn(tmp_path)


def test_live_pass_requires_negotiated_protocol_v2(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A v1 session must not be recorded as an rpc-v2 proof."""
    result = _live_result(monkeypatch, tmp_path, protocol_version=1)

    assert result.verdict == "FAIL"
    assert result.evidence_level == "offline"
    assert "negotiated protocol v1" in result.stderr


def test_live_pass_requires_the_parent_literal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The prompt's literal reply is part of the proof, not decoration."""
    result = _live_result(monkeypatch, tmp_path, reply="I did something else")

    assert result.verdict == "FAIL"
    assert "PARENT_DONE" in result.stderr


def test_live_pass_requires_exactly_one_child(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Two children make the settlement unattributable, so it must not pass."""
    result = _live_result(monkeypatch, tmp_path, children=("ChildX", "ChildY"))

    assert result.verdict == "FAIL"
    assert "no single terminal child lifecycle" in result.stderr


def test_live_pass_control_still_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    result = _live_result(monkeypatch, tmp_path)

    assert result.verdict == "PASS"
    assert result.evidence_level == "observed_live"
    assert result.settlement == _expected(model="model-a", child_id="ChildX")


def test_route_error_classification_is_route_specific() -> None:
    """A child or turn defect that mentions a model is a FAIL, not a missing route."""
    from scripts.drivers.omp import _model_route_error

    defect = [{"type": "prompt_result", "status": "error", "error": {"message": "child model failed: invalid tool call"}}]
    route = [{"type": "prompt_result", "status": "error", "error": {"message": "no route to provider for model x"}}]

    assert _model_route_error(defect) == ""
    assert _model_route_error(route) == "no route to provider for model x"


def test_wait_settled_ignores_pre_prompt_quiescence(tmp_path: Path) -> None:
    """A session_settled frame emitted before the prompt is not evidence of join."""
    early = _session(
        tmp_path,
        [
            READY,
            {"type": "session_settled"},
            {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "completed", "sessionSettled": True},
        ],
    )
    late = _session(
        tmp_path,
        [
            READY,
            {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "completed", "sessionSettled": True},
            {"type": "session_settled"},
        ],
    )

    assert early.wait_settled(prompt_id="q1", timeout=0.2) is False
    assert late.wait_settled(prompt_id="q1", timeout=0.2) is True


def test_wait_settled_rejects_a_non_completed_prompt_result(tmp_path: Path) -> None:
    session = _session(
        tmp_path,
        [
            READY,
            {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "error"},
            {"type": "session_settled"},
        ],
    )

    assert session.wait_settled(prompt_id="q1", timeout=0.2) is False


def test_wait_settled_fails_closed_without_a_prompt_id(tmp_path: Path) -> None:
    """Without a prompt to correlate against there is nothing to prove."""
    session = _session(
        tmp_path,
        [
            READY,
            {"type": "session_settled"},
            {"type": "prompt_result", "id": "q1", "agentInvoked": True, "status": "completed"},
            {"type": "session_settled"},
        ],
    )

    assert session.wait_settled(timeout=0.2) is False
    assert session.wait_settled(prompt_id="q1", timeout=0.2) is True


def test_live_spawn_reports_blocked_when_the_host_cannot_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A spawn or log-open failure is an unavailable host, not a traceback."""
    from scripts.drivers import omp as omp_driver

    monkeypatch.setenv(omp_driver.LIVE_GATE_ENV, "1")

    class _Unstartable:
        def __init__(self, *args: object, **_kwargs: object) -> None:
            pass

        def start(self, timeout: float = 30.0) -> dict:
            raise OSError("omp binary vanished")

        def close(self, grace: float = 10.0) -> int:
            return 1

    monkeypatch.setattr(omp_driver, "OmpRpcSession", _Unstartable)
    driver = get_driver("omp", ROOT)
    monkeypatch.setattr(type(driver), "get_binary_path", lambda self: ROOT / "scripts" / "drivers" / "omp.py")

    result = driver.child_spawn(tmp_path)

    assert result.verdict == "BLOCKED"
    assert "omp binary vanished" in result.stderr


# --- cancellation (#297): reducer negatives, bounded waits, live verdict path -----


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
