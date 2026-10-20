# Core Feature: decision-adapter

## Sub-features
- Single-operation SemanticDecisionProvider contract
- Strict egress boundary validation and SafeContext enforcement
- Lean native System One wire protocol over standard library urllib
- Provider profile configuration across opencode-console, opencode-zen, openrouter, and typesafe-direct
- Default-OFF feature gate, paid provider consent gate, and fail-open exception handling

## How to get to it (user POV)
Inspect `scripts/decision_adapter.py` and `references/jev-provider-options.md`. Run `pytest tests/test_decision_adapter.py` and `pytest tests/test_jev_transport_and_profiles.py`.

## Driving it with Codex
Execute `uv run pytest tests/test_decision_adapter.py tests/test_shadow_routing.py tests/test_jev_transport_and_profiles.py`.

## Gotchas
Provider failures, network timeouts, unapproved paid profiles, or invalid responses must never raise uncaught exceptions to the caller. Fail open cleanly to baseline.
