#!/usr/bin/env python3
"""Provider-neutral semantic decision adapter and egress boundary.

Implements the single-operation SemanticDecisionProvider contract defined in
openspec/specs/pstack-jev-decisions/spec.md. Provides strict egress boundary
validation, default-OFF feature gating, and fail-open exception handling.
Shared pstack code does not import wire types or provider-specific SDKs.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class EgressClass(str, Enum):
    """Classification for candidate context before provider dispatch."""

    LOCAL_ONLY = "local_only"
    SAFE_TO_SEND = "safe_to_send"
    DERIVED_SANITIZED = "derived_sanitized"
    PUBLIC_BENCHMARK = "public_benchmark"
    PROHIBITED = "prohibited"


# Conservative policy ceilings defined in spec
MAX_CONTEXT_BYTES = 2048
MAX_CHOICES_COUNT = 32
MAX_CHOICE_ID_BYTES = 64
MAX_CHOICE_LABEL_BYTES = 128
MAX_TOTAL_REQUEST_BYTES = 8192

_PROHIBITED_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"][^\s'\"]+"),
    re.compile(r"^diff --git a/.* b/.*", re.MULTILINE),
    re.compile(r"^index [0-9a-f]{7,40}\.\.[0-9a-f]{7,40}", re.MULTILINE),
]


@dataclass(frozen=True)
class SafeContext:
    """Validated sanitized context string satisfying egress boundary policy."""

    content: str
    egress_class: EgressClass

    def __post_init__(self) -> None:
        raw_bytes = self.content.encode("utf-8")
        if len(raw_bytes) > MAX_CONTEXT_BYTES:
            raise ValueError(
                f"Context exceeds maximum allowed size of {MAX_CONTEXT_BYTES} bytes (got {len(raw_bytes)})"
            )
        if self.egress_class in (EgressClass.LOCAL_ONLY, EgressClass.PROHIBITED):
            raise ValueError(f"Context egress class '{self.egress_class}' cannot be transmitted to provider")
        for pattern in _PROHIBITED_PATTERNS:
            if pattern.search(self.content):
                raise ValueError("Context contains prohibited sensitive or raw artifact patterns")


def validate_and_create_safe_context(
    raw_content: str,
    egress_class: Union[EgressClass, str] = EgressClass.SAFE_TO_SEND,
) -> SafeContext:
    """Validate raw context string against egress rules and return SafeContext."""
    if isinstance(egress_class, str):
        egress_class = EgressClass(egress_class)
    return SafeContext(content=raw_content, egress_class=egress_class)


@dataclass(frozen=True)
class ChoiceOption:
    """Non-empty choice identifier and label pair."""

    id: str
    label: str

    def __post_init__(self) -> None:
        id_bytes = self.id.encode("utf-8")
        label_bytes = self.label.encode("utf-8")
        if not self.id.strip():
            raise ValueError("Choice ID cannot be empty")
        if not self.label.strip():
            raise ValueError("Choice label cannot be empty")
        if len(id_bytes) > MAX_CHOICE_ID_BYTES:
            raise ValueError(f"Choice ID exceeds {MAX_CHOICE_ID_BYTES} bytes")
        if len(label_bytes) > MAX_CHOICE_LABEL_BYTES:
            raise ValueError(f"Choice label exceeds {MAX_CHOICE_LABEL_BYTES} bytes")


@dataclass(frozen=True)
class ScoreRange:
    """Bounded score range."""

    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if self.minimum >= self.maximum:
            raise ValueError(f"Score minimum ({self.minimum}) must be less than maximum ({self.maximum})")


@dataclass(frozen=True)
class ChoiceRequest:
    """Choice decision request over a non-empty list of candidate options."""

    question_id: str
    context: SafeContext
    choices: Tuple[ChoiceOption, ...]
    kind: str = "choice"

    def __post_init__(self) -> None:
        if not self.choices:
            raise ValueError("Choices list cannot be empty")
        if len(self.choices) > MAX_CHOICES_COUNT:
            raise ValueError(f"Choices count exceeds limit of {MAX_CHOICES_COUNT}")


@dataclass(frozen=True)
class ScoreRequest:
    """Numeric score request over a bounded range."""

    question_id: str
    context: SafeContext
    range: ScoreRange
    kind: str = "score"


@dataclass(frozen=True)
class BooleanRequest:
    """Binary boolean decision request."""

    question_id: str
    context: SafeContext
    kind: str = "boolean"


DecisionRequest = Union[ChoiceRequest, ScoreRequest, BooleanRequest]


@dataclass(frozen=True)
class DecisionOutcome:
    """Outcome of a provider judgment."""

    status: str  # "decided", "abstain", "unavailable", "invalid"
    kind: Optional[str] = None  # "choice", "score", "boolean", or None
    value: Any = None

    def __post_init__(self) -> None:
        valid_statuses = {"decided", "abstain", "unavailable", "invalid"}
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid outcome status: {self.status}")
        if self.status == "decided":
            if self.kind not in {"choice", "score", "boolean"}:
                raise ValueError("Decided outcome must declare kind ('choice', 'score', or 'boolean')")
            if self.kind == "choice" and not isinstance(self.value, str):
                raise ValueError("Decided choice outcome must have string value")
            if self.kind == "score" and not isinstance(self.value, (int, float)):
                raise ValueError("Decided score outcome must have numeric value")
            if self.kind == "boolean" and not isinstance(self.value, bool):
                raise ValueError("Decided boolean outcome must have boolean value")
        else:
            if self.value is not None:
                raise ValueError(f"Non-decided outcome ({self.status}) cannot carry a decided value")


@dataclass
class ProviderObservation:
    """Observation returned by a semantic decision provider."""

    outcome: DecisionOutcome
    provider_identity: str
    model_identity: str
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None

    def is_decided(self) -> bool:
        return self.outcome.status == "decided"


class SemanticDecisionProvider(ABC):
    """Abstract base provider exposing the single decide operation."""

    @abstractmethod
    def decide(self, request: DecisionRequest) -> ProviderObservation:
        """Execute one bounded decision judgment."""
        pass


@dataclass(frozen=True)
class JevProviderProfile:
    """Configuration profile for a System One decision endpoint."""

    profile_id: str
    api_root: str
    configured_model: str
    credential_env: str = "OPENCODE_API_KEY"
    paid: bool = False
    max_spend_usd: float = 0.0


KNOWN_PROFILES: Dict[str, JevProviderProfile] = {
    "opencode-console": JevProviderProfile(
        profile_id="opencode-console",
        api_root="https://opencode.ai/inference/systemone",
        configured_model="jev-1.13-free",
        credential_env="OPENCODE_API_KEY",
        paid=False,
    ),
    "opencode-zen": JevProviderProfile(
        profile_id="opencode-zen",
        api_root="https://opencode.ai/zen",
        configured_model="jev-1.13-free",
        credential_env="OPENCODE_API_KEY",
        paid=False,
    ),
    "openrouter": JevProviderProfile(
        profile_id="openrouter",
        api_root="https://openrouter.ai/api",
        configured_model="typesafe/jev-1.14",
        credential_env="OPENROUTER_API_KEY",
        paid=True,
        max_spend_usd=1.0,
    ),
    "typesafe-direct": JevProviderProfile(
        profile_id="typesafe-direct",
        api_root="https://api.typesafe.ai",
        configured_model="jev-1.13",
        credential_env="TYPESAFE_API_KEY",
        paid=True,
        max_spend_usd=1.0,
    ),
}


class JevDecisionAdapter(SemanticDecisionProvider):
    """Optional Jev decision provider adapter.

    Guards provider invocation behind an explicit default-OFF feature gate.
    Maps all provider communication, transport failures, and timeouts to
    the neutral outcome contract without raising exceptions to the caller.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        profile: Optional[Union[str, JevProviderProfile]] = None,
        provider_identity: str = "typesafe-jev",
        model_identity: str = "jev-pilot-v1",
        timeout_seconds: float = 2.0,
        transport_fn: Optional[Callable[[str, Dict[str, Any], str], Dict[str, Any]]] = None,
    ) -> None:
        if enabled is not None:
            self._enabled = enabled
        else:
            # Explicit default-OFF integration gate
            env_val = os.environ.get("PSTACK_JEV_ENABLED", "").strip().lower()
            self._enabled = env_val in ("1", "true", "yes", "on")

        # Resolve provider profile
        if isinstance(profile, JevProviderProfile):
            self.profile = profile
        elif isinstance(profile, str) and profile in KNOWN_PROFILES:
            self.profile = KNOWN_PROFILES[profile]
        else:
            profile_name = os.environ.get("PSTACK_JEV_PROFILE", "").strip()
            self.profile = KNOWN_PROFILES.get(profile_name, KNOWN_PROFILES["opencode-zen"])

        self.provider_identity = provider_identity
        self.model_identity = model_identity
        self.timeout_seconds = timeout_seconds
        self._transport_fn = transport_fn

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def decide(self, request: DecisionRequest) -> ProviderObservation:
        """Execute decision request against Jev provider, or fail open safely."""
        if not self._enabled:
            return ProviderObservation(
                outcome=DecisionOutcome(status="unavailable"),
                provider_identity=self.provider_identity,
                model_identity="none",
            )

        # Validate total request size
        serialized_len = len(repr(request).encode("utf-8"))
        if serialized_len > MAX_TOTAL_REQUEST_BYTES:
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )

        try:
            return self._invoke_provider(request)
        except TimeoutError:
            return ProviderObservation(
                outcome=DecisionOutcome(status="unavailable"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )
        except Exception:
            return ProviderObservation(
                outcome=DecisionOutcome(status="unavailable"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )

    def _invoke_provider(self, request: DecisionRequest) -> ProviderObservation:
        """Internal invocation hook implementing System One wire protocol."""
        # Phase 1: Only ChoiceRequest is invoked
        if not isinstance(request, ChoiceRequest):
            return ProviderObservation(
                outcome=DecisionOutcome(status="abstain"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
                confidence=0.0,
            )

        # Paid consent guard
        if self.profile.paid:
            allow_paid = os.environ.get("PSTACK_JEV_ALLOW_PAID", "").strip().lower()
            if allow_paid not in ("1", "true", "yes", "on"):
                return ProviderObservation(
                    outcome=DecisionOutcome(status="unavailable"),
                    provider_identity=self.provider_identity,
                    model_identity=self.model_identity,
                )

        # Check API key credentials
        api_key = os.environ.get(self.profile.credential_env, "").strip()
        if not api_key and self._transport_fn is None:
            # Baseline stub without active wire connection returns abstain or unavailable
            return ProviderObservation(
                outcome=DecisionOutcome(status="abstain"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
                confidence=0.0,
            )

        payload: Dict[str, Any] = {
            "model": self.profile.configured_model,
            "state": request.context.content,
            "questions": [
                {
                    "id": request.question_id,
                    "type": "choice",
                    "options": [{"id": c.id, "label": c.label} for c in request.choices],
                }
            ],
        }

        base = self.profile.api_root.rstrip("/")
        url = f"{base}/v1/systemone"

        try:
            if self._transport_fn is not None:
                resp_data = self._transport_fn(url, payload, api_key)
            else:
                body = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url=url,
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "User-Agent": "pstack-jev-client/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    resp_bytes = resp.read()
                    resp_data = json.loads(resp_bytes.decode("utf-8"))

            return self._parse_provider_response(request, resp_data)
        except urllib.error.HTTPError:
            return ProviderObservation(
                outcome=DecisionOutcome(status="unavailable"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )
        except (urllib.error.URLError, TimeoutError, OSError):
            return ProviderObservation(
                outcome=DecisionOutcome(status="unavailable"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )
        except Exception:
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )

    def _parse_provider_response(
        self, request: ChoiceRequest, data: Dict[str, Any]
    ) -> ProviderObservation:
        """Parse and strictly validate System One JSON response."""
        if not isinstance(data, dict):
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
            )

        resp_model = str(data.get("model") or self.profile.configured_model)
        resp_provider = str(data.get("provider") or self.profile.profile_id)

        results = data.get("results")
        if not isinstance(results, list) or not results:
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=resp_provider,
                model_identity=resp_model,
            )

        res = results[0]
        if not isinstance(res, dict):
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=resp_provider,
                model_identity=resp_model,
            )

        selected = res.get("selected")
        valid_choice_ids = {c.id for c in request.choices}
        if selected not in valid_choice_ids:
            return ProviderObservation(
                outcome=DecisionOutcome(status="invalid"),
                provider_identity=resp_provider,
                model_identity=resp_model,
            )

        confidence_val = res.get("confidence")
        confidence = float(confidence_val) if isinstance(confidence_val, (int, float)) else None

        probabilities_val = res.get("probabilities")
        probabilities: Optional[Dict[str, float]] = None
        if isinstance(probabilities_val, dict):
            probabilities = {
                str(k): float(v)
                for k, v in probabilities_val.items()
                if isinstance(v, (int, float))
            }

        return ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="choice", value=str(selected)),
            provider_identity=resp_provider,
            model_identity=resp_model,
            confidence=confidence,
            probabilities=probabilities,
        )


class FakeDecisionProvider(SemanticDecisionProvider):
    """Test-substitutable provider for deterministic offline evaluations."""

    def __init__(
        self,
        canned_observation: Optional[ProviderObservation] = None,
        exception_to_raise: Optional[Exception] = None,
        provider_identity: str = "fake-provider",
        model_identity: str = "mock-model-v1",
    ) -> None:
        self.canned_observation = canned_observation
        self.exception_to_raise = exception_to_raise
        self.provider_identity = provider_identity
        self.model_identity = model_identity
        self.recorded_requests: List[DecisionRequest] = []

    def decide(self, request: DecisionRequest) -> ProviderObservation:
        self.recorded_requests.append(request)
        if self.exception_to_raise:
            raise self.exception_to_raise
        if self.canned_observation:
            return self.canned_observation
        # Default behavior: decide matching choice if choice request, else abstain
        if isinstance(request, ChoiceRequest) and request.choices:
            ctx_lower = request.context.content.lower()
            if any(term in ctx_lower for term in ("stuff", "capital of france", "what is")):
                return ProviderObservation(
                    outcome=DecisionOutcome(status="abstain"),
                    provider_identity=self.provider_identity,
                    model_identity=self.model_identity,
                    confidence=0.1,
                )
            selected = None
            if any(k in ctx_lower for k in ("500", "crash", "defect", "regression")):
                selected = next((c for c in request.choices if c.id == "bug-fix"), None)
            elif any(k in ctx_lower for k in ("how does", "explain", "investigate", "why")):
                selected = next((c for c in request.choices if c.id == "investigation"), None)
            elif any(k in ctx_lower for k in ("prototype", "spike", "mock up", "sketch")):
                selected = next((c for c in request.choices if c.id == "prototype"), None)
            elif any(k in ctx_lower for k in ("duplicate", "extract", "clean")):
                selected = next((c for c in request.choices if c.id == "refactoring"), None)
            elif any(k in ctx_lower for k in ("latency", "slow", "ms on invoice")):
                selected = next((c for c in request.choices if c.id == "perf-issue"), None)

            if not selected:
                selected = request.choices[0]

            return ProviderObservation(
                outcome=DecisionOutcome(status="decided", kind="choice", value=selected.id),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
                confidence=0.95,
                probabilities={selected.id: 0.95},
            )
        return ProviderObservation(
            outcome=DecisionOutcome(status="abstain"),
            provider_identity=self.provider_identity,
            model_identity=self.model_identity,
            confidence=0.5,
        )
