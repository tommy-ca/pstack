# Thermo-Nuclear Code Quality Review: Epic #695 update train, open PRs, and recursive plan

- **Scope**: the landed train plus the three open PRs. Merged commits `ef34052` through `1002590`. PR #717 head `e18ba48`. PR #718 head `4befddd`. PR #719 head `9c4b680`.
- **Base revision**: `ef3405282e4afd2636923043ca59aac8a09d4170`
- **Head revision**: `10025900e8cb481540ce6f61f32d6b73ff638b3f`
- **Diff**: 24 files, 471 insertions, 114 deletions for the train. 47 files, 912 insertions, 281 deletions for PR #719.
- **Reviewed epic**: [#695](https://github.com/tommy-ca/pstack/issues/695). Gate [#706](https://github.com/tommy-ca/pstack/issues/706). Follow-ups [#703](https://github.com/tommy-ca/pstack/issues/703), [#709](https://github.com/tommy-ca/pstack/issues/709), [#699](https://github.com/tommy-ca/pstack/issues/699).
- **Verdict**: **FAIL**

---

## 1. Verdict

The train lands the structural intent of #695. Shared surfaces now resolve the active host from `profiles/<host>.json` instead of naming Grok, and PR #719 splits the Grok setup body into `setup-pstack-grok` with a host-neutral entry that carries no host path, no model slug, and no effort enum. That split is real work done correctly. Moved reference files have zero dangling pointers.

Two things fail, and both fail in the direction that matters.

The evidence system became one-directional. It can refuse a downgrade, so it cannot record a regression. When the OMP live driver reports a failure it emits `evidence_level="offline"` (`scripts/drivers/omp.py:427`), and `_is_preserved` requires `observed_live` plus `PASS` (`scripts/portability_types.py:560-571`). The refresh guard therefore reads a genuine failure as a dropped settlement, refuses to write (`scripts/evidence_index.py:150-166`), and leaves the previous runtime `PASS` in the tracked receipt. A real regression becomes unpublishable, and `derive_support_state` keeps returning `supported`. Two independent lanes reached this finding without contact.

The boundary gate cannot fail on the defect class it was built for. Its one carve-out is keyed to `skills/poteto-mode/SKILL.md` line 129, its routing detector misses `hand to Grok Build's /create-skill` while flagging `Use Grok Build to author`, and its exemption list skips `skills/setup-pstack/**`, the exact surface this epic is migrating. Measured on this tree the gate reports `PASS` while `skills/reflect/SKILL.md:56` routes every host to a Grok native command.

## 2. Findings

### Finding 1. A live regression cannot be recorded

`scripts/evidence_index.py:150-166` computes its own `prior` and `dropped` sets instead of asking the canonical helper. `preserve_observed_settlements` returns an empty preservation list as soon as the runtime plane is stale (`scripts/evidence_durability.py:44-58`), so the in-place mutation that makes the guard correct does not happen, and every prior live id lands in `dropped`. `sys.exit` then refuses the write. Because the driver publishes failure as `offline` and preservation requires `observed_live` plus `PASS`, the refusal fires hardest on bad news. The tracked receipt keeps the last `PASS`.

Verified by me at `1002590`. Consumer search: `verify-portable.py:522` (`refresh-static`), `run --host <host>` through `PortableVerifier.evidence`, `derive_support_state`, and `tests/test_evidence_settlement.py:333`. Behavior pin missing in the repo, because the failing case is never written to disk. Net obligation removed by the remedy: one duplicated predicate, one private import that bypasses the `portability_schema` facade, and one in-place mutation contract that no signature states.

Remedy: return `(preserved, dropped)` from the canonical traversal and branch once in the caller. Refuse only when the current row is a non-attempting refresh. Carry the attempt as data through the driver.

Full analysis: [`04_evidence_truth.md`](04_evidence_truth.md), corroborated by [`03_tests_quality.md`](03_tests_quality.md).

### Finding 2. PR #718 rewrote a claim inside a restamp

The commit says `chore(evidence): restamp durable receipts from merged head`. In `omp-receipt.json` the `doctor-canonical-index` stdout moved from `Freshness: CURRENT (0 commits ahead)` to `Freshness: DRIFT (34 commits ahead)` while `verdict` stayed `PASS`, and `surface_revisions.upstream_head` still equals `canonical_pin`. A restamp that changes meaning is a claim change, and nothing in the machine fields carries the drift, so `evaluate_plane_staleness` can never stale the canonical plane.

Verified by me by diffing `main...pr-718`. Remedy: record upstream freshness in `SurfaceRevisions` and fail or mark `UNTESTED` on `DRIFT`, or split the restamp into a claim PR with its own evidence.

Full analysis: [`04_evidence_truth.md`](04_evidence_truth.md).

### Finding 3. A vacuous no-op is recorded as a canonical PASS

`doctor-openspec-validation` now reports `No active OpenSpec change; nothing to validate (vacuous)` with a non-executable command string and `verdict: PASS, duration 0.0`, in all five receipts. The previous row validated a named change. Deleting the `state == "none"` branch changes no computed verdict, because the canonical plane still reduces to `PASS` from the canonical-index row.

Lane-verified, not replicated by me. Remedy: append no row on `state == "none"`, and drop the test assertion that pins the vacuous PASS.

Full analysis: [`04_evidence_truth.md`](04_evidence_truth.md).

### Finding 4. The boundary gate passes the file it exists to flag

Three separate defects in `scripts/scan-host-boundary.py`, each confirmed by probe at `1002590`.

The carve-out is keyed to a line number and restated three times. `QUOTED_PROHIBITION_CARVE_OUTS` at line 158 has zero readers. The same `(path, 129, token)` triple is hardcoded again at line 185, and the drift branch at lines 192-195 raises `ValueError`, so rewording the reviewed sentence turns the doctor step into a traceback rather than a graded violation.

The routing detector matches phrasing. `"hand to Grok Build's /create-skill and run its loop"` returns `None`. `"Use Grok Build to author"` returns a violation. The possessive lookahead `(?!['\u2019]s?)` exists to keep one reviewed prohibition quiet and blinds the detector to every possessive routing sentence.

The negation check spans the whole line. `"Do not use host emulation. Open Grok Build plugins first."` returns `None`, so a live directive passes whenever an unrelated negated verb appears earlier in the line.

Verified by me. Consumer search: `tests/test_scan_host_boundary.py` imports the module through `importlib` and calls `run_scan`, `scan_file`, `is_exempt`, `extract_forbidden_vocabulary`. `scripts/verify-portable.py` doctor calls the CLI. Behavior pin: the gate still fails on an install path, a bare routing directive, a per-host primitive, and a concrete default model.

Full analysis: [`02_boundary_gate.md`](02_boundary_gate.md).

### Finding 5. The exemption list exempts the surface under migration

`DEFAULT_EXEMPTIONS` includes `skills/setup-pstack/**` with the reason `Host-specific setup skill for Grok CLI configuration`, plus `scripts/**`, `tests/**`, `openspec/**`, and `.audit/**`. After PR #719, `setup-pstack` is the host-neutral entry, so the reason is stale and the exemption hides the one shared file the epic rewrote. A gate whose exemptions encode the current state cannot fail on the migration it guards.

Verified by me by calling `is_exempt` directly.

Full analysis: [`02_boundary_gate.md`](02_boundary_gate.md), [`05_pr719_setup_core.md`](05_pr719_setup_core.md).

### Finding 6. The scanner fails open on its own inputs

`load_profiles` swallows every exception and continues (`scripts/scan-host-boundary.py:140-148`), and `scan_file` returns an empty violation list when a file cannot be read. A corrupt profile or an unreadable surface narrows the gate silently instead of aborting it. For a gate that reports `PASS`, fail-open is the wrong default.

Verified by me. Remedy: raise on an unparsable profile and on an unreadable in-scope file.

Full analysis: [`02_boundary_gate.md`](02_boundary_gate.md).

### Finding 7. PR #719 declares per-host setup paths that nothing reads

`profiles/*.json#setup` now declares `catalog`, `overlay`, and `skill` per host, and `resolve_setup_projection` is the only reader. `git grep` on `pr-719` shows zero production callers: the tests call it, and `skills/setup-pstack/SKILL.md:30` documents the command. The writers still hardcode the same paths in four places (`adapt-harness.py:44`, `scan-host-boundary.py:152`, `setup_pstack.py:172-193`, `project-package.py`), so the declaration and the writes can disagree without any test noticing. A new host requires hand edits in four files while the profile claims to be the single source.

Verified by me by grepping callers and the literals. Remedy: derive the install-path table and the projection targets from `profiles/*/setup`, and delete the four literal sites. Net obligation removed: one declaration that no code obeys.

Full analysis: [`05_pr719_setup_core.md`](05_pr719_setup_core.md).

### Finding 8. PR #719 leaves eleven callers pointing at a file that no longer holds the keys

`skills/architect`, `arena`, `how`, `interrogate`, `swarm`, and `why` still say `toml key <role> per ../setup-pstack/SKILL.md`. The shared entry contains no toml key, no role key, and no resolver vocabulary. The keys live in `setup-pstack-grok/references/resolve-model.md`. One site, `poteto-mode/references/grok-tools.md:65`, was redirected correctly, so the migration is inconsistent by accident rather than by design.

Verified by me with `git grep -n "setup-pstack/SKILL.md" pr-719 -- skills`.

Full analysis: [`06_pr719_projections.md`](06_pr719_projections.md).

### Finding 9. Durable writes are not atomic and a refusal exits zero

`evidence_index.py:174,178` truncates the durable receipt and the index in place with `write_text`, so an interruption destroys the only tracked live settlement. The adjacent unreadable-durable branch prints `REFUSING` and leaves `all_pass` untouched, so the command exits 0 after refusing to write.

Verified by reading at `1002590`. Remedy: temp file plus `os.replace`, and one refusal mechanism that reaches the exit status.

Full analysis: [`04_evidence_truth.md`](04_evidence_truth.md), [`07_duplication_canonical.md`](07_duplication_canonical.md).

### Finding 10. Test-suite shape

Three classes, ranked by what they fail to catch.

A duplicate guard test exists in two files, `tests/test_evidence_settlement.py:333` and `tests/test_evidence_index_resilience.py:360`, with identical assertions. The resilience file owns it, because the guard lives in `evidence_index.py`.

`tests/test_architecture_documentation.py:91` pins thirteen exact bilingual sentences, which is a second copy of three README passages. It also misses the reverse case, where deleting a guide file leaves both READMEs green with a dead link.

`tests/test_scan_host_boundary.py:149` asserts SKILL.md prose instead of detector behavior, so it passes with `is_host_routing_directive` deleted. Two module constants it would otherwise cover are dead.

One changed test reads ambient state, `tests/test_verify_portable.py:301`, which requires the `openspec` CLI on PATH. That is the #709 defect class in a file the #709 fix did not touch.

Lane-verified with probes recorded in the detail file. File sizes: no changed file crossed 1000 lines. Maximum is `TEST-PLAN.md` at 1134.

Full analysis: [`03_tests_quality.md`](03_tests_quality.md).

### Finding 11. Reflect routes every host to a Grok native command

`skills/reflect/SKILL.md:56` sends substantive skill edits to `Grok Build's /create-skill`. The same train moved the router to `playbooks/authoring-a-skill.md` (`skills/poteto-mode/SKILL.md:29`), and that playbook already exists and is mapped for Grok and Codex. Line 23 also names `references/grok-transcript.md` inline, and no other host has a transcript reference, so the only satisfiable branch is Grok.

Verified by me. Remedy: point step 5 at the playbook, and name the transcript pattern rather than the one filename that exists.

Full analysis: [`01_router_authority.md`](01_router_authority.md).

### Finding 12. Smaller obligations

`--check` on the scanner has `default=True` with no negation, so `return 1 if args.check else 0` always takes the true branch. The refusal message hardcodes `PSTACK_RUN_OMP_LIVE=1` into a `{host}`-parameterized string, so a Codex refresh is told to set an OMP variable. `ROUTING_IMPERATIVES` has no readers. `"Grok Build"` is hardcoded three times in the one file that derives every other host fact from `host_identity`. `_repo_root()` in `openspec_change.py` duplicates the module-level `ROOT` that twenty sibling scripts declare, and `openspec list` still runs in the caller's cwd while `openspec validate` does not.

Verified by me or lane-verified, item by item, in [`07_duplication_canonical.md`](07_duplication_canonical.md) and [`02_boundary_gate.md`](02_boundary_gate.md).

## 3. What the updates got right

The router is single-sourced. `skill_order` and `plugin_manifest` resolve from `profiles/<host>.json`, and `test_portable_router_selects_the_active_host_not_grok` pins it.

The #717 fixture HOME does isolate the doctor mirrors, and the new test fails when the invariance breaks. It is the right seam for that test, and it needs the ambient `openspec` leak at `test_verify_portable.py:301` fixed to finish the job.

PR #719's split is honest. The Grok body moved verbatim, two lines differ, and `source`, `skill`, `catalog`, `overlay`, and `effort` are declared per host with `none` and `inherit` used where they are true.

The two evidence guards do forbid the transitions they name. Static refresh may not silently drop a live row, and a non-live row may not overwrite a live settlement at the same id. The defect is the missing third case, a failed live attempt.

No file crossed 1000 lines. No new third-party dependency. Nothing here is a unit-test-only concern; every blocker is reachable from the documented commands.

## 4. Remediation sequence

The recursive plan carries the identifiers and dependencies. Order by dependency, not by severity, because the gate must be trustworthy before it can verify anything else.

1. `evidence-truth` first. Fix the one-directional guard, the claim-meaning drift in #718, the vacuous PASS row, atomic writes, and the exit status. Nothing else can be trusted while a regression is unpublishable.
2. `boundary-gate` next. Replace the scanner's prose layer with the arena winner, key exemptions structurally, and fail closed. This gate is what proves the rest.
3. `host-authority-sweep` then. Fix `reflect`, the eleven dangling setup references, and the stale setup exemption with the new gate watching.
4. `hermetic-doctor` after. Land #717, absorb the `openspec` PATH leak, and make `test_omp_native_package` order-independent. I measured that pair as flaky in the full suite and green in isolation.
5. `setup-projection` then. Derive the install paths from profiles and delete the four literal sites.
6. `gate-reconcile` last. Restate #706 against the merged heads and record the independent verdicts this run produced.
7. `version-identity` stays outside the ceiling. #699 needs a SemVer decision that is the operator's.

## 5. Evidence status

Baseline at `1002590` with the CI gate selection, run by me. 836 passed, 2 failed, 10 skipped. The two failures are `tests/test_omp_native_package.py`, which passes in isolation twice and after the pair probe. That is an order-dependent gate, not a broken commit, and it belongs to the hermeticity section.

Lane reports are the detail files in this directory. Each carries the commands and the probes its findings rest on. Findings marked verified by me were re-run or re-read by me at the cited revision. Findings marked lane-verified carry one lane's probe and no replication, and the plan treats them as work to confirm before merge.
