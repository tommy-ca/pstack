#!/usr/bin/env python3
"""Base classes and scenario contracts for host-native harness drivers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DriverScenarioResult:
    scenario_id: str
    description: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    verdict: str  # "PASS", "FAIL", "BLOCKED"
    duration_s: float
    evidence_level: str = "offline"
    settlement: Optional[Dict[str, str]] = None
    live_attempted: bool = False

    @property
    def stdout_snippet(self) -> str:
        s = self.stdout.strip()
        if not s:
            s = self.stderr.strip()
        return s[:300]

    def to_scenario_result(self, plane: str = "runtime") -> Any:
        """Convert this driver result to a ScenarioResult."""
        from scripts.portability_types import ScenarioResult

        return ScenarioResult(
            id=self.scenario_id,
            description=self.description,
            plane=plane,
            command=self.command,
            exit_code=self.exit_code,
            stdout_snippet=self.stdout_snippet,
            verdict=self.verdict,
            duration_s=self.duration_s,
            evidence_level=self.evidence_level,
            settlement=self.settlement,
            live_attempted=self.live_attempted,
        )


def to_scenario_result(result: DriverScenarioResult, plane: str = "runtime") -> Any:
    """Convert a DriverScenarioResult to a ScenarioResult."""
    return result.to_scenario_result(plane=plane)


def find_executable(name: str, extra_search_dirs: Optional[List[Path]] = None) -> Optional[Path]:
    """Find executable in PATH or standard user install locations."""
    which_path = shutil.which(name)
    if which_path:
        p = Path(which_path).absolute()
        if p.is_file() and os.access(p, os.X_OK):
            return p

    if extra_search_dirs:
        for base_dir in extra_search_dirs:
            if not base_dir.is_dir():
                continue
            # Check direct child first
            direct = base_dir / name
            if direct.is_file() and os.access(direct, os.X_OK):
                return direct.absolute()
            # Check recursive search
            for match in base_dir.rglob(name):
                if match.is_file() and os.access(match, os.X_OK):
                    return match.absolute()
    return None


class HarnessDriver(ABC):
    """Abstract base class for host-native agent harness drivers.

    Each host driver owns:
    - Host binary detection and version querying
    - Invocation syntax and CLI execution
    - Host-native verification scenarios (discover, route, spawn, isolation, evidence)
    """

    display_name: str = ""
    route_cmd: Optional[str] = None
    route_requires_available: bool = True
    is_advisory_routing: bool = False

    def __init__(self, host: str, root: Path):
        self.host = host
        self.root = root
        self._profile_data: Optional[Dict] = None

    @property
    def host_id(self) -> str:
        return self.host.split(":")[-1]

    @property
    def effective_display_name(self) -> str:
        if self.display_name:
            return self.display_name
        name_map = {
            "antigravity": "Antigravity",
            "codex": "Codex",
            "grok": "Grok",
            "opencode": "OpenCode",
            "omp": "OMP",
            "claude": "Claude Code",
            "copilot": "Copilot",
            "droid": "Droid",
        }
        return name_map.get(self.host_id, self.host_id.capitalize())

    @property
    def effective_route_cmd(self) -> str:
        if self.route_cmd:
            return self.route_cmd
        if self.host_id == "antigravity":
            return "agy"
        return self.host_id

    @property
    def profile_data(self) -> Dict:
        if self._profile_data is None:
            from scripts.setup_pstack import resolve_profiles_dir

            profiles_dir = resolve_profiles_dir(self.root)
            profile_path = profiles_dir / f"{self.host}.json"
            if not profile_path.is_file() and ":" in self.host:
                alt_path = profiles_dir / f"{self.host.split(':')[-1]}.json"
                if alt_path.is_file():
                    profile_path = alt_path
            if profile_path.is_file():
                try:
                    self._profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
                except Exception:
                    self._profile_data = {}
            else:
                self._profile_data = {}
        return self._profile_data

    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Check if the harness binary or execution runtime is available."""
        pass

    @abstractmethod
    def get_binary_path(self) -> Optional[Path]:
        """Return the path to the harness CLI binary if found."""
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """Query and return the live host version string."""
        pass

    def run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
    ) -> Tuple[int, str, str, float]:
        start = time.time()
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd or self.root,
                capture_output=True,
                text=True,
                env=merged_env,
                check=False,
                timeout=timeout,
            )
            duration = round(time.time() - start, 3)
            return proc.returncode, proc.stdout, proc.stderr, duration
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start, 3)
            return 124, "", f"TIMEOUT: Command exceeded {timeout}s limit", duration
        except FileNotFoundError as exc:
            duration = round(time.time() - start, 3)
            return 127, "", f"NOT_FOUND: {exc}", duration
        except Exception as exc:
            duration = round(time.time() - start, 3)
            return 1, "", f"ERROR: {exc}", duration

    def blocked_result(self, scenario_id: str, desc: str, reason: str) -> DriverScenarioResult:
        return DriverScenarioResult(
            scenario_id=scenario_id,
            description=desc,
            command=f"check-harness-availability --host {self.host}",
            exit_code=127,
            stdout=f"BLOCKED: Host harness '{self.host}' is unavailable ({reason})",
            stderr="",
            verdict="BLOCKED",
            duration_s=0.0,
        )

    @abstractmethod
    def discover(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Live harness discovers and validates pstack plugin or configuration."""
        pass

    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Live harness routes representative playbook under its native conventions."""
        if self.route_requires_available:
            avail, reason = self.is_available()
            if not avail:
                return self.blocked_result(
                    f"runtime-route-playbook-{self.host_id}",
                    f"{self.effective_display_name} playbook routing for '{playbook}'",
                    reason,
                )

        try:
            from ..route_resolver import resolve_skill_order
        except (ImportError, ValueError):
            from scripts.route_resolver import resolve_skill_order

        route = resolve_skill_order(self.profile_data, playbook, self.root)
        if self.is_advisory_routing:
            return self._route_playbook_advisory(playbook, route)
        return self._route_playbook_standard(playbook, route)

    def _route_playbook_advisory(self, playbook: str, route: Any) -> DriverScenarioResult:
        if route.kind == "no-route":
            return DriverScenarioResult(
                scenario_id=f"runtime-route-playbook-{self.host_id}",
                description=f"Verify {self.effective_display_name} advisory skill_order routing for '{playbook}'; no row matches",
                command=f"offline profile skill_order check (playbook {playbook}; no CLI invocation)",
                exit_code=1,
                stdout=f"No skill_order row matches '{playbook}'; advisory routing declares no route",
                stderr="",
                verdict="FAIL",
                duration_s=0.01,
            )

        if route.kind == "declared-fallback":
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
            scenario_id=f"runtime-route-playbook-{self.host_id}",
            description=f"Verify {self.effective_display_name} advisory skill_order routing for '{playbook}' ({route.target}); native precedence shadows plugin skills",
            command=f"offline profile skill_order check (playbook {playbook} -> {route.target}; no CLI invocation)",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
            stderr="",
            verdict=verdict,
            duration_s=0.01,
        )

    def _route_playbook_standard(self, playbook: str, route: Any) -> DriverScenarioResult:
        if route.kind == "no-route":
            return DriverScenarioResult(
                scenario_id=f"runtime-route-playbook-{self.host_id}",
                description=f"Verify {self.effective_display_name} routes '{playbook}' via profile skill_order",
                command=f"{self.effective_route_cmd} route-check --playbook {playbook}",
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
            scenario_id=f"runtime-route-playbook-{self.host_id}",
            description=f"Verify {self.effective_display_name} routes '{playbook}' via profile skill_order ({route.target})",
            command=f"{self.effective_route_cmd} route-check --playbook {playbook} -> {route.target}",
            exit_code=0 if verdict == "PASS" else 1,
            stdout=stdout,
            stderr=route.error_reason,
            verdict=verdict,
            duration_s=0.01,
        )

    @abstractmethod
    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify child spawn capability against native harness bindings and conventions."""
        pass

    @abstractmethod
    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify workspace isolation contract (e.g. worktree, readonly)."""
        pass

    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify evidence capture binding for this host."""
        receipt_path = self.root / ".audit" / "evidence" / f"{self.host_id}-receipt.json"
        has_receipt = receipt_path.is_file()
        return DriverScenarioResult(
            scenario_id=f"runtime-evidence-capture-{self.host_id}",
            description=f"Verify {self.effective_display_name} durable evidence receipt binding",
            command=f"test -f {receipt_path}",
            exit_code=0 if has_receipt else 1,
            stdout=f"Durable receipt located at {receipt_path} (exists={has_receipt})",
            stderr="",
            verdict="PASS" if has_receipt else "FAIL",
            duration_s=0.01,
        )
