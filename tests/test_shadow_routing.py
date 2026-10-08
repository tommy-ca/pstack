#!/usr/bin/env python3
"""Tests for zero-behavior-change shadow routing resolution.

Verifies:
- Baseline deterministic route remains identical under all provider states.
- Shadow observation is captured when provider is present and enabled.
- Provider errors, timeouts, or exceptions never break routing.
- Egress boundary rejections fail open safely without raising exceptions.
- Disagreements between provider observation and baseline never alter resolved route.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    FakeDecisionProvider,
    JevDecisionAdapter,
    ProviderObservation,
)
from scripts.route_resolver import (
    RouteResolution,
    resolve_skill_order,
    resolve_skill_order_with_shadow,
)


@pytest.fixture
def grok_profile() -> dict:
    profile_path = ROOT / "profiles" / "grok.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


class TestShadowRoutingInvariants:
    """Tests verifying the zero-behavior-change guarantee of shadow routing."""

    def test_baseline_identical_when_provider_is_none(self, grok_profile: dict) -> None:
        query = "/tdd"
        baseline = resolve_skill_order(grok_profile, query, ROOT)
        shadow_res = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=None)

        assert shadow_res.status == baseline.status
        assert shadow_res.target == baseline.target
        assert shadow_res.kind == baseline.kind
        assert shadow_res.shadow_observation is None

    def test_baseline_identical_when_provider_disagrees(self, grok_profile: dict) -> None:
        query = "/tdd"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # Provider claims "feature" instead of "tdd"
        fake_obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="feature"),
            provider_identity="fake-provider",
            model_identity="fake-model",
            confidence=0.99,
        )
        provider = FakeDecisionProvider(canned_observation=fake_obs)

        shadow_res = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=provider)

        # Acting route remains the baseline route
        assert shadow_res.status == baseline.status
        assert shadow_res.target == baseline.target
        assert shadow_res.kind == baseline.kind
        assert shadow_res.target != "feature"

        # Shadow observation is captured separately
        assert shadow_res.shadow_observation is not None
        assert shadow_res.shadow_observation.outcome.value == "feature"

    def test_provider_exception_fails_open_silently(self, grok_profile: dict) -> None:
        query = "/tdd"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        failing_provider = FakeDecisionProvider(exception_to_raise=RuntimeError("Network crashed"))
        shadow_res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=failing_provider
        )

        assert shadow_res.status == baseline.status
        assert shadow_res.target == baseline.target
        assert shadow_res.shadow_observation is None

    def test_disabled_jev_adapter_captured_safely(self, grok_profile: dict) -> None:
        query = "review this diff"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        adapter = JevDecisionAdapter(enabled=False)
        shadow_res = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=adapter)

        assert shadow_res.status == baseline.status
        assert shadow_res.target == baseline.target
        assert shadow_res.shadow_observation is not None
        assert shadow_res.shadow_observation.outcome.status == "unavailable"

    def test_prohibited_context_fails_open_without_raising(self, grok_profile: dict) -> None:
        # Query with sensitive pattern
        query = "password = 'secret-value-1234'"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        provider = FakeDecisionProvider()
        shadow_res = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=provider)

        # No uncaught ValueError from SafeContext, baseline returned
        assert shadow_res.status == baseline.status
        assert shadow_res.target == baseline.target
        assert shadow_res.shadow_observation is None
