#!/usr/bin/env python3
"""Tests for per-class confidence calibration policy and margin enforcement.

Validates Requirements R-JEV-01, R-JEV-06, and R-JEV-09:
- Calibration is specific to class and consequence of error (R-JEV-06)
- Universal confidence thresholds (0.70) are explicitly prohibited as a sole gate
- Uncalibrated or unknown classes cannot receive promotion authority
- Multiple probabilities must satisfy minimum separation margin
- Fallback to precomputed baseline is preserved for all failure and edge cases
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    DecisionOutcome,
    FakeDecisionProvider,
    ProviderObservation,
)
from scripts.route_resolver import (
    CLASS_CONFIDENCE_THRESHOLDS,
    RouteResolution,
    resolve_skill_order,
    resolve_skill_order_with_shadow,
)


@pytest.fixture
def grok_profile() -> Dict[str, Any]:
    profile_path = ROOT / "profiles" / "grok.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


class TestClassConfidenceCalibration:
    """Tests for per-class thresholds and margin gates."""

    def test_class_confidence_threshold_registry(self) -> None:
        expected_classes = {
            "defect",
            "explain",
            "performance",
            "prototype",
            "refactor",
            "runtime_diagnosis",
            "trace_diagnosis",
        }
        assert set(CLASS_CONFIDENCE_THRESHOLDS.keys()) == expected_classes

        # Verify consequence-graded ordering
        assert CLASS_CONFIDENCE_THRESHOLDS["defect"] == 0.85
        assert CLASS_CONFIDENCE_THRESHOLDS["runtime_diagnosis"] == 0.85
        assert CLASS_CONFIDENCE_THRESHOLDS["trace_diagnosis"] == 0.85
        assert CLASS_CONFIDENCE_THRESHOLDS["performance"] == 0.80
        assert CLASS_CONFIDENCE_THRESHOLDS["refactor"] == 0.80
        assert CLASS_CONFIDENCE_THRESHOLDS["explain"] == 0.75
        assert CLASS_CONFIDENCE_THRESHOLDS["prototype"] == 0.70

    def test_universal_threshold_rejection_for_higher_consequence_classes(
        self, grok_profile: Dict[str, Any]
    ) -> None:
        """A confidence of 0.72 passes a generic 0.70 threshold, but MUST FAIL for defect (0.85)."""
        query = "Auth endpoint throws 500 on valid credentials"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.72,  # > 0.70 universal threshold, but < 0.85 defect threshold
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        # MUST NOT be promoted
        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_prototype_admits_lower_consequence_threshold(
        self, grok_profile: Dict[str, Any]
    ) -> None:
        """Prototype class has lower consequence of error (0.70 threshold)."""
        query = "Try out a quick spike for graph rendering"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="prototype"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.72,  # >= 0.70 prototype threshold
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == "matched"
        assert res.target == "prototype"
        assert res.advisory_promoted is True

    def test_investigation_adheres_to_explain_threshold(
        self, grok_profile: Dict[str, Any]
    ) -> None:
        """Explain class requires 0.75 threshold."""
        query = "How does the caching layer invalidate stale keys"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # 0.73 is below explain (0.75) -> demote
        obs_below = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="investigation"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.73,
        )
        provider_below = FakeDecisionProvider(canned_observation=obs_below)
        res_below = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider_below, mode="advisory"
        )
        assert res_below.advisory_promoted is False

        # 0.78 is above explain (0.75) -> promote
        obs_above = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="investigation"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.78,
        )
        provider_above = FakeDecisionProvider(canned_observation=obs_above)
        res_above = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider_above, mode="advisory"
        )
        assert res_above.advisory_promoted is True
        assert res_above.target == "investigation"

    def test_decision_margin_gate_rejects_ambiguous_distribution(
        self, grok_profile: Dict[str, Any]
    ) -> None:
        """When probabilities are present, margin between top 2 choices must be >= 0.10."""
        query = "Auth endpoint throws 500 on valid credentials"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # High confidence but razor-thin margin: 0.86 vs 0.83 (margin = 0.03 < 0.10)
        obs_thin = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.86,
            probabilities={"bug-fix": 0.86, "perf-issue": 0.83},
        )
        provider_thin = FakeDecisionProvider(canned_observation=obs_thin)

        res_thin = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider_thin, mode="advisory"
        )
        assert res_thin.advisory_promoted is False

        # Healthy margin: 0.88 vs 0.10 (margin = 0.78 >= 0.10) -> promote
        obs_healthy = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.88,
            probabilities={"bug-fix": 0.88, "perf-issue": 0.10},
        )
        provider_healthy = FakeDecisionProvider(canned_observation=obs_healthy)

        res_healthy = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider_healthy, mode="advisory"
        )
        assert res_healthy.advisory_promoted is True
        assert res_healthy.target == "bug-fix"
