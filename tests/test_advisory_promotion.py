#!/usr/bin/env python3
"""Tests for bounded advisory decision promotion policy behind reversible gate.

Implements Task #189 and ADR-0017 / ADR-0018 requirements:
- Promotes eligible low-risk semantic candidates when evidence is fresh and confidence >= 0.70.
- Explicit direct commands, System-Two playbooks, and slash commands are never overridden.
- Below-threshold confidence, abstention, provider failure, or stale evidence falls back to baseline.
- Mode is fully reversible via PSTACK_JEV_MODE (none | shadow | advisory).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

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
    RouteResolution,
    resolve_skill_order,
    resolve_skill_order_with_shadow,
)


@pytest.fixture
def grok_profile() -> dict:
    profile_path = ROOT / "profiles" / "grok.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


class TestAdvisoryPromotionPolicy:
    """Test suite for advisory promotion gates, safety invariants, and reversibility."""

    def test_promotes_eligible_semantic_candidate_when_confident_and_fresh(
        self, grok_profile: dict
    ) -> None:
        query = "The auth endpoint returns 500 when username contains plus sign"
        baseline = resolve_skill_order(grok_profile, query, ROOT)
        assert baseline.status == "unmatched"

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.88,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == "matched"
        assert res.target == "bug-fix"
        assert res.kind == "playbook"
        assert res.advisory_promoted is True
        assert res.artifact is not None
        assert res.shadow_observation == obs

    def test_below_threshold_confidence_demotes_to_baseline(
        self, grok_profile: dict
    ) -> None:
        query = "The auth endpoint returns 500 when username contains plus sign"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.55,  # Below 0.70 threshold
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False
        assert res.shadow_observation == obs

    def test_explicit_slash_command_never_overridden_by_advisory(
        self, grok_profile: dict
    ) -> None:
        query = "/tdd fix failing test in user service"
        baseline = resolve_skill_order(grok_profile, query, ROOT)
        assert baseline.status == "matched"
        assert baseline.target == "/tdd"

        # Provider claims "bug-fix" with high confidence
        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.99,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        # Baseline explicit command MUST be preserved
        assert res.status == baseline.status
        assert res.target == "/tdd"
        assert res.advisory_promoted is False

    def test_direct_command_bypass_never_overridden_by_advisory(
        self, grok_profile: dict
    ) -> None:
        query = "Babysit"
        baseline = resolve_skill_order(grok_profile, query, ROOT)
        assert baseline.status == "matched"
        assert baseline.target == "playbooks/babysit.md"

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="investigation"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.95,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == "playbooks/babysit.md"
        assert res.advisory_promoted is False

    def test_abstention_demotes_to_baseline(self, grok_profile: dict) -> None:
        query = "Look at the stuff in src/"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="abstain"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=None,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_non_candidate_playbook_rejected_under_scope_gate(
        self, grok_profile: dict
    ) -> None:
        query = "Complex program orchestration query"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        # Provider suggests "feature" (which is system_two, not semantic_candidate)
        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="feature"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.99,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_unknown_provider_identity_rejected_as_stale_evidence(
        self, grok_profile: dict
    ) -> None:
        query = "The auth endpoint returns 500 when username contains plus sign"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="unknown",
            model_identity="jev-pilot-v1",
            confidence=0.90,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_reversible_gate_environment_variable(
        self, grok_profile: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        query = "The auth endpoint returns 500 when username contains plus sign"
        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.92,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        # 1. Mode none: provider not called, baseline returned
        monkeypatch.setenv("PSTACK_JEV_MODE", "none")
        res_none = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=provider)
        assert res_none.advisory_promoted is False
        assert res_none.shadow_observation is None

        # 2. Mode shadow: observation captured, no promotion
        monkeypatch.setenv("PSTACK_JEV_MODE", "shadow")
        res_shadow = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=provider)
        assert res_shadow.advisory_promoted is False
        assert res_shadow.shadow_observation is not None
        assert res_shadow.status == "unmatched"

        # 3. Mode advisory: promoted
        monkeypatch.setenv("PSTACK_JEV_MODE", "advisory")
        res_advisory = resolve_skill_order_with_shadow(grok_profile, query, ROOT, provider=provider)
        assert res_advisory.advisory_promoted is True
        assert res_advisory.target == "bug-fix"
        assert res_advisory.status == "matched"

    def test_provider_exception_fails_open_silently(self, grok_profile: dict) -> None:
        query = "The auth endpoint returns 500 when username contains plus sign"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        failing_provider = FakeDecisionProvider(exception_to_raise=TimeoutError("Remote hung"))
        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=failing_provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_prohibited_pattern_fails_open_silently_in_advisory_mode(
        self, grok_profile: dict
    ) -> None:
        # Query with prohibited bearer token must fail SafeContext validation and fail open
        query = "Fix issue with auth header Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.secret"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.95,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False

    def test_slash_command_query_bypasses_advisory_promotion(
        self, grok_profile: dict
    ) -> None:
        # Query starting with slash command bypasses advisory promotion
        query = "/custom-command do something"
        baseline = resolve_skill_order(grok_profile, query, ROOT)

        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.95,
        )
        provider = FakeDecisionProvider(canned_observation=obs)

        res = resolve_skill_order_with_shadow(
            grok_profile, query, ROOT, provider=provider, mode="advisory"
        )

        assert res.status == baseline.status
        assert res.target == baseline.target
        assert res.advisory_promoted is False
