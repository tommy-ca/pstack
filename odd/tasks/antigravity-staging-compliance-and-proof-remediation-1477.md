# Feature: Antigravity Plugin Staging Spec Compliance and Proof Remediation
Epic #1477. Remediation of Antigravity commands staging defect, strict CLI validation conformance, and receipt refresh.

## Specs
S1. Revert commands projection in write_antigravity_assets(), align compute_managed_files() with Antigravity plugin contract, and update lifecycle safety assertions (Issue #1478).
S2. Verify prove_antigravity_native_package() passes with zero warnings under agy plugin validate --strict, qualify test_antigravity_native_package_proof, and refresh 6-harness static receipts (Issue #1479).
S3. Reconcile todo.md execution backlog, verify live plugin sync parity, and ship stacked PRs to main (Issue #1480).

## Tasks
- [x] T1: Remove commands directory from write_antigravity_assets, adjust managed files, and update test_package_lifecycle_safety.py (linked: S1, route: direct inline, commit: cde67ee)
- [x] T2: Qualify prove_antigravity_package, test_antigravity_native_package_proof, and refresh static receipts (linked: S2, route: direct inline, commit: cc32df9)
- [x] T3: Reconcile todo.md backlog, verify live sync, and ship stacked PRs (linked: S3, route: direct inline, commit: 8f2708a)

## Log
L1. User requested /swarm /pstack:poteto-mode clean up worktrees, deep review, audit the above, analyze repo with graphicle, with SOLID, KISS, DRY and YAGNI, review and sync upstream cursor pstack, with thermos, recursive plan and update epics/issues graph, build and verify, with swarm, arena, interrogate, new stacked prs, ship the stack then
