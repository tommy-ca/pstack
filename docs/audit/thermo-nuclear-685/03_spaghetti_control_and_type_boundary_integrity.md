# Detail Report 03: Spaghetti Control & Type Boundary Integrity

- **Subsystem**: Type Contracts, Constructor-Edge Invariants & Boundary Guards
- **Base Revision**: `5f649c6`
- **Head Revision**: `20164ba`
- **Reviewed Epic**: Issue [#685](https://github.com/tommy-ca/pstack/issues/685) (PR [#686](https://github.com/tommy-ca/pstack/pull/686), commit `7d0dbd2`)

---

## 1. Context & Standard

Standard 2 and Standard 5 of the Thermo-Nuclear Code Quality Review dictate:
> Do not allow random spaghetti growth in existing code. Be highly suspicious of new ad-hoc conditionals, scattered special cases, or one-off branches inserted into unrelated flows.
> Push hard on type and boundary cleanliness when they affect maintainability.

---

## 2. Evaluation of Boundary Invariants

### 2.1 Constructor-Edge Invariant Gate vs. Runtime Dispatch Branching
A common antipattern in network clients is to defer origin and credential validation to the point of network dispatch (e.g. inside `_invoke_provider`). When validation fails late:
- Requests may partially format HTTP headers, allocating memory and preparing payloads.
- Sensitive environment variables might be retrieved from `os.environ` before an invalid URL aborts the request.
- Error recovery is convoluted because runtime dispatch branches become littered with security checks alongside transport error handling.

PR [#686](https://github.com/tommy-ca/pstack/pull/686) placed `validate_provider_api_root` and `validate_credential_env_name` directly in `JevProviderProfile.__post_init__` ([`scripts/decision_adapter.py:295-297`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L295-L297)). Because `JevProviderProfile` is a frozen dataclass, once instantiated, it is guaranteed to possess a valid, secure HTTPS endpoint and an authorized credential environment name. The runtime dispatch path in `JevDecisionAdapter._invoke_provider` does not require additional ad-hoc checks or special-case branching, eliminating spaghetti control flow.

### 2.2 SpendLedger Admission Boundary vs. Account Ceiling Truth
In PR [#681](https://github.com/tommy-ca/pstack/pull/681), `SpendLedger.settle()` capped recorded cost to `amt` (`cost = min(amt, float(actual_cost))`). While this kept `cumulative_spend_usd` mathematically bounded by `max_spend_usd`, it concealed provider-side billing overshoots. If an external provider billed $0.025 on a $0.005 reservation, the ledger only recorded $0.005, leaving a false impression of remaining budget.

PR [#686](https://github.com/tommy-ca/pstack/pull/686) corrected this type boundary in [`scripts/decision_adapter.py:341-356`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L341-L356):
- `settle()` records the true actual cost returned by the provider: `self.cumulative_spend_usd += cost`.
- If `cost > amt + 1e-9`, it increments `self.overshoot_count += 1`.
- It exposes a typed, synchronized property `is_overspent` returning `self.cumulative_spend_usd > self.max_spend_usd + 1e-9`.
- When overspent, subsequent `reserve()` calls fail closed immediately (`cumulative_spend_usd + reserved_spend_usd + amt > max_spend_usd`), preventing any further provider dispatch.

This clean separation clarifies the contract: `SpendLedger` guarantees process-local admission control, while honestly acknowledging that provider billing anomalies must be settled truthfully.

---

## 3. Findings & Recommendations

### Finding 3.1: Explicit Boundary for `allow_insecure_origins`
In [`scripts/decision_adapter.py:293`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L293), `JevProviderProfile` includes `allow_insecure_origins: bool = False`. This parameter exists to support offline unit test harnesses running against local mock servers (e.g. `http://127.0.0.1:8080`).

**Recommendation**: Ensure that `allow_insecure_origins` cannot be toggled accidentally via environment variables in production. Currently, known profiles in `KNOWN_PROFILES` omit this argument (defaulting strictly to `False`), and environment resolution in `JevDecisionAdapter.__init__` only looks up known profiles or takes explicitly passed objects. This design maintains strict type and runtime containment.

### Finding 3.2: Clarification of Credential Environment Name Validation
In [`scripts/decision_adapter.py:272-279`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L272-L279):
```python
if raw in DISALLOWED_CREDENTIAL_ENVS:
    raise ValueError(...)
if not any(raw.startswith(prefix) for prefix in ALLOWED_CREDENTIAL_PREFIXES):
    raise ValueError(...)
```
Because `ALLOWED_CREDENTIAL_PREFIXES` are strictly `("OPENCODE_", "OPENROUTER_", "TYPESAFE_", "JEV_", "PSTACK_")`, checking `DISALLOWED_CREDENTIAL_ENVS` (which contains `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, etc.) is redundant from a purely boolean perspective. However, it serves a critical semantic role: emitting an explicit security warning explaining that sensitive cloud credentials cannot be exfiltrated to provider endpoints. 

**Recommendation**: Preserve both checks as intentional defense-in-depth, accompanied by clear docstrings explaining that the blacklist provides diagnostic specificity while the prefix allowlist enforces closed boundary admission.
