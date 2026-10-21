"""Model-checked atomic paid budget reservation and concurrency safety suite (#677, #680).

Verifies:
1. Thread-safe atomic reservation prevents overshoot under concurrent dispatch.
2. Mandatory settlement on error/timeout/abstain ensures no leaked reservations or unbilled charges.
3. State-machine model checker verifying safety invariants over all interleaved request lifecycle states.
4. Negative mutation control: disabling atomic reservation or bound check trips invariant assertion.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from scripts.decision_adapter import (
    ChoiceOption,
    ChoiceRequest,
    DecisionOutcome,
    JevDecisionAdapter,
    JevProviderProfile,
    ProviderObservation,
    SpendLedger,
    validate_and_create_safe_context,
)


@pytest.fixture
def sample_choice_request() -> ChoiceRequest:
    ctx = validate_and_create_safe_context("Fix concurrency bug in payment processor")
    return ChoiceRequest(
        question_id="route_selection",
        context=ctx,
        choices=[
            ChoiceOption(id="bug-fix", label="Bug fix workflow"),
            ChoiceOption(id="feature", label="Feature workflow"),
        ],
    )


class TestPaidBudgetConcurrency:
    """Concurrent multi-threaded verification of atomic reservation and spend ceiling (#677)."""

    def test_concurrent_requests_strictly_bounded_by_spend_cap(
        self, sample_choice_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PSTACK_JEV_ALLOW_PAID", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
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

        # Budget of $0.020 with $0.005 per reservation allows exactly 4 calls
        profile = JevProviderProfile(
            profile_id="openrouter-test",
            api_root="https://openrouter.ai/api",
            configured_model="typesafe/jev-1.14",
            credential_env="OPENROUTER_API_KEY",
            paid=True,
            max_spend_usd=0.020,
            reservation_usd=0.005,
        )
        adapter = JevDecisionAdapter(enabled=True, profile=profile, transport_fn=mock_transport)

        results: List[ProviderObservation] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(adapter.decide, sample_choice_request) for _ in range(16)]
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())

        decided = [r for r in results if r.is_decided()]
        unavailable = [r for r in results if r.outcome.status == "unavailable"]

        assert len(decided) == 4, f"Expected exactly 4 decided calls, got {len(decided)}"
        assert len(unavailable) == 12, f"Expected 12 blocked calls, got {len(unavailable)}"
        assert adapter.cumulative_spend_usd <= 0.020 + 1e-9
        assert adapter.reserved_spend_usd == 0.0

    def test_billed_error_settles_reservation(
        self, sample_choice_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """HTTP errors must settle reserved amount to prevent phantom capacity (#677)."""
        monkeypatch.setenv("PSTACK_JEV_ALLOW_PAID", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        import urllib.error

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, None)

        profile = JevProviderProfile(
            profile_id="openrouter-test",
            api_root="https://openrouter.ai/api",
            configured_model="typesafe/jev-1.14",
            credential_env="OPENROUTER_API_KEY",
            paid=True,
            max_spend_usd=0.010,
            reservation_usd=0.005,
        )
        adapter = JevDecisionAdapter(enabled=True, profile=profile, transport_fn=mock_transport)

        obs1 = adapter.decide(sample_choice_request)
        assert obs1.outcome.status == "unavailable"
        assert adapter.cumulative_spend_usd == 0.005
        assert adapter.reserved_spend_usd == 0.0

        obs2 = adapter.decide(sample_choice_request)
        assert obs2.outcome.status == "unavailable"
        assert adapter.cumulative_spend_usd == 0.010
        assert adapter.reserved_spend_usd == 0.0

        # Now budget is exhausted
        obs3 = adapter.decide(sample_choice_request)
        assert obs3.outcome.status == "unavailable"
        assert adapter.cumulative_spend_usd == 0.010

    def test_missing_or_nonfinite_usage_charges_conservative_reservation(
        self, sample_choice_request: ChoiceRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PSTACK_JEV_ALLOW_PAID", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        def mock_transport(url: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
            return {
                "model": "typesafe/jev-1.14",
                "provider": "openrouter",
                "usage": {"cost_usd": float("nan")},  # non-finite
                "answers": {
                    "route_selection": {
                        "type": "choice",
                        "choice": "bug-fix",
                        "confidence": 0.90,
                    }
                },
            }

        profile = JevProviderProfile(
            profile_id="openrouter-test",
            api_root="https://openrouter.ai/api",
            configured_model="typesafe/jev-1.14",
            credential_env="OPENROUTER_API_KEY",
            paid=True,
            max_spend_usd=0.010,
            reservation_usd=0.005,
        )
        adapter = JevDecisionAdapter(enabled=True, profile=profile, transport_fn=mock_transport)

        obs = adapter.decide(sample_choice_request)
        assert obs.is_decided()
        # Conservative fallback charged the reservation amount ($0.005), not fabricated $0.001
        assert adapter.cumulative_spend_usd == 0.005
        assert adapter.reserved_spend_usd == 0.0


class TestPaidBudgetFormalInterleavingModel:
    """Source-mapped state-machine exploration model checker (#680)."""

    def _explore_state_space(self, ledger_cls, cap: float, reservation: float, max_depth: int) -> Tuple[int, Optional[str]]:
        """Exhaustively explore interleaved request transitions and check safety invariants."""
        # State: (spent, reserved, tuple of request states for 3 request slots)
        # Request slot state in: "IDLE", "RESERVED", "SETTLED"
        visited: Set[Tuple[float, float, Tuple[str, ...]]] = set()
        queue = [(0.0, 0.0, ("IDLE", "IDLE", "IDLE"), 0)]
        counterexample: Optional[str] = None
        states_explored = 0

        while queue:
            spent, reserved, reqs, depth = queue.pop(0)
            state_key = (round(spent, 4), round(reserved, 4), reqs)
            if state_key in visited:
                continue
            visited.add(state_key)
            states_explored += 1

            # Invariant 1: Safety ceiling (spent + reserved <= cap)
            if spent + reserved > cap + 1e-9:
                counterexample = f"Safety violated: spent ({spent}) + reserved ({reserved}) > cap ({cap})"
                break
            # Invariant 2: Non-negative
            if spent < -1e-9 or reserved < -1e-9:
                counterexample = f"Non-negativity violated: spent={spent}, reserved={reserved}"
                break

            if depth >= max_depth:
                continue

            ledger = ledger_cls(max_spend_usd=cap, reservation_usd=reservation)

            for req_idx, req_state in enumerate(reqs):
                if req_state == "IDLE":
                    # Transition: RESERVE
                    ledger.cumulative_spend_usd = spent
                    ledger.reserved_spend_usd = reserved
                    if ledger.reserve():
                        new_reqs = list(reqs)
                        new_reqs[req_idx] = "RESERVED"
                        queue.append((ledger.cumulative_spend_usd, ledger.reserved_spend_usd, tuple(new_reqs), depth + 1))
                elif req_state == "RESERVED":
                    # Transition 1: SETTLE with actual cost bounded by reservation
                    for actual in (reservation * 0.5, reservation):
                        ledger.cumulative_spend_usd = spent
                        ledger.reserved_spend_usd = reserved
                        ledger.settle(reserved_amount=reservation, actual_cost=actual)
                        new_reqs = list(reqs)
                        new_reqs[req_idx] = "SETTLED"
                        queue.append((ledger.cumulative_spend_usd, ledger.reserved_spend_usd, tuple(new_reqs), depth + 1))

                    # Transition 2: FAIL / TIMEOUT (settle with reserved amount)
                    ledger.cumulative_spend_usd = spent
                    ledger.reserved_spend_usd = reserved
                    ledger.settle(reserved_amount=reservation, actual_cost=None)
                    new_reqs = list(reqs)
                    new_reqs[req_idx] = "SETTLED"
                    queue.append((ledger.cumulative_spend_usd, ledger.reserved_spend_usd, tuple(new_reqs), depth + 1))

                    # Transition 3: CANCEL before dispatch (release)
                    ledger.cumulative_spend_usd = spent
                    ledger.reserved_spend_usd = reserved
                    ledger.release(reserved_amount=reservation)
                    new_reqs = list(reqs)
                    new_reqs[req_idx] = "IDLE"
                    queue.append((ledger.cumulative_spend_usd, ledger.reserved_spend_usd, tuple(new_reqs), depth + 1))

        return states_explored, counterexample

    def test_state_machine_exploration_proves_budget_safety(self) -> None:
        """Prove safety across all reachable states with SpendLedger."""
        cap = 0.010
        reservation = 0.005
        states_count, counterexample = self._explore_state_space(
            SpendLedger, cap=cap, reservation=reservation, max_depth=6
        )
        assert counterexample is None, counterexample
        assert states_count > 10, f"Expected rich state exploration, explored {states_count}"

    def test_negative_mutation_control_trips_counterexample(self) -> None:
        """Mutant: remove reservation check, checker must catch the overspend violation (#680)."""
        class MutatedSpendLedger(SpendLedger):
            def reserve(self, amount: Optional[float] = None) -> bool:
                amt = self.reservation_usd if amount is None else float(amount)
                # MUTATION: blind reservation without checking cumulative + reserved <= max_spend
                self.reserved_spend_usd += amt
                return True

        cap = 0.010
        reservation = 0.005
        states_count, counterexample = self._explore_state_space(
            MutatedSpendLedger, cap=cap, reservation=reservation, max_depth=6
        )
        assert counterexample is not None
        assert "Safety violated" in counterexample
