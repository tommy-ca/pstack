---
name: verify-decision-contract
description: "Verify the pstack decision contract, System One wire transport, provider profiles, and canonical routing registry offline against an independently captured cursor/plugins Git tree."
disable-model-invocation: true
---

# Verify the decision contract

Use this skill to check the Jev contract specifications, provider profiles, class calibration policies, and `references/decision-routing.json`. The verifier does not call external providers during offline verification.

## Launch

Set up the verification environment and verify prerequisite tooling (`python3`, `uv`, `openspec`, `git`).
Create an isolated run directory for captured evidence.

```bash
run_dir=$(mktemp -d /tmp/verify-decision-contract.XXXXXX)
```

## Doctor

Run OpenSpec validation checks for the specification:

```bash
openspec validate pstack-jev-decisions --type spec --strict
uv run pytest tests/test_verify_decision_contract.py tests/test_jev_transport_and_profiles.py tests/test_class_calibration_policy.py
```

## Drive

Drive the contract verifier, eval suite, and rollback equivalence against local and upstream captures:

```bash
python3 scripts/verify-decision-contract.py --root . --upstream-commit <commit.json> --upstream-tree <tree.json> --evidence-dir "$run_dir"
python3 scripts/eval_decision_routing.py --format json
python3 scripts/eval_blinded_pstack.py --format json
python3 scripts/verify_rollback_equivalence.py --format json
```

## Proof bar

Assert zero verification errors, 100% route coverage across 23 playbooks, and strict specification parity between formal spec and change delta.
Enforce three-tier test classification with Tier 1 fast contract unit tests, Tier 2 offline integration fixtures, and Tier 3 host runtime probes.
Prove lean System One wire protocol compliance without third-party SDK dependencies per `references/jev-provider-options.md`.
Enforce per-class confidence thresholds and >=0.10 probability margins with fail-open baseline fallback.
Reduce scenario verdicts with the strict failure-first lattice where FAIL beats BLOCKED, BLOCKED beats UNTESTED, and UNTESTED beats PASS.

## Evidence

Receipts are persisted as structured JSON in the designated evidence directory.
Tag evidence with evidence_level (observed_live for live runs, offline for contract checks).
Bound driver command executions to 60 seconds with strict timeout handling.

## Cleanup

Remove temporary run directories and ephemeral test artifacts.

```bash
rm -rf "$run_dir"
```

## Helpers

Run the verification driver script:

```bash
./scripts/driver.sh doctor
./scripts/driver.sh drive
./scripts/driver.sh cleanup
```
