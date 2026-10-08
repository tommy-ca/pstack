import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.decision_adapter import (
    BooleanRequest,
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    EgressClass,
    FakeDecisionProvider,
    JevDecisionAdapter,
    MAX_CHOICE_ID_BYTES,
    MAX_CHOICE_LABEL_BYTES,
    MAX_CHOICES_COUNT,
    MAX_CONTEXT_BYTES,
    ProviderObservation,
    SafeContext,
    ScoreRange,
    ScoreRequest,
    validate_and_create_safe_context,
)


class TestSafeContextAndEgress:
    """Tests for egress boundary validation and SafeContext enforcement."""

    def test_valid_safe_context(self) -> None:
        ctx = validate_and_create_safe_context("Explain the plan", EgressClass.SAFE_TO_SEND)
        assert ctx.content == "Explain the plan"
        assert ctx.egress_class == EgressClass.SAFE_TO_SEND

    def test_context_exceeding_byte_limit_rejected(self) -> None:
        oversized = "a" * (MAX_CONTEXT_BYTES + 1)
        with pytest.raises(ValueError, match="Context exceeds maximum"):
            validate_and_create_safe_context(oversized)

    def test_local_only_and_prohibited_classes_rejected(self) -> None:
        with pytest.raises(ValueError, match="cannot be transmitted"):
            validate_and_create_safe_context("test", EgressClass.LOCAL_ONLY)

        with pytest.raises(ValueError, match="cannot be transmitted"):
            validate_and_create_safe_context("test", EgressClass.PROHIBITED)

    def test_prohibited_patterns_rejected(self) -> None:
        # Private key
        with pytest.raises(ValueError, match="prohibited sensitive"):
            validate_and_create_safe_context("-----BEGIN RSA PRIVATE KEY-----\nMIIE...")

        # Bearer token
        with pytest.raises(ValueError, match="prohibited sensitive"):
            validate_and_create_safe_context("Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...")

        # Git diff header
        with pytest.raises(ValueError, match="prohibited sensitive"):
            validate_and_create_safe_context("diff --git a/foo.py b/foo.py\nindex 1234567..89abcdef")

        # Secret / password
        with pytest.raises(ValueError, match="prohibited sensitive"):
            validate_and_create_safe_context("api_key = 'sk-1234567890abcdef'")


class TestDecisionShapes:
    """Tests for typed decision request and outcome invariants."""

    def test_choice_option_validation(self) -> None:
        opt = ChoiceOption(id="opt1", label="Option 1")
        assert opt.id == "opt1"

        with pytest.raises(ValueError, match="ID cannot be empty"):
            ChoiceOption(id="", label="Option 1")

        with pytest.raises(ValueError, match="label cannot be empty"):
            ChoiceOption(id="opt1", label="")

        with pytest.raises(ValueError, match="ID exceeds"):
            ChoiceOption(id="x" * (MAX_CHOICE_ID_BYTES + 1), label="Label")

        with pytest.raises(ValueError, match="label exceeds"):
            ChoiceOption(id="opt1", label="y" * (MAX_CHOICE_LABEL_BYTES + 1))

    def test_choice_request_validation(self) -> None:
        ctx = validate_and_create_safe_context("Task description")
        opts = (ChoiceOption(id="a", label="A"), ChoiceOption(id="b", label="B"))
        req = ChoiceRequest(question_id="q1", context=ctx, choices=opts)
        assert req.kind == "choice"

        with pytest.raises(ValueError, match="cannot be empty"):
            ChoiceRequest(question_id="q1", context=ctx, choices=())

        excessive_opts = tuple(ChoiceOption(id=f"o{i}", label=f"Option {i}") for i in range(MAX_CHOICES_COUNT + 1))
        with pytest.raises(ValueError, match="Choices count exceeds limit"):
            ChoiceRequest(question_id="q1", context=ctx, choices=excessive_opts)

    def test_score_request_validation(self) -> None:
        ctx = validate_and_create_safe_context("Task description")
        rng = ScoreRange(minimum=0.0, maximum=1.0)
        req = ScoreRequest(question_id="q1", context=ctx, range=rng)
        assert req.kind == "score"

        with pytest.raises(ValueError, match="must be less than maximum"):
            ScoreRange(minimum=1.0, maximum=0.5)

    def test_boolean_request(self) -> None:
        ctx = validate_and_create_safe_context("Task description")
        req = BooleanRequest(question_id="q1", context=ctx)
        assert req.kind == "boolean"

    def test_decision_outcome_invariants(self) -> None:
        # Valid decided outcomes
        dec_choice = DecisionOutcome(status="decided", kind="choice", value="opt1")
        assert dec_choice.status == "decided"
        assert dec_choice.value == "opt1"

        dec_score = DecisionOutcome(status="decided", kind="score", value=0.85)
        assert dec_score.value == 0.85

        dec_bool = DecisionOutcome(status="decided", kind="boolean", value=True)
        assert dec_bool.value is True

        # Non-decided outcomes cannot have value
        with pytest.raises(ValueError, match="cannot carry a decided value"):
            DecisionOutcome(status="abstain", value="some-value")

        with pytest.raises(ValueError, match="cannot carry a decided value"):
            DecisionOutcome(status="unavailable", value=123)

        # Invalid outcome kind/type combinations
        with pytest.raises(ValueError, match="must have string value"):
            DecisionOutcome(status="decided", kind="choice", value=123)

        with pytest.raises(ValueError, match="must have numeric value"):
            DecisionOutcome(status="decided", kind="score", value="high")

        with pytest.raises(ValueError, match="must have boolean value"):
            DecisionOutcome(status="decided", kind="boolean", value="yes")

        with pytest.raises(ValueError, match="Invalid outcome status"):
            DecisionOutcome(status="unknown_status")


class TestJevDecisionAdapter:
    """Tests for JevDecisionAdapter configuration and fail-open semantics."""

    def test_default_off_gate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PSTACK_JEV_ENABLED", raising=False)
        adapter = JevDecisionAdapter()
        assert not adapter.is_enabled

        ctx = validate_and_create_safe_context("Route this")
        req = ChoiceRequest(
            question_id="q1",
            context=ctx,
            choices=(ChoiceOption("a", "A"), ChoiceOption("b", "B")),
        )
        obs = adapter.decide(req)
        assert obs.outcome.status == "unavailable"
        assert obs.model_identity == "none"

    def test_explicit_enabled_gate(self) -> None:
        adapter = JevDecisionAdapter(enabled=True)
        assert adapter.is_enabled

        ctx = validate_and_create_safe_context("Route this")
        req = ChoiceRequest(
            question_id="q1",
            context=ctx,
            choices=(ChoiceOption("a", "A"), ChoiceOption("b", "B")),
        )
        obs = adapter.decide(req)
        assert obs.outcome.status == "abstain"
        assert obs.model_identity == "jev-pilot-v1"

    def test_timeout_and_exceptions_fail_open_to_unavailable(self) -> None:
        class FailingAdapter(JevDecisionAdapter):
            def _invoke_provider(self, request):
                raise TimeoutError("Provider timed out after 2000ms")

        adapter = FailingAdapter(enabled=True)
        ctx = validate_and_create_safe_context("Route this")
        req = BooleanRequest(question_id="q1", context=ctx)
        obs = adapter.decide(req)

        assert obs.outcome.status == "unavailable"
        assert not obs.is_decided()


class TestFakeDecisionProvider:
    """Tests for FakeDecisionProvider test double."""

    def test_default_choice_resolution(self) -> None:
        provider = FakeDecisionProvider()
        ctx = validate_and_create_safe_context("Route this")
        req = ChoiceRequest(
            question_id="q1",
            context=ctx,
            choices=(ChoiceOption("opt_x", "Option X"), ChoiceOption("opt_y", "Option Y")),
        )
        obs = provider.decide(req)

        assert obs.is_decided()
        assert obs.outcome.value == "opt_x"
        assert len(provider.recorded_requests) == 1

    def test_canned_observation(self) -> None:
        canned = ProviderObservation(
            outcome=DecisionOutcome(status="decided", kind="boolean", value=False),
            provider_identity="test-provider",
            model_identity="test-model",
            confidence=0.88,
        )
        provider = FakeDecisionProvider(canned_observation=canned)
        ctx = validate_and_create_safe_context("Query")
        req = BooleanRequest(question_id="q1", context=ctx)
        obs = provider.decide(req)

        assert obs == canned
