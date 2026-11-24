#!/usr/bin/env python3
"""Google Antigravity (AGY) harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from scripts.package_install_staging import stage_antigravity_package
from scripts.prove_antigravity_native_package import run_antigravity_validation

from .base import DriverScenarioResult, HarnessDriver, find_executable


class AntigravityDriver(HarnessDriver):
    """Host driver for Google Antigravity harness."""

    display_name = "Antigravity"
    route_cmd = "agy"

    def __init__(self, root: Path):
        super().__init__("antigravity", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "bin",
            ]
            self._binary = find_executable("agy", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found agy at {bin_path}"
        return False, "agy CLI binary not found in PATH or ~/.local/bin"

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
            return self.blocked_result(
                "runtime-discover-antigravity",
                "Antigravity strict native plugin validation",
                reason,
            )

        bin_path = self.get_binary_path()
        assert bin_path is not None

        staged_dir = run_dir / "staged-antigravity-plugin"
        stage_antigravity_package(staged_dir, source_root=self.root)
        val_pass, report = run_antigravity_validation(staged_dir, agy_bin=bin_path)
        components = report.get("components", {}) if isinstance(report, dict) else {}
        findings = report.get("findings", []) if isinstance(report, dict) else []
        skills_count = components.get("skills", 0)
        agents_count = components.get("agents", 0)
        rules_count = components.get("rules", 0)

        verdict = (
            "PASS"
            if val_pass
            and isinstance(findings, list)
            and len(findings) == 0
            and skills_count >= 65
            and agents_count >= 22
            and rules_count >= 1
            else "FAIL"
        )
        return DriverScenarioResult(
            scenario_id="runtime-discover-antigravity",
            description="Verify Antigravity validates staged pstack plugin strictly with JSON inventory",
            command=f"{bin_path} plugin validate {staged_dir} --strict --json",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"skills={skills_count} agents={agents_count} rules={rules_count} findings={len(findings)}",
            stderr=str(report.get("stderr", "")) if isinstance(report, dict) else "",
            verdict=verdict,
            duration_s=0.05,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result(
                "runtime-child-spawn-antigravity",
                "Antigravity child subagent spawn contract",
                reason,
            )

        bin_path = self.get_binary_path()
        assert bin_path is not None

        agents_dir = self.root / "agents"
        if not agents_dir.is_dir():
            agents_dir = Path.home() / ".gemini" / "config" / "plugins" / "pstack" / "agents"
        agent_count = len(list(agents_dir.glob("*.md"))) if agents_dir.is_dir() else 0

        rc = self.profile_data.get("runtime_conventions", {})
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        forbidden = rc.get("forbidden_spawn_fields", [])
        wire_aliases = rc.get("wire_aliases", {})
        conventions_ok = (
            depth_ok
            and "reasoning_effort" in forbidden
            and wire_aliases.get("view_file") == "read_file"
        )

        code, out, err, dur = self.run_command([str(bin_path), "agents"], cwd=self.root)
        cli_ok = code == 0 and bool(out.strip())

        verdict = "PASS" if agent_count >= 22 and conventions_ok and cli_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-antigravity",
            description="Verify Antigravity subagent projection, spawn constraints, and live agent discovery",
            command=f"{bin_path} agents (repo_agents={agent_count})",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=(
                f"repo_agents={agent_count} depth={rc.get('max_subagent_depth')} "
                f"conventions_ok={conventions_ok} cli_ok={cli_ok}"
            ),
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        rc = self.profile_data.get("runtime_conventions", {})
        iso_modes = rc.get("supported_isolation_modes", [])
        has_branch = "branch" in iso_modes or "worktree" in iso_modes
        has_share = "share" in iso_modes or "shared" in iso_modes
        verdict = "PASS" if has_branch and has_share else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-antigravity",
            description="Verify Antigravity workspace isolation modes (branch, share, inherit)",
            command="agy isolation-check",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Supported isolation modes: {iso_modes}",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )
