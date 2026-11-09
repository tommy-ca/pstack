# Feature: PStack Portability Spec Hygiene and Ceiling Reduction
Tracking document for Epic #1297: Reconcile 1,000-line ceiling and eliminate strict validation warnings in living portability specification openspec/specs/pstack-portability/spec.md.

## Specs
S1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review"
S2: "build and update verification skills/tools"
S3: "clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate"
S4: "new stacked prs, merge and ship then, end to end verify the workflows then"
S5: "Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason. Treat this as a strong code-quality smell by default."
S6: "Every OpenSpec state change must cross main before the next lifecycle phase depends on it."

## Tasks
- [x] T1 (S1, S3, S6) [route: inline] [commit: 77aab755] Propose OpenSpec change 2026-11-09-pstack-portability-spec-hygiene and land on main (Issue #1298).
- [x] T2 (S1, S3, S5) [route: inline] [commit: 824326ee] Apply change to openspec/specs/pstack-portability/spec.md, compacting 11 requirements <= 500 chars and total lines <= 900 lines (Issue #1299).
- [x] T3 (S1, S2, S4) [route: inline] [commit: 99741953] Refresh 6-harness static evidence, archive change from main, qualify 6-harness verification matrix and full test battery, update docs and close Epic 1297 (Issue #1300).

## Log
L1: "pick up and resume clean up worktrees, explore, review and aduit with /pstack:thermo-nuclear-code-quality-review build and update verification skills/tools, clean up, reconcile, recursive openspec intent driven flows, plan and update into github epics/issues graph, build and verify with SOLID, KISS, DRY, YAGNI with swarm, arena, interrogate, new stacked prs, merge and ship then, end to end verify the workflows then"
