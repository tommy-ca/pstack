#!/usr/bin/env python3
"""Tests for host-native harness drivers and runtime plane conformance."""

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import (
    AntigravityDriver,
    CodexDriver,
    GrokDriver,
    HarnessDriver,
    OMPDriver,
    OpenCodeDriver,
    get_driver,
)
loader = importlib.util.spec_from_file_location("verify_portable", ROOT / "scripts" / "verify-portable.py")
assert loader is not None and loader.loader is not None
verify_portable = importlib.util.module_from_spec(loader)
loader.loader.exec_module(verify_portable)
PortableVerifier = verify_portable.PortableVerifier

# These tests interrogate locally installed host CLIs; they do not prove
# real model-backed child spawn/join. Keep them opt-in in generic CI.
HOST_DEPENDENT = os.environ.get("PSTACK_RUN_HOST_DEPENDENT_TESTS") == "1"


def test_get_driver_factory() -> None:
    assert isinstance(get_driver("grok", ROOT), GrokDriver)
    assert isinstance(get_driver("antigravity", ROOT), AntigravityDriver)
    assert isinstance(get_driver("codex", ROOT), CodexDriver)
    assert isinstance(get_driver("omp", ROOT), OMPDriver)
    assert isinstance(get_driver("opencode", ROOT), OpenCodeDriver)

    with pytest.raises(ValueError, match="No native driver registered"):
        get_driver("unsupported_host", ROOT)


@pytest.mark.skipif(not HOST_DEPENDENT, reason="Opt-in host CLI smoke: set PSTACK_RUN_HOST_DEPENDENT_TESTS=1")
@pytest.mark.parametrize("host", ["grok", "antigravity", "codex", "omp", "opencode"])
def test_driver_scenarios(host: str, tmp_path: Path) -> None:
    driver = get_driver(host, ROOT)
    avail, reason = driver.is_available()
    assert avail is True, f"Host {host} should be available: {reason}"

    version = driver.get_version()
    assert version is not None, f"Host {host} should return a version string"
    assert len(version) > 0

    # Discover scenario
    sc_disc = driver.discover(tmp_path)
    assert sc_disc.verdict == "PASS", f"Discover failed for {host}: {sc_disc.stdout} {sc_disc.stderr}"
    assert sc_disc.exit_code == 0

    # Route scenario
    sc_route = driver.route_playbook("feature", tmp_path)
    assert sc_route.verdict == "PASS"

    # Child spawn scenario
    sc_spawn = driver.child_spawn(tmp_path)
    assert sc_spawn.verdict == "PASS"

    # Isolation scenario
    sc_iso = driver.isolation(tmp_path)
    assert sc_iso.verdict == "PASS"

    # Evidence capture scenario
    sc_ev = driver.evidence_capture(tmp_path)
    assert sc_ev.verdict == "PASS"


def test_blocked_driver_fallback(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    # Isolate unavailable-native-driver behavior: the other drive scenarios
    # invoke Bun, shell, and project packaging, none of which is relevant to
    # determining whether an absent host CLI reports BLOCKED.
    def fake_contract_check(scenario_id, desc, plane, cmd, cwd=None):
        result = verify_portable.ScenarioResult(
            id=scenario_id, description=desc, plane=plane,
            command="mock-offline-contract", exit_code=0,
            stdout_snippet="simulated contract PASS",
            verdict="PASS", duration_s=0.0,
        )
        verifier.scenarios.append(result)
        return result

    with (
        patch.object(verifier, "run_command", side_effect=fake_contract_check),
        patch.object(GrokDriver, "is_available", return_value=(False, "simulated missing grok binary")),
    ):
        ok = verifier.drive()
        assert ok is False

        # Verify a scenario with BLOCKED was recorded
        blocked_scenarios = [s for s in verifier.scenarios if s.verdict == "BLOCKED"]
        assert len(blocked_scenarios) >= 1
        assert blocked_scenarios[0].plane == "runtime"
        assert "BLOCKED" in blocked_scenarios[0].stdout_snippet

        receipt = verifier.proof_bar()
        assert receipt.planes["runtime"] == "BLOCKED"
        assert receipt.overall_verdict == "BLOCKED"


@pytest.mark.skipif(not HOST_DEPENDENT, reason="Opt-in host CLI smoke: set PSTACK_RUN_HOST_DEPENDENT_TESTS=1")
def test_reclassified_smoke_tests_planes(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()
    ok = verifier.drive()
    assert ok is True

    scenarios_by_id = {s.id: s for s in verifier.scenarios}

    # Verify planes for reclassified tests
    assert scenarios_by_id["drive-principles-load"].plane == "canonical"
    assert scenarios_by_id["drive-check-plan"].plane == "adapter"
    assert scenarios_by_id["drive-worktree-audit"].plane == "adapter"
    assert scenarios_by_id["drive-verification-skill-scaffold"].plane == "package"
    assert scenarios_by_id["drive-verification-skill-check"].plane == "package"

    # Verify native driver scenarios are in runtime plane
    assert scenarios_by_id["runtime-discover-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-route-playbook-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-child-spawn-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-isolation-grok"].plane == "runtime"
    assert scenarios_by_id["runtime-evidence-capture-grok"].plane == "runtime"
