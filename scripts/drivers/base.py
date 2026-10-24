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
from typing import Dict, List, Optional, Tuple


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


from scripts.portability_types import ScenarioResult

if not hasattr(ScenarioResult, "from_driver_result"):
    @classmethod
    def _from_driver_result(cls: Any, res: Any, plane: str = "runtime") -> Any:
        if hasattr(res, "to_scenario_result"):
            return res.to_scenario_result(plane=plane)
        return cls(
            id=getattr(res, "scenario_id", getattr(res, "id", "")),
            description=res.description,
            plane=plane,
            command=res.command,
            exit_code=res.exit_code,
            stdout_snippet=res.stdout_snippet,
            verdict=res.verdict,
            duration_s=res.duration_s,
            evidence_level=getattr(res, "evidence_level", "offline"),
            settlement=getattr(res, "settlement", None),
            live_attempted=getattr(res, "live_attempted", False),
        )

    setattr(ScenarioResult, "from_driver_result", _from_driver_result)


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

    def __init__(self, host: str, root: Path):
        self.host = host
        self.root = root
        self._profile_data: Optional[Dict] = None

    @property
    def profile_data(self) -> Dict:
        if self._profile_data is None:
            profile_path = self.root / "profiles" / f"{self.host}.json"
            if not profile_path.is_file() and ":" in self.host:
                alt_path = self.root / "profiles" / f"{self.host.split(':')[-1]}.json"
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

    @abstractmethod
    def route_playbook(self, playbook: str, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Live harness routes representative playbook under its native conventions."""
        pass

    @abstractmethod
    def child_spawn(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify child spawn capability against native harness bindings and conventions."""
        pass

    @abstractmethod
    def isolation(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify workspace isolation contract (e.g. worktree, readonly)."""
        pass

    @abstractmethod
    def evidence_capture(self, run_dir: Path) -> DriverScenarioResult:
        """Scenario: Verify evidence capture binding for this host."""
        pass
