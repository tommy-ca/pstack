# Core Feature: offline-eval

## Sub-features
- Rerunnable offline routing eval corpus and calibration lever
- Revision-bound evidence receipts and mechanical staleness detection
- Blinded behavioral evaluation comparing baseline and shadow candidates

## How to get to it (user POV)
Run `python3 scripts/eval_decision_routing.py` and `python3 scripts/eval_blinded_pstack.py`.

## Driving it with Codex
Execute `python3 scripts/eval_decision_routing.py --format json` and verify verdict is PASS.

## Gotchas
Receipts lacking complete revision bindings or having unknown model identity cannot authorize control.
