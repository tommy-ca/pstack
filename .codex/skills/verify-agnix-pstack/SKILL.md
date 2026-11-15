---
name: verify-agnix-pstack
description: "Use when changing PStack Agent Skills, AGENTS.md, agent definitions, host rules, or pinned Agnix lint configuration. Validates the static guard."
disable-model-invocation: true
---

# Verify Agnix PStack agent configuration guard

This Codex-local verification skill complements canonical creator and maintainer skills. It is not a replacement for host-dependent execution. Read `features/README.md` for the deterministic sweep order.

## Launch

There is no server. Use repository mise-pinned Agnix v0.61.0 and Python 3.12. Install pinned tools via mise install. Run `bash .codex/skills/verify-agnix-pstack/scripts/driver.sh launch` to check the static policy. No tracked files are modified.

## Doctor

Run `bash .codex/skills/verify-agnix-pstack/scripts/driver.sh doctor`. The doctor checks reviewed configuration and installed pinned Agnix binary. Missing dependencies are BLOCKED.

## Drive

Run `bash .codex/skills/verify-agnix-pstack/scripts/driver.sh drive`. This invokes the `scripts/agnix_guard.py` read-only CLI. It checks parsed JSON receipts and enforces a non-vacuous 325-file minimum, exact Agnix version, and zero errors.

## Proof bar

Every required active configuration stays in scope. The reviewed policy remains enabled. The pinned version matches and Agnix reports no errors. Nonzero, malformed, or contradictory receipts fail closed. A static PASS does not prove a skill triggers or an agent executes.

## Evidence

Record exact git commit, tool version, `files_checked`, diagnostic counts, exit status, and negative witness case IDs. The evidence tier is offline for the bounded checker and static for Agnix lint, never observed_live. FAIL beats BLOCKED. BLOCKED beats UNTESTED. UNTESTED beats PASS.

## Cleanup

The runner is read-only. It starts no persistent service, does not auto-fix, and creates no persistent data. Confirm no tracked files changed during a verification run.

## Helpers

Use `scripts/driver.sh` with `doctor | launch | drive | cleanup | all`. Never call agnix with fix flags in these drivers.
