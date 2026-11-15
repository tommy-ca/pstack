# Bounded Agnix guard predicate

## Sub-features

Wrong version, insufficient files, error-level diagnostic, nonzero exit, warning budget and failing mutant.

## How to get to it (user POV)

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh all` in a prepared checkout.

## Driving it with Codex

Run `mise exec -- python scripts/agnix_guard.py --formal`. It explores 216 bounded cases against the production verdict function.

## Gotchas

Counterexamples are bounded to the receipt-admission predicate. Model-to-tool semantic equivalence, external Agnix correctness and native harness behaviors remain UNTESTED.
