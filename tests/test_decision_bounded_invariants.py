"""Bounded exhaustive *code-level* safety verification of the JEV routing boundary.

This enumerates a declared, finite state space through the actual production
`resolve_skill_order_with_shadow` function (not a duplicate routing model).
It is NOT an unbounded TLA+/Lean proof, a network test, or proof that arbitrary
caller-controlled summaries are public. Mutation probe demonstrates sensitivity.
"""

from __future__ import annotations

from itertools import product
import json
from pathlib import Path

import pytest

import scripts.route_resolver as routing
from scripts.decision_adapter import (
    DecisionOutcome,
    ProviderObservation,
    SemanticDecisionProvider,
)

ROOT = Path(__file__).resolve().parents[1]

# 5 input route classes x 3 summary classes x 3 modes x 3 observations =
# 135 reachable combinations over the pinned Grok profile and canonical mapping.
ROUTES = {
    "slash": "/tdd fix failing test in user auth",
    "direct": "Babysit",
    "system_two": "Author a SKILL.md",
    "agent": "Read-only spawn",
    "unmatched": "The billing endpoint returns 500 when a subscription is overdue",
}
SUMMARIES = {
    "absent": None,
    "approved_fixture": "Public synthetic fixture: HTTP 500 on invalid user identifier",
    "prohibited": "Authorization: Bearer fake-sensitive-credential",
}
MODES = ("none", "shadow", "advisory")
OBSERVATIONS = ("decided_candidate", "abstain", "outside_scope")
BYPASS_ROUTES = frozenset({"slash", "direct", "system_two", "agent"})


class WitnessProvider(SemanticDecisionProvider):
    def __init__(self, status: str) -> None:
        self.calls = []
        if status == "abstain":
            outcome = DecisionOutcome(status="abstain")
        else:
            outcome = DecisionOutcome(
                status="decided",
                kind="choice",
                value="bug-fix" if status == "decided_candidate" else "feature",
            )
        self.observation = ProviderObservation(
            outcome=outcome,
            provider_identity="typesafe-jev",
            model_identity="jev-pilot-v1",
            confidence=0.92,
            probabilities={"bug-fix": 0.92, "investigation": 0.08}
            if status == "decided_candidate" else None,
        )

    def decide(self, request):
        self.calls.append(request)
        return self.observation


def _check_case(profile: dict, route_class: str, summary_class: str,
                mode: str, provider_status: str) -> None:
    query = ROUTES[route_class]
    safe_summary = SUMMARIES[summary_class]
    baseline = routing.resolve_skill_order(profile, query, ROOT)
    provider = WitnessProvider(provider_status)
    result = routing.resolve_skill_order_with_shadow(
        profile, query, ROOT, provider=provider, mode=mode, safe_summary=safe_summary,
    )
    witness = f"route={route_class}, summary={summary_class}, mode={mode}, provider={provider_status}"

    bypass = (
        mode == "none"
        or route_class in BYPASS_ROUTES
        or summary_class != "approved_fixture"
    )
    if bypass:
        assert len(provider.calls) == 0, f"provider egress on forbidden path: {witness}"
        assert result.advisory_promoted is False, f"promotion on forbidden path: {witness}"

    if mode in ("none", "shadow") or bypass or provider_status != "decided_candidate":
        assert (result.status, result.kind, result.target, result.artifact) == (
            baseline.status, baseline.kind, baseline.target, baseline.artifact
        ), f"baseline changed in noncontrolling path: {witness}"
        assert result.advisory_promoted is False, f"unauthorized promotion: {witness}"

    for req in provider.calls:
        assert req.context.content == SUMMARIES["approved_fixture"], (
            f"raw query or prohibited summary leaked: {witness}"
        )


def test_bounded_jev_routing_safety_state_space() -> None:
    profile = json.loads((ROOT / "profiles" / "grok.json").read_text(encoding="utf-8"))
    for route_class, summary_class, mode, status in product(
        ROUTES, SUMMARIES, MODES, OBSERVATIONS,
    ):
        _check_case(profile, route_class, summary_class, mode, status)


def test_bypass_mutation_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    """Negative control: remove early preflight and the real-code check must fail."""
    profile = json.loads((ROOT / "profiles" / "grok.json").read_text(encoding="utf-8"))
    _check_case(profile, "slash", "approved_fixture", "shadow", "decided_candidate")
    with monkeypatch.context() as mutated:
        mutated.setattr(routing, "_is_egress_bypassed", lambda *_a, **_kw: False)
        with pytest.raises(AssertionError, match="provider egress on forbidden path"):
            _check_case(profile, "slash", "approved_fixture", "shadow", "decided_candidate")
    _check_case(profile, "slash", "approved_fixture", "shadow", "decided_candidate")
