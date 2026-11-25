# Feature: Staging Primitives, Inverted Dependency Resolution, and Backlog Reconciliation
Epic #1463. Clean dependency inversion, DRY staging primitives, and execution backlog integrity.

## Specs
S1. Relocate skill_names and skill_files to package_install_staging.py and eliminate inverted circular import (Issue #1464).
S2. Streamline sync_antigravity_plugin.py reconciliation and harmonize staging helpers (Issue #1465).
S3. Reconcile todo.md execution program backlog and qualify 6-harness static matrix (Issue #1466).

## Tasks
- [x] T1 (S1): Move skill_names and skill_files to scripts/package_install_staging.py, re-export in sync_antigravity_plugin.py, and eliminate dynamic inline imports. (route: inline) [commit: 644916d, PR #1467]
- [x] T2 (S2): Streamline sync_live_plugin() in scripts/sync_antigravity_plugin.py to reuse staging primitives and eliminate redundant checks. (route: inline) [commit: 9770ed0, PR #1468]
- [x] T3 (S3): Reconcile todo.md execution program with Epics #1425, #1436, #1447, and #1456, refresh static receipts across all 6 harnesses, and verify full test suite. (route: inline) [commit: pending, PR #1469]

## Log
L1: /swarm /pstack:poteto-mode deep review, audit the above, with /pstack:thermos, analyze repo with graphicle, with SOLID, KISS, DRY and YAGNI, recursive plan and update epics/issues graph, build and verify, with swarm, arena, interrogate, new stacked prs, ship the stack then
