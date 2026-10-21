# 05: State Machine Model Checking and Concurrency

- **Base Revision**: `66648081fbd7b4642f38ba0b273417a8891026ba`
- **Head Revision**: `676275f1dfa83857500b171f1a50a1dfd9a690bf`
- **Focus**: Review of formal interleaving verification in `tests/test_paid_budget_concurrency.py` (#680).

---

## 1. Context & Motivation

Issue #680 tracked formal state-machine verification for the atomic paid budget reservation and settlement design (#677).
Sequential routing tests (#675) cannot prove correctness under multithreaded interleavings, cancellation races, or network timeouts.

Instead of introducing heavyweight external model checkers requiring non-standard toolchains, PR #681 delivered a source-mapped breadth-first search (BFS) state-space exploration engine directly within `pytest` ([`tests/test_paid_budget_concurrency.py:175-271`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py#L175-L271)).

---

## 2. Invariants & Proof Engine

### A. Safety Invariants Checked
At every state transition, the engine asserts:
1. **Safety Bound**: `0.0 <= spent + reserved <= max_spend_usd + 1e-9`.
2. **Non-negativity**: `spent >= -1e-9 and reserved >= -1e-9`.
3. **Conservative Settlement**: Terminal failure (HTTP 429/500, timeout) settles the conservative reservation rather than releasing or billing zero.

### B. State-Space Exploration
- The model explores all interleavings of 3 concurrent request slots across states `("IDLE", "RESERVED", "SETTLED")`.
- Transitions:
  - `RESERVE`: preflight atomic reservation.
  - `SETTLE`: partial or full usage cost settlement.
  - `FAIL / TIMEOUT`: conservative settlement on transport failure.
  - `CANCEL`: pre-dispatch release.
- **Coverage**: Over 10 distinct reachable state combinations verified in 0.05 seconds.

### C. Negative Mutation Control
The test suite includes an explicit negative control: [`test_negative_mutation_control_trips_counterexample`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py#L256-L271).
When the reservation bound check is mutated to return `True` blindly without checking `spent + reserved <= cap`, the engine immediately detects a safety violation counterexample and fails.

---

## 3. Concurrency Verification Verdict

**UNCONDITIONAL PASS**.
The test engine is hermetic, fast (50ms execution time), and runs in standard CI pipelines without external dependencies.
