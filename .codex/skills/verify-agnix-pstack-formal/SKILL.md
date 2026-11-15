---
name: verify-agnix-pstack-formal
description: "Use when changing PStack Agnix receipt acceptance, fail-closed policy, or finite-state negative witnesses. Verifies bounded receipt guard invariants."
disable-model-invocation: true
---

# Formally analyze Agnix receipt guard invariants (bounded)

Derived from `skills/create-formal-verification-skill/SKILL.md`. This verification skill validates the bounded real-code receipt acceptance predicate in `scripts/agnix_guard.py`.

## Coverage and sync record

- Covered production commit is `416ca0b0` (Agnix guard and receipt consistency in `scripts/agnix_guard.py`).
- Target code is `scripts/agnix_guard.py::receipt_errors` and `scripts/agnix_guard.py::bounded_model`.
- Safety property guarantees that contradictory receipts where summary counts disagree with diagnostics detail fail closed. Only valid receipts with matching version, sufficient files, zero errors, zero exit status, and consistent counts can pass.
- State bound covers 288 receipt configurations across version, file counts, error counts, warning counts, exit codes, budgets, and inconsistent summary and detail states. This is a finite bounded exploration, not an unbounded formal proof of external Agnix binary behavior.
- Code-alignment rule requires inspecting git diff HEAD~1..HEAD against declared invariants and confirming negative mutant detection.

## Model and checker choice

The command `scripts/agnix_guard.py --formal` exhausts all 288 states of the receipt acceptance lattice in production Python.
A deliberate failing mutant simulates dropping detail reconciliation and must produce a failing mutant witness.

## Launch

There is no live server. Python 3.12 via mise is used. Isolated temporary state is maintained without persistent artifacts. Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh launch` to verify environment readiness.

## Doctor

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh doctor`. The doctor runs policy and configuration checks.

## Drive

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh drive`. This invokes `scripts/agnix_guard.py --formal` and runs `uv run pytest -q tests/test_agnix_guard.py`.

## Proof bar

All 288 bounded real-code receipt states must match expected verdicts. The deliberate negative mutant must be caught. Reduce scenario verdicts with the strict failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.

## Evidence

Capture git commit, exit code receipts, tool version, and negative witness detection status. The evidence tier is offline for the bounded checker, never observed_live.

## Cleanup

The driver creates no persistent files and cleans up any isolated scratch state. No processes remain running.

## Helpers

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh all` to execute doctor, launch, drive, and cleanup in sequence.
