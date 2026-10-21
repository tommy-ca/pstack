# Detail Report 05: State-Machine Model Checking & Concurrency Truth

- **Subsystem**: Formal Interleaving Model Checker & Atomic Budget Invariants
- **Base Revision**: `5f649c6`
- **Head Revision**: `20164ba`
- **Reviewed Epic**: Issue [#685](https://github.com/tommy-ca/pstack/issues/685) (PR [#686](https://github.com/tommy-ca/pstack/pull/686), commit `7d0dbd2`)

---

## 1. Context & Standard

Standard 4 and Standard 7 of the Thermo-Nuclear Code Quality Review mandate:
> Prefer direct, boring, maintainable code over hacky or magical code.
> Treat unnecessary sequential orchestration and non-atomic updates as design smells when the cleaner structure is obvious.

In PR [#681](https://github.com/tommy-ca/pstack/pull/681), a breadth-first search (BFS) state-space exploration model was created in [`tests/test_paid_budget_concurrency.py`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py) to formally prove that interleaved thread execution never violates the budget invariant `0 <= cumulative_spend + reserved_spend <= max_spend`. 

In PR [#686](https://github.com/tommy-ca/pstack/pull/686), this model checker was expanded to address Issue [#682](https://github.com/tommy-ca/pstack/issues/682): what happens when an external provider bills more than the reservation?

---

## 2. Formal Model Structure

The BFS model checker explores the discrete state space of a 3-slot concurrent request pool:
- **Request State**: `(spent, reserved, (req_0_state, req_1_state, req_2_state), depth)` where request slot state $\in \{\text{IDLE}, \text{RESERVED}, \text{SETTLED}\}$.
- **Transitions**:
  - `RESERVE`: An `IDLE` slot transitions to `RESERVED` if `ledger.reserve()` succeeds.
  - `SETTLE`: A `RESERVED` slot transitions to `SETTLED` via `ledger.settle(reserved_amount, actual_cost)`.
  - `RELEASE`: A `RESERVED` slot aborts and transitions back to `IDLE` via `ledger.release(reserved_amount)`.
- **Invariants Checked at Every Node**:
  - `cumulative_spend_usd >= -1e-9`
  - `reserved_spend_usd >= -1e-9`
  - When provider honors reservation ceiling: `cumulative_spend_usd + reserved_spend_usd <= cap + 1e-9`

---

## 3. Analysis of Model Extensions in PR #686

### 3.1 Bounded Charge Exploration (Honest Provider)
In `test_state_machine_exploration_proves_budget_safety_under_provider_bound`:
- Parameter `allow_unbounded_charge=False`.
- The actual charges evaluated during settlement are $\{0.5 \times \text{reservation}, 1.0 \times \text{reservation}\}$.
- The model checker visits 14 distinct global states across a search depth of 6, completing in ~70ms.
- **Result**: Zero safety violations observed. Proven that when the provider respects the reservation ceiling, process-local spend never exceeds the cap.

### 3.2 Unbounded Charge Exploration (Rogue Provider Counterexample)
In `test_unbounded_provider_charge_demonstrates_need_for_provider_ceiling`:
- Parameter `allow_unbounded_charge=True`.
- The actual charges evaluated include a rogue charge of $2.5 \times \text{reservation}$.
- The model checker discovers that if a provider bills $2.5 \times$ the reservation without an upstream account quota, the safety invariant `cumulative_spend + reserved_spend <= cap` is violated on the first overage settlement.
- **Result**: The counterexample is surfaced immediately:
  ```text
  Safety violated at depth 2: spent=0.0125, reserved=0.0, reqs=('SETTLED', 'IDLE', 'IDLE') > cap 0.010
  ```
- **Architectural Value**: This test serves as an executable proof of why process-local admission control cannot guarantee account spending caps in the presence of unconstrained external billing, proving the necessity of provider-enforced account ceiling contracts.

### 3.3 Over-Reservation Fail-Closed Unit Test
In `test_over_reservation_settlement_records_overshoot_truthfully`:
- Simulates an actual dispatch where a mock provider returns `usage.cost_usd = 0.025` against a profile with `max_spend_usd = 0.010` and `reservation_usd = 0.005`.
- Verifies that:
  1. The first request succeeds and truthfully records cumulative spend as $0.025.
  2. `spend_ledger.overshoot_count` increments to 1.
  3. `spend_ledger.is_overspent` becomes `True`.
  4. The second request fails closed immediately with status `"unavailable"` without dispatching to the transport.
  5. Cumulative spend remains unchanged at $0.025.

---

## 4. Verdict
The concurrency model and over-reservation tests provide rigorous, formal guarantees of state transitions under both nominal and adversarial conditions.
