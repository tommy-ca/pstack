#!/usr/bin/env python3
"""Provider-neutral semantic decision adapter and egress boundary.

Implements the single-operation SemanticDecisionProvider contract defined in
openspec/specs/pstack-jev-decisions/spec.md. Provides strict egress boundary
validation, default-OFF feature gating, and fail-open exception handling.
Shared pstack code does not import wire types or provider-specific SDKs.
"""

from __future__ import annotations

import ipaddress
import json
import math
import os
import re
import threading
import urllib.error
import urllib.parse
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


ALLOWED_CREDENTIAL_PREFIXES: Tuple[str, ...] = ("OPENCODE_", "OPENROUTER_", "TYPESAFE_", "JEV_", "PSTACK_")
DISALLOWED_CREDENTIAL_ENVS: frozenset[str] = frozenset({
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "SSH_AUTH_SOCK",
    "SSH_PRIVATE_KEY",
    "DATABASE_URL",
    "DB_PASSWORD",
    "PATH",
    "HOME",
    "USER",
    "SHELL",
    "TERM",
})
DISALLOWED_HOSTS: frozenset[str] = frozenset({
    "localhost",
    "instance-data",
    "metadata.google.internal",
    "metadata.azure.com",
    "metadata.packet.net",
    "metadata",
})


def validate_provider_api_root(api_root: str, allow_insecure_origins: bool = False) -> None:
    """Validate that provider api_root uses HTTPS and targets a permitted remote origin (#683)."""
    raw = api_root.strip()
    if not raw:
        raise ValueError("Provider api_root cannot be empty")

    parsed = urllib.parse.urlparse(raw)
    if not allow_insecure_origins and parsed.scheme != "https":
        raise ValueError(
            f"Provider api_root must use 'https' scheme (got '{parsed.scheme}://'). "
            "Plaintext HTTP is rejected to prevent credential leakage."
        )

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        raise ValueError(f"Provider api_root '{raw}' lacks a valid hostname")

    if not allow_insecure_origins:
        if hostname in DISALLOWED_HOSTS or hostname.endswith(".localhost"):
            raise ValueError(
                f"Provider api_root hostname '{hostname}' is a disallowed loopback or cloud metadata target (#683)"
            )

        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_loopback:
                raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed loopback address (#683)")
            if ip.is_private:
                raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed private IP address (#683)")
            if ip.is_link_local:
                raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed link-local/cloud-metadata IP address (#683)")
            if ip.is_unspecified or ip.is_multicast or ip.is_reserved:
                raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed reserved/multicast IP address (#683)")
        except ValueError as exc:
            if "disallowed" in str(exc):
                raise


def validate_credential_env_name(env_name: str) -> None:
    """Ensure credential environment variable name conforms to provider allowlist (#683)."""
    raw = env_name.strip()
    if not raw:
        raise ValueError("credential_env cannot be empty")
    if raw in DISALLOWED_CREDENTIAL_ENVS:
        raise ValueError(
            f"credential_env '{raw}' is a sensitive system/cloud credential and cannot be transmitted to provider endpoints (#683)"
        )
    if not any(raw.startswith(prefix) for prefix in ALLOWED_CREDENTIAL_PREFIXES):
        raise ValueError(
            f"credential_env '{raw}' does not match allowed provider prefixes: {ALLOWED_CREDENTIAL_PREFIXES} (#683)"
        )


@dataclass(frozen=True)
class JevProviderProfile:
    """Configuration profile for a System One decision endpoint."""

    profile_id: str
    api_root: str
    configured_model: str
    credential_env: str = "OPENCODE_API_KEY"
    paid: bool = False
    max_spend_usd: float = 0.0
    reservation_usd: float = 0.005
    allow_insecure_origins: bool = False

    def __post_init__(self) -> None:
        validate_provider_api_root(self.api_root, allow_insecure_origins=self.allow_insecure_origins)
        validate_credential_env_name(self.credential_env)
        if self.paid:
            if self.max_spend_usd < 0.0 or not math.isfinite(self.max_spend_usd):
                raise ValueError(f"Paid provider profile max_spend_usd must be non-negative finite float (got {self.max_spend_usd})")
            if self.reservation_usd <= 0.0 or not math.isfinite(self.reservation_usd):
                raise ValueError(f"Paid provider profile reservation_usd must be positive finite float (got {self.reservation_usd})")


class SpendLedger:
    """Thread-safe atomic budget reservation and settlement ledger (#677, #680, #682).

    Distinction:
    This ledger provides local, process-level thread-safe admission control based on preflight
    reservation. It guarantees that local requests will not be dispatched if local estimated
    spend exceeds max_spend_usd.

    However, without a provider-enforced account-level quota or hard provider charge ceiling,
    an external provider may return actual usage exceeding the reservation.
    """

    def __init__(self, max_spend_usd: float, reservation_usd: float = 0.005) -> None:
        self.max_spend_usd = float(max_spend_usd)
        self.reservation_usd = float(reservation_usd)
        self.cumulative_spend_usd = 0.0
        self.reserved_spend_usd = 0.0
        self.overshoot_count = 0
        self._lock = threading.Lock()

    @property
    def is_overspent(self) -> bool:
        """Return True if cumulative spend has exceeded max_spend_usd (#682)."""
        with self._lock:
            return self.cumulative_spend_usd > self.max_spend_usd + 1e-9

    def reserve(self, amount: Optional[float] = None) -> bool:
        amt = self.reservation_usd if amount is None else float(amount)
        if amt <= 0.0 or not math.isfinite(amt):
            return False
        with self._lock:
            if self.cumulative_spend_usd + self.reserved_spend_usd + amt > self.max_spend_usd + 1e-9:
                return False
            self.reserved_spend_usd += amt
            return True

    def settle(self, reserved_amount: Optional[float] = None, actual_cost: Optional[float] = None) -> float:
        amt = self.reservation_usd if reserved_amount is None else float(reserved_amount)
        with self._lock:
            self.reserved_spend_usd = max(0.0, self.reserved_spend_usd - amt)
            if actual_cost is None or not math.isfinite(actual_cost) or actual_cost < 0.0:
                cost = amt
            else:
                cost = float(actual_cost)

            # Record overshoot if provider billed more than reserved amount (#682)
            if cost > amt + 1e-9:
                self.overshoot_count += 1

            self.cumulative_spend_usd += cost
            return cost

    def release(self, reserved_amount: Optional[float] = None) -> None:
        amt = self.reservation_usd if reserved_amount is None else float(reserved_amount)
        with self._lock:
            self.reserved_spend_usd = max(0.0, self.reserved_spend_usd - amt)

    def reset(self, cumulative_spend_usd: float = 0.0, reserved_spend_usd: float = 0.0) -> None:
        """Reset ledger state with internal synchronization (#677, #680)."""
        with self._lock:
            self.cumulative_spend_usd = float(cumulative_spend_usd)
            self.reserved_spend_usd = float(reserved_spend_usd)
            self.overshoot_count = 0

    def set_cumulative_spend(self, val: float) -> None:
        """Thread-safe setter for cumulative spend (#677, #680)."""
        with self._lock:
            self.cumulative_spend_usd = float(val)


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


def _parse_unit_interval(val: Any) -> Optional[float]:
    """Parse and strictly validate a finite float in [0.0, 1.0], rejecting booleans."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    num = float(val)
    if not math.isfinite(num) or num < 0.0 or num > 1.0:
        return None
    return num


class JevDecisionAdapter(SemanticDecisionProvider):
    """Optional Jev decision provider adapter.

    Guards provider invocation behind an explicit default-OFF feature gate.
    Maps all provider communication, transport failures, and timeouts to
    the neutral outcome contract without raising exceptions to the caller.
    """

    @staticmethod
    def _invalid_obs(provider: str = "unknown", model: str = "unknown") -> ProviderObservation:
        return ProviderObservation(
            outcome=DecisionOutcome(status="invalid"),
            provider_identity=provider,
            model_identity=model,
        )

    def _obs(self, status: str, confidence: float = 0.0) -> ProviderObservation:
        """Helper to construct self-bound ProviderObservation instances."""
        return ProviderObservation(
            outcome=DecisionOutcome(status=status),
            provider_identity=self.provider_identity,
            model_identity=self.model_identity,
            confidence=confidence,
        )

    def __init__(
        self,
        enabled: Optional[bool] = None,
        profile: Optional[Union[str, JevProviderProfile]] = None,
        provider_identity: str = "typesafe-jev",
        model_identity: str = "jev-pilot-v1",
        timeout_seconds: float = 2.0,
        transport_fn: Optional[Callable[[str, Dict[str, Any], str], Dict[str, Any]]] = None,
        spend_ledger: Optional[SpendLedger] = None,
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

        if spend_ledger is not None:
            self.spend_ledger = spend_ledger
        else:
            reservation = getattr(self.profile, "reservation_usd", 0.005)
            self.spend_ledger = SpendLedger(
                max_spend_usd=self.profile.max_spend_usd,
                reservation_usd=reservation,
            )

    @property
    def cumulative_spend_usd(self) -> float:
        return self.spend_ledger.cumulative_spend_usd

    @cumulative_spend_usd.setter
    def cumulative_spend_usd(self, val: float) -> None:
        self.spend_ledger.set_cumulative_spend(val)

    @property
    def reserved_spend_usd(self) -> float:
        return self.spend_ledger.reserved_spend_usd

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
            return self._obs("abstain")

        # Check API key credentials before reservation
        api_key = os.environ.get(self.profile.credential_env, "").strip()
        if not api_key and self._transport_fn is None:
            # Baseline stub without active wire connection returns abstain or unavailable
            return self._obs("abstain")

        # Paid consent and atomic budget reservation guards (Issue #660, #677)
        is_reserved = False
        if self.profile.paid:
            allow_paid = os.environ.get("PSTACK_JEV_ALLOW_PAID", "").strip().lower()
            if allow_paid not in ("1", "true", "yes", "on"):
                return self._obs("unavailable")
            if self.profile.max_spend_usd <= 0.0:
                return self._obs("unavailable")
            if not self.spend_ledger.reserve():
                return self._obs("unavailable")
            is_reserved = True

        # Official System One wire format (Issue #664):
        # questions is a mapping keyed by question ID with type, instructions, criteria
        payload: Dict[str, Any] = {
            "model": self.profile.configured_model,
            "state": request.context.content,
            "questions": {
                request.question_id: {
                    "type": "choice",
                    "instructions": "Select the appropriate route candidate",
                    "criteria": {c.id: c.label for c in request.choices},
                }
            },
        }

        base = self.profile.api_root.rstrip("/")
        url = f"{base}/v1/systemone"

        actual_cost: Optional[float] = None
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

            parsed_obs = self._parse_provider_response(request, resp_data)
            if isinstance(resp_data, dict):
                usage = resp_data.get("usage")
                if isinstance(usage, dict) and "cost_usd" in usage:
                    try:
                        c = float(usage["cost_usd"])
                        if math.isfinite(c) and c >= 0.0:
                            actual_cost = c
                    except (ValueError, TypeError):
                        pass
            return parsed_obs
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            return self._obs("unavailable")
        except Exception:
            return self._obs("invalid")
        finally:
            if self.profile.paid and is_reserved:
                self.spend_ledger.settle(actual_cost=actual_cost)

    def _parse_provider_response(
        self, request: ChoiceRequest, data: Dict[str, Any]
    ) -> ProviderObservation:
        """Parse and strictly validate System One JSON response."""
        if not isinstance(data, dict):
            return self._invalid_obs(self.provider_identity, self.model_identity)

        resp_model = data.get("model")
        resp_provider = data.get("provider")
        # Require non-empty model and provider identity (Issue #660)
        if not resp_model or not resp_provider or not str(resp_model).strip() or not str(resp_provider).strip():
            return self._invalid_obs(str(resp_provider or "unknown"), str(resp_model or "unknown"))
        resp_model_str = str(resp_model).strip()
        resp_provider_str = str(resp_provider).strip()

        # Official System One answers format (Issue #664) with legacy results fallback
        ans: Optional[Dict[str, Any]] = None
        answers = data.get("answers")
        if isinstance(answers, dict):
            if request.question_id in answers and isinstance(answers[request.question_id], dict):
                ans = answers[request.question_id]
            else:
                return self._invalid_obs(resp_provider_str, resp_model_str)
        elif isinstance(data.get("results"), list) and data["results"]:
            cand = data["results"][0]
            if isinstance(cand, dict):
                # Verify matching question id if present
                if "id" in cand and cand["id"] != request.question_id:
                    return self._invalid_obs(resp_provider_str, resp_model_str)
                ans = cand

        if ans is None or not isinstance(ans, dict):
            return self._invalid_obs(resp_provider_str, resp_model_str)

        selected = ans.get("choice") or ans.get("selected")
        valid_choice_ids = {c.id for c in request.choices}
        if selected not in valid_choice_ids:
            return self._invalid_obs(resp_provider_str, resp_model_str)

        # Validate finite [0, 1] confidence (Issue #660)
        confidence_val = ans.get("confidence")
        confidence: Optional[float] = None
        if confidence_val is not None:
            confidence = _parse_unit_interval(confidence_val)
            if confidence is None:
                return self._invalid_obs(resp_provider_str, resp_model_str)

        # Validate finite [0, 1] probabilities dictionary (Issue #660)
        probabilities_val = ans.get("probabilities")
        probabilities: Optional[Dict[str, float]] = None
        if probabilities_val is not None:
            if not isinstance(probabilities_val, dict):
                return self._invalid_obs(resp_provider_str, resp_model_str)
            probabilities = {}
            for opt_id, p_val in probabilities_val.items():
                if opt_id not in valid_choice_ids:
                    return self._invalid_obs(resp_provider_str, resp_model_str)
                p_float = _parse_unit_interval(p_val)
                if p_float is None:
                    return self._invalid_obs(resp_provider_str, resp_model_str)
                probabilities[opt_id] = p_float

        return ProviderObservation(
            outcome=DecisionOutcome(
                status="decided",
                kind="choice",
                value=str(selected),
            ),
            provider_identity=resp_provider_str,
            model_identity=resp_model_str,
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
