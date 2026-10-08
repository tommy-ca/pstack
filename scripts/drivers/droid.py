#!/usr/bin/env python3
"""Factory Droid harness native driver.

Thin offline driver: packaging, discovery, and contract checks only.
Model-backed capabilities (role serving, model selection, actual Task
spawn/join/cancel) are never invoked here and stay explicitly untested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .base import DriverScenarioResult, HarnessDriver, find_executable

REQUIRED_SPAWN_FIELDS = ("subagent_type", "description", "prompt")

from ..route_resolver import (
    SkillRoute,
    resolve_primary_artifact as _resolve_primary_artifact,
    resolve_skill_order,
)


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
        return False, "droid CLI binary not found in PATH, ~/.local/bin, or ~/.factory/bin"

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
        route = resolve_skill_order(self.profile_data, playbook, self.root)

        if route.kind == "no-route":
            # Unknown query: report no route honestly. Never present None/null
            # as a routed target and never claim success.
            return DriverScenarioResult(
                scenario_id="runtime-route-playbook-droid",
                description=f"Verify Droid advisory skill_order routing for '{playbook}'; no row matches",
                command=f"offline profile skill_order check (playbook {playbook}; no CLI invocation)",
                exit_code=1,
                stdout=f"No skill_order row matches '{playbook}'; advisory routing declares no route",
                stderr="",
                verdict="FAIL",
                duration_s=0.01,
            )

        if route.kind == "declared-fallback":
            # Null-primary row: resolve the declared fallback as an honest
            # configuration-routing claim (no primary artifact to check).
            routed = route.target is not None
            verdict = "PASS" if routed else "FAIL"
            stdout = (
                f"Null-primary row '{route.need}' routes to declared fallback '{route.target}' (configuration-routing claim; no primary artifact)"
                if routed
                else f"Null-primary row '{route.need}' declares no fallback to route"
            )
        else:
            exists = bool(route.artifact and route.artifact.exists())
            verdict = "PASS" if exists else "FAIL"
            stdout = (
                f"Advisory-routed '{playbook}' to '{route.target}' ({route.artifact}; exists={exists})"
                if exists
                else f"Row '{route.need}' declares '{route.target}' but no artifact exists at {route.artifact}"
            )

        return DriverScenarioResult(
            scenario_id="runtime-route-playbook-droid",
            description=f"Verify Droid advisory skill_order routing for '{playbook}' ({route.target}); native precedence shadows plugin skills",
            command=f"offline profile skill_order check (playbook {playbook} -> {route.target}; no CLI invocation)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
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
            command="offline profile spawn-contract check (no CLI invocation)",
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
            command=f"offline profile support-state check ({gap_ref}; no CLI invocation)",
            exit_code=0 if ok else 1,
            stdout=f"support_state={profile_state}, gap reference exists={gap_ref.is_file()}",
            stderr="",
            verdict="PASS" if ok else "FAIL",
            duration_s=0.01,
        )
