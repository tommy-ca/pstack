#!/usr/bin/env python3
"""Tests for verdict reduction lattice, proof bar truth, and subprocess bounds.

Verifies:
- Explicit severity lattice: FAIL > BLOCKED > UNTESTED > PASS
- Failure is never masked by BLOCKED
- proof_bar plane and overall reduction truth
- Bounded subprocess execution and timeout handling
- Missing executable handling (BLOCKED, not crash)
- Evidence level preservation
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util
loader = importlib.util.spec_from_file_location("verify_portable", ROOT / "scripts" / "verify-portable.py")
verify_portable = importlib.util.module_from_spec(loader)
loader.loader.exec_module(verify_portable)

reduce_verdicts = verify_portable.reduce_verdicts
ScenarioResult = verify_portable.ScenarioResult
PortableVerifier = verify_portable.PortableVerifier


# --- 1. Severity Lattice Invariants ---


def test_lattice_fail_beats_blocked() -> None:
    assert reduce_verdicts(["FAIL", "BLOCKED"]) == "FAIL"
    assert reduce_verdicts(["BLOCKED", "FAIL"]) == "FAIL"
    assert reduce_verdicts(["FAIL", "BLOCKED", "PASS"]) == "FAIL"
    assert reduce_verdicts(["BLOCKED", "PASS", "FAIL", "UNTESTED"]) == "FAIL"


def test_lattice_blocked_beats_untested_and_pass() -> None:
    assert reduce_verdicts(["BLOCKED", "PASS"]) == "BLOCKED"
    assert reduce_verdicts(["BLOCKED", "UNTESTED"]) == "BLOCKED"
    assert reduce_verdicts(["PASS", "BLOCKED"]) == "BLOCKED"


def test_lattice_untested_beats_pass() -> None:
    assert reduce_verdicts(["UNTESTED", "PASS"]) == "UNTESTED"
    assert reduce_verdicts(["PASS", "UNTESTED"]) == "UNTESTED"


def test_lattice_all_pass_is_pass() -> None:
    assert reduce_verdicts(["PASS"]) == "PASS"
    assert reduce_verdicts(["PASS", "PASS", "PASS"]) == "PASS"


def test_lattice_empty_is_untested() -> None:
    assert reduce_verdicts([]) == "UNTESTED"


# --- 2. proof_bar Mixed Outcomes ---


def test_proof_bar_fail_with_blocked_yields_fail(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    # Canonical plane: 1 PASS, 1 FAIL, 1 BLOCKED -> must be FAIL
    verifier.scenarios.extend([
        ScenarioResult("s1", "pass item", "canonical", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s2", "fail item", "canonical", "false", 1, "failed", "FAIL", 0.01),
        ScenarioResult("s3", "blocked item", "canonical", "none", 127, "blocked", "BLOCKED", 0.01),
        # Adapter plane: BLOCKED
        ScenarioResult("s4", "adapter blocked", "adapter", "none", 127, "blocked", "BLOCKED", 0.01),
        # Package plane: PASS
        ScenarioResult("s5", "package pass", "package", "echo ok", 0, "ok", "PASS", 0.01),
        # Runtime plane: PASS
        ScenarioResult("s6", "runtime pass", "runtime", "echo ok", 0, "ok", "PASS", 0.01),
    ])

    receipt = verifier.proof_bar()
    assert receipt.planes["canonical"] == "FAIL"
    assert receipt.planes["adapter"] == "BLOCKED"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "PASS"
    # Overall must be FAIL, NOT BLOCKED!
    assert receipt.overall_verdict == "FAIL"


def test_proof_bar_blocked_with_pass_yields_blocked(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    verifier.scenarios.extend([
        ScenarioResult("s1", "pass item", "canonical", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s2", "blocked item", "adapter", "none", 127, "blocked", "BLOCKED", 0.01),
        ScenarioResult("s3", "pass item", "package", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s4", "pass item", "runtime", "echo ok", 0, "ok", "PASS", 0.01),
    ])

    receipt = verifier.proof_bar()
    assert receipt.overall_verdict == "BLOCKED"


# --- 3. Subprocess Bounds, Timeouts, and Missing Binaries ---


def test_subprocess_timeout_produces_fail(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-timeout",
        "Command exceeding timeout",
        "adapter",
        ["python3", "-c", "import time; time.sleep(2)"],
        timeout=0.1,
    )
    assert res.verdict == "FAIL"
    assert res.exit_code == 124
    assert "TIMEOUT" in res.stdout_snippet


def test_missing_binary_produces_blocked(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-missing-bin",
        "Command with non-existent binary",
        "runtime",
        ["non_existent_binary_xyz_12345", "--version"],
    )
    assert res.verdict == "BLOCKED"
    assert res.exit_code == 127
    assert "NOT_FOUND" in res.stdout_snippet


def test_evidence_level_preservation(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-level",
        "Command with explicit evidence level",
        "canonical",
        ["echo", "static check"],
        evidence_level="static",
    )
    assert res.evidence_level == "static"

    receipt = verifier.proof_bar()
    scenario = next(s for s in receipt.scenarios if s.id == "test-level")
    assert scenario.evidence_level == "static"
