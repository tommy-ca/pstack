#!/usr/bin/env python3
"""Oh-My-Pi (OMP) harness native driver."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

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


_LITERAL_PATTERN = re.compile(r"PARENT[\s_]*DONE", re.IGNORECASE)


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
            return self._child_spawn_live(run_dir)

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

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-isolation-omp", "OMP worktree isolation check", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "--help"], cwd=self.root)
        has_worktree = "worktree" in out.lower()
        verdict = "PASS" if code == 0 and has_worktree else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-omp",
            description="Verify OMP native git worktree workspace isolation command (static CLI probe only, no observed isolation)",
            command=f"{bin_path} --help (check worktree)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OMP CLI supports git worktree management (found={has_worktree})",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
            evidence_level="static",
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
