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

## Second-pass issue refinement and measurable gates (2026-10-11)

**Review outcome:** no new epic needed. Keep root #305 and re-use #308–#315; link the three new companion spec files from draft PR #317. Distinguish source pin from current main drift.

- **#308 (source facts):** convert the 16-row ledger into source-pinned entries with exact source paths, skill trigger, pstack owner, positive/negative task and evidence-level. Read supporting source references for high-priority candidates; file risk/assumption corrections.
- **#309 (requirements):** map B01–B20 to owners and scenario IDs, document smallest chosen contracts, confirm no added router/reducer/runtime enum. Validate the qualification schema with valid/invalid fixture records.
- **#310 (eval in two passes):** collect unmodified baseline E01–E07 / negative N01–N07 **before** implementation; rerun a candidate after #311–#314. Publish sanitized blinded scoring plus external proof and uncertainty. This is an ongoing issue, not a dependency cycle.
- **#311 (pilot 1):** run one Python and one TypeScript resource isolation case with a pre-fix collision, controlled barrier, unique allocation, deterministic postcondition and quiescent release.
- **#312 (pilot 2):** run one revised-head invalidation case, dirty-scope cases if available, and negative false-PASS cases; keep existing portability receipt schema.
- **#313 (quality):** review external reachability, partial write/unknown effects and outcome disclosure. Small focused behavioral tests; no new competing slash command.
- **#314 (conditional):** measure total context cost; use explicit activation fences for UI, bilingual docs, upgrade guides, archival governance, browser recording and stack APIs.
- **#315 (acceptance):** Arena challenge architecture and applicability; Swarm independently verify artifacts; Interrogate attack source trust, false PASS, stale-head, resource leaks and host command leakage. **If a host is unavailable, report its native status as BLOCKED/UNTESTED rather than require fabricated universal success.**

See [qualification-and-eval.md](qualification-and-eval.md) for the exact corpus, acceptance thresholds and stopping rules. A completed source audit is not a completed end-to-end implementation. Native OMP lifecycle is owned by #288 and security containment by #303.
