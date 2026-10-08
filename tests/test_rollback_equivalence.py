#!/usr/bin/env python3
"""Tests for Jev kill-switch and fail-open rollback equivalence verifier."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_rollback_equivalence import (
    run_all_rollback_scenarios,
    verify_scenario_abstention,
    verify_scenario_below_threshold,
    verify_scenario_gate_off,
    verify_scenario_malformed_result,
    verify_scenario_provider_timeout,
    verify_scenario_provider_unavailable,
    verify_scenario_receipt_failure,
    verify_scenario_stale_evidence,
)


@pytest.fixture
def fixtures_and_profile():
    corpus_file = ROOT / "tests" / "fixtures" / "decision_corpus.json"
    fixtures = json.loads(corpus_file.read_text(encoding="utf-8")).get("fixtures", [])
    profile_path = ROOT / "profiles" / "grok.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    return fixtures, profile


class TestRollbackEquivalence:
    """Test suite proving baseline equivalence across all 8 failure scenarios."""

    def test_run_all_rollback_scenarios_passes(self) -> None:
        report = run_all_rollback_scenarios(ROOT)
        failures = [(s.scenario_name, s.failure_reasons) for s in report.scenarios if s.verdict != "PASS"]
        assert report.overall_verdict == "PASS", f"Scenarios failed: {failures}"
        assert report.total_scenarios == 8
        assert report.scenarios_passed == 8
        for scenario in report.scenarios:
            assert scenario.verdict == "PASS"
            assert scenario.equivalent_to_baseline is True
            assert scenario.latency_budget_met is True
            assert len(scenario.failure_reasons) == 0

    def test_gate_off_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_gate_off(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_provider_unavailable_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_provider_unavailable(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_provider_timeout_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_provider_timeout(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_malformed_result_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_malformed_result(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_abstention_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_abstention(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_below_threshold_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_below_threshold(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_stale_evidence_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_stale_evidence(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True

    def test_receipt_failure_scenario(self, fixtures_and_profile) -> None:
        fixtures, profile = fixtures_and_profile
        verdict = verify_scenario_receipt_failure(fixtures, profile, ROOT)
        assert verdict.verdict == "PASS"
        assert verdict.equivalent_to_baseline is True
