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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class EgressClass(str, Enum):
    """Classification for candidate context before provider dispatch."""

    LOCAL_ONLY = "local_only"
    SAFE_TO_SEND = "safe_to_send"
    DERIVED_SANITIZED = "derived_sanitized"
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


class JevDecisionAdapter(SemanticDecisionProvider):
    """Optional Jev decision provider adapter.

    Guards provider invocation behind an explicit default-OFF feature gate.
    Maps all provider communication, transport failures, and timeouts to
    the neutral outcome contract without raising exceptions to the caller.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        provider_identity: str = "typesafe-jev",
        model_identity: str = "jev-pilot-v1",
        timeout_seconds: float = 2.0,
    ) -> None:
        if enabled is not None:
            self._enabled = enabled
        else:
            # Explicit default-OFF integration gate
            env_val = os.environ.get("PSTACK_JEV_ENABLED", "").strip().lower()
            self._enabled = env_val in ("1", "true", "yes", "on")
        self.provider_identity = provider_identity
        self.model_identity = model_identity
        self.timeout_seconds = timeout_seconds

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
        """Internal invocation hook; overridden by concrete adapters or mocks."""
        # Baseline stub without active wire connection returns abstain or unavailable
        return ProviderObservation(
            outcome=DecisionOutcome(status="abstain"),
            provider_identity=self.provider_identity,
            model_identity=self.model_identity,
            confidence=0.0,
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
        # Default behavior: decide first choice if choice request, else abstain
        if isinstance(request, ChoiceRequest) and request.choices:
            first_choice = request.choices[0]
            return ProviderObservation(
                outcome=DecisionOutcome(status="decided", kind="choice", value=first_choice.id),
                provider_identity=self.provider_identity,
                model_identity=self.model_identity,
                confidence=0.95,
                probabilities={first_choice.id: 0.95},
            )
        return ProviderObservation(
            outcome=DecisionOutcome(status="abstain"),
            provider_identity=self.provider_identity,
            model_identity=self.model_identity,
            confidence=0.5,
        )
