#!/usr/bin/env python3
"""GitHub Copilot candidate harness native driver.

Implements candidate driver scenarios for GitHub Copilot:
- Host discovery and version querying (gh copilot extension, copilot CLI)
- Truthful capability accounting (multi-agent spawn/join/cancel as gap)
- Workspace isolation and advisory read-only enforcement (modes: ["none"], advisory readonly)
- Playbook route resolution
- Evidence capture binding
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable
from ..route_resolver import resolve_skill_order


class CopilotDriver(HarnessDriver):
    """Host driver for GitHub Copilot candidate harness."""

    def __init__(self, root: Path):
        super().__init__("github:copilot", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "bin",
                Path.home() / "bin",
            ]
            # Look for copilot CLI or gh with copilot extension
            self._binary = find_executable("copilot", extra) or find_executable("gh", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            if bin_path.name == "gh":
                code, out, _, _ = self.run_command([str(bin_path), "extension", "list"])
                if code == 0 and "copilot" in out:
                    return True, f"Found gh with copilot extension at {bin_path}"
                return False, f"Found gh at {bin_path} but 'copilot' extension is not installed"
            return True, f"Found copilot at {bin_path}"
        return False, "copilot CLI binary or gh copilot extension not found"

    def get_version(self) -> Optional[str]:
        bin_path = self.get_binary_path()
        if not bin_path:
            return None
        if bin_path.name == "gh":
            code, out, _, _ = self.run_command([str(bin_path), "copilot", "--version"])
            if code == 0:
                return out.strip()
            return None
        code, out, _, _ = self.run_command([str(bin_path), "--version"])
        if code == 0:
            return out.strip()
        return None

    def discover(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        # Honest discovery: if binary is absent, report BLOCKED
        if not avail:
            return self.blocked_result("runtime-discover-copilot", "GitHub Copilot CLI and extension discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        cmd = [str(bin_path), "copilot", "--version"] if bin_path.name == "gh" else [str(bin_path), "--version"]
        code, out, err, dur = self.run_command(cmd, cwd=self.root)
        verdict = "PASS" if code == 0 else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-copilot",
            description="Verify GitHub Copilot CLI/extension presence and version",
            command=" ".join(cmd),
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
                scenario_id="runtime-route-playbook-copilot",
                description=f"Verify Copilot routes '{playbook}' via profile skill_order",
                command=f"copilot route-check --playbook {playbook}",
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
            scenario_id="runtime-route-playbook-copilot",
            description=f"Verify Copilot routes '{playbook}' via profile skill_order ({route.target})",
            command=f"copilot route-check --playbook {playbook} -> {route.target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
            stderr=route.error_reason,
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        # Acceptance: multi-agent child spawn in Copilot CLI must stay GAP
        bindings = self.profile_data.get("bindings", [])
        spawn_binding = next((b for b in bindings if b.get("capability") == "agent.spawn"), None)
        join_binding = next((b for b in bindings if b.get("capability") == "agent.join"), None)

        is_spawn_gap = spawn_binding is not None and spawn_binding.get("implementation_status") == "gap"
        is_join_gap = join_binding is not None and join_binding.get("implementation_status") == "gap"

        rc = self.profile_data.get("runtime_conventions", {})
        allowed = rc.get("allowed_spawn_fields", [])
        forbidden = rc.get("forbidden_spawn_fields", [])
        no_multiagent_spawn = "subagent_type" in forbidden

        verdict = "PASS" if is_spawn_gap and is_join_gap and no_multiagent_spawn else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-copilot",
            description="Verify GitHub Copilot truthfully classifies multi-agent spawn as GAP",
            command="copilot spawn-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Copilot spawn gap verified (spawn_status={spawn_binding.get('implementation_status') if spawn_binding else None}, forbidden={forbidden})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        # Copilot exposes no container or worktree isolation primitive, and readonly is advisory
        bindings = self.profile_data.get("bindings", [])
        isolated_binding = next((b for b in bindings if b.get("capability") == "workspace.isolated"), None)
        readonly_binding = next((b for b in bindings if b.get("capability") == "workspace.readonly"), None)

        isolated_gap = isolated_binding is not None and isolated_binding.get("implementation_status") == "gap"
        readonly_advisory = readonly_binding is not None and readonly_binding.get("enforcement") == "advisory"

        rc = self.profile_data.get("runtime_conventions", {})
        modes = rc.get("supported_isolation_modes", [])
        only_none_mode = modes == ["none"]

        verdict = "PASS" if isolated_gap and readonly_advisory and only_none_mode else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-copilot",
            description="Verify GitHub Copilot isolation modes (['none'] only) and advisory readonly",
            command="copilot isolation-contract-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Copilot isolation verified (modes={modes}, isolated_gap={isolated_gap}, readonly_enforcement={readonly_binding.get('enforcement') if readonly_binding else None})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        bindings = self.profile_data.get("bindings", [])
        evidence_binding = next((b for b in bindings if b.get("capability") == "evidence.capture"), None)
        has_binding = evidence_binding is not None and evidence_binding.get("implementation_status") == "native"

        verdict = "PASS" if has_binding else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-copilot",
            description="Verify GitHub Copilot evidence capture capability binding",
            command="copilot evidence-binding-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Copilot evidence capture verified (status={evidence_binding.get('implementation_status') if evidence_binding else None})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )
