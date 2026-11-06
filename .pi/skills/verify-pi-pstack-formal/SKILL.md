---
name: verify-pi-pstack-formal
description: "Run bounded source-contract mutation checks for the Pi PStack candidate; do not claim model-checking of actual Pi runtime or sandbox authorization."
disable-model-invocation: true
---

# Formal verification of Pi candidate contract — bounded source domain

This is a project-local instance of the existing `create-formal-verification-skill` discipline, not a new generic verification registry or a proof of Pi runtime security.

## Code relation and bounds

Current source surfaces are `scripts/portability_types.py` (the actual `HarnessProfile.validate` and `Binding.validate`), `scripts/verify_pi_candidate.py` (`check_contract` and `bounded_negative_controls`), `profiles/pstack-pi.json`, and `references/pi-essential-extensions.json`.

Sync revision: **candidate branch only**; exact validated runtime Pi revision is not recorded. A change to those functions invalidates this bounded model's applicability until rerun and reviewed.

Finite domain checks, using code-level mutant rejection:
1. Four invalid support-state promotions must fail.
2. False verified status for each of 17 capabilities must fail.
3. Duplicate binding for each of 17 capabilities must fail.
4. Four original configuration mutants must fail (extra engine, credential write, headless bypass, unreviewed auto-install).
5. Unverified `human.gate` native promotion must fail.
6. Ten pi-verdict policy mutants must fail: absent extension, wrong owner, disabled-gate requirement, disabled deterministic deny floor, permissive headless ask, ignored child launch, allowed classifier rescue, false verified child interception, external gate-off bypass and classifier opinion promoted to a hard gate.

Total: **53 negative cases**. This proves only the enumerated source-contract failure cases. It does NOT formally verify subprocess isolation, `subagent_launch`, scheduling or approval traces in the actual Pi runtime.

## Reproducible command and negative control

Run `python3 scripts/verify_pi_candidate.py model` and `python3 -m pytest -q tests/test_pi_candidate_profile.py`. An accepted mutant is FAIL; unavailable checker is BLOCKED, never PASS. Tests use the real PStack validator, not a separately simulated permission engine.

## Maintenance

Use `maintain-formal-verification-skill`: record source commit before and after any validator change, rerun all bounded negatives, refuse stale proof promotion. For actual Pi race/security properties, choose TLC, SMT or a code-level checker based on the real implementation and replay a deliberate broken variant (#898).

## Launch

No long-lived process or network daemon required. Verify Python 3.10+ and pytest availability before running model suites.

## Doctor

Run `python3 scripts/verify_pi_candidate.py check` to confirm candidate profile integrity and essential extension schema adherence.

## Drive

Run `python3 scripts/verify_pi_candidate.py model` and `python3 -m pytest -q tests/test_pi_candidate_profile.py` to drive all 53 bounded mutation proofs.

## Proof bar

Verify all 53 bounded mutants are rejected. Any accepted mutant yields FAIL. Missing environment yields BLOCKED, never PASS.

## Evidence

Capture stdout, exit codes, and exact git commit hash. Distinguish offline contract checking from live runtime receipts.

## Cleanup

No persistent filesystem state or orphan processes remain after mutation suite execution.

## Helpers

Run the verification suite:
```bash
python3 scripts/verify_pi_candidate.py model
python3 -m pytest -q tests/test_pi_candidate_profile.py
```
