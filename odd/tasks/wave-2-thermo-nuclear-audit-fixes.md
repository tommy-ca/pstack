# Feature: wave-2-thermo-nuclear-audit-fixes
Epic #1335: Wave 2 Thermo-Nuclear Audit Fixes: Check Selection, Surface Revisions, Upstream Guide Regex, and Skill Links

## Specs
S1: Fix shadowed CHECK_SELECTION_TABLE rules, catch (OSError, ValueError) on corrupt receipts in select_checks_action, and accept 7-40 hex char abbreviated SHAs in tests/test_verify_harness_guides.py.
S2: Deduplicate 3x JSON canonical hashing into _hash_json_file, align geteuid() in _read_driver_core_cache, guard curr_val in evaluate_plane_staleness, and fix broken links and table formatting across skills and references.
S3: Sync live Antigravity plugin, refresh 6-harness durable evidence receipts, qualify offline test suite, and close Epic #1335.

## Tasks
- [x] T1: S1, Issue #1336 Fix check selection shadowing, receipt unreadability ValueError, and 7-40 hex SHA regex (inline direct, 002f0817, PR #1339)
- [x] T2: S2, Issue #1337 Deduplicate JSON hashing, align geteuid(), guard evaluate_plane_staleness, and fix skill links (inline direct, af327658, PR #1342)
- [x] T3: S3, Issue #1338 Sync Antigravity plugin, refresh 6-harness receipts, qualify full gate, and close Epic 1335 (inline direct, c49ae3c8, PR #1343)

## Log
L1: /pstack:poteto-mode research, explore, review and audit, recursive plan and update to epics/issues graph, with /thermos, build and verify with swarm, arena, interrogate, new stacked prs, ship the stack then
