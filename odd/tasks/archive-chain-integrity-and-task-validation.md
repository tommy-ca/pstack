# Feature: Archive Chain Integrity and Task Validation
Tracking document for Epic #1272: Reconcile archived OpenSpec task completion, wire archived validation into mise and verification tooling, and qualify full offline gate.

## Specs
S1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review"
S2: "build and update verification skills/tools"
S3: "clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate"
S4: "new stacked prs, merge and ship then, end to end verify the workflows then"
S5: "Every completed archived OpenSpec change MUST contain proposal.md, at least one Markdown specification under specs/, design.md, adr.md, tasks.md, and .openspec.yaml. Each task checkbox MUST have a closed outcome."
S6: "Validate that archived changes have all tasks completed (for pre-commit linting)"

## Tasks
- [x] T1 (S1, S3, S5) [route: inline] [commit: 8fde721] Reconcile archived task outcomes in 2026-10-11-deepseek-skill-portability, 2026-10-12-poteto-audit-reconcile, and 2026-10-13-pstack-jev-decision-plane per archive-chain-integrity.
- [x] T2 (S1, S2, S6) [route: inline] [commit: 66716c7] Expose validate:openspec:archived and update validate:openspec in mise.toml, extend audit_openspec_status in scripts/scaffold_verification_skill.py, and wire test_direct_bunx_openspec_validate_archived_execution in tests/test_openspec_direct.py.
- [x] T3 (S1, S3, S4) [route: inline] [commit: pending] Author thermo-nuclear review deliverable in /tmp/pstack-thermo/, update summary.md, sync docs/verification-test-tiers.md and todo.md, execute stacked PRs, merge, and qualify 6-harness matrix end-to-end.

## Log
L1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review build and update verification skills/tools, clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate, new stacked prs, merge and ship then, end to end verify the workflows then"
