# Recursive plan and proof dependencies

Tracking [#871](https://github.com/tommy-ca/pstack/issues/871): initial dependency `#872 -> #873 -> (#874, #875) -> #876 -> #877`. **Current evidence:** research #878 merged; accepted baseline choice #873 closed via #880 (source-evidence Arena, not externally measured); #875 deferred by binding decision. Former implementation #879 was closed unmerged on base-ref deletion, so live main lacked its safety code. Draft successor #881 is stacked on main; the current formal spec PR is based on #881.

## Phase 0 — inventory and choice

- [x] Pin PStack `f7e7fbaee23bd19ae7c03861f121ea65c756650f`, Atomicstrata `0f8ff86ef0a28f4c15627a2ea5e94a96cadd834e`, Geronimo `9d974c9e4d9d6c21638a5f520e6d89f79647724e`, QStack `149b6082fe7bcd00e86a13ed48fbf8ee51268882`.
- [x] Read upstream architecture/model, citation, review policy, state recovery, typed frontmatter, ingest, index and architectural invariant specifications.
- [x] Preserve #873 option A as decision and #875 optional adapters as deferred; no claim of live benchmarking.
- [ ] Check licensing and actual upstream SDK/runtime status in future opt-in-only proposal.

## Phase 1 — repair baseline and create skills (#874; review in #881)

- [x] Rebase previously tested 16 changed files from closed #879 into a new branch based on main.
- [x] Include actual stdlib CLI hardening, negative tests, Codex verify skill, bounded-code formal-analysis skill and CI drive.
- [ ] Run exact-head CI on the rebased **new** PR #881 and review its logs.
- [ ] Check CodeQL/host tooling and verify exit codes, symlink threat model, crash/recovery and reporter truth.
- [ ] Run actual pinned TLC or report `UNTESTED`; do not confuse 39 serial histories with concurrent safety.

## Phase 2 — formalize and update wiki (#876; this change)

- [x] Write OpenSpec requirements R-WIKI-001..010 with GIVEN/WHEN/THEN and explicit implementation status.
- [x] Write code/data flows, contract schemas, stable semantic atoms and upstream references.
- [x] Define CandidateEnvelope.v1 JSON Schema with no automatic publication authority.
- [ ] Add schema test vectors (valid and deliberate invalids), run via CI and verification skill.
- [ ] Append source-pinned wiki synthesis and existing index link; never rewrite historical log events.
- [ ] Confirm OpenSpec markdown links, spec source pins and JSON Schema Draft2020-12 syntax with exact-head tests.

## Phase 3 — independent acceptance (#877)

- [ ] Diff-scoped `thermo-nuclear-review` on security, correctness, authorization and races; do not suppress blockers.
- [ ] Diff-scoped `thermo-nuclear-code-quality-review` on SOLID/KISS/DRY/YAGNI, minimal owner planes and tests.
- [ ] If multiple independent models/tools are actually executed, attach **separate** Swarm lanes, Arena deliberation and Interrogate counterexamples. No simulated independent reviewers.
- [ ] Verify PR base/head, stacked dependencies, fresh CI, duplicate-surface audit and rights/citation proof.
- [ ] Merge bottom-up only when accepted. Update #874/#876/#877 appropriately; leave root #871 OPEN until actual acceptance.

## Status model

`PASS` = command executed against exact code state and verified assertions; `FAIL` = observed counterexample; `BLOCKED` = mandatory unavailable dependency / rights / authorization; `UNTESTED` = no actual observation. `FAIL > BLOCKED > UNTESTED > PASS`. A test that verifies proposed schema structure cannot promote PStack's runtime validator to typed schema conformance.
