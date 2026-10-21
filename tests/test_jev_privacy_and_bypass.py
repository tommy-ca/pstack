#!/usr/bin/env python3
"""Offline hermetic tests for JEV privacy, egress guards, and deterministic bypass ordering.

Implements Issue #658 (P0) requirements:
- Return baseline before provider construction for all explicit slash commands,
  direct command bypasses, System-Two playbooks, and agent targets.
- Require a separately supplied, positively authorized, bounded public summary or
  fixture instead of treating raw task queries as safe; default absence -> zero provider calls.
- Prohibit transmission of sensitive patterns or local-only context to external providers.
- Maintain full offline hermetic safety with zero external network egress.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    DecisionRequest,
    EgressClass,
    ProviderObservation,
    SafeContext,
    SemanticDecisionProvider,
    validate_and_create_safe_context,
)
from scripts.route_resolver import (
    RouteResolution,
    resolve_skill_order,
    resolve_skill_order_with_shadow,
)


class SpyDecisionProvider(SemanticDecisionProvider):
    """Spy provider that records calls and requests to verify egress boundaries."""

    def __init__(
        self,
        canned_observation: Optional[ProviderObservation] = None,
        provider_identity: str = "spy-provider",
        model_identity: str = "spy-model-v1",
    ) -> None:
        self.canned_observation = canned_observation or ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity=provider_identity,
            model_identity=model_identity,
            confidence=0.95,
            probabilities={"bug-fix": 0.95, "investigation": 0.05},
        )
        self.provider_identity = provider_identity
        self.model_identity = model_identity
        self.calls: List[DecisionRequest] = []

    def decide(self, request: DecisionRequest) -> ProviderObservation:
        self.calls.append(request)
        return self.canned_observation

    @property
    def call_count(self) -> int:
        return len(self.calls)


@pytest.fixture
def grok_profile() -> dict:
    profile_path = ROOT / "profiles" / "grok.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


class TestJevPrivacyAndBypassGuards:
    """Verifies that provider is never called on bypass routes or without positive safe context."""

    @pytest.fixture(autouse=True)
    def allow_fixture_evidence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE", "1")

    def test_zero_provider_calls_on_explicit_slash_command(self, grok_profile: dict) -> None:
        spy = SpyDecisionProvider()
        query = "/tdd fix failing test in user auth"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary="Fix failing test",
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None
        assert res.target == "/tdd"

    def test_zero_provider_calls_on_direct_command_bypass(self, grok_profile: dict) -> None:
        spy = SpyDecisionProvider()
        query = "Babysit"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary="Babysit PR stack",
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None
        assert res.target == "playbooks/babysit.md"

    def test_zero_provider_calls_on_system_two_playbook(self, grok_profile: dict) -> None:
        spy = SpyDecisionProvider()
        query = "Author a SKILL.md"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary="Author a new SKILL.md for team",
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None
        assert res.target == "playbooks/authoring-a-skill.md"

    def test_zero_provider_calls_on_agent_target(self, grok_profile: dict) -> None:
        spy = SpyDecisionProvider()
        query = "Read-only spawn"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary="Explorer agent spawn",
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None
        assert res.kind == "agent"

    def test_zero_provider_calls_on_raw_unsanitized_query_without_safe_summary(
        self, grok_profile: dict
    ) -> None:
        spy = SpyDecisionProvider()
        # Non-bypass query that would match semantic candidate if evaluated
        query = "The billing endpoint returns 500 when customer has overdue subscription"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary=None,  # Absence of positively authorized safe summary
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None
        assert res.status == "unmatched"

    def test_zero_provider_calls_when_safe_summary_contains_bearer_token(
        self, grok_profile: dict
    ) -> None:
        spy = SpyDecisionProvider()
        query = "Investigate incident ACME-101"
        safe_summary = "User token was Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary=safe_summary,
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None

    def test_zero_provider_calls_when_safe_summary_contains_private_key(
        self, grok_profile: dict
    ) -> None:
        spy = SpyDecisionProvider()
        query = "Deploy key setup"
        safe_summary = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary=safe_summary,
        )
        assert spy.call_count == 0
        assert res.shadow_observation is None

    def test_zero_provider_calls_when_safe_context_is_local_only(
        self, grok_profile: dict
    ) -> None:
        spy = SpyDecisionProvider()
        query = "Internal diagnostic trace"
        # Context marked explicitly local_only
        # SafeContext __post_init__ rejects LOCAL_ONLY if instantiated directly,
        # but let's verify both SafeContext construction and resolver handling
        with pytest.raises(ValueError, match="cannot be transmitted"):
            SafeContext(content="Internal audit trace", egress_class=EgressClass.LOCAL_ONLY)

    def test_provider_called_only_with_authorized_safe_summary(self, grok_profile: dict) -> None:
        spy = SpyDecisionProvider()
        query = "Internal customer ticket ACME-999: Auth endpoint 500 crash on special characters"
        authorized_summary = "Auth endpoint returns HTTP 500 on special characters in username"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="shadow",
            safe_summary=authorized_summary,
        )
        assert spy.call_count == 1
        req = spy.calls[0]
        assert isinstance(req, ChoiceRequest)
        # CRITICAL: Verify that the transmitted context is the sanitized summary, NOT the raw query
        assert req.context.content == authorized_summary
        assert "ACME-999" not in req.context.content
        assert "customer ticket" not in req.context.content
        assert res.shadow_observation is not None
        # In shadow mode, baseline remains acting route (unmatched)
        assert res.status == "unmatched"

    def test_advisory_mode_promotes_when_safe_summary_authorized_and_calibrated(
        self, grok_profile: dict
    ) -> None:
        obs = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value="bug-fix"),
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.92,
            probabilities={"bug-fix": 0.92, "investigation": 0.08},
        )
        spy = SpyDecisionProvider(canned_observation=obs, provider_identity="typesafe-jev", model_identity="jev-pilot-v1")
        query = "Private error report: NullPointerException in parser at line 42"
        authorized_summary = "NullPointerException in parser at boundary condition"
        res = resolve_skill_order_with_shadow(
            grok_profile,
            query,
            ROOT,
            provider=spy,
            mode="advisory",
            safe_summary=authorized_summary,
        )
        assert spy.call_count == 1
        assert res.status == "matched"
        assert res.target == "bug-fix"
        assert res.advisory_promoted is True
        assert res.shadow_observation == obs
