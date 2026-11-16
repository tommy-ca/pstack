# Feature agnix-warning-budget-ratchet
Epic #1411. Triage and Ratchet Agnix Warning Budget Down to 31

## Specs
S1. Eliminate XP-SK-002 author identity path leakage and XML-001 unclosed XML tags (Issue #1412).
S2. Resolve AS-013 multi-level reference nesting in setup-pstack and benny automations (Issue #1413).
S3. Ratchet Agnix warning baseline budget ceiling from 37 down to 31 and verify bounded model (Issue #1414).

## Tasks
- [x] T1 (S1) Implement Unit 1 (Issue #1412) eliminate XP-SK-002 and XML-001 warnings (inline direct) (commit 544243fa, PR #1415)
- [ ] T2 (S2) Implement Unit 2 (Issue #1413) resolve AS-013 reference nesting (inline direct)
- [ ] T3 (S3) Implement Unit 3 (Issue #1414) ratchet warning budget to 31 and verify 288-state model (inline direct)

## Log
L1. /pstack:poteto-mode clean up worktrees, research, explore, review and audit the recent prs, recursive plan and update to epics/issues graph, with /thermos, build and verify with swarm, arena, interrogate, new stacked prs, ship the stack then
