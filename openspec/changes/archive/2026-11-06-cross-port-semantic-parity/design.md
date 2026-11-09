# Cross-Port Semantic Parity Design: 2026-11-06

## Context & Architecture

Target `tommy-ca/pstack` maintains six native host adapters (Grok, Codex, OMP, OpenCode, Antigravity, Droid) with strict host-neutral adapter boundaries and typed portability schemas. Canonical PStack (`cursor/plugins`) reached 0.15.36 with agentic Orchestrate. Comparator `michael-denyer/pstack-claude` synchronized to 0.15.36 while expanding declared policy forks and host packaging guidance across 86 commits.

This design reconciles the comparator's advancements into target's existing architecture while strictly preserving:
1. SOLID, KISS, DRY, and YAGNI engineering discipline.
2. Single host-owned control plane (no imported Node child-process runners or `~/.claude/orchestrate` stores).
3. Clear separation of offline static checks from observed live runtime receipts.

## Pinned Source Ledger

| Role | Repository | Commit SHA | Release Tag | Date |
| --- | --- | --- | --- | --- |
| Canonical | `cursor/plugins` | `c742dd61706fbacc1b95f1a20b7b988cf096ce6c` | `v0.15.36` | 2026-10-27 |
| Comparator | `michael-denyer/pstack-claude` | `d88063f3355a5ecff0e6dbb890a11bab4b08bc2e` | `v0.9.130` | 2026-11-05 |
| Target Base | `tommy-ca/pstack` | `5d58283f40f7fc8f56a536946abe79418538fe6e` | `v0.15.29-preview.0` | 2026-11-06 |

## Fork Disposition Taxonomy

Comparator `tools/forks.json` lists 65 entries:
- **Adapt (14)**: Adopted as host-neutral conventions (`agents/comment-sicko.md`, `skills/deslop/SKILL.md`, `skills/no-comments/SKILL.md`, architectural reconciliation prompts).
- **Preserve (28)**: Canonical cursor behavior maintained against comparator rephrasing.
- **Policy-Fork (6)**: Comparator-specific policy adjustments retained in reference inventory but never promoted to canonical target behavior.
- **Exclude (17)**: Windows Node script wrappers, TLC-specific line ending filters, and Claude-only state directories.

## Portable Negative Invariant Contracts

To verify cross-port equivalence without importing comparator runtime code, we harvest 5 portable negative invariants into contract tests:
1. **Settled / Canceled Non-Pass**: A canceled or terminated child process cannot report a passing verdict.
2. **Identity-Bound Settlement**: Tool completion must match the exact child invocation ID.
3. **Worktree Confinement**: Modifications outside the allocated worktree root or untracked file leaks must fail verification.
4. **Authorization Denials**: Sensitive paths and headless asks without explicit grant must fail-closed.
5. **Scheduler Wakeup Discipline**: A timer canceled before fire must not deliver a delayed wakeup.

## Verification & Guardrails

- Offline static checks run hermetically without requiring external daemons or non-standard PATH tools.
- Live proofs require real binary observations; missing tools produce `BLOCKED` or `UNTESTED`, never simulated `PASS`.
- Changed patches undergo Thermo-Nuclear review for code quality and maintainability.
