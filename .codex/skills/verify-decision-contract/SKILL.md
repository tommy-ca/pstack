---
name: verify-decision-contract
description: "Verify the pstack decision contract and canonical routing registry offline against an independently captured cursor/plugins Git tree."
disable-model-invocation: true
---

# Verify the decision contract

Use this skill to check the Jev contract specifications and `references/decision-routing.json`. The verifier does not call a provider or change routing.

## Launch

Set up the verification environment and verify prerequisite tooling (`python3`, `openspec`, `git`).
Create an isolated run directory for captured evidence.

```bash
run_dir=$(mktemp -d /tmp/verify-decision-contract.XXXXXX)
```

## Doctor

Run strict OpenSpec validation checks for the change and specification:

```bash
openspec validate pstack-jev-decision-plane --type change --strict
openspec validate pstack-jev-decisions --type spec --strict
```

## Drive

Drive the contract verifier against upstream commit and tree captures:

```bash
python3 scripts/verify-decision-contract.py --root . --upstream-commit <commit.json> --upstream-tree <tree.json> --evidence-dir "$run_dir"
```

## Proof bar

Assert zero verification errors, 100% route coverage (23/23 playbooks), and strict specification parity between formal spec and change delta.
Enforce three-tier test classification: Tier 1 fast contract unit tests, Tier 2 offline integration fixtures, and Tier 3 host runtime probes.
Reduce scenario verdicts with the strict failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.

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
