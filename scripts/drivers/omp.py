#!/usr/bin/env python3
"""Oh-My-Pi (OMP) harness native driver."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable
from .omp_rpc import OmpRpcError, OmpRpcSession, reduce_child_settlement

# Opt-in gate: the live path spawns a real model-backed child and needs a model
# route, so the offline path (and generic CI) never requires one.
LIVE_GATE_ENV = "PSTACK_RUN_OMP_LIVE"
LIVE_MAX_SECONDS = 240

# The parent is told to spawn exactly one `task` child that emits a literal
# token, then to stop. The parent's own reply is asserted before a PASS; the
# child's token is requested but not asserted, because the child transcript is
# not part of the reduced evidence.
LIVE_PROMPT = (
    "Use the task tool exactly once to spawn a subagent whose assignment is: "
    "Reply with exactly CHILD_OK and nothing else. "
    "Wait for that subagent result, then reply with exactly PARENT_DONE"
)

# A cancel run needs a child that outlives the runner's cancel request, so the child is
# told to hold a shell for two minutes. The parent's own reply is not part of the proof:
# the evidence is the cancelled child's terminal lifecycle frame.
CANCEL_PROMPT = (
    "Use the task tool exactly once to spawn a subagent whose assignment is: "
    "Run the shell command `sleep 120` with the bash tool, then reply with exactly CHILD_OK. "
    "Do not reply before that command returns."
)
CHILD_START_TIMEOUT_S = 60.0
CANCEL_SETTLE_TIMEOUT_S = 30.0

# A failed provider turn is not a failed child: these route-specific phrases mean the
# model route itself was unavailable, which is BLOCKED rather than FAIL. Bare words such
# as "model" or "provider" are deliberately absent: a genuine child or turn defect can
# mention them, and downgrading a defect to BLOCKED corrupts triage.
_MODEL_ROUTE_MARKERS = (
    "no route",
    "no provider",
    "rate limit",
    "quota",
    "insufficient balance",
    "unauthorized",
    "invalid api key",
    "api key",
    "api_key",
    "credential",
    "not authenticated",
    "auth token",
)


def _model_route_error(frames: Sequence[Dict[str, Any]]) -> str:
    """Return the provider/model error text when a live failure is a missing model route."""
    for frame in frames:
        if frame.get("type") == "prompt_result" and frame.get("status") == "error":
            message = (frame.get("error") or {}).get("message", "")
        elif frame.get("type") == "response" and frame.get("success") is False:
            error = frame.get("error")
            message = error if isinstance(error, str) else (error or {}).get("message", "")
        else:
            continue
        if message and any(marker in message.lower() for marker in _MODEL_ROUTE_MARKERS):
            return message
    return ""


# Isolation probe: one isolated `task` child writes this token into a fresh file in
# its own workspace while `task.isolation.apply=false` forbids the merge. The parent
# checkout sentinel is committed before the run, so a byte-identical sentinel plus a
# captured-but-unapplied patch is the whole filesystem boundary proof.
ISOLATION_TOKEN = "CHILD_ISO_OK"
ISOLATION_CHILD_FILE = "ISO_CHILD.txt"
ISOLATION_SENTINEL_FILE = "PARENT_SENTINEL.txt"
ISOLATION_SENTINEL_BODY = "PARENT-SENTINEL-UNTOUCHED\n"
ISOLATION_PROMPT = (
    "Use the task tool exactly once with isolated: true (an isolated worktree) to spawn a subagent "
    f"whose assignment is: run exactly `printf '{ISOLATION_TOKEN}' > {ISOLATION_CHILD_FILE}` in your "
    "working directory, then run `pwd` and reply with the absolute path pwd printed and nothing else. "
    "Do not create, edit or delete any other file yourself. "
    "When that subagent result arrives, reply with exactly PARENT_DONE"
)
ISOLATION_CONFIG = """task:
  isolation:
    enabled: true
    apply: false
    merge: patch
isolation:
  backend: auto
worktree:
  base: {base}
"""

_LITERAL_PATTERN = re.compile(r"PARENT[\s_]*DONE", re.IGNORECASE)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|\s)(/[^\s`\"']+)")


def _git(cwd: Path, *args: str) -> Tuple[int, str]:
    """Run one git command with a hard floor on output size."""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, str(exc)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _prepare_isolation_repo(repo: Path, worktree_base: Path) -> str:
    """Create the parent checkout, its committed sentinel and the isolation overlay."""
    repo.mkdir(parents=True)
    worktree_base.mkdir(parents=True)
    (repo / ISOLATION_SENTINEL_FILE).write_text(ISOLATION_SENTINEL_BODY, encoding="utf-8")
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "probe@pstack.local"),
        ("config", "user.name", "pstack isolation probe"),
        ("add", ISOLATION_SENTINEL_FILE),
        ("commit", "-q", "-m", "sentinel"),
    ):
        code, out = _git(repo, *args)
        if code != 0:
            return f"git {' '.join(args)} failed: {out.strip()}"
    return ""


def _isolation_residue(repo: Path, worktree_base: Path) -> Dict[str, Any]:
    """Post-run parent-checkout invariants: sentinel, unapplied delta, cleanup."""
    sentinel = repo / ISOLATION_SENTINEL_FILE
    sentinel_intact = sentinel.is_file() and sentinel.read_text(encoding="utf-8") == ISOLATION_SENTINEL_BODY
    child_file_absent = not (repo / ISOLATION_CHILD_FILE).exists()
    status_code, status_out = _git(repo, "status", "--porcelain", "-uall")
    tree_clean = status_code == 0 and not status_out.strip()
    _, worktrees_out = _git(repo, "worktree", "list", "--porcelain")
    worktree_count = len([ln for ln in worktrees_out.splitlines() if ln.startswith("worktree ")])
    leftover = sorted(p.name for p in worktree_base.iterdir()) if worktree_base.is_dir() else []
    return {
        "sentinel_intact": sentinel_intact,
        "child_file_absent": child_file_absent,
        "tree_clean": tree_clean,
        "worktree_count": worktree_count,
        "worktree_leftovers": leftover,
    }


def _isolated_child_patch(frames: Sequence[Dict[str, Any]]) -> Tuple[str, str]:
    """Child id and captured patch path of the isolated child, derived from the stream.

    The isolation runner writes the captured delta to `<artifacts>/<child>.patch`, beside
    the child session file the lifecycle frame names, and only the isolation path writes
    it. A patch that holds the probe token is therefore the observation that this child ran
    in its own workspace and that its write never reached the parent checkout.
    """
    child_id = ""
    session_file = ""
    for frame in frames:
        if frame.get("type") != "subagent_lifecycle":
            continue
        payload = frame.get("payload") or {}
        if not payload.get("id"):
            continue
        child_id = str(payload["id"])
        if payload.get("sessionFile"):
            session_file = str(payload["sessionFile"])
    if not child_id or not session_file:
        return "", ""
    return child_id, str(Path(session_file).with_name(f"{child_id}.patch"))


def _patch_excerpt(patch_path: str, limit: int = 65536) -> str:
    """Bounded read of the captured patch, which is the only copy of the child's write."""
    try:
        with open(patch_path, "rb") as handle:
            return handle.read(limit).decode("utf-8", "replace")
    except OSError:
        return ""


def _reported_workspace(frames: Sequence[Dict[str, Any]]) -> str:
    """Last absolute path the parent named, used only to contradict a false isolation claim."""
    matches = _ABSOLUTE_PATH_PATTERN.findall(_assistant_text(frames))
    return matches[-1] if matches else ""


def _assistant_text(frames: Sequence[Dict[str, Any]]) -> str:
    """Text of the last assistant message, which is where the parent's own reply lands."""
    text = ""
    for frame in frames:
        if frame.get("type") != "message_end":
            continue
        message = frame.get("message") or {}
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        text = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return text


class OMPDriver(HarnessDriver):
    """Host driver for Oh-My-Pi (OMP) harness."""

    def __init__(self, root: Path):
        super().__init__("omp", root)
        self._binary: Optional[Path] = None

    @staticmethod
    def _attempted(result: DriverScenarioResult) -> DriverScenarioResult:
        """Mark a row as produced by an attempted live gate arm, not a static contract check."""
        result.live_attempted = True
        return result

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "share" / "mise" / "installs",
                Path.home() / ".local" / "bin",
            ]
            self._binary = find_executable("omp", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found omp at {bin_path}"
        return False, "omp CLI binary not found in PATH or mise installs"

    def get_version(self) -> Optional[str]:
        bin_path = self.get_binary_path()
        if not bin_path:
            return None
        code, out, _, _ = self.run_command([str(bin_path), "--version"])
        if code == 0:
            return out.strip()
        return None

    def discover(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-discover-omp", "OMP plugin and extension discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "plugin", "list"], cwd=self.root)
        verdict = "PASS" if code == 0 else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-omp",
            description="Verify OMP plugin system and package registry via omp plugin list",
            command=f"{bin_path} plugin list",
            exit_code=code,
            stdout=out[:250],
            stderr=err[:250],
            verdict=verdict,
            duration_s=dur,
        )

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-route-playbook-omp", f"OMP playbook routing for '{playbook}'", reason)

        from ..route_resolver import resolve_skill_order

        route = resolve_skill_order(self.profile_data, playbook, self.root)
        if route.kind == "declared-fallback":
            verdict = "PASS" if route.target is not None else "FAIL"
            stdout = f"Routed '{playbook}' to declared fallback '{route.target}'"
        elif route.is_matched and route.artifact_exists:
            verdict = "PASS"
            stdout = f"Routed '{playbook}' to {route.kind} '{route.target}' ({route.artifact}; exists=True)"
        else:
            verdict = "FAIL"
            stdout = f"No valid route/artifact for '{playbook}' (status={route.status}, target={route.target})"

        return DriverScenarioResult(
            scenario_id="runtime-route-playbook-omp",
            description=f"Verify OMP routes '{playbook}' via profile skill_order ({route.target})",
            command=f"omp route-check --playbook {playbook} -> {route.target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
            stderr=route.error_reason,
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-omp", "OMP child subagent spawn contract", reason)

        if os.environ.get(LIVE_GATE_ENV) == "1":
            return self._attempted(self._child_spawn_live(run_dir))

        # OMP native subagent tool is 'task'
        tm = self.profile_data.get("tool_mappings", {})
        has_task = tm.get("agent_spawn") == "task"
        rc = self.profile_data.get("runtime_conventions", {})
        has_alias = rc.get("wire_aliases", {}).get("task") == "spawn_subagent"
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if has_task and has_alias and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-omp",
            description="Verify OMP native 'task' subagent tool capability binding and wire alias (static contract only, no observed child)",
            command="omp subagent-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OMP subagent primitive verified (spawn={tm.get('agent_spawn')}, alias={rc.get('wire_aliases')}, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
            evidence_level="static",
        )

    def _child_spawn_live(self, run_dir: Path) -> DriverScenarioResult:
        """Spawn a real RPC session, prompt one `task` child, and reduce its settlement."""
        bin_path = self.get_binary_path()
        assert bin_path is not None
        start = time.time()
        work_dir = Path(tempfile.mkdtemp(prefix="omp-rpc-live-"))
        log_path = run_dir / "omp-rpc-live.jsonl"
        command = (
            f"{bin_path} --mode rpc --no-session --no-title --no-ui --max-time {LIVE_MAX_SECONDS}"
            " (prompt -> 1 task child)"
        )
        session = OmpRpcSession(str(bin_path), cwd=work_dir, max_seconds=LIVE_MAX_SECONDS, log_path=log_path)
        frames: list = []
        settled = False
        failure = ""
        try:
            session.start()
            descriptor = session.negotiate()
            session.subscribe_subagents("events")
            admission = session.prompt(LIVE_PROMPT)
            settled = session.wait_settled(prompt_id=admission.get("id"))
            frames = session.frames
        except (OmpRpcError, OSError) as exc:
            # A missing binary, an unwritable run directory or a failed spawn is an
            # unavailable host, not a failed child, and must not abort the matrix run.
            failure = str(exc)
        finally:
            exit_code = session.close()
            shutil.rmtree(work_dir, ignore_errors=True)
        duration = round(time.time() - start, 3)

        if failure:
            return DriverScenarioResult(
                scenario_id="runtime-child-spawn-omp",
                description="Observed OMP RPC v2 session failed before a child settlement",
                command=command,
                exit_code=1,
                stdout=f"BLOCKED: {failure} (log={log_path})",
                stderr=failure,
                verdict="BLOCKED",
                duration_s=duration,
                evidence_level="offline",
            )

        settlement = reduce_child_settlement(frames, timed_out=not settled)
        route_error = _model_route_error(frames)
        literal_seen = bool(_LITERAL_PATTERN.search(_assistant_text(frames)))
        protocol_v2 = descriptor.get("protocol_version") == 2
        observed = (
            f"child={settlement['child_id']} outcome={settlement['terminal_outcome']} "
            f"model={settlement['model']} effective_rpc={settlement['effective_rpc']}"
            if settlement
            else "no single terminal child lifecycle observed"
        )
        summary = (
            f"RPC v{descriptor['protocol_version']} exit={exit_code} settled={settled} "
            f"literal={literal_seen} {observed}"
        )

        if (
            settlement is not None
            and settlement["terminal_outcome"] == "success"
            and settled
            and exit_code == 0
            and protocol_v2
            and literal_seen
        ):
            return DriverScenarioResult(
                scenario_id="runtime-child-spawn-omp",
                description="Observed live OMP RPC v2 'task' child spawn/join with typed settlement",
                command=command,
                exit_code=0,
                stdout=summary,
                stderr="",
                verdict="PASS",
                duration_s=duration,
                evidence_level="observed_live",
                settlement=settlement,
            )

        unmet: List[str] = []
        if settlement is None:
            unmet.append("no single terminal child lifecycle")
        elif settlement["terminal_outcome"] != "success":
            unmet.append(f"child outcome {settlement['terminal_outcome']}")
        if not settled:
            unmet.append("session did not settle after the prompt")
        if exit_code != 0:
            unmet.append(f"process exit {exit_code}")
        if not protocol_v2:
            unmet.append(f"negotiated protocol v{descriptor.get('protocol_version')}")
        if not literal_seen:
            unmet.append("parent reply did not carry PARENT_DONE")

        verdict = "BLOCKED" if route_error else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-omp",
            description="Observed live OMP RPC v2 'task' child spawn/join did not settle successfully",
            command=command,
            exit_code=exit_code if exit_code is not None else 1,
            stdout=summary,
            stderr=route_error or failure or "; ".join(unmet),
            verdict=verdict,
            duration_s=duration,
            evidence_level="offline",
        )

    def child_cancel(self, run_dir: Path) -> DriverScenarioResult:
        """Prove OMP cancels one in-flight child over RPC, or record the bounded negative."""
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-cancel-omp", "OMP in-flight child cancellation over RPC", reason)

        if os.environ.get(LIVE_GATE_ENV) == "1":
            return self._attempted(self._child_cancel_live(run_dir))

        binding = next(
            (b for b in self.profile_data.get("bindings", []) if b.get("capability") == "agent.cancel"),
            {},
        )
        declared = (
            binding.get("implementation_status") == "native"
            and binding.get("enforcement") == "hard"
            and "cancel" in str(binding.get("primitive", "")).lower()
        )
        surface = all(
            hasattr(OmpRpcSession, name)
            for name in ("subagents", "cancel_subagent", "wait_child_started", "wait_child_terminal")
        )
        verdict = "PASS" if declared and surface else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-cancel-omp",
            description=(
                "Verify OMP cancellation is a declared native hard capability with a bounded RPC "
                "surface (static contract only, no observed cancellation)"
            ),
            command="omp cancel-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=(
                f"OMP cancel contract (declared={declared}, primitive={binding.get('primitive')!r}, "
                f"bounded_surface={surface})"
            ),
            stderr="" if verdict == "PASS" else "cancel contract or bounded RPC surface missing",
            verdict=verdict,
            duration_s=0.01,
            evidence_level="static",
        )

    def _child_cancel_live(self, run_dir: Path) -> DriverScenarioResult:
        """Drive a bounded session, cancel one in-flight child, reduce the settlement."""
        bin_path = self.get_binary_path()
        assert bin_path is not None
        start = time.time()
        work_dir = Path(tempfile.mkdtemp(prefix="omp-rpc-cancel-"))
        log_path = run_dir / "omp-rpc-cancel.jsonl"
        command = (
            f"{bin_path} --mode rpc --no-session --no-title --no-ui --max-time {LIVE_MAX_SECONDS}"
            " (prompt -> 1 task child -> cancel_subagent)"
        )
        session = OmpRpcSession(str(bin_path), cwd=work_dir, max_seconds=LIVE_MAX_SECONDS, log_path=log_path)
        descriptor: Dict[str, Any] = {"protocol_version": 0}
        frames: List[Dict[str, Any]] = []
        child_id: Optional[str] = None
        listed: Optional[List[str]] = None
        cancel_ack = False
        cancel_success = False
        cancel_killed = False
        cancel_error = ""
        terminal: Optional[Dict[str, Any]] = None
        cancel_latency: Optional[float] = None
        failure = ""
        try:
            session.start()
            descriptor = session.negotiate()
            session.subscribe_subagents("events")
            session.prompt(CANCEL_PROMPT)
            child_id = session.wait_child_started(timeout=CHILD_START_TIMEOUT_S)
            if child_id is not None:
                listed = [str(s.get("id")) for s in session.subagents()]
                cancel_started = time.monotonic()
                cancel_response = session.cancel_subagent(child_id)
                # Upstream answers `data.cancelled=false` for an id that is not a running
                # subagent of this session (finished, unknown, already cancelled), so the
                # success flag alone would read an idempotent no-op as a kill.
                cancel_success = bool(cancel_response.get("success"))
                cancel_killed = bool((cancel_response.get("data") or {}).get("cancelled"))
                cancel_ack = cancel_success and cancel_killed
                if not cancel_success:
                    error = cancel_response.get("error")
                    cancel_error = error if isinstance(error, str) else str((error or {}).get("message", ""))
                terminal = session.wait_child_terminal(child_id, timeout=CANCEL_SETTLE_TIMEOUT_S)
                cancel_latency = round(time.monotonic() - cancel_started, 3)
        except (OmpRpcError, OSError) as exc:
            failure = str(exc)
        finally:
            # Frames collected before a failure are still evidence of what the host did.
            frames = session.frames
            exit_code = session.close()
            shutil.rmtree(work_dir, ignore_errors=True)
        duration = round(time.time() - start, 3)

        if failure and not frames:
            # A missing binary, an unwritable run directory or a session that died before
            # emitting anything is an unavailable host, not a failed cancellation.
            return DriverScenarioResult(
                scenario_id="runtime-child-cancel-omp",
                description="Observed OMP RPC v2 cancel session failed before any frame arrived",
                command=command,
                exit_code=1,
                stdout=f"BLOCKED: {failure} (log={log_path})",
                stderr=failure,
                verdict="BLOCKED",
                duration_s=duration,
                evidence_level="offline",
            )

        settlement = (
            reduce_child_settlement(frames, child_id=child_id, timed_out=terminal is None)
            if child_id is not None
            else None
        )
        route_error = _model_route_error(frames)
        in_flight = child_id is not None and listed is not None and child_id in listed
        protocol_v2 = descriptor.get("protocol_version") == 2
        observed = (
            f"child={settlement['child_id']} outcome={settlement['terminal_outcome']} "
            f"model={settlement['model']} effective_rpc={settlement['effective_rpc']}"
            if settlement
            else "no terminal child lifecycle observed"
        )
        summary = (
            f"RPC v{descriptor['protocol_version']} exit={exit_code} ack={cancel_success} "
            f"killed={cancel_killed} listed={len(listed) if listed is not None else 'none'} "
            f"in_flight={in_flight} latency={cancel_latency if cancel_latency is not None else 'n/a'}s "
            f"{observed}" + (f" error={cancel_error}" if cancel_error else "")
        )

        if (
            settlement is not None
            and settlement["terminal_outcome"] == "cancelled"
            and cancel_ack
            and terminal is not None
            and protocol_v2
            and exit_code is not None
        ):
            return DriverScenarioResult(
                scenario_id="runtime-child-cancel-omp",
                description=(
                    "Observed live OMP RPC v2 in-flight child cancellation: the accepted "
                    "cancel_subagent request reduced to a typed cancelled settlement"
                ),
                command=command,
                exit_code=0,
                stdout=summary,
                stderr="",
                verdict="PASS",
                duration_s=duration,
                evidence_level="observed_live",
                settlement=settlement,
            )

        unmet: List[str] = []
        if child_id is None:
            unmet.append(f"no child lifecycle within {CHILD_START_TIMEOUT_S}s")
        if not cancel_ack:
            if cancel_success:
                unmet.append("cancel_subagent found no running subagent to cancel (cancelled=false)")
            else:
                unmet.append(
                    f"cancel_subagent was rejected ({cancel_error})" if cancel_error else "cancel_subagent was rejected"
                )
        if child_id is not None and terminal is None:
            unmet.append(f"no terminal child lifecycle within {CANCEL_SETTLE_TIMEOUT_S}s after the cancel")
        if settlement is None:
            unmet.append("no typed settlement")
        elif settlement["terminal_outcome"] != "cancelled":
            unmet.append(f"child outcome {settlement['terminal_outcome']}")
        if not protocol_v2:
            unmet.append(f"negotiated protocol v{descriptor.get('protocol_version')}")
        if exit_code is None:
            unmet.append("RPC process did not exit")

        verdict = "BLOCKED" if route_error else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-cancel-omp",
            description="Observed live OMP RPC v2 cancellation did not record a typed cancelled settlement",
            command=command,
            exit_code=exit_code if exit_code is not None else 1,
            stdout=summary,
            stderr=route_error or failure or "; ".join(unmet),
            verdict=verdict,
            duration_s=duration,
            evidence_level="offline",
            settlement=settlement,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-isolation-omp", "OMP worktree isolation check", reason)

        if os.environ.get(LIVE_GATE_ENV) == "1":
            return self._attempted(self._isolation_live(run_dir))

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "--help"], cwd=self.root)
        has_worktree = "worktree" in out.lower()
        verdict = "PASS" if code == 0 and has_worktree else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-omp",
            description=(
                "Verify OMP native git worktree isolation CLI surface "
                f"(static contract only; observed live only under {LIVE_GATE_ENV}=1)"
            ),
            command=f"{bin_path} --help (check worktree)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OMP CLI supports git worktree management (found={has_worktree})",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
            evidence_level="static",
        )

    def _isolation_live(self, run_dir: Path) -> DriverScenarioResult:
        """Observe one isolated child: sentinel untouched, delta captured, nothing applied."""
        bin_path = self.get_binary_path()
        assert bin_path is not None
        start = time.time()
        work_dir = Path(tempfile.mkdtemp(prefix="omp-iso-live-"))
        repo = work_dir / "parent-checkout"
        worktree_base = work_dir / "worktrees"
        config_path = work_dir / "isolation.yml"
        log_path = run_dir / "omp-isolation-live.jsonl"
        command = (
            f"{bin_path} --mode rpc --config {config_path} (isolated:true child, apply:false)"
        )
        failure = _prepare_isolation_repo(repo, worktree_base)
        config_path.write_text(
            ISOLATION_CONFIG.format(base=worktree_base.as_posix()), encoding="utf-8"
        )

        frames: list = []
        settled = False
        child_id = ""
        patch_path = ""
        patch_excerpt = ""
        reported = ""
        exit_code: Optional[int] = None
        if not failure:
            session = OmpRpcSession(
                str(bin_path),
                cwd=repo,
                max_seconds=LIVE_MAX_SECONDS,
                log_path=log_path,
                # The overlay is what turns task isolation on with apply=false; without it
                # the child runs in the parent checkout and the probe must fail, not pass.
                extra_args=["--config", str(config_path)],
                # The isolation workspace must live inside this run's temp root so the
                # residue check can prove the probe left no worktree behind.
                env={"OMP_WORKTREE_DIR": str(worktree_base)},
            )
            try:
                session.start()
                descriptor = session.negotiate()
                session.subscribe_subagents("events")
                admission = session.prompt(ISOLATION_PROMPT)
                settled = session.wait_settled(prompt_id=admission.get("id"))
                frames = session.frames
                child_id, patch_path = _isolated_child_patch(frames)
                patch_excerpt = _patch_excerpt(patch_path) if patch_path else ""
                reported = _reported_workspace(frames)
            except (OmpRpcError, OSError) as exc:
                failure = str(exc)
            finally:
                exit_code = session.close()

        residue = _isolation_residue(repo, worktree_base)
        shutil.rmtree(work_dir, ignore_errors=True)
        duration = round(time.time() - start, 3)

        if failure:
            return DriverScenarioResult(
                scenario_id="runtime-isolation-omp",
                description="Observed OMP isolation run failed before a settled isolated child",
                command=command,
                exit_code=1,
                stdout=f"BLOCKED: {failure} (log={log_path})",
                stderr=failure,
                verdict="BLOCKED",
                duration_s=duration,
                evidence_level="offline",
            )

        settlement = reduce_child_settlement(frames, timed_out=not settled)
        route_error = _model_route_error(frames)
        literal_seen = bool(_LITERAL_PATTERN.search(_assistant_text(frames)))
        protocol_v2 = descriptor.get("protocol_version") == 2
        token_in_patch = ISOLATION_TOKEN in patch_excerpt
        # A parent naming its own checkout as the child's workspace contradicts isolation.
        reported_elsewhere = not reported or (
            not reported.startswith(str(repo)) and str(repo) not in reported
        )
        summary = (
            f"RPC v{descriptor['protocol_version']} exit={exit_code} settled={settled} "
            f"literal={literal_seen} child={child_id or 'none'} patch={patch_path or 'none'} "
            f"token_in_patch={token_in_patch} reported={reported or 'none'} "
            f"sentinel_intact={residue['sentinel_intact']} child_file_absent={residue['child_file_absent']} "
            f"tree_clean={residue['tree_clean']} worktrees={residue['worktree_count']} "
            f"worktree_leftovers={residue['worktree_leftovers'] or 'none'}"
        )

        isolation_observed = (
            bool(patch_path)
            and bool(patch_excerpt)
            and token_in_patch
            and residue["sentinel_intact"]
            and residue["child_file_absent"]
            and residue["tree_clean"]
            and residue["worktree_count"] == 1
            and not residue["worktree_leftovers"]
        )

        if (
            settlement is not None
            and settlement["terminal_outcome"] == "success"
            and settled
            and exit_code == 0
            and protocol_v2
            and literal_seen
            and reported_elsewhere
            and isolation_observed
        ):
            return DriverScenarioResult(
                scenario_id="runtime-isolation-omp",
                description=(
                    "Observed live OMP isolated `task` child: parent sentinel untouched, "
                    "delta captured under apply=false, no worktree residue"
                ),
                command=command,
                exit_code=0,
                stdout=summary,
                stderr="",
                verdict="PASS",
                duration_s=duration,
                evidence_level="observed_live",
                settlement=settlement,
            )

        unmet: List[str] = []
        if settlement is None:
            unmet.append("no single terminal child lifecycle")
        elif settlement["terminal_outcome"] != "success":
            unmet.append(f"child outcome {settlement['terminal_outcome']}")
        if not settled:
            unmet.append("session did not settle after the prompt")
        if exit_code != 0:
            unmet.append(f"process exit {exit_code}")
        if not protocol_v2:
            unmet.append(f"negotiated protocol v{descriptor.get('protocol_version')}")
        if not literal_seen:
            unmet.append("parent reply did not carry PARENT_DONE")
        if not reported_elsewhere:
            unmet.append(f"parent named its own checkout as the child workspace ({reported})")
        if not patch_path:
            unmet.append("no captured isolation patch (child was not observed isolated)")
        elif not patch_excerpt or not token_in_patch:
            unmet.append(f"captured patch did not hold the {ISOLATION_TOKEN} write")
        if not residue["sentinel_intact"]:
            unmet.append("parent sentinel changed")
        if not residue["child_file_absent"] or not residue["tree_clean"]:
            unmet.append("isolated delta reached the parent checkout")
        if residue["worktree_count"] != 1 or residue["worktree_leftovers"]:
            unmet.append(f"worktree residue left behind: {residue['worktree_leftovers']}")

        verdict = "BLOCKED" if route_error else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-omp",
            description="Observed live OMP isolation run did not prove the workspace boundary",
            command=command,
            exit_code=exit_code if exit_code is not None else 1,
            stdout=summary,
            stderr=route_error or "; ".join(unmet),
            verdict=verdict,
            duration_s=duration,
            evidence_level="offline",
        )

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        receipt_path = self.root / ".audit" / "evidence" / "omp-receipt.json"
        has_receipt = receipt_path.is_file()
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-omp",
            description="Verify OMP durable evidence receipt binding",
            command=f"test -f {receipt_path}",
            exit_code=0 if has_receipt else 1,
            stdout=f"Durable receipt located at {receipt_path} (exists={has_receipt})",
            stderr="",
            verdict="PASS" if has_receipt else "FAIL",
            duration_s=0.01,
        )
