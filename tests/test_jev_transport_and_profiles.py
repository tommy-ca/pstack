#!/usr/bin/env python3
"""Tests for Jev provider profile configurations, System One transport, and safety guards.

Validates Requirements R-JEV-01 through R-JEV-10, addressing:
- #515: single native Python System One transport behind SemanticDecisionProvider
- #519: OpenCode Console/Zen profile configurations and endpoint contracts
- #520: OpenRouter paid profile configuration and pinned models
- #521: Provider parity, free retirement fallback, and explicit paid consent guards
- #517: Model and role fit boundaries preserving baseline authority
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    EgressClass,
    JevDecisionAdapter,
    JevProviderProfile,
    KNOWN_PROFILES,
    ProviderObservation,
    ScoreRange,
    ScoreRequest,
    validate_and_create_safe_context,
)


class TestJevProviderProfiles:
    """Tests for configured provider profiles and endpoint contracts."""

    def test_known_profiles_definitions(self) -> None:
        assert "opencode-console" in KNOWN_PROFILES
        assert "opencode-zen" in KNOWN_PROFILES
        assert "openrouter" in KNOWN_PROFILES
        assert "typesafe-direct" in KNOWN_PROFILES

        zen = KNOWN_PROFILES["opencode-zen"]
        assert zen.api_root == "https://opencode.ai/zen"
        assert zen.configured_model == "jev-1.13-free"
        assert zen.paid is False
        assert zen.credential_env == "OPENCODE_API_KEY"

        console = KNOWN_PROFILES["opencode-console"]
        assert console.api_root == "https://opencode.ai/inference/systemone"
        assert console.configured_model == "jev-1.13-free"
        assert console.paid is False
        assert console.credential_env == "OPENCODE_API_KEY"

        openrouter = KNOWN_PROFILES["openrouter"]
        assert openrouter.api_root == "https://openrouter.ai/api"
        assert openrouter.configured_model == "typesafe/jev-1.14"
        assert openrouter.paid is True
        assert openrouter.credential_env == "OPENROUTER_API_KEY"

        direct = KNOWN_PROFILES["typesafe-direct"]
        assert direct.api_root == "https://api.typesafe.ai"
        assert direct.paid is True
        assert direct.credential_env == "TYPESAFE_API_KEY"

    def test_adapter_profile_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Default fallback to opencode-zen
        monkeypatch.delenv("PSTACK_JEV_PROFILE", raising=False)
        adapter = JevDecisionAdapter(enabled=True)
        assert adapter.profile.profile_id == "opencode-zen"

        # Env override
        monkeypatch.setenv("PSTACK_JEV_PROFILE", "opencode-console")
        adapter_console = JevDecisionAdapter(enabled=True)
        assert adapter_console.profile.profile_id == "opencode-console"

        # Explicit profile string
        adapter_or = JevDecisionAdapter(enabled=True, profile="openrouter")
        assert adapter_or.profile.profile_id == "openrouter"
        assert adapter_or.profile.paid is True

        # Custom JevProviderProfile instance
        custom_prof = JevProviderProfile(
            profile_id="custom-profile",
            api_root="https://custom.example.com",
            configured_model="jev-custom-v1",
            paid=False,
        )
        adapter_custom = JevDecisionAdapter(enabled=True, profile=custom_prof)
        assert adapter_custom.profile.profile_id == "custom-profile"


class TestJevTransportAndGuards:
    """Tests for wire execution, paid guards, failure modes, and response parsing."""

    @pytest.fixture
    def sample_request(self) -> ChoiceRequest:
        ctx = validate_and_create_safe_context("Fix null pointer in auth handler", EgressClass.SAFE_TO_SEND)
        return ChoiceRequest(
            question_id="route_selection",
            context=ctx,
            choices=(
                ChoiceOption("bug-fix", "Bug fix"),
                ChoiceOption("investigation", "Investigation"),
                ChoiceOption("perf-issue", "Performance issue"),
            ),
        )

    def test_paid_consent_guard_blocks_unauthorized_egress(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PSTACK_JEV_ALLOW_PAID", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-mock-key")

        # OpenRouter is a paid profile
        adapter = JevDecisionAdapter(enabled=True, profile="openrouter")

        obs = adapter.decide(sample_request)
        # MUST fail open to unavailable without network egress
        assert obs.outcome.status == "unavailable"
        assert not obs.is_decided()

    def test_paid_consent_guard_allows_when_explicitly_granted(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PSTACK_JEV_ALLOW_PAID", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-mock-key")

        captured: Dict[str, Any] = {}

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            captured["url"] = url
            captured["payload"] = payload
            captured["api_key"] = api_key
            return {
                "model": "typesafe/jev-1.14@20261017",
                "provider": "openrouter",
                "results": [
                    {
                        "id": "route_selection",
                        "selected": "bug-fix",
                        "confidence": 0.94,
                        "probabilities": {"bug-fix": 0.94, "investigation": 0.04, "perf-issue": 0.02},
                    }
                ],
            }

        adapter = JevDecisionAdapter(enabled=True, profile="openrouter", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert obs.outcome.status == "decided"
        assert obs.outcome.value == "bug-fix"
        assert obs.confidence == 0.94
        assert obs.provider_identity == "openrouter"
        assert obs.model_identity == "typesafe/jev-1.14@20261017"

        # Verify wire payload structure
        assert captured["url"] == "https://openrouter.ai/api/v1/systemone"
        assert captured["payload"]["model"] == "typesafe/jev-1.14"
        assert captured["payload"]["state"] == "Fix null pointer in auth handler"
        assert len(captured["payload"]["questions"][0]["options"]) == 3

    def test_opencode_free_wire_contract(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        captured_url = None

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            nonlocal captured_url
            captured_url = url
            return {
                "model": "jev-1.13-free@20261017",
                "provider": "opencode",
                "results": [
                    {
                        "id": "route_selection",
                        "selected": "investigation",
                        "confidence": 0.89,
                        "probabilities": {"investigation": 0.89, "bug-fix": 0.11},
                    }
                ],
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert captured_url == "https://opencode.ai/zen/v1/systemone"
        assert obs.is_decided()
        assert obs.outcome.value == "investigation"
        assert obs.confidence == 0.89
        assert obs.provider_identity == "opencode"

    def test_unrecognized_choice_rejected_as_invalid(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                "model": "jev-1.13-free",
                "results": [
                    {
                        "id": "route_selection",
                        "selected": "unrecognized-playbook-id",
                        "confidence": 0.99,
                    }
                ],
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert obs.outcome.status == "invalid"
        assert not obs.is_decided()

    def test_malformed_response_fails_open(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Any:
            # Not a dictionary or missing results
            return ["malformed", "list"]

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert obs.outcome.status == "invalid"
        assert not obs.is_decided()

    def test_transport_exception_fails_open_to_unavailable(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Any:
            raise ConnectionResetError("Connection dropped by peer")

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert obs.outcome.status == "unavailable"
        assert not obs.is_decided()

    def test_non_choice_request_in_phase_one_abstains(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")
        ctx = validate_and_create_safe_context("Numeric score evaluation")
        score_req = ScoreRequest(
            question_id="score_q", context=ctx, range=ScoreRange(minimum=0.0, maximum=1.0)
        )

        transport_called = False

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Any:
            nonlocal transport_called
            transport_called = True
            return {}

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(score_req)

        assert not transport_called
        assert obs.outcome.status == "abstain"
        assert not obs.is_decided()
