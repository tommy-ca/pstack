# Recursive execution graph: DeepSeek portable skill patterns

**Status:** proposed / specification only; no native behavioral tests executed by this document.

## Graph

```text
#305 Epic — DeepSeek skill curation into pstack
├── #306 Sub-epic — source/spec/eval
│   ├── #308 [P0] pinned 16-skill inventory and overlap crosswalk
│   ├── #309 [P0] formal semantic contracts and composition      ← #308
│   └── #310 [P1] baseline/candidate eval + negative controls     ← #308, #309
└── #307 Sub-epic — reuse/acceptance
    ├── #311 [P0] CI test isolation pilot                         ← #309
    ├── #312 [P0] change-scoped verification pilot                ← #309, #311
    ├── #313 [P1] exact-head code review/error/simplification     ← #309, #311, #312
    ├── #314 [P2] context/prose and optional domain overlays      ← #309, #310
    └── #315 [Gate] six-host Swarm/Arena/Interrogate             ← #310–#314
```

Existing external owners: #259 verification skill/scaffolding, #281 role boundary, #288 OMP actual native evidence and #303 route containment. They remain separately owned and MUST NOT be closed or treated as proved by this program.

## Phase 0 — prove selection [#308, #309]

- [x] Audit the list of 16 source SKILL.md files at a frozen DSH commit (desk review).
- [x] Draft a full 16-row decision crosswalk (this change).
- [x] Draft requirements, design, source trail, contracts and negative-control scenarios (this change).
- [ ] Review all adjacent reference materials in task #308 and verify every source-to-pstack behavioral mapping.
- [ ] Cross-check against canonical current tree at refreshed pins; run OpenSpec validators.

## Phase 1 — one vertical slice [#311, #312]

- [ ] Model per-fixture resource lifecycle and cross-process contention (RED).
- [ ] Implement host-neutral resource allocation, readiness and quiescence (GREEN).
- [ ] Verify state-based negative control, cross-platform behavior, no test flake masking.
- [ ] Resolve exact-head changed scope and map to relevant gates; refresh on head change.
- [ ] Issue durable receipts in existing schemas, no new reducer or global runner.

## Phase 2 — measured optional enrichment [#310, #313, #314]

- [ ] Run blinded existing vs proposed behavior cases and include false activations.
- [ ] Incorporate typed partial/unknown effects and review/source pin checks.
- [ ] Prove simplification with consumer search and equivalence, not byte count.
- [ ] Validate context work (tokens + repeated reads + errors) before optimizing tool/skill prose.
- [ ] Keep UI, docs, release, translation, archive and GIF behaviors opt-in by project capability.

## Phase 3 — verification/acceptance [#315]

- [ ] Arena: compare enrich-existing vs standalone new skill; require evidence to deviate from enrich-existing.
- [ ] Swarm: independent code/eval/host parity lanes with actual artifacts and revision hashes.
- [ ] Interrogate: challenge false PASS, stale receipts, untrusted skill text, partial-state retries, flaky resource cleanup, source drift, destructive ownership, DSH-specific commands.
- [ ] Six-host offline verification; host-dependent smoke and observed-live only where actually executed.
- [ ] Check #303 path containment regression and #288 OMP runtime proof independently.
- [ ] PR merge and exact-head receipt reconciliation. Close graph only with documented residual gaps.

## Stop conditions

No production skill import until #308 and #309 are reviewed. No claim of transferable success until #310 corpus, no general rollout before #311/#312 pilot proves positive and negative cases. No `verified` host status from offline-only receipts. Keep DSH source instructions out of executable authority.
