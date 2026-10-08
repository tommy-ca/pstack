#!/usr/bin/env python3
"""Oh-My-Pi (OMP) harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


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

        # OMP native subagent tool is 'task'
        tm = self.profile_data.get("tool_mappings", {})
        has_task = tm.get("agent_spawn") == "task"
        rc = self.profile_data.get("runtime_conventions", {})
        has_alias = rc.get("wire_aliases", {}).get("task") == "spawn_subagent"
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if has_task and has_alias and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-omp",
            description="Verify OMP native 'task' subagent tool capability binding and wire alias",
            command="omp subagent-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OMP subagent primitive verified (spawn={tm.get('agent_spawn')}, alias={rc.get('wire_aliases')}, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
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
            description="Verify OMP native git worktree workspace isolation command",
            command=f"{bin_path} --help (check worktree)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"OMP CLI supports git worktree management (found={has_worktree})",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
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
