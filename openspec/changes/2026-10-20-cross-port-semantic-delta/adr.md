# ADR Review Manifest

- Status: accepted (Program #636, Waves 1-2 #637/#638 fulfilled)
- Review date: 2026-10-20
- Change: 2026-10-20-cross-port-semantic-delta

## In-Force ADRs Reviewed

- `adr/0006-host-owned-orchestration-state.md` - State remains host-owned; no parallel orchestration store or foreign runtime engines imported. Child progress and agent activity remain ephemeral and private.
- `adr/0012-portable-package-descriptor-and-projection.md` - `pstack.package.json` stays the authority across the 6-host matrix; comparator foreign files are rejected or adapted as host-scoped tests.
- `adr/0014-portable-verification-skills-architecture.md` - Verification skills stay host-scoped; contract tests verify observable postconditions directly.
- `adr/0021-harness-neutral-model-role-policy.md` - Model role policy resolves against observed host catalogs; unobserved foreign reference aliases fail closed without claiming native capability.

## Architectural Decision

- Comparator delta from `michael-denyer/pstack-claude@88f6d39` (0.9.95) is resolved without importing foreign runtime/session engines.
- Worktree cleanup guarantees user data safety by forcing `-uall` on `git status --porcelain`, overriding `status.showUntrackedFiles = no`.
- Observable negative contracts are codified in `tests/test_cross_port_contracts.py`.
