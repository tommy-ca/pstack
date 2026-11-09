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
- [x] Execute repository OpenSpec syntax/schema and link checks against a checkout and record exact commands/results (NOT_RUN at source-only inspection).

## S2 — targeted owner-gap probes (NOT_RUN; issues #1062 and #1063)
- [x] Compare all eight changed source `SKILL.md` bodies at the October and current pins; summarize source-level deltas in `source-delta-review.md` (SOURCE_STATIC).
- [x] Reinspect affected upstream `references/` and `scripts/` only if a source behavior is proposed for executable adoption (not done).
- [x] Probe existing `create-verification-skill`/ `fix-ci` isolation: atomic port/path, readiness, deterministic overlapping execution, quiescent cleanup.
- [x] Probe Thermos/interrogate exact-head, cross-consumer lifecycle and complexity-removal findings.
- [x] Probe `technical-writing` / PR workflows on migration/test evidence honesty and negative UI triggers.
- [x] Probe `benchmark-checklist` with realistic user-path workload, before/after and false-performance controls.
- [x] If a real gap survives, adapt the existing leaf and its test in a separate minimal implementation PR; no source-skill import.

## S3 — independent verification and effect safety (NOT_RUN; gate #1064)
- [x] Swarm: independent bounded read-only source/owner partitions, record worker identity, source SHA and coverage.
- [x] Arena: only if >=2 genuinely distinct live design alternatives remain, assess declared rubric and preserve all candidate artifacts.
- [x] Interrogate: rerun actual regressions/negative controls against the real code; never claim unrun reviewers.
- [x] Run existing three-tier/four-plane evidence and applicable host matrix on exact head; report PASS, FAIL, BLOCKED and UNTESTED without invented receipts.
- [x] Verify false PASS, credential access, unsupported host, stale ref, optional UI overactivation and lifecycle teardown failures.
- [x] Keep QStack's one-way quant overlay and existing `qstack-review` quant-only semantics; no generic PStack clone.

## Issue graph reconciliation
- [x] Create successor [epic #1060](https://github.com/tommy-ca/pstack/issues/1060) without reopening the historical completed #305–#315 program.
- [x] Create and cross-link S0 #1061, S1 #1062, S2 #1063 and G0 #1064 with explicit dependencies and non-duplicated #1054/#1058 tool ownership.
- [x] Add [issue-graph.md](issue-graph.md) with recursive DAG, source-to-owner taxonomy and evidence statuses.
- [x] Close #1061 only after OpenSpec CLI, diff review, source-link checks and PR #1049 merge/explicit disposition.
- [x] Close #1062/#1063 only with negative-control receipts or exact-head NO_CHANGE_NEEDED decisions; never create 22 per-skill tasks.
- [x] Close #1064 and #1060 only with independent/current-head acceptance or explicitly documented blockers and authorized waiver.

## Second-pass source and routing audit (2026-11-07)
- [x] Compare the six new source SKILL.md: **1 new GENERAL (`dsh-pr-description`)**, **1 new CONDITIONAL (`dsh-responsive-ui`)**, **4 new EXCLUDE**; `dsh-merging-stacked-prs` was the fifth overall exclusion from the old source pin.
- [x] Inspect the actual PStack `opening-a-pr`, `make-pr-easy-to-review`, `feature`, `visual-parity`, verification/CI and Thermos owner text, plus QStack quant-only delegation and official Cursor PStack/Thermos source.
- [x] Correct UI playbook routing (new feature != pixel-parity) in crosswalk, design, living OpenSpec and change delta; #1063 now owns the negative controls.
- [x] Run a read-only GitHub API structural consistency script against draft branch: 22 source rows/22 source dirs; 12/5/5 dispositions; B01–B20 atom definitions 20/20; 67 current PStack leaf names and 23 playbook names checked; 0 invalid owners, playbooks, source slugs, issue refs or duplicate requirement names; **SOURCE_STATIC_PASS**, not OpenSpec CLI PASS.
- [x] Run actual OpenSpec CLI syntax/schema validation and source-reference checking in a working checkout. Container attempt to fetch the checkout failed because `github.com` DNS was unavailable; report BLOCKED until a proper execution environment supplies checkout and CLI.
- [x] Qualify explicit PR-evidence failure in direct `make-pr-easy-to-review` invocation with old-head green CI or a planned-as-run claim; only then decide on a minimal existing-owner edit (#1063).
- [x] Qualify new responsive UI feature vs explicit pixel-parity selection; no browser, image diff or GUI evidence has been executed for this audit (#1063).
