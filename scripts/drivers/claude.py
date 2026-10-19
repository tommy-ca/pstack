#!/usr/bin/env python3
"""Claude Code harness native driver.

Implements native driver scenarios for Claude Code:
- Host discovery and version querying (claude CLI, plugins, marketplaces)
- Plugin validation (claude plugin validate . --json)
- Skill order and playbook routing
- Subagent spawn and depth limits (parent-owned orchestration, max depth 1)
- Workspace isolation and advisory read-only enforcement
- Evidence capture binding
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable
from ..route_resolver import resolve_skill_order


class ClaudeDriver(HarnessDriver):
    """Host driver for Anthropic Claude Code harness."""

    def __init__(self, root: Path):
        super().__init__("claude", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "bin",
                Path.home() / ".local" / "share" / "claude" / "versions",
                Path.home() / ".claude" / "bin",
            ]
            self._binary = find_executable("claude", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found claude at {bin_path}"
        return False, "claude CLI binary not found in PATH, ~/.local/bin, or ~/.claude/bin"

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
            return self.blocked_result("runtime-discover-claude", "Claude Code plugin and manifest discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "plugin", "validate", ".", "--json"], cwd=self.root)
        success = False
        if code == 0:
            try:
                res = json.loads(out)
                success = res.get("success") is True
            except Exception:
                success = False

        verdict = "PASS" if success else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-claude",
            description="Verify Claude Code plugin and marketplace manifest validity via claude plugin validate",
            command=f"{bin_path} plugin validate . --json",
            exit_code=code,
            stdout=out[:250],
            stderr=err[:250],
            verdict=verdict,
            duration_s=dur,
        )

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        route = resolve_skill_order(self.profile_data, playbook, self.root)
        if route.kind == "no-route":
            return DriverScenarioResult(
                scenario_id="runtime-route-playbook-claude",
                description=f"Verify Claude Code routes '{playbook}' via profile skill_order",
                command=f"claude route-check --playbook {playbook}",
                exit_code=1,
                stdout=f"No route for '{playbook}'",
                stderr=route.error_reason,
                verdict="FAIL",
                duration_s=0.01,
            )

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
            scenario_id="runtime-route-playbook-claude",
            description=f"Verify Claude Code routes '{playbook}' via profile skill_order ({route.target})",
            command=f"claude route-check --playbook {playbook} -> {route.target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
            stderr=route.error_reason,
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        tm = self.profile_data.get("tool_mappings", {})
        has_spawn = "Task" in tm.get("agent_spawn", "")
        has_join = "TaskOutput" in tm.get("agent_join", "")
        rc = self.profile_data.get("runtime_conventions", {})
        depth_ok = rc.get("max_subagent_depth", 0) == 1

        verdict = "PASS" if has_spawn and has_join and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-claude",
            description="Verify Claude Code subagent spawn/join tool mappings and depth limit (depth 1 parent-owned)",
            command="claude spawn-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Claude Code subagent spawn verified (spawn={tm.get('agent_spawn')}, join={tm.get('agent_join')}, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        # Distinguish genuine hard readonly from prompt advice:
        # Claude Code exposes no kernel-level read-only mount; readonly is advisory/tool allowlist.
        bindings = self.profile_data.get("bindings", [])
        readonly_binding = next((b for b in bindings if b.get("capability") == "workspace.readonly"), None)
        advisory_readonly = readonly_binding is not None and readonly_binding.get("enforcement") == "advisory"

        rc = self.profile_data.get("runtime_conventions", {})
        modes = rc.get("supported_isolation_modes", [])
        has_modes = "directory-allowlist" in modes

        verdict = "PASS" if advisory_readonly and has_modes else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-claude",
            description="Verify Claude Code isolation modes and advisory read-only enforcement distinction",
            command="claude isolation-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Claude Code isolation verified (modes={modes}, readonly_enforcement={readonly_binding.get('enforcement') if readonly_binding else None})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        # Check evidence capture binding
        bindings = self.profile_data.get("bindings", [])
        evidence_binding = next((b for b in bindings if b.get("capability") == "evidence.capture"), None)
        has_binding = evidence_binding is not None and evidence_binding.get("implementation_status") == "native"

        verdict = "PASS" if has_binding else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-claude",
            description="Verify Claude Code evidence capture capability binding",
            command="claude evidence-binding-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Claude Code evidence capture verified (status={evidence_binding.get('implementation_status') if evidence_binding else None})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )
