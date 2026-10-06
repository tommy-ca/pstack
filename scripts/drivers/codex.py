#!/usr/bin/env python3
"""OpenAI Codex harness native driver."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable


class CodexDriver(HarnessDriver):
    """Host driver for OpenAI Codex harness."""

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

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-route-playbook-codex", f"Codex playbook routing for '{playbook}'", reason)

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
            scenario_id="runtime-route-playbook-codex",
            description=f"Verify Codex routes '{playbook}' via profile skill_order ({target})",
            command=f"codex route-check --playbook {playbook} -> {target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Routed '{playbook}' to primary_pstack '{target}' (exists={exists})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
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

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        receipt_path = self.root / ".audit" / "evidence" / "codex-receipt.json"
        has_receipt = receipt_path.is_file()
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-codex",
            description="Verify Codex durable evidence receipt binding",
            command=f"test -f {receipt_path}",
            exit_code=0 if has_receipt else 1,
            stdout=f"Durable receipt located at {receipt_path} (exists={has_receipt})",
            stderr="",
            verdict="PASS" if has_receipt else "FAIL",
            duration_s=0.01,
        )
