# Feature: upstream-pin-and-canonical-conformance
Epic #1358: Refresh Canonical Pin to 0.15.42 and Align Conformance Artifacts

## Specs
S1: Clean up worktrees and verify strict confinement per principle-boundary-discipline.
S2: Research, explore, review and audit the above with /thermos across correctness, security, and code quality.
S3: Promote UPSTREAM pin and pstack.package.json upstream_pin to 0.15.42 (commit bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7).
S4: Regenerate openspec/canonical-inventory.json and openspec/canonical-drift.json with zero unmapped gaps.
S5: Build and verify with swarm, arena, and interrogate, project manifests, sync live Antigravity plugin, refresh 6-harness receipts with ALL FRESH status, ship new stacked PRs, and close Epic #1358.

## Tasks
- [ ] T1: S1, S2, S3, Issue #1359 Update UPSTREAM pin and pstack.package.json to 0.15.42 (inline direct, pending)
- [ ] T2: S4, Issue #1360 Regenerate canonical inventory and canonical drift artifacts (inline direct, pending)
- [ ] T3: S5, Issue #1361 Sync Antigravity plugin, refresh 6-harness receipts, qualify full gate, and close Epic 1358 (inline direct, pending)

## Log
L1: /pstack:poteto-mode clean up worktrees, research, explore, review and audit the abve, recursive plan and update to epics/issues graph, with /thermos, build and verify with swarm, arena, interrogate, new stacked prs, ship the stack then
