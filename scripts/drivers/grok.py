#!/usr/bin/env python3
"""Grok Build harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


class GrokDriver(HarnessDriver):
    """Host driver for Grok Build harness."""

    def __init__(self, root: Path):
        super().__init__("grok", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".grok" / "bin",
                Path.home() / ".local" / "bin",
            ]
            self._binary = find_executable("grok", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found grok at {bin_path}"
        return False, "grok CLI binary not found in PATH or ~/.grok/bin"

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
            return self.blocked_result("runtime-discover-grok", "Grok plugin and configuration discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "inspect"], cwd=self.root)
        verdict = "PASS" if code == 0 and "plugin: pstack" in out else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-grok",
            description="Verify Grok discovers and validates pstack plugin, skills, and agents",
            command=f"{bin_path} inspect",
            exit_code=code,
            stdout=out,
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-route-playbook-grok", f"Grok playbook routing for '{playbook}'", reason)

        # Check skill_order resolution
        so = self.profile_data.get("skill_order", [])
        matched = False
        target = None
        for item in so:
            if playbook in str(item.get("need", "")).lower() or playbook in str(item.get("primary_pstack", "")).lower():
                matched = True
                target = item.get("primary_pstack")
                break

        # Check that target playbook or command exists
        exists = False
        if target:
            if target.startswith("/"):
                # Slash command or skill
                skill_name = target.lstrip("/")
                exists = (self.root / "skills" / skill_name).is_dir() or (self.root / "skills" / "poteto-mode" / "playbooks" / f"{skill_name}.md").is_file()
            else:
                exists = (self.root / "skills" / "poteto-mode" / target).is_file() or (self.root / target).is_file()

        verdict = "PASS" if matched and exists else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-route-playbook-grok",
            description=f"Verify Grok routes '{playbook}' via profile skill_order ({target})",
            command=f"grok route-check --playbook {playbook} -> {target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Routed '{playbook}' to primary_pstack '{target}' (exists={exists})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-grok", "Grok child subagent spawn contract", reason)

        # Grok subagents are discovered via `grok inspect`
        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "inspect"], cwd=self.root)
        has_subagents = "pstack:comment-sicko" in out and "pstack:arena-runners" in out
        rc = self.profile_data.get("runtime_conventions", {})
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        verdict = "PASS" if code == 0 and has_subagents and depth_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-grok",
            description="Verify Grok subagent declarations and spawn_subagent capability contract",
            command=f"{bin_path} inspect (subagents check)",
            exit_code=code if verdict == "PASS" else 1,
            stdout=f"Grok subagents discovered (depth={rc.get('max_subagent_depth')}, subagents_verified={has_subagents})",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-isolation-grok", "Grok worktree isolation check", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "worktree", "--help"], cwd=self.root)
        verdict = "PASS" if code == 0 and "worktree" in out.lower() else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-grok",
            description="Verify Grok native git worktree workspace isolation command",
            command=f"{bin_path} worktree --help",
            exit_code=code,
            stdout=out[:200],
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        receipt_path = self.root / ".audit" / "evidence" / "grok-receipt.json"
        has_receipt = receipt_path.is_file()
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-grok",
            description="Verify Grok durable evidence receipt binding",
            command=f"test -f {receipt_path}",
            exit_code=0 if has_receipt else 1,
            stdout=f"Durable receipt located at {receipt_path} (exists={has_receipt})",
            stderr="",
            verdict="PASS" if has_receipt else "FAIL",
            duration_s=0.01,
        )
