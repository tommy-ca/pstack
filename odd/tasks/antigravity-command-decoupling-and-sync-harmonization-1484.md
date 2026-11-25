# Feature: Antigravity Command Staging Decoupling and Sync Harmonization
Epic #1484. Decouple Antigravity command projection between package staging and host installation, harmonize live sync and test contracts.

## Specs
S1. Parameterize write_antigravity_assets with include_commands, stage package without commands (strict agy validate compliance), and project commands on host installation (Issue #1485).
S2. Qualify full test_sync_antigravity_plugin, test_antigravity_verification, and refresh durable static receipts (Issue #1486).
S3. Reconcile todo.md execution backlog, track feature tasks, and ship stacked PRs to main (Issue #1487).

## Tasks
- [x] T1: Decouple command projection in write_antigravity_assets and restore managed files tracking (linked: S1, route: direct inline, commit: 3234982, PR #1480)
- [x] T2: Qualify antigravity driver and sync tests, refresh static receipts (linked: S2, route: direct inline, commit: 32098f6, PR #1481)
- [x] T3: Reconcile todo.md backlog, verify live sync, and ship stacked PRs (linked: S3, route: direct inline, commit: pending, PR #1482)

## Log
L1. User requested /swarm /pstack:poteto-mode clean up worktrees, deep review, audit the above, analyze repo with graphicle, with SOLID, KISS, DRY and YAGNI, review and sync upstream cursor pstack, with thermos, recursive plan and update epics/issues graph, build and verify, with swarm, arena, interrogate, new stacked prs, ship the stack then
L2. Decoupled write_antigravity_assets(..., include_commands=False) for package validation and include_commands=True for host installation / live sync.
L3. Refreshed 6-harness static receipts via verify_portable.py refresh-static --host all to align package_driver_revision with modified package_install_staging.py.
L4. Synchronized leftover-scanner gotchas doc with .graphicle skip dir in scripts/verify_harness.py.
