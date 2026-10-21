# Detail Report 01: Code Judo Moves & Structural Simplification

- **Subsystem**: JEV Decision Adapter, Provider Origin Security & Spend Ledger
- **Base Revision**: `5f649c6`
- **Head Revision**: `20164ba`
- **Reviewed Epic**: Issue [#685](https://github.com/tommy-ca/pstack/issues/685) (PR [#686](https://github.com/tommy-ca/pstack/pull/686), commit `7d0dbd2`)

---

## 1. Context & Motivation

Epic [#685](https://github.com/tommy-ca/pstack/issues/685) introduced custom provider profile origin security validation ([#683](https://github.com/tommy-ca/pstack/issues/683)) and budget settlement truth accounting with over-reservation state tracking ([#682](https://github.com/tommy-ca/pstack/issues/682)). While the implementation in PR [#686](https://github.com/tommy-ca/pstack/pull/686) is fully functional and passes all 108 contract tests, an aggressive thermo-nuclear code quality review identifies three distinct "Code Judo" moves: structural refactorings that preserve behavior while deleting incidental complexity.

---

## 2. Code Judo Proposals

### Judo Move 1: Decouple IP Parsing from Address Classification

#### The Problem
In [`scripts/decision_adapter.py:252-265`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L252-L265):
```python
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
```

The `try` block attempts to parse `hostname` as an IP address via `ipaddress.ip_address(hostname)`. When `hostname` is a standard domain name (such as `openrouter.ai` or `opencode.ai`), `ipaddress.ip_address` raises a `ValueError`. However, the developer also raises custom `ValueError` exceptions inside the same `try` block for disallowed IP classes (loopback, private, link-local, multicast). 

To prevent catching its own exceptions, the handler performs string matching on the error message: `if "disallowed" in str(exc): raise`. This is an unnecessary and brittle control-flow pattern.

#### The Code Judo Move
Isolate the parsing call so the `try/except` block only handles the `ValueError` from `ipaddress.ip_address`. If the hostname is an IP address, evaluate the classification predicates outside the exception handler:

```python
try:
    ip = ipaddress.ip_address(hostname)
except ValueError:
    ip = None

if ip is not None:
    if ip.is_loopback:
        raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed loopback address (#683)")
    if ip.is_private:
        raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed private IP address (#683)")
    if ip.is_link_local:
        raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed link-local/cloud-metadata IP address (#683)")
    if ip.is_unspecified or ip.is_multicast or ip.is_reserved:
        raise ValueError(f"Provider api_root IP '{hostname}' is a disallowed reserved/multicast IP address (#683)")
```

#### Consumer Reachability & Pin
- **Consumers**: [`validate_provider_api_root`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L229), called from [`JevProviderProfile.__post_init__`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L296).
- **Behavior Pin**: All 36 tests in [`tests/test_jev_transport_and_profiles.py`](file:///home/tommyk/projects/pstack/tests/test_jev_transport_and_profiles.py) continue to pass. Domain names parse cleanly without exception, while loopback, private, and link-local literals raise identical error messages.
- **Net Maintained Obligation**: Deletes string sniffing in exception handlers; eliminates coupled exception types.

---

### Judo Move 2: Centralize Floating-Point Comparison Tolerance in SpendLedger

#### The Problem
In [`scripts/decision_adapter.py:329, 336, 351`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L329):
The floating-point epsilon constant `1e-9` is hardcoded repeatedly across three methods in `SpendLedger`:
- In `is_overspent`: `self.cumulative_spend_usd > self.max_spend_usd + 1e-9`
- In `reserve`: `self.cumulative_spend_usd + self.reserved_spend_usd + amt > self.max_spend_usd + 1e-9`
- In `settle`: `cost > amt + 1e-9`

#### The Code Judo Move
Define a module-level constant `_FLOAT_TOLERANCE: float = 1e-9` at the top of the ledger section in [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py). Reference `_FLOAT_TOLERANCE` across all comparison sites to ensure uniform arithmetic boundaries and ease auditing.

#### Consumer Reachability & Pin
- **Consumers**: [`SpendLedger.is_overspent`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L326), [`SpendLedger.reserve`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L331), [`SpendLedger.settle`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L341).
- **Behavior Pin**: Verified by 7 concurrency and state-machine tests in [`tests/test_paid_budget_concurrency.py`](file:///home/tommyk/projects/pstack/tests/test_paid_budget_concurrency.py).
- **Net Maintained Obligation**: Eliminates magic numbers in budget arithmetic.

---

### Judo Move 3: Unify Reservation Decrement in SpendLedger

#### The Problem
In [`scripts/decision_adapter.py:344, 360`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L344):
Both `settle()` and `release()` contain identical logic for decrementing active reservations:
```python
amt = self.reservation_usd if reserved_amount is None else float(reserved_amount)
self.reserved_spend_usd = max(0.0, self.reserved_spend_usd - amt)
```
In `settle()`, this precedes the actual cost addition, whereas `release()` exists specifically to return the reserved amount without adding cost when a request aborts or fails.

#### The Code Judo Move
Extract an internal helper `_unreserve_locked(self, amount: Optional[float] = None) -> float` called under the existing lock by both `settle()` and `release()`. This ensures that reservation arithmetic remains unified and cannot drift if future reservation tracking rules are updated.

#### Consumer Reachability & Pin
- **Consumers**: Internal to [`SpendLedger`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L305).
- **Behavior Pin**: Multithreaded race conditions tested by `test_concurrent_spend_reservation_race` and BFS model exploration.
- **Net Maintained Obligation**: Single point of truth for reservation subtraction.
