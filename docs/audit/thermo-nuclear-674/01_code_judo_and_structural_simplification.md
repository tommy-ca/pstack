# 01: Code Judo and Structural Simplification

- **Base Revision**: `66648081fbd7b4642f38ba0b273417a8891026ba`
- **Head Revision**: `676275f1dfa83857500b171f1a50a1dfd9a690bf`
- **Focus**: Eliminating incidental complexity, boundary leaks, and repetitive control flows in `SpendLedger` and `JevDecisionAdapter`.

---

## 1. Analysis of Current State

In commits `103a466` (PR #679) and `676275f` (PR #681), `pstack` introduced:
1. `SpendLedger` in [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L215-L255) to manage atomic budget reservation and settlement.
2. A provenance gate in [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L162-L235) to distinguish checked-in specimen fixtures from live calibrated receipts.

While functionally sound and 100% green across all unit, regression, and model-checked tests, the implementation contains opportunities for "Code Judo" simplification that delete boilerplate and eliminate leaky boundaries.

---

## 2. Findings & Judo Proposals

### Finding CJ-1: SpendLedger Boundary Leak in JevDecisionAdapter Property Setter

- **Severity**: Structural / Encapsulation Debt
- **Location**: [`scripts/decision_adapter.py:359-363`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L359-L363)
- **Problem**:
  In `JevDecisionAdapter`:
  ```python
  @cumulative_spend_usd.setter
  def cumulative_spend_usd(self, val: float) -> None:
      with self.spend_ledger._lock:
          self.spend_ledger.cumulative_spend_usd = float(val)
  ```
  `JevDecisionAdapter` reaches directly into the private `_lock` attribute of `SpendLedger` to synchronize a property assignment. Furthermore, in [`tests/test_paid_budget_concurrency.py:212-213`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py#L212-L213), the state-machine exploration assigns directly to `ledger.cumulative_spend_usd` and `ledger.reserved_spend_usd` without locking.
- **Consumer Reachability**:
  - `JevDecisionAdapter.cumulative_spend_usd`: read by `tests/test_decision_adapter.py`, `tests/test_paid_budget_concurrency.py`, `tests/test_eval_decision_routing.py`.
  - `SpendLedger._lock`: only referenced internally in `SpendLedger` methods and this single setter.
- **Code Judo Solution**:
  Encapsulate state reset and thread-safe mutation inside `SpendLedger`:
  ```python
  class SpendLedger:
      ...
      def reset(self, cumulative_spend_usd: float = 0.0, reserved_spend_usd: float = 0.0) -> None:
          with self._lock:
              self.cumulative_spend_usd = float(cumulative_spend_usd)
              self.reserved_spend_usd = float(reserved_spend_usd)

      def set_cumulative_spend(self, val: float) -> None:
          with self._lock:
              self.cumulative_spend_usd = float(val)
  ```
  And in `JevDecisionAdapter`:
  ```python
  @cumulative_spend_usd.setter
  def cumulative_spend_usd(self, val: float) -> None:
      self.spend_ledger.set_cumulative_spend(val)
  ```
- **Behavior Pin**: All 5 concurrency tests in `tests/test_paid_budget_concurrency.py` and 12 adapter tests in `tests/test_decision_adapter.py` remain byte-identical in outcome.
- **Net Maintained Obligation**: Eliminates external access to private lock attributes, preventing lock contention bugs and establishing a clean abstraction boundary.

---

### Finding CJ-2: Repetitive Raw Observation Factories in `_invoke_provider`

- **Severity**: Redundancy / Boilerplate Debt
- **Location**: [`scripts/decision_adapter.py:411-450, 502-518`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L411-L450)
- **Problem**:
  `_invoke_provider` constructs raw `ProviderObservation` instances across 8 separate branch exits:
  ```python
  # 8 separate occurrences:
  return ProviderObservation(
      outcome=DecisionOutcome(status="unavailable"),
      provider_identity=self.provider_identity,
      model_identity=self.model_identity,
  )
  ```
  `JevDecisionAdapter` already defined `_invalid_obs` at line 310, but failed to provide equivalent helpers for `unavailable` and `abstain`.
- **Consumer Reachability**:
  Internal to `JevDecisionAdapter._invoke_provider`.
- **Code Judo Solution**:
  Generalize `_obs(status: str, confidence: float = 0.0)` or define `_unavailable_obs()` and `_abstain_obs()`:
  ```python
  def _obs(self, status: str, confidence: float = 0.0) -> ProviderObservation:
      return ProviderObservation(
          outcome=DecisionOutcome(status=status),
          provider_identity=self.provider_identity,
          model_identity=self.model_identity,
          confidence=confidence,
      )
  ```
  This turns 40 lines of scattered boilerplate into single-line declarative returns:
  ```python
  if not api_key and self._transport_fn is None:
      return self._obs("abstain")
  if not self.spend_ledger.reserve():
      return self._obs("unavailable")
  ```
- **Behavior Pin**: Preserves exact dataclass output across all 91 regression tests and 5 concurrency tests.
- **Net Maintained Obligation**: Reduces `_invoke_provider` by ~30 lines, eliminating copy-paste drift in observation construction.

---

### Finding CJ-3: SpendLedger Context Manager (`lease`)

- **Severity**: Modularity & Elegance Opportunity
- **Location**: [`scripts/decision_adapter.py:430-452, 520-522`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L430-L452)
- **Problem**:
  `_invoke_provider` tracks a boolean flag `is_reserved = False`, sets it conditionally `is_reserved = True`, and then in a `finally` block checks `if self.profile.paid and is_reserved: self.spend_ledger.settle(...)`.
- **Code Judo Solution**:
  Introduce a context manager on `SpendLedger` that yields a `SpendLease`:
  ```python
  class SpendLease:
      def __init__(self, ledger: SpendLedger, amount: float) -> None:
          self.ledger = ledger
          self.amount = amount
          self.actual_cost: Optional[float] = None
          self.settled = False

      def record_cost(self, cost: Optional[float]) -> None:
          self.actual_cost = cost

      def close(self) -> None:
          if not self.settled:
              self.ledger.settle(reserved_amount=self.amount, actual_cost=self.actual_cost)
              self.settled = True
  ```
  When used in `_invoke_provider`, reservation, error handling, and conservative settlement are bound to lexical scope without manual boolean flags.
- **Behavior Pin**: `tests/test_paid_budget_concurrency.py` verifies zero budget leakage under thread contention.
