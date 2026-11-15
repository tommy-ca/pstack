# Feature: post-0-15-42-thermo-nuclear-hardening
Epic #1376: Post-0.15.42 Thermo-Nuclear Code Quality Hardening & Import Hygiene Remediation

## Specs
S1: Clean up worktrees and verify strict confinement per principle-boundary-discipline.
S2: Research, explore, review and audit the recent PRs with /thermos across correctness, security, performance, and code quality.
S3: Recursive plan and update to epics/issues graph (Epic #1376, Issues #1377, #1378, #1379).
S4: Build and verify Unit 1 (Issue #1377) eliminating unused imports and dead symbols across scripts/ while preserving re-export facades.
S5: Build and verify Unit 2 (Issue #1378) cleansing import blocks, unsorted imports, and typing hygiene across tests/.
S6: Build and verify Unit 3 (Issue #1379) synchronizing live Antigravity plugin, verifying 6-harness package lifecycle, refreshing durable receipts, opening stacked PRs, shipping the stack, and closing Epic #1376.

## Tasks
- [ ] T1: S1, S2, S3 Audit delta, verify worktrees, and initialize graph (inline direct) - Epic #1376
- [ ] T2: S4 Implement Unit 1 (Issue #1377) scripts/ import hygiene and facade preservation (inline direct)
- [ ] T3: S5 Implement Unit 2 (Issue #1378) tests/ import block and typing hygiene (inline direct)
- [ ] T4: S6 Implement Unit 3 (Issue #1379) gate qualification, 6-harness receipts, and shipping (inline direct)

## Log
L1: /pstack:poteto-mode clean up worktrees, research, explore, review and audit the recent prs, recursive plan and update to epics/issues graph, with /thermos, build and verify with swarm, arena, interrogate, new stacked prs, ship the stack then
