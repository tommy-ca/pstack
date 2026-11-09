# Feature: recursive-plan-validation-and-spec-hygiene
Epic #1304: Thermo-Nuclear Review, Recursive Plan Validation Tooling, and Living Spec Hygiene

## Specs
S1: Propose OpenSpec change `2026-11-09-recursive-plan-validation-and-spec-hygiene` with ADR, proposal, and tasks per openspec-git-discipline.
S2: Support `--help` and `-h` in `skills/poteto-mode/scripts/check-plan.mjs`, exiting with code 0 and displaying usage without `ENOENT: no such file or directory, open '--help'`.
S3: Decompose `Requirement: Multi-phase plans expose a validated dependency graph` in `openspec/specs/pstack-recursive-plan-validation/spec.md` into two requirements under 500 characters each to clear OpenSpec strict validation warnings.
S4: Qualify 6-harness verification matrix (`verify_portable.py check-evidence --host all`), refresh static evidence receipts, archive OpenSpec change per openspec-git-discipline, and close Epic #1304.

## Tasks
- [x] T1: S1, Issue #1305 Propose change `2026-11-09-recursive-plan-validation-and-spec-hygiene` (inline direct, 60376c41)
- [x] T2: S2, S3, Issue #1306 Implement `--help` CLI handling and spec requirement decomposition (inline direct, c5ee70a4)
- [x] T3: S4, Issue #1307 Refresh evidence, archive change, qualify 6-harness matrix, and close Epic 1304 (inline direct, 10add86a)

## Log
L1: /goal /pstack:poteto-mode pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review build and update verification skills/tools, clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate, new stacked prs, merge and ship then, end to end verify the workflows then
