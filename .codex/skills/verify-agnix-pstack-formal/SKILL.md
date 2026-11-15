---
name: verify-agnix-pstack-formal
description: "Use when changing PStack Agnix receipt acceptance, fail-closed policy, or finite-state negative witnesses; verifies bounded receipt guard invariants."
disable-model-invocation: true
---

# Verify Agnix receipt guard invariants

This Codex-local verification skill complements PStack's canonical creator/maintainer skills; it is not a replacement for host-dependent execution. Read `features/README.md` for the deterministic sweep order.

## Launch

There is no server. Use Python 3.12 via the PStack mise toolchain; no Agnix binary is required to exhaust the real verdict predicate. Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh launch` to check the static policy. No tracked files are modified.

## Doctor

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh doctor`. The doctor checks the static governed configuration without executing a host agent.

## Drive

Run `bash .codex/skills/verify-agnix-pstack-formal/scripts/driver.sh drive`. This invokes the production `scripts/agnix_guard.py --formal` acceptance predicate across 216 bounded states and verifies that a deliberately weakened error filter produces a negative witness.

## Proof bar

Every enumerated receipt state agrees with the independently described expected decision; the weakened error-filter mutant must be caught. This is finite, bounded acceptance-logic assurance, not proof of the external Agnix binary or of live agent behavior.

## Evidence

Record the exact git commit, tool version, `files_checked`, diagnostic counts, exit status, and negative witness state count. The evidence tier is `offline` for the bounded checker and `static` for Agnix lint, never `observed_live`. FAIL beats BLOCKED; BLOCKED beats UNTESTED; UNTESTED beats PASS.

## Cleanup

The runner is read-only, starts no persistent service, does not auto-fix and creates no persistent data. Confirm no tracked files changed during a verification run.

## Helpers

Use `scripts/driver.sh` with `doctor | launch | drive | cleanup | all`. Never call `agnix --fix` in these drivers.
