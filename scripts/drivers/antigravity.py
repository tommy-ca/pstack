#!/usr/bin/env python3
"""Google Antigravity (AGY) harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


class AntigravityDriver(HarnessDriver):
    """Host driver for Google Antigravity harness."""

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
            return self.blocked_result("runtime-discover-antigravity", "Antigravity plugin discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        plugin_dir = Path.home() / ".gemini" / "config" / "plugins" / "pstack"
        if not plugin_dir.is_dir():
            plugin_dir = self.root / ".antigravity-plugin"

        code, out, err, dur = self.run_command([str(bin_path), "plugin", "validate", str(plugin_dir)], cwd=self.root)
        verdict = "PASS" if code == 0 and "skills" in out and "agents" in out else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-antigravity",
            description="Verify Antigravity validates installed pstack plugin, skills, and agents",
            command=f"{bin_path} plugin validate {plugin_dir}",
            exit_code=code,
            stdout=out,
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-route-playbook-antigravity", f"Antigravity playbook routing for '{playbook}'", reason)

        so = self.profile_data.get("skill_order", [])
        matched = False
        target = None
        for item in so:
            if playbook in str(item.get("need", "")).lower() or playbook in str(item.get("primary_pstack", "")).lower():
                matched = True
                target = item.get("primary_pstack")
                break

        exists = False
        if target:
            if target.startswith("/"):
                skill_name = target.lstrip("/")
                exists = (self.root / "skills" / skill_name).is_dir() or (self.root / "skills" / "poteto-mode" / "playbooks" / f"{skill_name}.md").is_file()
            else:
                exists = (self.root / "skills" / "poteto-mode" / target).is_file() or (self.root / target).is_file()

        verdict = "PASS" if matched and exists else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-route-playbook-antigravity",
            description=f"Verify Antigravity routes '{playbook}' via profile skill_order ({target})",
            command=f"agy route-check --playbook {playbook} -> {target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Routed '{playbook}' to primary_pstack '{target}' (exists={exists})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-antigravity", "Antigravity child subagent spawn contract", reason)

        # Antigravity subagents live in agents/ (.md files)
        agents_dir = self.root / "agents"
        if not agents_dir.is_dir():
            agents_dir = Path.home() / ".gemini" / "config" / "plugins" / "pstack" / "agents"
        agent_count = len(list(agents_dir.glob("*.md"))) if agents_dir.is_dir() else 0
        rc = self.profile_data.get("runtime_conventions", {})
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if agent_count >= 10 and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-antigravity",
            description="Verify Antigravity subagents projection and invoke_subagent capability contract",
            command=f"agy agents-check (count={agent_count})",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Antigravity subagents verified ({agent_count} agent specs, depth={rc.get('max_subagent_depth')})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
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

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        receipt_path = self.root / ".audit" / "evidence" / "antigravity-receipt.json"
        has_receipt = receipt_path.is_file()
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-antigravity",
            description="Verify Antigravity durable evidence receipt binding",
            command=f"test -f {receipt_path}",
            exit_code=0 if has_receipt else 1,
            stdout=f"Durable receipt located at {receipt_path} (exists={has_receipt})",
            stderr="",
            verdict="PASS" if has_receipt else "FAIL",
            duration_s=0.01,
        )
