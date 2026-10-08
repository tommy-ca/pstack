# Core Feature: rollback-equivalence

## Sub-features
- Rerunnable 8-scenario kill-switch and fail-open rollback equivalence verification
- Mechanical staleness detection and threshold-based demotion to baseline
- Sub-millisecond fallback latency budget verification

## How to get to it (user POV)
Run `python3 scripts/verify_rollback_equivalence.py --format json`.

## Driving it with Codex
Execute `python3 scripts/verify_rollback_equivalence.py --format json` and verify `overall_verdict` is `PASS`.

## Gotchas
Fallback latency must remain strictly below budget (10.0ms) and never leak unhandled exceptions to callers.
