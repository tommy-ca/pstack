# Core Feature: decision-adapter

## Sub-features
- Single-operation SemanticDecisionProvider contract
- Strict egress boundary validation and SafeContext enforcement
- Default-OFF feature gate and fail-open exception handling

## How to get to it (user POV)
Inspect `scripts/decision_adapter.py` and run `pytest tests/test_decision_adapter.py`.

## Driving it with Codex
Execute `uv run pytest tests/test_decision_adapter.py tests/test_shadow_routing.py`.

## Gotchas
Provider failures, timeouts, or invalid requests must never raise uncaught exceptions to the caller.
