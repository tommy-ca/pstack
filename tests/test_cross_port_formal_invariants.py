"""Tests for code-linked formal safety/liveness invariants (#909).

Verifies 5 formal invariant properties, their reachable mutants, and external
checker fail-closed behavior without importing foreign runtime code.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.verify_cross_port_invariants as invariants


def test_property_no_duplicate_schedule_holds_and_mutant_fails() -> None:
    # Baseline holds
    assert invariants.check_property_no_duplicate_schedule() is True
    # Mutant is detected
    assert invariants.check_property_no_duplicate_schedule(invariants.mutant_duplicate_schedule_allowed) is False


def test_property_no_pass_on_cancel_holds_and_mutant_fails() -> None:
    # Baseline holds
    assert invariants.check_property_no_pass_on_cancel() is True
    # Mutant is detected
    assert invariants.check_property_no_pass_on_cancel(invariants.mutant_cancel_yields_pass) is False


def test_property_no_privilege_escalation_holds_and_mutant_fails() -> None:
    # Baseline holds
    assert invariants.check_property_no_privilege_escalation() is True
    # Mutant is detected
    assert invariants.check_property_no_privilege_escalation(invariants.mutant_privilege_escalation) is False


def test_property_cleanup_authority_holds_and_mutant_fails() -> None:
    # Baseline holds
    assert invariants.check_property_cleanup_authority() is True
    # Mutant is detected
    assert invariants.check_property_cleanup_authority(invariants.mutant_cleanup_authority) is False


def test_property_evidence_head_binding_holds_and_mutant_fails() -> None:
    # Baseline holds
    assert invariants.check_property_evidence_head_binding() is True
    # Mutant is detected
    assert invariants.check_property_evidence_head_binding(invariants.mutant_evidence_binding) is False


def test_external_checkers_report_blocked_when_absent() -> None:
    status = invariants.check_external_model_checker_status()
    # Missing tools report BLOCKED, never PASS
    for tool, state in status.items():
        assert state in ("AVAILABLE", "BLOCKED")
        assert state != "PASS"


def test_full_invariants_verifier_suite_passes() -> None:
    report = invariants.run_all_formal_invariants()
    assert report["verdict"] == "PASS"
    assert report["all_properties_hold"] is True
    assert report["all_mutants_caught"] is True
    assert len(report["properties"]) == 5
    assert len(report["mutants"]) == 5
