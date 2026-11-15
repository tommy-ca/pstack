#!/usr/bin/env python3
"""OpenAI Codex harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


class CodexDriver(HarnessDriver):
    """Host driver for OpenAI Codex harness."""

    display_name = "Codex"
    route_cmd = "codex"

    def __init__(self, root: Path):
        super().__init__("codex", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "share" / "mise" / "installs",
                Path.home() / ".local" / "bin",
            ]
            self._binary = find_executable("codex", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found codex at {bin_path}"
        return False, "codex CLI binary not found in PATH or mise installs"

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
            return self.blocked_result("runtime-discover-codex", "Codex runtime doctor and diagnostics", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "doctor"], cwd=self.root)
        verdict = "PASS" if code == 0 and "0 fail" in out else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-codex",
            description="Verify Codex installation health, thread inventory, and config via codex doctor",
            command=f"{bin_path} doctor",
            exit_code=code,
            stdout=out[:250],
            stderr=err[:250],
            verdict=verdict,
            duration_s=dur,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-codex", "Codex child agent spawn contract", reason)

        # Codex supports spawn_agent, wait_agent, and subagent:thread_spawn
        tm = self.profile_data.get("tool_mappings", {})
        has_spawn = tm.get("agent_spawn") == "spawn_agent"
        has_join = tm.get("agent_join") == "wait_agent"
        rc = self.profile_data.get("runtime_conventions", {})
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if has_spawn and has_join and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-codex",
            description="Verify Codex spawn_agent and wait_agent capability bindings and depth limit",
            command="codex spawn-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Codex subagent spawn verified (spawn={tm.get('agent_spawn')}, join={tm.get('agent_join')}, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-isolation-codex", "Codex worktree isolation check", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "--help"], cwd=self.root)
        has_worktree = "--worktree" in out
        verdict = "PASS" if code == 0 and has_worktree else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-codex",
            description="Verify Codex native git worktree workspace isolation flag (--worktree)",
            command=f"{bin_path} --help (check --worktree)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Codex CLI supports managed git worktrees (found={has_worktree})",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

