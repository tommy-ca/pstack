# Execution plan: reusable PStack skills, not a DSH import

**Live issue graph:** [#1060](https://github.com/tommy-ca/pstack/issues/1060) → [#1061](https://github.com/tommy-ca/pstack/issues/1061) → ([#1062](https://github.com/tommy-ca/pstack/issues/1062) ∥ [#1063](https://github.com/tommy-ca/pstack/issues/1063)) → [#1064](https://github.com/tommy-ca/pstack/issues/1064). See [issue-graph.md](issue-graph.md). Prior frozen program [#305](https://github.com/tommy-ca/pstack/issues/305) remains closed; independent verification tooling [#1054](https://github.com/tommy-ca/pstack/issues/1054)/[#1058](https://github.com/tommy-ca/pstack/issues/1058) remains separately owned.

**At this source-only planning checkpoint:** no independent Swarm, Arena, Interrogate or Thermos execution occurred. The GitHub Actions offline contract run observed on prior head `98c9b8a` succeeded, but subsequent commits require a fresh current-head check. OpenSpec CLI, issue behavioral probes, host-live conformance remain NOT_RUN.

## S0 — read-only source authority (SOURCE_STATIC; issue #1061)
- [x] Resolve pinned DeepSeek 22-skill source and archived 16-skill source.
- [x] Read each of 22 source `SKILL.md` frontmatter/behavior sections and inspect current PStack skill and playbook names.
- [x] Classify all source entries: 12 GENERAL, 5 CONDITIONAL, 5 EXCLUDE.
- [x] Confirm no `dsh-*` skill directory exists in current PStack's top-level skills/ inventory; no source file deletion is needed.
- [x] Preserve original archive and source license/provenance; revise the current PR rather than creating another architecture fork.

## S1 — OpenSpec contract reconciliation (issue #1061)
- [x] Update source-to-owner crosswalk with existing leaf/principle/playbook for each retained behavior.
- [x] Remove DSH-only projection, signing, artwork and Cordis/gh-stack implementation obligations from living generic requirements.
- [x] Keep one route and one implementation owner; formalize lifecycle/test and PR-evidence constraints with negative scenarios.
- [x] Align proposal, design, ADR and delta spec with the same disposition totals.
- [ ] Execute repository OpenSpec syntax/schema and link checks against a checkout and record exact commands/results (NOT_RUN at source-only inspection).

## S2 — targeted owner-gap probes (NOT_RUN; issues #1062 and #1063)
- [x] Compare all eight changed source `SKILL.md` bodies at the October and current pins; summarize source-level deltas in `source-delta-review.md` (SOURCE_STATIC).
- [ ] Reinspect affected upstream `references/` and `scripts/` only if a source behavior is proposed for executable adoption (not done).
- [ ] Probe existing `create-verification-skill`/ `fix-ci` isolation: atomic port/path, readiness, deterministic overlapping execution, quiescent cleanup.
- [ ] Probe Thermos/interrogate exact-head, cross-consumer lifecycle and complexity-removal findings.
- [ ] Probe `technical-writing` / PR workflows on migration/test evidence honesty and negative UI triggers.
- [ ] Probe `benchmark-checklist` with realistic user-path workload, before/after and false-performance controls.
- [ ] If a real gap survives, adapt the existing leaf and its test in a separate minimal implementation PR; no source-skill import.

## S3 — independent verification and effect safety (NOT_RUN; gate #1064)
- [ ] Swarm: independent bounded read-only source/owner partitions, record worker identity, source SHA and coverage.
- [ ] Arena: only if >=2 genuinely distinct live design alternatives remain, assess declared rubric and preserve all candidate artifacts.
- [ ] Interrogate: rerun actual regressions/negative controls against the real code; never claim unrun reviewers.
- [ ] Run existing three-tier/four-plane evidence and applicable host matrix on exact head; report PASS, FAIL, BLOCKED and UNTESTED without invented receipts.
- [ ] Verify false PASS, credential access, unsupported host, stale ref, optional UI overactivation and lifecycle teardown failures.
- [ ] Keep QStack's one-way quant overlay and existing `qstack-review` quant-only semantics; no generic PStack clone.

## Issue graph reconciliation
- [x] Create successor [epic #1060](https://github.com/tommy-ca/pstack/issues/1060) without reopening the historical completed #305–#315 program.
- [x] Create and cross-link S0 #1061, S1 #1062, S2 #1063 and G0 #1064 with explicit dependencies and non-duplicated #1054/#1058 tool ownership.
- [x] Add [issue-graph.md](issue-graph.md) with recursive DAG, source-to-owner taxonomy and evidence statuses.
- [ ] Close #1061 only after OpenSpec CLI, diff review, source-link checks and PR #1049 merge/explicit disposition.
- [ ] Close #1062/#1063 only with negative-control receipts or exact-head NO_CHANGE_NEEDED decisions; never create 22 per-skill tasks.
- [ ] Close #1064 and #1060 only with independent/current-head acceptance or explicitly documented blockers and authorized waiver.
