# Recursive implementation plan

This change is design-stage with static planner landed on trunk; it does not assert production runtime implementation.

- [ ] **G0** Approve canonical/reference parity and explicit policy-fork classification; check frozen commits and licenses.
- [ ] **G1** Accept Arena architecture seam, Interrogate review of the formal change, and unique-role model with schema fixtures.
- [ ] **G2** Implement deterministic role/model/effort resolver with model discovery, precedence, fail-closed negative paths and receipt identity.
- [ ] **G3** Integrate projector/model roles and host-local hooks; preserve installed files and opt-out; do not overwrite user configuration.
- [ ] **G4** Add Claude Code native profile/manifest and limited runtime smoke; classify supported capabilities honestly.
- [ ] **G5** Add Copilot candidate/profile only after source/license and host capability analysis.
- [ ] **G6** Run Pi-vs-OMP *separate* parity and capability checks; do not copy another host's process/session manager.
- [ ] **G7** Run Swarm host matrix, Arena design comparison and independent Interrogate review on exact implementation head.
- [ ] **G8** Run strict OpenSpec, schema, projection, role fixture and host-native acceptance tests with durable receipts, then apply/archive accepted requirements.

Dependency graph:

```mermaid
flowchart LR
  G0[Provenance & inventory] --> G1[Formal schema acceptance]
  G1 --> G2[Resolver & catalog]
  G2 --> G3[Projection and hooks]
  G1 --> G3b[Host identity registry #446]
  G2 --> G3b
  G2 --> G4[Claude runtime]
  G3 --> G4
  G2 --> G5[Copilot candidate]
  G3 --> G5
  G3b --> G5
  G0 --> G6[Pi/OMP parity]
  G2 --> G6
  G4 --> G7[Swarm/Arena/Interrogate]
  G5 --> G7
  G6 --> G7
  G7 --> G8[Proof and archive]
```

Every child issue MUST state its dependency, deterministic acceptance, file/API ownership and evidence type. Parent closes only when all dependent tasks are proven or explicitly descoped with reason.

## Published GitHub execution graph (2026-10-15)

Program: [#429](https://github.com/tommy-ca/pstack/issues/429). Superseded draft: [PR #428](https://github.com/tommy-ca/pstack/pull/428) (CLOSED; landed on trunk via #450 as 66f67c8, #451 spec change, #452 as 59a6d0c, #453 as ca6f8d9, #454 supersede marker, #455 as 5115205, #456 as dca31a7, #457 fork matrix, #458 skill-token tests, #459/#460/#461 license disposition; then thermo pass #464/#465/#467/#468 at 419fb36, arena record #469, repins and guard coverage #470/#471/#472 at 0bf5657).

| Epic | Children | Dependencies |
| --- | --- | --- |
| [#430](https://github.com/tommy-ca/pstack/issues/430) Provenance/spec | #434, #435, #436 | #434 → #435 → #436 |
| [#431](https://github.com/tommy-ca/pstack/issues/431) Role/model | #437, #438, #439 | #436 → #437 → (#438, #439) |
| [#432](https://github.com/tommy-ca/pstack/issues/432) Adapters | #440, #441, #442, #443, #446 | #437/#438 → #440 → (#439 →) #441; #434/#437 → #443; #436/#437 → #446; #440/#446 → #442 |
| [#433](https://github.com/tommy-ca/pstack/issues/433) Verification | #444, #473, #445 | #435/#437/#440/#441/#442/#443 → #444; #444 related #473 (lineage, not a dependency); #436/#438/#439/#444/#473 → #445 |

These are **open issues** until their acceptance criteria receive independent evidence. The source review is not a completed live multi-model Swarm/Arena/Interrogate run.

## Design-to-code progress snapshot (2026-10-15, superseded draft #428; landed state)

The policy schema now supports bounded `seats` independent of distinct model slugs. The landed implementation includes `scripts/model_role_resolver.py`, a pure role-planning seam with explicit precedence, declared capability gaps, cross-judge selection, and honest status labels. No native harness is dispatched. Host integrations are tracked under #440-#443; #444 owns verification fixtures and receipts. Issue #437 stays open until actual host integration and runtime receipts settle. The planner output has a JSON Schema Draft 2020-12 wire contract (`schemas/portability/model-plan.schema.json`); tests check both honest error plans and rejection of forged runtime PASS. This is a **static type contract**, not a live host integration or settlement protocol.

## New design task #446 (P1) — extensible host identity

Parent: #432. Dependencies: #436 and #437. Implement a bounded, backwards-compatible declarative host identity registry following the formal OpenSpec requirement, with unique namespaced IDs and fail-closed capability states. No host is added automatically by the static model-role policy. Future Copilot issue #442 MUST consider this contract before extending the closed enums; do not duplicate host inventory sources. Superseded PR #428 documented the contract; trunk carries it through #472 at 0bf5657; #446 performs code migration only after acceptance.

## Dated evidence (2026-10-16, thermo pass)

A thermo-nuclear review of the landed stack plus three audit lanes produced the plan for the runtime and evidence gates. Its findings are recorded rather than folded into this change's requirements, because the change is design-stage and G2 through G8 stay open.

Four code units landed: an ownership guard making uninstall refuse a foreign-source install (#464, extended in #472 to refuse install behind a symlinked ancestor and to refuse install over a foreign tree at all), one canonical choice-list rule with a cached validator (#465), skills reconciliation with evidence regeneration (#467), and a decomposition of the role policy and resolver hot paths (#468). Test coverage for each landed behaviour is pinned, including a mutation-proven case for the duplicate-choice rule (#471) and a repin of the DSH candidate table to a trunk revision (#470).

The design question the review surfaced, that the module interpreting evidence is byte-hashed and therefore costs a full multi-host re-proof on a comment, is recorded at [`docs/research/arena-surface-revision-2026-10-16.md`](../../../docs/research/arena-surface-revision-2026-10-16.md) with three candidate designs, two of them measured with runnable harnesses, and a selected base. Its boundary is a product question: whether the freshness gate answers "is this claim still true" or "has anything in the interpretation path changed". G7 and G8 stay open on that decision, and on multi-family independence, which no run in this pass supplied.

## Dated evidence (2026-10-16, wave-2 reconcile)

Trunk moved `3852f4e` to `7a10736` across nine commits: thermo-pass plan reconcile (#474), ownership-guard extension (#472 at `0bf5657`), duplicate-choice guard coverage (#471), DSH candidate repin (#470), surface-revision arena record (#469), role policy and resolver decomposition (#468), skills reconciliation (#467), single choice-list rule (#465), and foreign-source uninstall refusal (#464). This wave-2 note sits outside that range on trunk `927a2d0` (PR #475).

Wave-2 baseline is green: full suite `961 passed, 10 skipped` with `TMPDIR` on a multi-GB filesystem (receipt `.audit/evidence/full-suite-20261016-receipt.json` at head `7a10736`), and `scripts/verify-portable.py doctor --host all` reports `6-Harness Matrix Verdict: PASS` with all six hosts `PASS` at the offline planes and `Runtime: UNTESTED` after syncing the live Antigravity install to trunk. The one full-suite failure seen mid-run was `tests/test_verify_portable.py::test_portable_verifier_antigravity`; the failing receipt said `Stale installed copy`, and the designed sync script fixed the drift, so the cause is recorded as a stale live install rather than a code regression. That failure mode also shows the suite reads live-install state through the durable receipts; this coupling is identified here but has no tracking issue yet, and `#473` owns only the freshness-plane gaps, not this coupling.

Eighteen open issues (`#429`–`#446`) keep their delivery refs historical at `3852f4e`; this note records trunk `7a10736` alongside them without editing those refs. `#473` carries no `3852f4e` delivery pin and dates its measurements to `0bf5657`. The freshness gaps that review proved, four of six hosts unable to fail on a stale package driver and a vacuous droid row, remain tracked in issue #473 rather than fixed here.

## Dated evidence (2026-10-16, wave-3 reconcile)

Trunk moved `927a2d0` to `c6bd628` across two commits: interrogate-findings record plus suite receipt (#476 at `af1b12e`), and hermeticity-coupling scope note (#477). No code changed. This note also records the graph wiring made in this pass: #473 is now a #433 child feeding #445 (#429 inventory and mermaid, #433 checklist, #445 dependencies, #473 parent plus owned-surfaces and evidence-type fields, and the §Published-graph table row for #433). The 19 wave-3 comments posted during this pass say dependencies are unchanged; that sentence is superseded by this paragraph for #429, #433, #445 and #473.

Wave-2 baseline stands with one correction: full suite `961 passed, 10 skipped` (receipt `.audit/evidence/full-suite-20261016-receipt.json` at head `7a10736`). The receipt's `timestamp` field reads `2026-10-16T22:20:00Z` but is local `+02:00` wall clock mislabeled `Z` (true UTC `20:20:00Z`); it postdates its introducing commit and must be regenerated from UTC before being cited as a durable artifact. `scripts/verify-portable.py doctor --host all` reports `6-Harness Matrix Verdict: PASS` with all six hosts `PASS` at the offline planes and `Runtime: UNTESTED`.

Nineteen open issues (`#429`–`#446` plus `#473`): the eighteen pinned issues keep delivery refs historical at `3852f4e` with the wave-2 footer at trunk `7a10736` (pilot #475 at `927a2d0`); `#473` (measured at `0bf5657`, REOPENED 2026-10-16 after a premature COMPLETED closure with acceptance unmet) is the live freshness-gate gap tracker, not a delivery pin. Related to `#444` by studied-surface lineage, not a dependency. The suite's live-install coupling identified in #477 has no tracking issue yet and is not owned by #473. G7 and G8 stay open on the freshness-design decision (#473 live gate blocks #445), the untracked hermeticity coupling, and multi-family independence, which no run in this pass supplied.

## Dated evidence (2026-10-17, thermo-nuclear review)

Three read-only lanes on trunk `d61a2fd`, single model family, no multi-model
PASS claimed. Lane A (freshness gate, `scripts/portability_schema.py`):
verdict not approvable as-is; `supported` derived from a weaker per-row proof
than `verified` (foreign-host and all-FAIL-plane receipts accepted, probe 2
also accepted by `check_evidence_durability`); code-judo ladder fix proven
74/74 in a disposable copy, filed as proposal. Lane B (verifier lever,
`scripts/verify-portable.py` 1305 L): honesty machinery sound; four P1 seam
defects (filename-list binding misses `route_resolver.py`; self-hash freezes
the file; runtime PASS on zero live evidence; corrupt `index.json` silently
reset). Lane C (planner/spec): split earns its keep, boundary misdrawn
(whole-document revalidation per call, three rules written twice, 16-seat cap
planner-only); one wording ambiguity on Interrogate model diversity (delta conditions
diversity on declared policy and permits one-model multi-seat panels, main
spec calls diversity an adapter choice; filed as conflict, corrected to
ambiguity with a one-sentence clarification proposed). Findings filed as
comments on #473 (lane A), #444 (lane B), #437 + #436 (lane C); no trunk code
changed by this review. Full reports: `/tmp/pstack-thermo-a/`,
`/tmp/pstack-thermo-b/`, `/tmp/pstack-thermo-c/` plus `/tmp/00_summary.md`
(disk-backed copies under `/var/tmp/pstack-thermo/`; `/tmp` was 100% full
tmpfs mid-run). G7/G8 stay open; the review adds unmet-acceptance evidence and
closes nothing.

## Dated evidence (2026-10-17, wave-4 reconcile)

Trunk moved `c6bd628` to `4daf1d3` across six commits: wave-3 reconcile with graph wiring (#478), dependency direction correction to lineage (#479), closed-473 record (#480), restore of 473 as reopened live gate (#481), thermo-nuclear review record with lane findings filed (#482), and diversity-conflict correction to wording ambiguity (#483). No code changed in this range; all six are docs notes on the plan.

Current-head checks on `4daf1d3`: `openspec validate --changes --strict` reports 1 passed; `scripts/verify-portable.py doctor --host all` reports 6/6 PASS on offline planes with Runtime UNTESTED on every host; `tests/test_model_role_policy.py` reports 48 passed as a focused-only result. Full-suite status at this head is unverified; 971 tests collect cleanly and the run is in flight.

Nineteen open issues (`#429`-`#446` plus `#473`): the eighteen bodies `#429`-`#446` still pin delivery at `3852f4e` with a wave-2 footer at `7a10736`; `#473` carries no delivery pin by design. No body carries a wave-3 footer or references `4daf1d3`. The `#429` mermaid now carries the five direct table edges and labels the `#444`-`#473` dashed edge as lineage, corrected live on the issue in this pass. The 2026-10-17 thermo lanes filed proposals on `#473`, `#444`, `#437`, and `#436` with no trunk code changed. G7/G8 stay open on multi-family independence, the freshness-design decision, and exact-head independent review. Child-issue body pins and footers stay deferred: eighteen bodies keep historical pins until a dedicated reconcile pass rewrites them with evidence, not bulk text.
<!-- wave-5 verification at 24f0178: interrogate (correctness ISSUES fixed: packaged planes narrowed to package-only; evidence-honesty ISSUES fixed: test parametrized over 5 hosts) + arena (A/B/C: keep per-level tuples, no graft) + independent verifier PASS on 3467ed2->24f0178 (openspec 1 passed, doctor 6/6, check-evidence durable PASS, durability 62 passed, stale-driver probe exit 1 per host). Durability 62 passed. -->

## Dated evidence (2026-10-17, wave-5 reconcile)

Trunk `3467ed2` plus the shipped stack (PR #486, merged as `24f0178`): package-plane freshness enforced per claimed level (packaged checks package-only; verified adds canonical, adapter and runtime; supported enforces all four). The `#473` probe now fails closed: a stale package driver makes `check-evidence` exit 1 for every packaged host while `check-staleness` reports REGENERATE, and fresh receipts keep `check-evidence` green. Pin violations report before staleness so the omp live remedy stays visible.

Current-head checks on `24f0178`: `tests/test_evidence_durability.py` reports 62 passed (parametrized over all five packaged hosts); `scripts/verify-portable.py doctor --host all` reports 6/6 PASS on offline planes with Runtime UNTESTED on every host; `check-evidence --host all` reports durable PASS for five packaged hosts plus droid candidate. Independent verifier confirms the stale-driver probe fails closed per host at this head (finding filed inline in the verification report). Full-suite status at this head is unverified; baseline `957 passed, 10 skipped` was measured at `3467ed2` with 5 tmp-full failures unrelated to this change, plus `893 passed, 7 skipped` over the non-verifier subset at the pre-ship head.

Nineteen open issues (`#429`-`#446` plus `#473`): open state unchanged. `#473` stays open as the live tracker; the packaged-plane gap it measured is closed by `24f0178` and the remaining work is the `supported`-derivation proof-equivalence row plus the hermeticity coupling question, neither owned here. G7/G8 stay open on multi-family independence and exact-head independent review. Child-issue body pins stay deferred as in wave-4.

## Dated evidence (2026-10-17, wave-6 reconcile)

Trunk `104cf9f` plus one code unit: candidate rows report NOT_COVERED instead of PASS (`aa0efab`). A candidate row evaluates no planes, so the honest label names the gap instead of claiming durability. Exit stays 0; only the label changes.

Current-head checks on `aa0efab`: `tests/test_evidence_durability.py` reports 63 passed (62 plus the new NOT_COVERED regression test); `scripts/verify-portable.py doctor --host all` reports 6/6 PASS on offline planes with Runtime UNTESTED on every host; `check-evidence --host all` reports durable PASS for five packaged hosts plus droid NOT_COVERED. Coordinator-run six-host matrix at this head (scout lanes blocked on no exec tool; the six fresh, mutated, restored probes were run by the coordinator and recorded here, not an independent Swarm): five packaged hosts fail closed naming the package plane under a stale package driver and return to PASS on restore; droid stays NOT_COVERED exit 0 under mutation and restore.

Nineteen open issues (`#429`-`#446` plus `#473`): open state unchanged. `#473` packaged-plane gap (closed by `24f0178`) and droid-reporting row (closed by `aa0efab`) are done; remaining work is the `supported`-derivation proof-equivalence row plus the hermeticity coupling question, neither owned here. The role-policy-module line in #473 acceptance stays unbound prose in this note and is not claimed as dispositioned. G7/G8 stay open on multi-family independence and exact-head independent review. Child-issue body pins stay deferred as in wave-5.

## Dated evidence (2026-10-17, wave-7 reconcile)

Trunk `7e59c2c` (PR #487 merged). No code change in this wave. Two records closed: the #473 body now keeps its original acceptance bullets verbatim with a Historical note marking waves 5 to 6 as superseding findings (preference 4 holds; the residual rewrite was reverted), and the swarm lanes SW1 to SW4 plus SW6 are DONE via Task agents with exec in isolated worktrees at `7e59c2c` while SW5 (antigravity) is DONE via Task agent TechnicalHummingbird with exec in an isolated worktree at `6e128dd` (first scout attempt blocked on no-exec; first antigravity run covered staleness only and is superseded; the coordinator re-ran isolated check-evidence fresh exit 0 PASS, mutated exit 1 FAIL naming package_driver_revision mismatch on the package plane, restored exit 0 PASS, then the Task-agent lane repeated the same three steps at `6e128dd`). Coordinator direct probes remain evidence only.

Current-head checks on `7e59c2c`: `tests/test_evidence_durability.py` plus `tests/test_eval_blinded_pstack_dsh_candidate.py` report 74 passed; `scripts/verify-portable.py doctor --host all` reports 6 of 6 PASS on offline planes with Runtime UNTESTED on every host; `check-evidence --host all` reports durable PASS for five packaged hosts plus droid NOT_COVERED. Independent verifier PASS on `104cf9f` to `097ec48` plus full suite 968 passed 10 skipped recorded for PR #487.

Nineteen open issues (`#429` to `#446` plus `#473`): open state unchanged. `#473` keeps its original acceptance verbatim; the packaged-plane row (closed by `24f0178`) and droid-reporting row (closed by `7e59c2c`) are marked as delivered in the wave notes, not in the bullets. Remaining work is the supported-derivation proof-equivalence row, the hermeticity question, and the role-policy-module scope line, none owned here. G7 and G8 stay open on multi-family independence and exact-head independent review. Child-issue body pins stay deferred as in wave-6.

## Dated evidence (2026-10-17, wave-10 reconcile: lane-B F1/F3/F4 shipped)

Trunk `b0f9aa7` plus the shipped stack (PR #492 merged as `a9329d4`, PR #493 merged as `bc401ae`, PR #494 merged as `0769e2f`): three lane-B verifier-lever defects closed with worker/verifier separation on every unit.

F1 (route_resolver outside driver_revision): one-line binding plus regression param. Repro pre-fix FRESH exit 0, post-fix REGENERATE adapter+runtime exit 1. Evidence scope 117 passed. Independent verifier APPROVE.

F3 (runtime PASS on zero live evidence): proof_bar demotes settlement-free runtime PASS to UNTESTED; dict settlements normalized; evidence() re-reduces planes+overall after preserve_observed_settlements (round-1 BLOCK on the #322 preservation path, repaired and re-verified). Settlement-free codex run now Runtime UNTESTED exit 1; preserved live settlement keeps runtime PASS with derive supported. Named suite 115 passed. Independent verifier APPROVE at 6988bfe.

F4 (corrupt index silently reset): corrupt index now refused loudly (exit 1 naming the file, bytes untouched). Missing index still initializes. Tooth check fails without the fix, passes with it. Full offline CI 694 passed 10 skipped. Post-merge independent verifier APPROVE at 0769e2f with a LOW-MODERATE partial-write residue filed as #495 (durable receipt lands before index refusal; no gate reads index.json).

DSH candidate table repinned twice at the F3 then F4 driver scopes (verdict/counts unchanged). doctor 6/6 offline PASS Runtime UNTESTED; check-evidence 5 PASS + droid NOT_COVERED throughout.

Nineteen open issues (#429-#446 plus #473) plus new follow-up #495: open state otherwise unchanged. G7/G8 stay open on multi-family independence and exact-head independent review. Remaining lane-B row: F2 self-hash coupling (scouted: verifier 1380 lines, three test pins reject unrefreshed edits; minimal seam is hashing a behavior-bearing core, not the whole wrapper).

## Dated evidence (2026-10-17, wave-10 closeout correction)

Correction to the wave-10 note above: it was committed directly to main as `f6b1f5d`, against the deviation record that resumed changes via PR. This note records that as a second exception. Subsequent reconciliation updates go through a docs PR.

Post-merge independent F4 verification (APPROVE, main `0769e2f`): named evidence suites 128 passed; check-evidence 5 PASS plus droid NOT_COVERED; doctor 6/6 offline PASS Runtime UNTESTED; tooth check re-derived (reverted arm fails with DID NOT RAISE, fixed arm refuses with named path, index bytes byte-identical). One non-reproducible droid-lookup failure traced to the live-install openspec-list probe (same non-hermetic class as #477), not F4.

Partial-write residue is tracked as #495, not as transactional F4: a corrupt-index abort rewrites the current host receipt before the index refusal, so restoring the old index leaves its run_id stale, and deleting the index plus rerunning re-enters the omit-other-hosts class. Supported recovery is uncommitted; no index/receipt atomicity is claimed.

## Dated evidence (2026-10-17, wave-11 reconcile: graph note for #495/#444 and swarm lane classes)

Docs-only wave on branch `docs/wave-11-graph-495-444-note` from main `c10df56`. No code, receipt or fixture file is touched. The four items below close the two documentation gaps an interrogate-scout pass found in the wave-10 records.

**(a) #495 is a related, non-blocking follow-up to #444/F4, not a dependency.** #495 tracks the partial-write residue left after the F4 corrupt-index refusal: `evidence()` writes the durable host receipt before it parses and refuses `index.json`, so repairing the index afterwards leaves its `run_id` behind the receipt's, and the remedy of deleting the index re-enters the omit-other-hosts class F4 closed. Severity LOW-MODERATE and non-blocking: the abort is loud, no gate reads `index.json`, and that file has a single writer read only by tests and prose. The `#444` edge to `#495` is lineage, not a dependency, and no `#444` acceptance criterion changes.

**(b) Wave-10 F1/F3/F4 dispositions for #444.** F1 (`route_resolver.py` outside `driver_revision`) fixed by PR [#492](https://github.com/tommy-ca/pstack/pull/492), merged as `a9329d4`. F3 (runtime PASS on zero live evidence) fixed by PR [#493](https://github.com/tommy-ca/pstack/pull/493), merged as `bc401ae`. F4 (corrupt `index.json` silently reset) fixed by PR [#494](https://github.com/tommy-ca/pstack/pull/494), merged as `0769e2f`. Each unit carried worker/verifier separation with an independent verifier APPROVE, and F4 was re-verified post-merge at `0769e2f` (APPROVE; the residue it could not close became #495).

**(c) Arena seam recommendation for the remaining lane-B row F2 — proposal, not a decision.** F2 (the verifier hashes its own source, so a comment freezes the file and stales every host) has no fix on trunk. The arena pass for this wave recommends option B: hash a behavior-bearing core rather than the whole wrapper file, so a byte edit that cannot move a verdict stops costing a multi-host re-proof. This is recorded as a candidate seam only; no decision is taken here, no implementation exists, and the F2 acceptance row on #444 stays open on the owner's call.

**(d) Swarm lane classification (scout pass at `c10df56`; no lanes spawned, no commands run).** Runnable-now: [#473](https://github.com/tommy-ca/pstack/issues/473) supported-derivation plus hermeticity probes (offline and synthetic), and [#495](https://github.com/tommy-ca/pstack/issues/495) partial-write regression in a disposable evidence root. Blocked-on-design: [#437](https://github.com/tommy-ca/pstack/issues/437) native resolver wiring (the planner is planning-only), [#440](https://github.com/tommy-ca/pstack/issues/440) hook lifecycle (role-name consumer contract unresolved), [#442](https://github.com/tommy-ca/pstack/issues/442) Copilot profile (awaits the #446 registry contract), [#446](https://github.com/tommy-ca/pstack/issues/446) registry migration (design-only until accepted). Blocked-on-live-host: [#436](https://github.com/tommy-ca/pstack/issues/436) multi-family review (prior arms are single-family), [#441](https://github.com/tommy-ca/pstack/issues/441) Claude native install and discovery, [#443](https://github.com/tommy-ca/pstack/issues/443) Pi/OMP live parity (needs `PSTACK_RUN_OMP_LIVE=1` and a model route). Runnable-now means acceptance-relevant evidence can be gathered offline; it does not make any of these issues closable. G7 and G8 stay open on multi-family independence and exact-head independent review, neither of which any wave so far has supplied. Issue bodies keep their historical pins; nothing in this note rewrites an acceptance criterion, a dependency or an open state.

## Dated evidence (2026-10-17, wave-12: swarm lanes, arena F2 base, interrogate act-ons)

Docs-only wave on branch `docs/wave-12-498-swarm-arena-interrogate` from main `f3fb816`. No code, receipt, fixture or evidence-index file is touched.

**PR [#498](https://github.com/tommy-ca/pstack/pull/498) merged as `f3fb816`** (`fix(evidence): close the #495 partial durable write and the #473 package-only supported proof`). `evidence()` now parses and refuses `index.json` before the durable write, so a corrupt-index abort leaves the index bytes and the durable receipt byte-identical; the `supported` derivation now requires a `validate()`-clean this-host receipt with all four planes PASS plus the OMP settlement bar. Both guards carry tests that fail at the parent commit (negative control run at `9f9be63`).

**(a) Swarm lane verdicts: five lanes, five PASS, all offline at `f3fb816`.** Each lane ran in its own detached worktree, left it clean at the pin, and reverted its own mutation; `grok-lane`, `omp-lane` and `residue-lane` are retained under `.worktrees/swarm/` as evidence, `codex-lane` and `antigravity-lane` were removed after teardown. `python3` is the lane's interpreter for the driver CLI; the two `pytest` lanes ran the primary checkout's `.venv` with the lane worktree as cwd (the worktrees carry no venv).

| lane | probe | commands (cwd = lane worktree) | result |
| --- | --- | --- | --- |
| SW-Grok | package plane is the sole freshness gate for `packaged` | `verify-portable.py check-evidence --host grok`; `check-staleness --host all --json`; append a comment to `scripts/package-lifecycle.py`; re-run both; `git checkout -- scripts/package-lifecycle.py`; re-run both | PASS: 0 / 0 → 1 / 1 (`package_driver_revision mismatch`, plane named) → 0 / 0 |
| SW-Omp | consumer-side three-step plus settlement preservation | `check-evidence --host omp` fresh, mutate `scripts/project-package.py`, restore; `pytest tests/test_evidence_durability.py -k "preserve or package_driver or refresh or unreadable or corrupt or partial or drop"`; `pytest tests/test_evidence_durability.py tests/test_verdict_reduction.py -q` | PASS: 0 → 1 (naming `(package)`) → 0; 14 passed; 88 passed |
| SW-Residue | #495 corrupt-index refusal and its regression pin | `pytest tests/test_evidence_durability.py -k corrupt_index -q`; the full file; the same test file copied into a temp worktree at parent `9f9be63`; `/tmp/probe_corrupt_index.py` against the lane's own fixtures | PASS: 1 passed; 68 passed; control 1 failed, so the pin is not vacuous; probe shows durable receipt **and** index byte-identical after the refusal, the refused run's own receipt on disk and named by the refusal |
| SW-Codex | codex freshness lane | `check-evidence --host codex`; `check-staleness --host codex`; mutate `scripts/package-lifecycle.py`; re-run both; restore; re-run both | PASS: 0 / 0 → 1 / 1 (both gates name the `package` plane) → 0 / 0 |
| SW-Antigravity | antigravity freshness plus live-plugin sync | `check-evidence --host antigravity`; `check-staleness --host antigravity`; mutate; restore; `sync-antigravity-plugin.py --check`; `pytest tests/test_verify_portable.py::test_portable_verifier_antigravity` | PASS: 0 / 0 → 1 (five mandatory capabilities, each `(package)`) → 0 / 0; sync checker PASS exit 0; detector test 1 passed |

The four lanes that mutate a package driver (`package-lifecycle.py`, `project-package.py`) reproduce one contract from four independent worktrees: a comment-only edit to a file hashed into `package_driver_revision` fails the `packaged` claim closed on exactly the `package` plane, and the restore returns it to PASS. No lane wrote to the coordinator checkout.

**(b) Arena F2 seam: base B, graft C's declaration discipline, selected result B+ (24/25).** The arena run for the remaining lane-B row — `compute_surface_revisions` hashing `verify-portable.py` itself — measured four recipes over the trunk's exact input sets: A whole-file byte hash (trunk), B behavior-bearing core (`ast.unparse` with docstrings stripped), B+ B plus the raw module docstring that `argparse` publishes at runtime, C an explicit declared-surface registry. Record: `arena/f2/ARENA.md` at `1c78a17` on branch `arena/f2-seam`; harness `arena/f2/f2_arena.py` (`demo | compare | pins | unparse | steady A|B|C | migrate B | suite A|B|B+`). No trunk change.

| recipe | neutral edits that staled | behavior edits missed | hosts REGENERATE after a comment (CLI) | after a behavior edit (CLI) | score /25 |
| --- | --- | --- | --- | --- | --- |
| A whole-file (trunk) | 6/6 | 0 | 5/6 | 5/6 | 21 |
| B `ast.unparse` core | 1/6 | 0 | 0/6 | 5/6 | 23 |
| **B+ (B plus declared docstring complement)** | **1/6** | **0** | **0/6** | **5/6** | **24** |
| C explicit dependency list | 1/6 | 1 (`_is_observed_settlement` body) | 0/6 | 0/6 — fail-open | 19 |

Defect reproduced end to end: one comment inside `if __name__ == "__main__":` flips 5 of 6 hosts to `REGENERATE` (`adapter, runtime`), exit 1, with droid exempt as a `candidate` host holding no durable receipt. A is rejected because it is the defect; C is rejected as a base on the measured fail-open — a behavior edit to the private predicate that decides whether a `runtime` settlement counts leaves every host FRESH. The graft keeps C's "silence must be a failure" without its registry: an explicit two-entry docstring complement hashed raw, a parse failure that raises instead of degrading to bytes, and the trunk's own file set so a new driver joins the fingerprint automatically. Two sub-variants (`ast.dump()` instead of `ast.unparse`, and byte-fallback on parse failure) were rejected unmeasured and recorded so they are not re-proposed blind. The record states its own gaps: neutral statement-level refactors are not free under any recipe, `__doc__` is a declared rather than discovered complement, and any recipe change needs a one-time restamp of the 5 durable receipts plus `index.json` plus the DSH fixture. Row F2 on [#444](https://github.com/tommy-ca/pstack/issues/444) stays open on the owner's call: this is a measured proposal, not a shipped change.

**(c) Interrogate #498: APPROVE WITH FOLLOW-UPS at `f3fb816`.** Four arms plus the lead: arm A `reviewer`, arm B `cursor-agent`, arm C `antigravity`, each with its own probes and mutations, plus the lead's own probes, mutations and full suite. Recorded caveat: no `~/.claude/pstack-models.md` exists and the `task` tool exposes no model pin, so arm C collapsed into arm B's family — two distinct model families, not three, and the arm-set is partly degenerate. Suites exercised: `tests/test_evidence_durability.py` plus `tests/test_verify_portable.py` 92 passed; `tests/test_portability_schemas.py`, `tests/test_evidence_receipts.py`, `tests/test_droid_integration.py` 44 passed; full `pytest -q -p no:randomly` 974 passed, 10 skipped; the DSH pair 22 passed; `doctor --host all` 6/6 PASS, `check-evidence` 5 PASS plus droid NOT_COVERED, `check-staleness` ALL FRESH. Reverting either script fails three receipt-freshness pins plus the behavioural test, so a reverted state cannot hide in CI. Verdict: both tickets' exact reproductions are closed and pinned by non-vacuous tests and every numeric claim in the commit message reproduces, so nothing blocks the merge — but two act-ons are reachable counterexamples to the invariant the commit message states, so that claim is not left standing as written. Also noted, not actioned here: the commit says "six" durable receipts where five files exist (six hosts; droid writes none by design), and the refresh moved `opencode-receipt.json`'s `host_version` from `v2.0.30` to `v2.0.31` outside the claimed delta.

**(d) Interrogate act-ons, summarized (four; filed as comments on their owner issues in this wave).** (1) A valid-JSON but wrong-shaped `index.json` — a list, or `{"hosts": []}` — still splits the receipt from its row and surfaces a raw traceback instead of the refusal: raised independently by all four arms, probed as `index.json = "[]"` giving `AttributeError: 'list' object has no attribute 'setdefault'` at `verify-portable.py:1086` after the durable receipt was already rewritten, with `refresh-static --host all` exit 1 and `md5sum -c` reporting the receipt FAILED and the index OK; the fix is a shape check inside the existing guarded block, routed to the same `sys.exit` before the durable write. (2) A refused durable overwrite still advances the index row, so the index names a run whose bytes are not on disk — a defect #495 names in its own body; the fix is to build and write the row inside `if reusable:`, or to write the row's `run_id` from the bytes actually on disk. (3) The `supported` bar is a second copy of the floor bar (`portability_schema.py:840-876` versus `:890-928`) and the copies already diverge, which is the mechanism that produced #473; the fix is one shared row-bar helper (arm C's `_row_level()` refactor ran 144 tests green). (4) The bar polices *declared* planes and never ties them to scenario evidence: a foreign receipt with zero scenarios and four declared PASS planes derives `supported`, and a declared runtime PASS alongside a FAIL runtime scenario also derives `supported`; only hand-written or foreign receipt bytes can reach that shape, which is precisely #473's premise, and the fix is three assertions in `validate()` (planes equal the scenario reduction, `overall_verdict` equals the plane reduction, every scenario carries `evidence_level`), after which the newly added clauses in both loops collapse. Consider-tier and Noted-tier observations stay in the review report rather than here. Filed this wave: act-ons 1–2 as [comment 6236304068 on #495](https://github.com/tommy-ca/pstack/issues/495#issuecomment-6236304068), act-ons 3–4 as [comment 6236304304 on #473](https://github.com/tommy-ca/pstack/issues/473#issuecomment-6236304304), and the arena F2 base selection as [comment 6236304638 on #444](https://github.com/tommy-ca/pstack/issues/444#issuecomment-6236304638).

No issue state, acceptance criterion or dependency changed in this wave. G7 and G8 stay open on multi-family independence and exact-head independent review; the arena run above is single-family by its own account and the interrogate arm-set resolved to two families, so neither supplies the independence row.

## Dated evidence (2026-10-17, wave-13: the U1-U6a follow-up stack landed, dispositions on #495/#473/#444)

Docs-only wave on branch `docs/wave-13-u1-u6-stack` from main `7ce3c6f`. No code, receipt, fixture or evidence-index file is touched. The six units of `/var/tmp/pstack-test/followup-stack-plan.md` (planned at `e29c35b`) landed as six PRs, each with worker/verifier separation and an independent verifier verdict recorded on its PR, and each unit's migration — durable-receipt restamp (invariant R) and/or DSH candidate re-record (invariant D) — rode its own PR.

| unit | owner | act-on closed | PR | head | landed | verifier verdict |
| --- | --- | --- | --- | --- | --- | --- |
| U1 the index row and the receipt it names move together | #495 | act-ons 1 + 2 plus the reader-side cross-check (decision D2 = include) | [#500](https://github.com/tommy-ca/pstack/pull/500) | `f538ccd` | `ce05650` | PASS |
| U2 a receipt must be evidence-shaped before any bar reads it | #473 | act-on 4 (the three `validate()` assertions) | [#501](https://github.com/tommy-ca/pstack/pull/501) | `f15c80c` | `33486c8` | PASS (re-verified after restack; earlier head `967bf0c`) |
| U3 one row bar for the floor and for `supported` | #473 | act-on 3 | [#503](https://github.com/tommy-ca/pstack/pull/503) | `65737e5` | `bfc9249` | PASS |
| U4 one profile-validation gate, duplicates fail closed | #473 | act-on 4 scope notes | [#504](https://github.com/tommy-ca/pstack/pull/504) | `2a64c87` | `d927e83` | PASS (rebased head; earlier head `4b93848`) |
| U5 behaviour-bearing driver fingerprint (F2, recipe B+) | #444 | lane-B row F2 (decision D1 = ship B+) | [#505](https://github.com/tommy-ca/pstack/pull/505) | `aadb978` | `501c88f` | PASS |
| U6a `_probe_scope_hash` recipe and DSH re-record | #444 | ARENA follow-up 1 (decision D4 = adopt here) | [#506](https://github.com/tommy-ca/pstack/pull/506) | `f63a94e` | `7ce3c6f` | PASS+NOTES |

**(a) Teeth, one line per unit.** U1 pins the wrong-shaped index (`[]`, `{"version":1,"hosts":[]}`), the refused durable overwrite and the reader-side row-to-receipt cross-check; reverting `verify-portable.py` reddens four cases at the parent (`AttributeError` / `TypeError` / row advanced / mismatch silent). U2 pins zero-scenario and FAIL-plane declared-PASS receipts plus a null `evidence_level`; reverting the three `validate()` assertions gives 3 failed `DID NOT RAISE`. U3 pins the runtime-only-FAIL row and the package-only PASS row against the single `_row_level` evaluator; deleting either clause reddens its own pin, and `grep -c 'planes.get("runtime")' scripts/portability_schema.py` drops 2 to 1. U4 pins the duplicate-binding refusal and the mandatory-floor gap refusal on both the API and the `check-evidence --host grok` CLI; reverting reddens 3. U5 pins the comment-inert / statement-moves / parse-fails-loud triple; the parent recipe with the new test file gives 10 failed, and the defect is measured gone (comment edit: `check-staleness --host all` exit 0 at head, exit 1 with 5 hosts REGENERATE at `d927e83`). U6a pins the same triple for the four scripts in `_probe_scope_hash`, each window first asserting a copy of the scope equals the live tree; the parent gives 6 failed.

**(b) Decision D4, split.** Adopted in U6a: the B+ behaviour-core recipe for `_probe_scope_hash`, imported from `portability_schema._update_driver_digest` so the recipe has exactly one implementation, with the one required fixture re-record (`tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json`: `probe_scope_hash`, recording revision and wall-clock only — every count, case row and verdict unchanged). Deferred: `skills_tree_hash` (`scripts/portability_schema.py:627-637`) still hashes all of `skills/` byte-wise inside the `runtime` plane, so a comment under `skills/` stales runtime for every host; whether `skills/` markdown belongs in a plane at all is a spec/scope decision with a wider blast radius than a fingerprint-recipe change, so it stays whole-file and open on #444 (ARENA follow-up 2).

**(c) Remaining open scope, per issue (filed as disposition comments this wave).** #495: act-ons 1 and 2 and the reader-side item are closed by U1; what remains is the byte-level repair question on the unreadable-durable-receipt path, which U1 deliberately does not touch — the reader cross-check *detects* the split rather than preventing it, so the `PermissionError`/ENOSPC/SIGINT write window keeps detection-only coverage. #473: the `supported`-loop rows (act-ons 3 and 4) are closed by U2-U4; what remains is the hermeticity coupling parked in #477 and the role-module surface question — whether `scripts/model_role_policy.py` and `scripts/model_role_resolver.py` are claim-relevant surfaces that need a revision input. #444: lane-B row F2 is closed by U5 and ARENA follow-up 1 by U6a; what remains is the `skills_tree_hash` plane scope in (b). G7 and G8 keep their independence rows open as in wave-12.

**(d) No live gate verdict moves.** U2-U4 tighten the `supported` bar only: `derive_support_state` returns `packaged` for all five host profiles and `candidate` for droid before and after each unit (differential run on all six profiles in U3's verification), because every binding still carries `evidence_ref: null`. The tightening is defence for future `supported` profiles, not a change to today's rows.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-13-u1-u6-stack`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named in (c).

## Dated corrections (2026-10-17, wave-13 corrections: stale lane retention, #444 helper-scope residual)

Docs-only correction wave on branch `docs/wave-13-corrections` from main `8286f2f`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) The wave-12 lane-retention claim is historical-at-wave-12.** Wave-12 §(a) at line 181 says of the five swarm lanes that "`grok-lane`, `omp-lane` and `residue-lane` are retained under `.worktrees/swarm/` as evidence". That sentence is stale at this head, and line 181 is consequently a record of what was true at `f3fb816` and not of the current tree: the three lane worktrees were removed in the final cleanup, so `.worktrees/swarm/` is now empty and `git worktree list` plus `.git/worktrees/` show only the primary checkout and this correction worktree. The correction does not withdraw or re-grade a lane verdict — no lane result depends on the worktrees surviving. The durable evidence for the lane and arena records is (1) `arena/f2/ARENA.md` with its nine sibling artifacts (`f2_arena.py`, `results.json`, `pins.json`, `suite-A.json`, `suite-B.json`, `suite-B+.json`, `migrate-B.json`, `unparse.json`, `c_registry.json`) on branch `arena/f2-seam` at commit `1c78a17`, pushed to `origin` and still resolving there (`git ls-remote origin refs/heads/arena/f2-seam` -> `1c78a175dff54b535838aa2193fdd5933f867c63`), (2) the trunk-side record `docs/research/arena-f2-seam-2026-10-17.md` and its harness `docs/research/arena-f2-seam-2026-10-17/f2_arena.py`, and (3) the lane and unit verdicts' own PR bodies and verifier verdict comments (#498, #500, #501, #503, #504, #505, #506). The retention clause was true when written; only its present-tense reading is corrected.

**(b) #444 residual scope gains the probe-hash helper-scope note.** Tracked residual, alongside the `skills_tree_hash` plane-scope item in wave-13 §(b): `_probe_scope_hash` (`scripts/eval_blinded_pstack.py:259-281`) folds every in-scope Python file through `portability_schema._update_driver_digest` (imported at `scripts/eval_blinded_pstack.py:26`, defined at `scripts/portability_schema.py:724`), but `scripts/portability_schema.py` is not in the function's own scope list — `skills/**/SKILL.md`, `skills/**/playbooks/*.md`, `agents/*.md`, `profiles/grok.json`, and `scripts/{verify-portable.py,route_resolver.py,decision_adapter.py,eval_blinded_pstack.py}` and nothing else. So the recipe's one implementation is an input the pin does not name: a change to the shared normalizer moves the recipe without moving the pin, because no declared scope input changes and the recorded `provenance.probe_scope_hash` in `tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json` is reconciled only by the fixture test that recomputes it, never by the scope declaration that is supposed to announce a re-record. This is the same class as the deferred `skills_tree_hash` item: a fingerprint's declared inputs and the code that computes it can diverge, and the declaration is what a re-record trigger reads. No fix is taken here — recording the dependency edge is the act, #444 stays OPEN on both residuals, and the repair (naming the shared recipe module as a scope input, or hoisting the normalizer behind a pinned revision) stays an owner decision with a wider blast radius than a docs wave.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-13-corrections`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above. The #444 residuals recorded in (b) are posted as a follow-up comment on the issue in this wave.

## Dated evidence (2026-10-18, wave-16: swarm, arena, interrogate and the #513/#514 follow-up stack)

Docs-only record on branch `docs/wave-16-record` from main `3f06c93`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) Swarm, six of six PASS at `53f855b`.** One lane per host, each in its own detached worktree with `TMPDIR=/home/tommyk/.tmp-pstack-429`, three-step probe fresh PASS / AST-bearing package mutation FAIL naming the package plane / restored PASS. grok, codex, opencode, antigravity: fresh exit 0, mutated exit 1 with five rows each naming `(package)`, restored exit 0. omp: packaged scope holds exactly `{package}`; adapter and runtime mutations correctly stay out of the claim gate. droid: NOT_COVERED exit 0 across all three steps, with the grok control flipping FAIL under the same mutated tree to prove liveness. Lane recipe finding, measured independently by three lanes: comment-only edits are inert post-#505 (`_update_driver_digest` folds `ast.unparse` docstring-stripped), so future stale-package probes MUST use AST-bearing mutations or the mutated step vacuously passes. Worktrees removed, main untouched.

**(b) Arena mini-run: `skills_tree_hash` plane scope, base A status quo.** One-family degenerate arm set (stated as such): keep the behaviour-core fingerprint with markdown raw. Scores: teeth 5 vs 2, re-proof cost 1 vs 5, spec-blast-radius 5 vs 1. Graft from the loser: markdown contributes path only inside the runtime fingerprint (membership, what the recorded runtime scenarios read) and md content moves to the plane that records a scenario reading it (antigravity-tools content assert under adapter), per the #512 role-module precedent. Needs cross-family re-judge before it closes the wave-13 residual. Verification recipe recorded in the unit brief.

**(c) Interrogate, two arms, both single-family degraded.** Arm A (correctness): ISSUES, four findings. F1 act-on: `_file_or_denied` covered 2 of 4 `is_file` guards; reader gates at `verify-portable.py:1148/:1199/:1290` crashed or lied on denied stats. F2 consider (latent): an unparseable `skills/**/*.py` aborts the whole matrix via unguarded `RecipeError`. F3 consider: four skill scripts publishing `__doc__` lose their `--help` tooth under the AST recipe. F4 act-on: #512 heading splice. Verified clean: #511 recipe matches its implementation, #509 restamp integrity, #512 no-caller claim, tree clean. Arm B (honesty): PASS on evidence integrity (5-host hash match, index row match, per-head self-consistency, DSH match, ALL FRESH, pins pass), ISSUES on prose (F1 same splice confirmed; F2 scope-overreach note on the docs wording; F3 stale line citation; F4 inaccurate justification clause; F5 leaf arithmetic in the #511 message; F6 run-receipt provenance gap). Both arms note the brief range was 11 commits (`ce05650..53f855b`), not four; the four named landings are `d2dd3c5..53f855b`.

**(d) The #513/#514 follow-up stack, landed.** #513 (`f1b1e7c`, squash `963bf93`): three reader guards plus two read refusals, three new stat-denied tests, docs splice repaired; independent verifier PASS+NOTES; durability 87 passed. The unit also surfaced and fixed a `claimed_state` `UnboundLocalError` at `:1215` introduced by the extra guard swap. #514 (`9d55590`, squash `3f06c93`): DSH candidate re-record on the moved probe scope (`debc2e35` to `6ebe57e`, 17 of 257 leaves: revision, hash, wall-clock only); independent verifier PASS; DSH pair 29 passed. Full suite at this head: 961 passed, 10 skipped. Doctor 6-host PASS, Runtime UNTESTED. Changes strict 1 passed. CI on the branch head failed one DSH pin before the re-record (expected: the fixture must move with its scope input); the re-record closes it.

**(e) Deferred with owners, no code.** F2 unparseable-skills hardening and F3 docstring teeth need the arena base decision on the `skills_tree_hash` scope. F6 run-receipt provenance is a record-keeping question: the five durable receipts point at run dirs culled after landing; bytes recompute correctly and index rows agree field-for-field, so nothing is invalidated. Arm B F5 leaf arithmetic is a git message, not an editable file: disposition goes to #444 as an issue comment, not a rewrite.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-16-record`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above. Arm finding dispositions post as follow-up comments on their owner issues in this wave.

## Dated evidence (2026-10-18, wave-18: F3 docstring teeth landed via #523)

Docs-only record on branch `docs/wave-18-record` from main `928fb0a`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) F3 closed.** `DOCSTRING_CONSUMED_DRIVERS` (`scripts/portability_schema.py:694`) grows from two entries to six: the four skills CLIs publishing `__doc__` as `--help` (`pack.py`, `partition.py`, `apply.py`, `refresh-hygiene.py`) rejoin the `skills_tree_hash` pin. New parametrized test pins all four (docstring edit moves the hash). Receipts restamped, DSH candidate re-recorded (17 of 257 leaves: revision, hash, wall-clock only). Independent verifier PASS at `7f2b46c`: durability 91 passed, DSH pair 29 passed, staleness ALL FRESH, evidence 5 PASS plus droid NOT_COVERED. Landed as `928fb0a`. CI success on the branch head.

**(b) Remaining open scope, unchanged owners.** F2 unparseable-skills hardening still needs the arena base decision (same-family G agreement only; cross-family row open). The graft itself (path-only md membership plus adapter-plane content re-home) stays held for that judge. skills_tree_hash plane-scope residual in #444 stays open alongside it. No other wave-17 finding moved.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-18-record`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above. F3 closure posts as a follow-up comment on #444 in this wave.

## Dated evidence (2026-10-18, wave-19: F2 per-file failure landed via #525)

Docs-only record on branch `docs/wave-19-record` from main `3758f23`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) F2 closed.** The skills fingerprint catches `RecipeError` per file, folding the stable error category plus the sha256 of the bad bytes — never the exception string, which carries the absolute root path. The matrix reports every host instead of aborting; a changed bad file moves the pin even under an identical parse error; identical bytes pin identically across roots. Three reviewer catches shaped the unit: arm A's latent-hardening note, the collision catch (content digest added), the root-stability catch (category plus bytes, cross-root test). Test pins no-raise, determinism, same-error-class byte change, cross-root stability, and removal restore. Independent re-verifier PASS at `cb6dc24` (superseding a FAIL on the pre-restamp head, itself an exact pin mismatch the gates caught): durability 92 passed, DSH pair 29 passed, ALL FRESH, 5 PASS plus droid NOT_COVERED. Landed as `3758f23`. CI success on the branch head.

**(b) Remaining open scope.** The graft itself (path-only md membership plus adapter-plane content re-home) stays held for the cross-family judge. The skills_tree_hash plane-scope residual in #444 stays open alongside it. No other wave-18 finding moved.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-19-record`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above. F2 closure posts as a follow-up comment on #444 in this wave.

## Dated evidence (2026-10-18, wave-20: worktree contract landed via #527)

Docs-only record on branch `docs/wave-20-record` from main `dd90e96`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) Contract landed.** Swarm and arena direct repo-backed lanes to project worktrees under the ignored `.worktrees/` root per using-git-worktrees; scratch `/tmp` only with no repo checkout; bare branch only for branch-local edits. TMPDIR stays the pytest-private dir, never lane placement. The unit itself was rehomed mid-flight from an in-place branch to `.worktrees/fix/worktree-contract` before any merge, per the reviewer catch. Independent re-verifier PASS at `baa4187` from a project worktree (superseding a pre-restamp FAIL): 87 skill-contract tests, ALL FRESH, 5 PASS plus droid NOT_COVERED, 6-host doctor PASS, changes strict 1 passed. Landed as `dd90e96`. CI success on the branch head. Live Antigravity plugin synced from the worktree (its package plane checks the live install, which had drifted on exactly the two edited files).

**(b) Remaining open scope.** The graft itself stays held for the cross-family judge. The F2/F3 closures stand. No other finding moved.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-20-record`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above.

## Dated evidence (2026-10-18, wave-21: receipts after contract landed via #529)

Docs-only record on branch `docs/wave-21-record` from main `0e4e0e1`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten, so every claim above stands as dated at its own head and the diff is insertions only.

**(a) Receipts landed.** #527's SKILL.md prose moved five receipts (skills text feeds `skills_tree_hash`) and the live Antigravity install had drifted on exactly the two edited files, failing its package plane. #529 restamped all receipts against the synced live install and re-recorded the DSH candidate (20 of 257 leaves: revision, hash, context size, wall-clock only). Independent verifier PASS at `251fdf4` from a project worktree: durability 92, DSH pair 29, ALL FRESH, 5 PASS plus droid NOT_COVERED, 6-host doctor PASS. Landed as `0e4e0e1`. CI success on the branch head. The receipts branch was rehomed mid-flight into `.worktrees/fix/receipts-after-contract` before verification, per the worktree contract.

**(b) Remaining open scope.** The graft itself stays held for the cross-family judge. All other wave findings stand closed. No other scope moved.

Gate: `openspec validate --changes --strict` -> 1 passed, 0 failed. Head is this wave's docs commit on `docs/wave-21-record`; diff stat: 1 file changed, insertions only.

No issue state, acceptance criterion or dependency changed in this wave. #495, #473 and #444 all stay OPEN on the rows named above.

## Dated evidence (2026-10-18, wave-23: source reconciliation)

This checkpoint appends current source findings after the historical wave-21 record. It does not change the G0–G8 acceptance criteria, dependencies, or unchecked status.

**Source pins.** The graph audit began at main `3f4cd124f27cab90865df79d18d376e2f4335b2c`. PR #544 head `6b986dcec7fde7899f2d689f481a7b73b69909f1` subsequently landed as `c1d03e521042735e6c76cea1abdde2039cde0c8b` after an exact-head native independent-verifier `PASS+NOTES` and controlled common-workload timing. The verifier model was `openai-codex/gpt-6.1-sol`, different from writer `gpt-6-luna` but the same family. This does not close the multi-family gates. See the controlled result in `docs/superpowers/plans/2026-10-19-driver-core-disk-cache.md`.

**Provenance ledger.** The immutable comparator inventory contains 48 rows. Per-file source review covers all 48 rows with pinned comparator, canonical, and target evidence, semantic dispositions, attribution and NOTICE implications, and test/check gaps. All 48 rows are source-reviewed. Source review is not approval, implementation, runtime verification, or independent acceptance; #434 remains open.

**Host identity.** PR #533's implementation is present in `scripts/host_identity.py` and `schemas/portability/host-id.schema.json`, with host-bearing schemas and Python consumers using the shared identity contract. The six built-in host identities remain distinct from declared external identities. Registry support does not supply external-host drivers or runtime proof, and #446 remains open pending its acceptance and dependencies.

**Runtime evidence boundary.** After #544, the durable index and `.audit/evidence/omp-receipt.json` identify run `omp-1792337990-2b1585ba` on OMP 18.11.3 with observed-live spawn, cancellation, and isolation rows. Direct `check-staleness --host all --json` on that candidate reported no stale planes; `check-evidence --host all` accepted the packaged claims and reported Droid `NOT_COVERED`. The earlier OMP 18.11.2 run remains historical. These observations prove neither Pi parity nor another host's runtime, and they do not bind the unresolved model-catalog/schema/implementation requirements in #444.

**Watcher correction.** Issue #545 tracks the reproduced watcher readiness defect. A clean-check snapshot with unknown GitHub mergeability returns `ready` with a clear mergeability proof through the real reducer/classifier. The reproduction is recorded on #545; no watcher fix is included in this documentation checkpoint.

**Scope and gates.** #502 and #540 remain separate OmO and OMC/OMX proposal programs. #522 remains a separate JEV program. None is absorbed into #429, and no issue is closed here. All G0–G8 boxes above remain unchecked. The current evidence does not establish all-host runtime parity, multi-family verification for this source head, or promotion/archive acceptance. The proposed ADR remains proposed, and the canonical portability spec remains unchanged because this delta is not accepted or archived.

Parent verification command: `openspec validate 2026-10-15-harness-neutral-role-policy --type change --strict`.

Native GitHub parent/sub-issue metadata now mirrors the existing declared hierarchy. The reconciliation read back every parent edge and preserved all issue bodies and open states. #495 remains related, non-blocking lineage rather than an added dependency. #545 is a linked correction, not a silent acceptance dependency.

## Dated evidence (2026-10-19, wave-24: ledger guard, side-quest closures, hill-climb evidence)

Docs-only record from main `556b63b`. No code, receipt, fixture or evidence-index file is touched: this section is appended and no earlier wave's prose is rewritten.

**Ledger acceptance test.** PR #560 restored the ledger guard deleted by #550 in reviewed form (`test_reference_fork_ledger_records_completed_source_review` in `tests/test_model_role_policy.py`): pins the three counterpart commits (`94f5ce9`/`1dcc2ba`/`3f4cd12`), 48 unique `source-reviewed` rows, four review fields per row, and the single absent target counterpart. Interrogate verdict `PASS+NOTES` on the PR head with all four mutation axes failing closed. `tests/test_model_role_policy.py` 57 pass, combined with `tests/test_evidence_durability.py` 170 pass on merged main. This covers the row-count/pin half of #434 closure-rule line 1; per-value validation (blob contents) and independent acceptance remain open, and #434 stays OPEN.

**Side-quest closures.** #545 closed by PR #558 (UNKNOWN mergeability waits with `mergeability-unknown` reason; 52 watch-pr bun tests pass). #548 closed by PRs #556/#557 (wrapper mode 100755, exec-bit guard in CI-covered `tests/test_canonical_index.py`, direct launch exits 0). #546 closed by PR #559 (release-tag feature states read-only scope; `tests/test_release.py` 2 pass). Each closure verified live on main HEAD before closing.

**Hill-climb evidence.** #473 evidence comment records live `check-evidence`/`check-staleness` output per residual row at `2641999`: package-plane and omp/droid rows do not reproduce as stated, role-module revision input is folded into `package_driver_revision`, hermeticity parked per #477. #434 evidence comment records 48/48 `source-reviewed` ledger state with blob hash. Neither comment closes its issue.

No issue state, acceptance criterion or dependency changed in this wave beyond the three side-quest closures above. All G0–G8 boxes remain unchecked. #434, #444, #445, #473 stay OPEN on the rows named above.
