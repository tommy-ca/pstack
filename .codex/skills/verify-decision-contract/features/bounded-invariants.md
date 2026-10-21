# Core Feature: bounded-invariants

## Sub-features

- Code-level exhaustive finite-state exploration over **135 cases** (5 query classes × 3 summary classes × 3 modes × 3 provider outcomes) against the real `resolve_skill_order_with_shadow`.
- Early bypass/zero provider invocation, safe-summary-only context egress, shadow/off baseline equivalence, and no unauthorized advisory promotion.
- Provenance-backed calibration verification gate distinguishing specimen fixtures from promoted receipts (#676); default specimen fixtures cannot authorize live advisory promotion without independent provenance.
- Thread-safe atomic spend reservation and settlement ledger (`SpendLedger`) with model-checked state interleaving and negative mutation control (#677, #680, #682); documents distinction between local admission control and provider-side account ceiling guarantees.
- Origin security validation on provider profiles rejecting insecure HTTP, loopback, private IP ranges, cloud metadata endpoints, and unauthorized credential environment names (#683).
- Mutation negative controls that temporarily replace `_is_egress_bypassed` with a disabled gate, disable `SpendLedger` budget bounds, or test unbounded provider charges; the actual invariant checkers must detect forbidden egress and overspend. Python `monkeypatch` restores the production functions.
- Source sync record and bounded scope are in `../SKILL.md`; no fictional `TLA+`/Lean proof or model-family independence claim.

## How to get to it (user POV)

Inspect `scripts/route_resolver.py`, `scripts/decision_adapter.py`, `references/decision-routing.json`, and `tests/test_decision_bounded_invariants.py`. The verified source baseline is `66648081fbd7b4642f38ba0b273417a8891026ba`. If any covered path changes, inspect its diff from that SHA and maintain the bounded state categories before renewing this record.

## Driving it with Codex

Run `python3 -m pytest -q tests/test_decision_bounded_invariants.py` from repository root, or `bash .codex/skills/verify-decision-contract/scripts/driver.sh doctor`. Then run canonical source parity with independently captured upstream JSON per `../SKILL.md`. A model/check PASS is only a bounded conformance verdict; native/API evidence remains UNTESTED.

## Gotchas

- The human-approved public summary is an assumption, not established by regex.
- Only the enumerated route/input classes and pinned Grok profile are explored; unbounded concurrency, user data, billing and external provider behavior are excluded.
- The mutation test is an executable negative control, not a second copy of the production algorithm.
- Do not promote a fixture's `references/calibrated-evidence.json` metadata to provenance-backed calibration or label synthetic benchmark assumptions as measured latency/cost.
