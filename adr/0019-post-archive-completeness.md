# ADR 0019: Post-Archive Completeness and its relation to ADR-0007

- Status: accepted
- Date: 2026-10-13

## Context

ADR-0007 (`adr/0007-openspec-archive-chain-gate.md`, 2026-08-31) records one gate: active task-complete changes MUST carry `design.md` and `adr.md` before archive, and `openspec/changes/archive/` is out of that guard's scope.

Later the same day, commit `ad0392b` ("fix(openspec): complete archived intent chains") added a second, independent gate to `scripts/verify-harness.py`: `archived_changes_missing_artifacts()` fails the harness when any directory under `openspec/changes/archive/` lacks `proposal.md`, `design.md`, `adr.md`, `tasks.md`, `.openspec.yaml`, or any `specs/**/*.md`. That commit also backfilled `design.md` and `adr.md` into the four archived changes that lacked them (`2026-08-31-pstack-atomic-blocks`, `-grok-host-contract`, `-plugin-schema`, `-sync-from-upstream`).

ADR-0007 alone therefore cannot be read to describe current behaviour: its "historical archives are preserved as-is" consequence holds for the pre-archive guard, but the archive tree is now separately checked and was repaired. Two different gates exist — pre-archive readiness and post-archive completeness — and only the first is recorded in a durable decision.

## Decision

1. Keep `scripts/verify-harness.py::archived_changes_missing_artifacts()` in force (introduced by `ad0392b`, 2026-08-31): every directory under `openspec/changes/archive/` MUST contain `proposal.md`, `design.md`, `adr.md`, `tasks.md`, `.openspec.yaml`, and at least one `specs/**/*.md`; the harness exits non-zero listing each gap.
2. Treat the two gates as distinct contracts with distinct failure messages, neither substituting for the other: pre-archive readiness (`archivable_changes_missing_artifacts()`, ADR-0007) applies to active task-complete changes, post-archive completeness (this ADR) applies to everything already under `openspec/changes/archive/`.
3. New archives MUST carry the full intent chain at archive time. The completeness gate is a defect detector, not an archiving mechanism.
4. The `ad0392b` backfill of archives that lacked the chain is the deliberate, one-time exception to ADR-0007's "preserved as-is" wording. That wording continues to govern the pre-archive guard's scope; it does not license new archive gaps.
5. ADR-0007 stays accepted and unamended. Accepted ADRs are immutable history, so the later policy and its relation to ADR-0007 are recorded here rather than by rewriting ADR-0007's Decision section.
