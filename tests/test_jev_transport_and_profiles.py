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

    def test_reject_insecure_http_scheme(self) -> None:
        with pytest.raises(ValueError, match="must use 'https' scheme"):
            JevProviderProfile(
                profile_id="insecure-profile",
                api_root="http://api.example.com",
                configured_model="jev-v1",
            )

    def test_reject_loopback_origins(self) -> None:
        for bad_url in ("https://127.0.0.1", "https://localhost", "https://app.localhost", "https://[::1]"):
            with pytest.raises(ValueError, match="disallowed loopback"):
                JevProviderProfile(
                    profile_id="loopback-profile",
                    api_root=bad_url,
                    configured_model="jev-v1",
                )

    def test_reject_cloud_metadata_origins(self) -> None:
        for bad_url in (
            "https://169.254.169.254",
            "https://metadata.google.internal",
            "https://instance-data",
            "https://metadata.azure.com",
        ):
            with pytest.raises(ValueError, match="disallowed"):
                JevProviderProfile(
                    profile_id="metadata-profile",
                    api_root=bad_url,
                    configured_model="jev-v1",
                )

    def test_reject_private_ip_origins(self) -> None:
        for bad_url in ("https://10.0.0.1", "https://192.168.1.1", "https://172.16.0.1"):
            with pytest.raises(ValueError, match="disallowed private IP"):
                JevProviderProfile(
                    profile_id="private-ip-profile",
                    api_root=bad_url,
                    configured_model="jev-v1",
                )

    def test_reject_sensitive_credential_envs(self) -> None:
        for bad_env in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "SSH_AUTH_SOCK", "DATABASE_URL", "PATH"):
            with pytest.raises(ValueError, match="sensitive system/cloud credential"):
                JevProviderProfile(
                    profile_id="credential-leak-profile",
                    api_root="https://api.example.com",
                    configured_model="jev-v1",
                    credential_env=bad_env,
                )

    def test_reject_unprefixed_credential_envs(self) -> None:
        with pytest.raises(ValueError, match="does not match allowed provider prefixes"):
            JevProviderProfile(
                profile_id="unknown-env-profile",
                api_root="https://api.example.com",
                configured_model="jev-v1",
                credential_env="MY_ARBITRARY_TOKEN",
            )

    def test_allow_insecure_origins_flag_for_test_harness(self) -> None:
        # Insecure origin permitted only when explicit allow_insecure_origins=True
        prof = JevProviderProfile(
            profile_id="test-harness",
            api_root="http://127.0.0.1:8080",
            configured_model="jev-test",
            allow_insecure_origins=True,
        )
        assert prof.api_root == "http://127.0.0.1:8080"

    def test_paid_profile_validation_guards(self) -> None:
        with pytest.raises(ValueError, match="max_spend_usd must be non-negative"):
            JevProviderProfile(
                profile_id="bad-paid-spend",
                api_root="https://api.example.com",
                configured_model="jev-v1",
                paid=True,
                max_spend_usd=-1.0,
            )
        with pytest.raises(ValueError, match="reservation_usd must be positive"):
            JevProviderProfile(
                profile_id="bad-reservation",
                api_root="https://api.example.com",
                configured_model="jev-v1",
                paid=True,
                reservation_usd=0.0,
            )


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
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.94,
                        "probabilities": {"bug-fix": 0.94, "investigation": 0.04, "perf-issue": 0.02},
                    }
                },
            }

        adapter = JevDecisionAdapter(enabled=True, profile="openrouter", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)

        assert obs.outcome.status == "decided"
        assert obs.outcome.value == "bug-fix"
        assert obs.confidence == 0.94
        assert obs.provider_identity == "openrouter"
        assert obs.model_identity == "typesafe/jev-1.14@20261017"

        # Verify wire payload structure (official System One mapping contract, #664)
        assert captured["url"] == "https://openrouter.ai/api/v1/systemone"
        assert captured["payload"]["model"] == "typesafe/jev-1.14"
        assert captured["payload"]["state"] == "Fix null pointer in auth handler"
        assert isinstance(captured["payload"]["questions"], dict)
        assert "route_selection" in captured["payload"]["questions"]
        q_spec = captured["payload"]["questions"]["route_selection"]
        assert q_spec["type"] == "choice"
        assert len(q_spec["criteria"]) == 3
        assert q_spec["criteria"]["bug-fix"] == "Bug fix"

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
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "investigation",
                        "confidence": 0.89,
                        "probabilities": {"investigation": 0.89, "bug-fix": 0.11},
                    }
                },
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

    @pytest.mark.parametrize("bad_conf", [float("nan"), float("inf"), float("-inf"), -0.1, 1.1, True, False, "0.9"])
    def test_nonfinite_confidence_rejected_as_invalid(
        self, sample_request: ChoiceRequest, bad_conf: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                "model": "jev-1.13-free",
                "provider": "opencode",
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": bad_conf,
                    }
                },
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)
        assert obs.outcome.status == "invalid"
        assert not obs.is_decided()

    @pytest.mark.parametrize("bad_prob", [float("nan"), float("inf"), float("-inf"), -0.05, 1.2, True, False, "high"])
    def test_nonfinite_probabilities_rejected_as_invalid(
        self, sample_request: ChoiceRequest, bad_prob: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                "model": "jev-1.13-free",
                "provider": "opencode",
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.90,
                        "probabilities": {"bug-fix": bad_prob},
                    }
                },
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)
        assert obs.outcome.status == "invalid"
        assert not obs.is_decided()

    def test_unmatched_question_id_rejected_as_invalid(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                "model": "jev-1.13-free",
                "provider": "opencode",
                "answers": {
                    "unrelated_question_id": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.95,
                    }
                },
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)
        assert obs.outcome.status == "invalid"

    def test_missing_model_or_provider_rejected_as_invalid(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENCODE_API_KEY", "opencode-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                # missing model and provider
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.95,
                    }
                },
            }

        adapter = JevDecisionAdapter(enabled=True, profile="opencode-zen", transport_fn=mock_transport)
        obs = adapter.decide(sample_request)
        assert obs.outcome.status == "invalid"

    def test_paid_spend_budget_enforcement(
        self, sample_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PSTACK_JEV_ALLOW_PAID", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-mock-key")

        call_count = 0

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {
                "model": "typesafe/jev-1.14",
                "provider": "openrouter",
                "usage": {"cost_usd": 0.005},
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.95,
                    }
                },
            }

        # Budget of 0.010 allows exactly 2 calls at 0.005 each
        custom_profile = JevProviderProfile(
            profile_id="openrouter-test",
            api_root="https://openrouter.ai/api",
            configured_model="typesafe/jev-1.14",
            credential_env="OPENROUTER_API_KEY",
            paid=True,
            max_spend_usd=0.010,
        )
        adapter = JevDecisionAdapter(enabled=True, profile=custom_profile, transport_fn=mock_transport)

        # Call 1: spend 0.005 -> cumulative 0.005 <= 0.010
        obs1 = adapter.decide(sample_request)
        assert obs1.is_decided()

        # Call 2: spend 0.005 -> cumulative 0.010 <= 0.010
        obs2 = adapter.decide(sample_request)
        assert obs2.is_decided()

        # Call 3: cumulative 0.010 >= max_spend_usd 0.010 -> blocked before transport
        obs3 = adapter.decide(sample_request)
        assert obs3.outcome.status == "unavailable"
        assert call_count == 2
