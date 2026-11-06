# Tasks: Cross-Port Semantic Parity (Epic #906)

## Unit 1: Source Pins & Fork Classification (Issue #907)
- [x] Pin three sources: `cursor/plugins@c742dd61`, `pstack-claude@d88063f3`, `tommy-ca/pstack@5d58283f`.
- [x] Classify all 65 declared comparator fork paths in `docs/research/pstack-claude-forks-2026-11-06.json`.
- [x] Produce comprehensive three-source analysis in `docs/research/cross-port-semantic-delta-2026-11-06.md`.
- [x] Verify license and NOTICE posture (MIT, clean-room adapter boundaries).

## Unit 2: Portable Negative Scenarios (Issue #908)
- [x] Port negative scenario contracts into `tests/test_cross_port_contracts.py`.
- [x] Verify canceled/settled non-passage contract.
- [x] Verify exact tool invocation ID binding contract.
- [x] Verify worktree untracked and symlink isolation contract.
- [x] Verify headless permission fail-closed contract.
- [x] Verify scheduler late-wakeup cancellation contract.

## Unit 3: Code-Linked Formal Invariants (Issue #909)
- [x] Specify bounded safety and liveness properties in target verifiers (`scripts/verify_cross_port_invariants.py`).
- [x] Bind each invariant to atomic transition and code paths.
- [x] Implement mutant falsifiers for each property.
- [x] Verify reachable mutants fail and baseline passes (`tests/test_cross_port_formal_invariants.py`).

## Unit 4: Source-Backed LLMWiki Curation (Issue #910)
- [x] Create source-attributed cross-port analysis in `.llm-wiki/wiki/analyses/cross-port-semantic-atoms-2026-11-06.md`.
- [x] Extract semantic atoms (intent, policy, lifecycle, worktree, admission, evidence, review).
- [x] Run `python3 scripts/llm_wiki.py check` and `python3 scripts/llm_wiki.py index`.
- [x] Verify graph connectivity with `python3 scripts/llm_wiki.py graph`.

## Unit 5: Acceptance Gate & Verification (Issue #911)
- [x] Run Swarm matrix across independent lanes.
- [x] Arena comparison on candidate designs (Candidate B selected in `docs/research/arena-cross-port-architecture-2026-11-06.md`).
- [x] Interrogate adversarial tests.
- [x] Run Thermo-Nuclear code quality and maintainability review against changed diff (`docs/audit/thermo-nuclear-cross-port-acceptance-2026-11-06.md`).
- [x] Refresh durable evidence receipts.
