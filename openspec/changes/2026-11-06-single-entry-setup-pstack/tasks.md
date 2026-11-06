# Recursive plan, dependencies and acceptance — parent epic #948

One authoritative OpenSpec change: `2026-11-06-single-entry-setup-pstack`. Modify the living `pstack-setup-overlays` requirements, not a second capability. Existing #703 and #937 are completed foundations, not new implementation tasks.

~~~text
#948 Single setup skill (PStack semantic boundary)
  |
  +-- #949 SP-01: audit pinned upstream + exact caller/schema/profile inventory
        |
        +-- #950 SP-02: reconcile MODIFIED living requirements, ADR, data schema, design
              |
              +-- #951 SP-03: native references and single public setup skill
              |         includes six legacy skill-key migrations
              |
              +-- #952 SP-04: canonical packaged host profiles -> generated root mirror
                   and canonical-first validated resolver
                      |
          #951 + #952 + #950 --> #953 SP-05: final-head review and verification
~~~

## #949 — Source audit (partially evidenced, not closed)
- [x] Compare applied `cursor/plugins@88d47514` setup against `2776ddd` candidate; one cross-judge wording delta, not a pin promotion.
- [x] Compare local neutral and Grok adapter, nine host profiles, setup projection schema/model, role resolver and verification skill offers.
- [x] Identify **six** setup profiles with `skill`, including five `null` values; document exact migration matrix.
- [x] Source-find operational paths in `verify_harness`, setup tests, scanner, package lifecycle/projection, model refs, README.
- [ ] Prove exhaustive all-repository caller scan and generated-artifact dependency scan at implementation branch SHA; record exact grep paths/line locations.
- [ ] Verify current `main` implementation delta and pin at the moment source audit closes.

## #950 — Formal specs and design (this PR; subject to review)
- [x] Reconcile old two living requirements as **MODIFIED** before adding independent new requirements; include named GWT scenarios.
- [x] Re-evaluate ADR and remove the unnecessary proposed `SetupProjection.reference` field; specify convention path derived from validated profile filename.
- [x] Formal code/data flows, typed `SetupProjection`, source-mode JSON Schema contract, profile copy/authority and exact runtime versus static evidence.
- [x] Preserve **both** optional upstream verification creation skills; distinguish setup-only writes and a separate operator-requested follow-up.
- [ ] Run standalone OpenSpec `validate` with tool available; until then UNTESTED.
- [ ] Get external independent changed-diff/spec approval; until then NOT_RUN.

## #951 — One skill and source field migration (NOT DONE)
- [ ] Preserve Grok-only detection/ask/model/effort write rules under `setup-pstack/references/grok.md` plus four Grok subreferences; migrate links.
- [ ] Derive reference solely by exact validated profile filename and reject missing/out-of-tree/symlinked references.
- [ ] Remove `SetupProjection.skill` from **all six** populated profile setup blocks (and mirrored copies), schema, Python model, caller tests, and all manifests.
- [ ] Update native verification tool `scripts/verify_harness.py` path/expectation checks; remove old scanner exemption while keeping a scoped references exemption.
- [ ] Migrate `README.md`, `README.zh-CN.md`, `TEST-PLAN.md`, skill links and package projections; do not rewrite historical audit files.
- [ ] Delete the separate public Grok setup skill only in the same complete implementation wave after running caller test gates.
- [ ] Retain optional ordinary and formal verification offers without auto-creating project-local skills.

## #952 — Profile authority/compatibility (NOT DONE)
- [ ] Declare `skills/setup-pstack/profiles/*.json` sole editable authority; generate root compatibility mirror with existing packaging/projection helpers.
- [ ] Make `resolve_profiles_dir` canonical-first; if both trees exist assert byte parity and fail closed.
- [ ] Keep Antigravity native `agy plugin install` package lifecycle and unmanaged-file preservation from newer `main` changes.
- [ ] Test installed packaged-only plugin, checkout with both mirrors, stale mirror negative mutation and deterministic idempotent rebuild.
- [ ] Do not move profiles into `poteto-mode` and do not delete root until another explicit proven compatibility decision.

## #953 — Exact-head completion (NOT DONE)
- [ ] OpenSpec strict validation and offline source/schema tests.
- [ ] All six built-in-host doctor and packaging tests, consistent receipts and rollback proof.
- [ ] Available/authorized native host smoke; no invented success for unavailable hosts.
- [ ] Actual Swarm, Arena, Interrogate and both Thermos reviews with independently identifiable artifacts; otherwise NOT_RUN.
- [ ] Confirm no critical/major findings, no user-config clobber, no model or effort family leakage and no second setup skill.
- [ ] Verify exact final head SHA CI before shipping; keep draft until gates are satisfied.

## Latest baseline
The docs PR initially passed offline CI at `f5dbccd` (973 passed, 28 skipped in its main Python batch) but that evidence does **not** apply to later specification changes. OpenSpec CLI and independent review were explicitly NOT_RUN at that head. Revalidate at the new head before making claims.

## Work not in this epic
No agent orchestration runtime, PStack-owned quant research workflow, QStack reverse dependency, second model/provider registry, LLMWiki compiler, generic setup executor SDK or unverified host promotion.
