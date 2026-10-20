# Core Feature: offline-eval

## Sub-features
- Rerunnable offline routing eval corpus and calibration lever
- Class-specific confidence thresholds and minimum probability margin requirement
- Uncalibrated class fencing and graceful fallback to baseline routing
- Revision-bound evidence receipts and mechanical staleness detection
- Blinded behavioral evaluation comparing baseline and shadow candidates

## How to get to it (user POV)
Run `python3 scripts/eval_decision_routing.py` and `python3 scripts/eval_blinded_pstack.py`. Inspect `scripts/route_resolver.py` and run `pytest tests/test_class_calibration_policy.py`.

## Driving it with Codex
Execute `python3 scripts/eval_decision_routing.py --format json` and `uv run pytest tests/test_class_calibration_policy.py`.

## Gotchas
Receipts lacking complete revision bindings, having uncalibrated classes, or failing margin requirements cannot authorize control. Baseline routing remains active.
