#!/usr/bin/env python3
"""Factory Droid harness native driver.

Thin offline driver: packaging, discovery, and contract checks only.
Model-backed capabilities (role serving, model selection, actual Task
spawn/join/cancel) are never invoked here and stay explicitly untested.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable

REQUIRED_SPAWN_FIELDS = ("subagent_type", "description", "prompt")


class DroidDriver(HarnessDriver):
    """Host driver for Factory Droid harness (offline surfaces only)."""

    def __init__(self, root: Path):
        super().__init__("droid", root)
        self._binary: Optional[Path] = None

    def get_binary_path(self) -> Optional[Path]:
        if self._binary is None:
            extra = [
                Path.home() / ".local" / "bin",
                Path.home() / ".factory" / "bin",
            ]
            self._binary = find_executable("droid", extra)
        return self._binary

    def is_available(self) -> Tuple[bool, str]:
        bin_path = self.get_binary_path()
        if bin_path and bin_path.is_file():
            return True, f"Found droid at {bin_path}"
        return False, "droid CLI binary not found in PATH or ~/.local/bin"

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
            return self.blocked_result("runtime-discover-droid", "Droid offline configuration discovery", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "doctor", "--config", "--json"], cwd=self.root)
        verdict = "PASS" if code == 0 and '"ok": true' in out else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-discover-droid",
            description="Verify Droid offline configuration health via droid doctor --config --json",
            command=f"{bin_path} doctor --config --json",
            exit_code=code,
            stdout=out[:250],
            stderr=err[:250],
            verdict=verdict,
            duration_s=dur,
        )

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-route-playbook-droid", f"Droid playbook routing for '{playbook}'", reason)

        # Droid skill precedence inverts pstack-first hosts: folder/project and
        # personal skills shadow plugin skills. The profile table is advisory.
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
            scenario_id="runtime-route-playbook-droid",
            description=f"Verify Droid advisory skill_order routes '{playbook}' ({target}); native precedence shadows plugin skills",
            command=f"droid route-check --playbook {playbook} -> {target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Advisory-routed '{playbook}' to primary_pstack '{target}' (exists={exists})",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-child-spawn-droid", "Droid spawn contract check", reason)

        # Contract check only: no live spawn (model-backed behavior untested).
        tm = self.profile_data.get("tool_mappings", {})
        rc = self.profile_data.get("runtime_conventions", {})
        allowed = set(rc.get("allowed_spawn_fields", []))
        forbidden = set(rc.get("forbidden_spawn_fields", []))
        has_spawn = str(tm.get("agent_spawn", "")).startswith("Task")
        required_ok = all(f in allowed for f in REQUIRED_SPAWN_FIELDS)
        depth_ok = rc.get("max_subagent_depth", 0) == 1
        leak_ok = not (allowed & forbidden)
        verdict = "PASS" if has_spawn and required_ok and depth_ok and leak_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-child-spawn-droid",
            description="Verify Droid spawn field contract (required fields, depth 1, no per-spawn model/readonly/cwd); no live spawn",
            command="droid spawn-contract-check (profile, offline)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Droid spawn contract verified offline (spawn={tm.get('agent_spawn')}, depth={rc.get('max_subagent_depth')}, live_spawn=untested)",
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        avail, reason = self.is_available()
        if not avail:
            return self.blocked_result("runtime-isolation-droid", "Droid session worktree check", reason)

        bin_path = self.get_binary_path()
        assert bin_path is not None
        code, out, err, dur = self.run_command([str(bin_path), "--help"], cwd=self.root)
        has_worktree = "--worktree" in out
        modes = str(self.profile_data.get("runtime_conventions", {}).get("supported_isolation_modes", []))
        mode_ok = "session-worktree" in modes
        verdict = "PASS" if code == 0 and has_worktree and mode_ok else "FAIL"
        return DriverScenarioResult(
            scenario_id="runtime-isolation-droid",
            description="Verify Droid isolation is session-level worktree only (droid --worktree); no per-spawn isolation",
            command=f"{bin_path} --help (check --worktree)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=f"Droid session worktree flag found={has_worktree}; profile modes={modes}",
            stderr=err,
            verdict=verdict,
            duration_s=dur,
        )

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        # No durable droid receipt exists by design: support_state "candidate"
        # records that model-backed capabilities are untested. The honest
        # evidence binding is the candidate profile plus the gap reference.
        profile_state = self.profile_data.get("support_state")
        gap_ref = self.root / "skills" / "poteto-mode" / "references" / "droid-tools.md"
        ok = profile_state == "candidate" and gap_ref.is_file()
        return DriverScenarioResult(
            scenario_id="runtime-evidence-capture-droid",
            description="Verify Droid evidence binding: candidate profile plus droid-tools.md gap record; no durable runtime receipt by design",
            command=f"check profile support_state=candidate and {gap_ref}",
            exit_code=0 if ok else 1,
            stdout=f"support_state={profile_state}, gap reference exists={gap_ref.is_file()}",
            stderr="",
            verdict="PASS" if ok else "FAIL",
            duration_s=0.01,
        )
