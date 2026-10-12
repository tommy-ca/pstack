#!/usr/bin/env python3
"""Bounded OMP RPC v2 session: spawn a session, prompt, and join a child agent.

The session speaks OMP's newline-delimited JSON protocol over stdio (see the
upstream ``docs/rpc.md`` pinned in ``UPSTREAM``). Every wait is bounded: the
session can stall a caller for at most its own deadline, never forever.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

DEFAULT_MAX_SECONDS = 240.0
READY_TIMEOUT_S = 30.0
RESPONSE_TIMEOUT_S = 30.0
POLL_INTERVAL_S = 0.05

# Terminal subagent_lifecycle statuses mapped onto the receipt's outcome enum.
TERMINAL_LIFECYCLE_STATUS: Dict[str, str] = {
    "completed": "success",
    "error": "error",
    "failed": "error",
    "aborted": "cancelled",
    "cancelled": "cancelled",
}


class OmpRpcError(RuntimeError):
    """The RPC session could not start, or a command exceeded its deadline."""


def format_effective_rpc(version: int, ready: Optional[Dict[str, Any]] = None) -> str:
    """Compact descriptor of the negotiated transport plus its advertised limits."""
    parts = [f"rpc-v{version}"]
    ready = ready or {}
    if ready.get("maxFrameBytes") is not None:
        parts.append(f"maxFrameBytes={ready['maxFrameBytes']}")
    if ready.get("maxReassembledFrameBytes") is not None:
        parts.append(f"maxReassembledFrameBytes={ready['maxReassembledFrameBytes']}")
    return ":".join(parts)


def negotiated_descriptor(frames: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Recover the effective transport descriptor from a frame stream."""
    version = 1
    ready: Optional[Dict[str, Any]] = None
    for frame in frames:
        if frame.get("type") == "ready":
            ready = frame
            version = frame.get("protocolVersion", version)
        elif (
            frame.get("type") == "response"
            and frame.get("command") == "negotiate_protocol"
            and frame.get("success")
        ):
            version = (frame.get("data") or {}).get("protocolVersion", version)
    return {
        "protocol_version": version,
        "supported_protocol_versions": (ready or {}).get("supportedProtocolVersions", [version]),
        "max_frame_bytes": (ready or {}).get("maxFrameBytes"),
        "max_reassembled_frame_bytes": (ready or {}).get("maxReassembledFrameBytes"),
        "effective_rpc": format_effective_rpc(version, ready),
    }


def reduce_child_settlement(
    frames: Sequence[Dict[str, Any]],
    child_id: Optional[str] = None,
    timed_out: bool = False,
) -> Optional[Dict[str, str]]:
    """Reduce a frame stream to the typed child spawn/join settlement, or None.

    Returns None unless the child has a terminal lifecycle frame (or the caller
    timed out waiting) *and* a resolved model identity was observed.
    """
    children: Dict[str, Optional[str]] = {}
    order: List[str] = []
    models: Dict[str, str] = {}
    for frame in frames:
        ftype = frame.get("type")
        if ftype == "subagent_lifecycle":
            payload = frame.get("payload") or {}
            cid = payload.get("id")
            if not cid:
                continue
            if cid not in children:
                children[cid] = None
                order.append(cid)
            status = payload.get("status")
            if status in TERMINAL_LIFECYCLE_STATUS:
                children[cid] = status
        elif ftype == "subagent_progress":
            payload = frame.get("payload") or {}
            progress = payload.get("progress") or {}
            cid = progress.get("id") or payload.get("id")
            if not cid:
                continue
            identity = progress.get("resolvedModelIdentity") or progress.get("resolvedModel")
            if identity:
                models[cid] = identity

    if child_id is not None:
        target = child_id
    elif len(order) != 1:
        # More than one child means the settlement cannot be attributed to the prompted
        # one, and a settlement on the wrong child is worse than no settlement at all.
        return None
    else:
        target = order[0]
    if target is None or target not in children:
        return None

    terminal = children[target]
    if terminal is not None:
        outcome = TERMINAL_LIFECYCLE_STATUS[terminal]
    elif timed_out:
        outcome = "timeout"
    else:
        return None

    model = models.get(target)
    if not model:
        return None

    return {
        "child_id": target,
        "terminal_outcome": outcome,
        "model": model,
        "transport": "rpc",
        "effective_rpc": negotiated_descriptor(frames)["effective_rpc"],
    }


class OmpRpcSession:
    """A single bounded ``omp --mode rpc`` process with JSONL framing."""

    def __init__(
        self,
        omp_bin: Path | str,
        cwd: Path | str,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        log_path: Optional[Path | str] = None,
        env: Optional[Dict[str, str]] = None,
        extra_args: Optional[Sequence[str]] = None,
    ):
        self.omp_bin = str(omp_bin)
        self.cwd = Path(cwd)
        self.max_seconds = float(max_seconds)
        self.log_path = Path(log_path) if log_path else None
        # Extra environment for the child (e.g. an isolated PI_CONFIG_DIR); the
        # ambient environment stays in place for the model route and PATH.
        self.env = dict(env) if env else None
        # Extra argv (e.g. "-e <package dir>") appended after the base flags.
        self.extra_args = list(extra_args) if extra_args else None
        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[threading.Thread] = None
        self._log_fh = None
        self._lock = threading.Lock()
        self._frames: List[Dict[str, Any]] = []
        self._raw_lines: List[str] = []
        self._counter = 0
        self._ready: Optional[Dict[str, Any]] = None

    # --- framing ---------------------------------------------------------
    def _ingest(self, raw: str) -> None:
        """Parse one stdout line; non-JSON lines are logged raw and tolerated."""
        line = raw.rstrip("\n")
        if not line.strip():
            return
        if self._log_fh is not None:
            self._log_fh.write(line + "\n")
            self._log_fh.flush()
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            frame = None
        if not isinstance(frame, dict):
            with self._lock:
                self._raw_lines.append(line)
            return
        with self._lock:
            self._frames.append(frame)

    def _read_stdout(self) -> None:
        proc = self._proc
        assert proc is not None and proc.stdout is not None
        for chunk in proc.stdout:
            self._ingest(chunk.decode("utf-8", "replace"))

    @property
    def frames(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._frames)

    @property
    def raw_lines(self) -> List[str]:
        with self._lock:
            return list(self._raw_lines)

    # --- transport -------------------------------------------------------
    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    def _send(self, obj: Dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise OmpRpcError("RPC session is not started")
        try:
            proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            proc.stdin.flush()
        except OSError as exc:
            raise OmpRpcError(f"RPC stdin write failed: {exc}") from exc

    def _wait_for(
        self,
        predicate: Callable[[Dict[str, Any]], bool],
        timeout: float,
        start: int = 0,
    ) -> Optional[Dict[str, Any]]:
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            with self._lock:
                for frame in self._frames[start:]:
                    if predicate(frame):
                        return frame
            if time.monotonic() >= deadline:
                return None
            time.sleep(POLL_INTERVAL_S)

    def _index_of(self, frame: Optional[Dict[str, Any]]) -> int:
        """Position of a frame in the stream, or -1 when it is not present."""
        if frame is None:
            return -1
        with self._lock:
            for index, candidate in enumerate(self._frames):
                if candidate is frame:
                    return index
        return -1

    def _request(
        self, command: Dict[str, Any], prefix: str, timeout: float = RESPONSE_TIMEOUT_S
    ) -> Dict[str, Any]:
        request = dict(command)
        request_id = self._next_id(prefix)
        request["id"] = request_id
        self._send(request)
        response = self._wait_for(
            lambda f: f.get("type") == "response" and f.get("id") == request_id, timeout
        )
        if response is None:
            raise OmpRpcError(
                f"No response to {command.get('type')!r} (id={request_id}) within {timeout}s"
            )
        return response

    # --- lifecycle -------------------------------------------------------
    def start(self, timeout: float = READY_TIMEOUT_S) -> Dict[str, Any]:
        """Spawn the RPC process and wait for its ready frame."""
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_fh = self.log_path.open("w", encoding="utf-8")
        cmd = [
            self.omp_bin,
            "--mode",
            "rpc",
            "--no-session",
            "--no-title",
            "--no-ui",
            "--max-time",
            str(int(self.max_seconds)),
            *(self.extra_args or []),
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(self.cwd),
            env={**os.environ, **self.env} if self.env else None,
        )
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        ready = self._wait_for(lambda f: f.get("type") == "ready", timeout)
        if ready is None:
            self.close()
            raise OmpRpcError(f"omp rpc session emitted no ready frame within {timeout}s")
        self._ready = ready
        return ready

    def negotiate(self, protocol_version: int = 2, timeout: float = RESPONSE_TIMEOUT_S) -> Dict[str, Any]:
        """Negotiate the protocol version and return the effective transport descriptor."""
        response = self._request(
            {"type": "negotiate_protocol", "protocolVersion": protocol_version}, "p", timeout
        )
        if not response.get("success"):
            raise OmpRpcError(f"negotiate_protocol failed: {response.get('error')}")
        return negotiated_descriptor([self._ready or {}, response])

    def subscribe_subagents(self, level: str = "events", timeout: float = RESPONSE_TIMEOUT_S) -> Dict[str, Any]:
        response = self._request({"type": "set_subagent_subscription", "level": level}, "s", timeout)
        if not response.get("success"):
            raise OmpRpcError(f"set_subagent_subscription failed: {response.get('error')}")
        return response

    def prompt(self, message: str, timeout: float = RESPONSE_TIMEOUT_S) -> Dict[str, Any]:
        """Send a prompt and return its admission response (not its completion)."""
        response = self._request({"type": "prompt", "message": message}, "q", timeout)
        if not response.get("success"):
            raise OmpRpcError(f"prompt rejected: {response.get('error')}")
        return response

    def wait_settled(self, prompt_id: Optional[str] = None, timeout: Optional[float] = None) -> bool:
        """Wait for this prompt's completion and post-prompt quiescence.

        A ``session_settled`` frame that predates the prompt's own result describes an
        earlier stretch of activity, so only a frame at a later index counts as join.
        A prompt whose result reports anything but ``completed`` is not a settled join.
        Without a prompt id there is nothing to correlate against, so the answer is no.
        """
        if prompt_id is None:
            return False
        deadline = time.monotonic() + (self.max_seconds if timeout is None else timeout)
        result = self._wait_for(
            lambda f: f.get("type") == "prompt_result" and f.get("id") == prompt_id,
            deadline - time.monotonic(),
        )
        if result is None or result.get("status") != "completed":
            return False
        index = self._index_of(result)
        if index < 0:
            return False
        settled = self._wait_for(
            lambda f: f.get("type") == "session_settled", deadline - time.monotonic(), start=index + 1
        )
        return settled is not None

    def subagents(self, timeout: float = RESPONSE_TIMEOUT_S) -> List[Dict[str, Any]]:
        response = self._request({"type": "get_subagents"}, "g", timeout)
        return (response.get("data") or {}).get("subagents", [])

    def cancel_subagent(self, subagent_id: str, timeout: float = RESPONSE_TIMEOUT_S) -> Dict[str, Any]:
        return self._request(
            {"type": "cancel_subagent", "subagentId": subagent_id}, "c", timeout
        )

    def wait_child_started(self, timeout: float = RESPONSE_TIMEOUT_S) -> Optional[str]:
        """Bounded wait for the first child lifecycle frame; returns its child id.

        A caller that needs an in-flight child to cancel has nothing to cancel when no
        lifecycle frame carries an id before the deadline, so the answer is None rather
        than a wait the caller's own deadline does not bound.
        """
        frame = self._wait_for(
            lambda f: f.get("type") == "subagent_lifecycle" and (f.get("payload") or {}).get("id"),
            timeout,
        )
        return (frame.get("payload") or {}).get("id") if frame else None

    def wait_child_terminal(self, child_id: str, timeout: float = RESPONSE_TIMEOUT_S) -> Optional[Dict[str, Any]]:
        """Bounded wait for this child's terminal lifecycle frame, or None on deadline.

        Only a terminal status counts: a cancel acknowledgement, a progress frame or an
        earlier `started` frame is not evidence that the child stopped.
        """
        return self._wait_for(
            lambda f: f.get("type") == "subagent_lifecycle"
            and (f.get("payload") or {}).get("id") == child_id
            and (f.get("payload") or {}).get("status") in TERMINAL_LIFECYCLE_STATUS,
            timeout,
        )

    def close(self, grace: float = 10.0) -> Optional[int]:
        """Close stdin, wait for exit, kill after the grace period, report exit code."""
        proc = self._proc
        if proc is None:
            self._close_log()
            return None
        try:
            if proc.stdin is not None:
                proc.stdin.close()
        except OSError:
            pass
        code: Optional[int] = None
        try:
            code = proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                code = proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                code = None
        if self._reader is not None:
            self._reader.join(timeout=2.0)
        self._proc = None
        self._close_log()
        return code

    def _close_log(self) -> None:
        if self._log_fh is not None:
            self._log_fh.close()
            self._log_fh = None
