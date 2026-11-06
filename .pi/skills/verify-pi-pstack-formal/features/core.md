# Core Feature: Pi candidate formal verification

## Sub-features

- 53 bounded code-level mutant rejections across profile and extension policies
- Single-point validation of typed candidate profile and extension pins
- Negative control detection refusing premature runtime promotion

## How to get to it (user POV)

Run `python3 scripts/verify_pi_candidate.py model` to observe bounded invariant checking.

## Driving it with Pi candidate

Execute `python3 -m pytest -q tests/test_pi_candidate_profile.py` to drive model verification.

## Gotchas

This is source-contract proof; actual Pi runtime sandbox and authorization remain unverified.
