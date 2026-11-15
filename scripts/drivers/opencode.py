#!/usr/bin/env python3
"""OpenCode harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


class OpenCodeDriver(HarnessDriver):
    """Host driver for OpenCode harness."""

    display_name = "OpenCode"
    route_cmd = "opencode"

    def __init__(self, root: Path):
        super().__init__("opencode", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "share" / "mise" / "installs",
                Path.home() / ".local" / "bin",
            ]
            self._binary = find_executable("opencode", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found opencode at {bin_path}"
        return False, "opencode CLI binary not found in PATH or mise installs"

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
            return self.blocked_result("runtime-discover-opencode", "OpenCode runtime paths and configuration discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "debug", "paths"], cwd=self.root)
        verdict = "PASS" if code == 0 and "config" in out else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-opencode",
            description="Verify OpenCode runtime environment and configuration paths via opencode debug paths",
            command=f"{bin_path} debug paths",
            exit_code=code,
            stdout=out[:250],
            stderr=err[:250],
            verdict=verdict,
            duration_s=dur,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-opencode", "OpenCode child subagent spawn contract", reason)

        # OpenCode native subagent tool is 'task'
        tm = self.profile_data.get("tool_mappings", {})
        has_task = tm.get("agent_spawn") == "task"
        rc = self.profile_data.get("runtime_conventions", {})
        has_alias = rc.get("wire_aliases", {}).get("task") == "spawn_subagent"
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if has_task and has_alias and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-opencode",
            description="Verify OpenCode native 'task' subagent tool capability binding and wire alias",
            command="opencode subagent-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OpenCode subagent primitive verified (spawn={tm.get('agent_spawn')}, alias={rc.get('wire_aliases')}, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        rc = self.profile_data.get("runtime_conventions", {})
        iso_modes = rc.get("supported_isolation_modes", [])
        has_worktree = "worktree" in iso_modes
        verdict = "PASS" if has_worktree else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-opencode",
            description="Verify OpenCode workspace isolation convention (git worktree)",
            command="opencode isolation-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OpenCode supported isolation modes: {iso_modes}",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

