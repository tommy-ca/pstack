# Portability gate truth and boundary enforcement plan

Seven PRs take epic #695 from a stack that merged without an independent verdict to a portability gate that can record bad news. The rule the program enforces is that no claim in `.audit/evidence` may be stronger than a command in this repository can reproduce. Order is `evidence-truth`, `boundary-gate`, `host-authority-sweep`, `hermetic-doctor`, `setup-projection`, `gate-reconcile`, `version-identity`. No box is checked without its artifact.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a saved capture, a test run, or a SHA. The body is a how-to. The appendices explain and record.

This plan follows `skills/poteto-mode/playbooks/multi-phase-plan.md`. The surfaces here are CLI and contract surfaces, not a browser, so a live lane saves the command transcript and its exit status under `/tmp/swarm-<pr-id>/worker-<n>/` and prints the path. A capture is a screenshot of the terminal for this product.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified contiguous run bottom-up. Only `version-identity` stops at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. `docs/audit/thermo-nuclear-695/program-plan.md`, PR ids in order `evidence-truth`, `boundary-gate`, `host-authority-sweep`, `hermetic-doctor`, `setup-projection`, `gate-reconcile`, `version-identity`, the verification rule, the root merges, and the done condition is every box checked with its evidence.
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:skills/swarm/SKILL.md`
  - [ ] `git show origin/main:skills/thermo-nuclear-code-quality-review/SKILL.md`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:skills/interrogate/SKILL.md`
- [ ] Arm a 30-minute audit tick with the host schedule capability (`scheduler_create`, interval `30m`, fire immediately) and `monitor` for event wakes. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message, whether or not anything changed, with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] From this parent session, spawn one owner per PR with the host `task` primitive, isolated workspace, depth 1. Owners do not spawn.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges.
  - [ ] `evidence-truth` and `boundary-gate` are independent and first. Both branch from `main`.
  - [ ] `host-authority-sweep` after `boundary-gate`.
  - [ ] `hermetic-doctor` after `evidence-truth`, because both touch `scripts/verify-portable.py` receipt writing.
  - [ ] `setup-projection` after `host-authority-sweep`, because both edit the same skill reference lines.
  - [ ] `gate-reconcile` after the five above.
  - [ ] `version-identity` after `setup-projection`.
- [ ] Hold the file boundaries. `boundary-gate` touches only `scripts/scan-host-boundary.py`, `scripts/host_identity.py`, and `tests/test_scan_host_boundary.py`. `evidence-truth` touches only `scripts/evidence_*.py`, `scripts/portability_types.py`, `scripts/drivers/**`, `tests/test_evidence_*.py`, and `.audit/evidence/**`. `setup-projection` touches only `profiles/**`, `scripts/setup_pstack.py`, `scripts/project-package.py`, `scripts/adapt-harness.py`, and `tests/test_setup_projection.py`.
- [ ] Hold the review gate. `version-identity` changes a published version identity and waits for the operator in chat before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Use `gh` for every PR operation unless `command -v origin` succeeds and Origin resolves this repository. Record any fallback.
- [ ] Open the PR ready, never draft, with `gh pr create --base main`. A dependent PR targets its parent branch and retargets to `main` after the parent lands.
- [ ] Run the no-comments pass before review and the unslop pass on prose before each commit.
- [ ] Triage every Bugbot and security-reviewer comment per `skills/poteto-mode/references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before the verdict and again before the merge-ready report.

### Verdict and merge, for every PR

- [ ] Run the full swarm once, at the code-ready head. One gate lane, the ten live lanes from the PR section, the perf lane, and two audit lanes that read the diff and distrust the PR body. Another full swarm only for new behavior or a redesign.
- [ ] Clean only when every lane reports `PASS`. A defect a lane filed as a note goes back to the owner. A new head gets a fresh verdict.
- [ ] The root merges the verified run bottom-up with `gh pr merge --squash --delete-branch`, and stops on the first failed link. `version-identity` stops at merge-ready for the operator.
- [ ] After each merge, confirm `merged_at`, `base=main`, and the newest check run on the merged commit.

### Boot recipe, for every live lane

Each live lane runs in its own isolated worktree child at the PR head and drives the real CLI surface.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Create a fixture home with `mktemp -d` and export it as `HOME` so no lane reads the developer's plugin mirrors.
- [ ] Run the command the lane names and capture stdout, stderr, and exit status with `tee`.
- [ ] Save every capture to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.log` and return the path with the report.

## Make a regression publishable again (evidence-truth)

**Depends on.** None.

**Files.**

- [ ] Edit `scripts/evidence_index.py`.
- [ ] Edit `scripts/evidence_durability.py`.
- [ ] Edit `scripts/portability_types.py`.
- [ ] Edit `scripts/drivers/omp.py` and `scripts/drivers/grok.py` failure returns.
- [ ] Edit `tests/test_evidence_settlement.py`, `tests/test_evidence_index_resilience.py`, `tests/evidence_test_helpers.py`, `tests/test_evidence_durability.py`.
- [ ] Edit `.audit/evidence/*.json` for the canonical freshness field and the vacuous row.

**Build.**

- [ ] Replace the duplicated `prior` and `dropped` computation in `write_verification_evidence` with one call that returns a typed `Preservation(preserved, dropped)` from the canonical traversal, and delete the private `_is_preservable_settlement` import.
- [ ] Carry attempt state as data. A live driver failure returns `evidence_level="observed_live_failed"` (or an explicit `live_attempted` field), and the refusal fires only for a refresh that did not attempt a live run.
- [ ] Scope the refusal to a downgrade, so a same-id failure row is written rather than refused.
- [ ] Write the durable receipt and the index through a temp file plus `os.replace`.
- [ ] Route every refusal through one path that reaches the exit status.
- [ ] Delete the `state == "none"` branch that writes a vacuous `doctor-openspec-validation` PASS row, and drop the test assertion that pins it.
- [ ] Record upstream freshness in `SurfaceRevisions` and make `DRIFT` fail or report `UNTESTED` instead of `PASS`.

**You see.**

- [ ] `python scripts/verify-portable.py refresh-static --host all` either completes for every host or exits nonzero naming the host and the reason, and never leaves earlier hosts silently rewritten.
- [ ] A simulated OMP failure writes the failing settlement into the durable receipt with its own run id, and `derive_support_state` drops to the matching state instead of `supported`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Add the `evidence_level="offline"` plus `verdict="FAIL"` case to `tests/evidence_test_helpers.py`, parameterized over static and offline rows, and assert the durable receipt accepts the failure. Run `.venv/bin/python -m pytest -q tests/test_evidence_settlement.py tests/test_evidence_index_resilience.py tests/test_evidence_durability.py`.
- [ ] Delete the duplicate guard test from `tests/test_evidence_settlement.py` and keep the resilience-file owner.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `refresh-static --host grok` at trunk and head with a fixture HOME. Save `refresh-grok.log`. Pass when both exit 0 and the head receipt keeps its prior live rows byte-identical.
- [ ] Lane 2. Run `refresh-static --host all` with a fixture HOME and a pre-seeded stale surface revision. Save `refresh-all.log`. Pass when the command names the refusing host, exits nonzero, and leaves no host half-written.
- [ ] Lane 3. Inject a failing OMP driver arm with `PSTACK_RUN_OMP_LIVE=1` and a broken route. Save `omp-failure.log`. Pass when the receipt records the FAIL settlement and its evidence level.
- [ ] Lane 4. Read `derive_support_state` for omp after lane 3. Save `support-state.log`. Pass when the state is no longer `supported`.
- [ ] Lane 5. Run `doctor --host omp` and inspect the openspec row. Save `doctor-openspec.log`. Pass when no row exists for an inactive change set and the canonical plane still reduces to PASS.
- [ ] Lane 6. Interrupt a refresh with SIGINT during the write and read the receipt. Save `interrupt.log`. Pass when the receipt is either the old bytes or the new bytes and never a truncated file.
- [ ] Lane 7. Check the exit status of a refused write. Save `refusal-exit.log`. Pass when the status is nonzero.
- [ ] Lane 8. Run the canonical-index doctor and read the freshness line. Save `canonical-freshness.log`. Pass when a DRIFT statement appears only on a row that is not PASS.
- [ ] Lane 9. Run `python -m pytest -q tests/test_evidence_durability.py` against the checked-in receipts. Save `offline-gate.log`. Pass when the assertion is shape-only and no live id is pinned in the offline gate.
- [ ] Lane 10. Run `python scripts/verify-portable.py doctor --host codex` and read the refusal text. Save `refusal-text.log`. Pass when the remedy names a host-appropriate command and no OMP variable.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `refresh-static --host all` with a fixture HOME, and the number of file writes per host.
- [ ] Probe. Run the command three times at trunk and three times at head, interleaved, with `time` and `strace -f -e trace=openat,rename,write` filtered to `.audit/evidence`.
- [ ] Baseline. Record the trunk median wall time first.
- [ ] Rule. Head against trunk within 20 percent, and writes per host must be exactly two atomic replacements instead of in-place truncation.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges, then retargets and verifies `boundary-gate`.

## Make the boundary gate able to fail (boundary-gate)

**Depends on.** None.

**Files.**

- [ ] Edit `scripts/scan-host-boundary.py`.
- [ ] Edit `scripts/host_identity.py`.
- [ ] Edit `tests/test_scan_host_boundary.py`.
- [ ] Edit `skills/reflect/SKILL.md` and `skills/automate-me/SKILL.md`, for the two lines the stricter detector flags.
- [ ] Add fixtures under `tests/fixtures/boundary/`.

**Build.**

- [ ] Base this branch on `feat/703-setup-projection` (PR #719), which already rewrites `scripts/scan-host-boundary.py`. Do not open a parallel scanner change against main.
- [ ] Replace the scanner body with candidate A from the arena, keeping `run_scan`, `scan_file`, `is_exempt`, `extract_forbidden_vocabulary`, `Violation`, `Exemption`, `DEFAULT_EXEMPTIONS`, and `main`.
- [ ] Graft candidate B's per-occurrence allowance accounting, so an allowance cannot shelter a directive elsewhere on the same line.
- [ ] Graft candidate B's CLI test that asserts a non-zero exit on a real leak.
- [ ] Scope the negation test to the sentence that names the host, and delete the possessive and colon shape exemptions.
- [ ] Move the display name to `scripts/host_identity.py`, and iterate every declared host instead of the one hardcoded name.
- [ ] Express the reviewed prohibition as data that survives a line move. Delete `QUOTED_PROHIBITION_CARVE_OUTS` and the `ValueError` drift branch.
- [ ] Derive install and overlay paths from `profiles/*/setup` and `plugins_dir`, including `~/.grok/roles`, and delete `HOST_INSTALL_PATHS`.
- [ ] Replace the Grok native command at `skills/reflect/SKILL.md:56` and the same route at `skills/automate-me/SKILL.md:67` with the host-neutral `create-skill` form those files already use below. Both candidates had to make this edit to reach a clean tree, so it belongs in the PR that tightens the detector, not in a later sweep.
- [ ] Fail closed on an unparsable profile and on an unreadable in-scope file.
- [ ] Delete `ROUTING_IMPERATIVES`, and either make `--check` meaningful or delete the flag.

**You see.**

- [ ] `python scripts/scan-host-boundary.py -v` reports the scanned file count and exits 0 on this tree.
- [ ] Moving the reviewed prohibition one line down changes nothing in the verdict.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Replace the prose assertion at `tests/test_scan_host_boundary.py:149` with four `scan_file` cases for neutral, imperative, negated, and reviewed-prohibition text, and add the fixture cases for install path, routing directive, primitive, and default model. Run `.venv/bin/python -m pytest -q tests/test_scan_host_boundary.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the scanner at trunk and head on the same tree. Save `scan-tree.log`. Pass when both report the same file count and both exit 0.
- [ ] Lane 2. Write `skills/reflect/SKILL.md` line 56 content into a fixture and scan it. Save `possessive-routing.log`. Pass when it is reported.
- [ ] Lane 3. Write `Do not use host emulation. Open Grok Build plugins first.` into a fixture. Save `negation-scope.log`. Pass when it is reported.
- [ ] Lane 4. Move the reviewed prohibition to a different line and scan. Save `carve-shift.log`. Pass when the verdict is unchanged and no traceback appears.
- [ ] Lane 5. Corrupt `profiles/grok.json` in a fixture profiles directory and scan. Save `corrupt-profile.log`. Pass when the scan aborts with a named error instead of passing.
- [ ] Lane 6. Make an in-scope file unreadable and scan. Save `unreadable.log`. Pass when the scan aborts.
- [ ] Lane 7. Place a host install path in a scanned shared surface. Save `install-path.log`. Pass when it is reported.
- [ ] Lane 8. Place a per-host primitive in a scanned shared surface. Save `primitive.log`. Pass when it is reported.
- [ ] Lane 9. Place a concrete host default model string in a scanned shared surface. Save `default-model.log`. Pass when it is reported.
- [ ] Lane 10. Scan with a second host profile added and no shared-surface change. Save `new-host.log`. Pass when the vocabulary grows from the profile alone with no code edit.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scanner wall time and vocabulary size on the unchanged tree.
- [ ] Probe. Run `python scripts/scan-host-boundary.py -v` five times at trunk and five at head, interleaved, and record vocabulary size from the verbose header.
- [ ] Baseline. Record the trunk median wall time and the trunk vocabulary size first.
- [ ] Rule. Head wall time within 25 percent of trunk, and vocabulary size must not shrink unless the shrink is a deleted duplicate with the same detection proven by lane 7 through lane 9.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges, then spawns `host-authority-sweep` against the new trunk.

## Remove the remaining Grok authority from shared skills (host-authority-sweep)

**Depends on.** `boundary-gate`

**Files.**

- [ ] Edit `skills/reflect/SKILL.md` and `skills/reflect/references/*.md`.
- [ ] Edit `skills/architect/SKILL.md`, `skills/arena/SKILL.md`, `skills/how/SKILL.md`, `skills/interrogate/SKILL.md`, `skills/swarm/SKILL.md`, `skills/why/SKILL.md`.
- [ ] Edit `skills/setup-pstack/SKILL.md`.
- [ ] Edit `tests/test_architecture_documentation.py` and `tests/test_verify_harness_guides.py`.

**Build.**

- [ ] Name the transcript pattern in `skills/reflect/SKILL.md:23` and state which hosts have a reference, instead of naming the one file that exists. Line 56 belongs to `boundary-gate`, which must make the gate green first.
- [ ] Replace the Grok sandbox diagnostic paths in `skills/how/SKILL.md:64-66` with the active host's reference, since the tightened gate does not yet detect a sandbox events file.
- [ ] Redirect every `../setup-pstack/SKILL.md` model reference to `../setup-pstack-grok/references/resolve-model.md`, or rewrite it in projection language with no toml key.
- [ ] Replace the doc-sentence asserts in `tests/test_architecture_documentation.py` with a host-set equality check and a link check over both READMEs.

**You see.**

- [ ] `grep -rn "Grok Build" skills --include=SKILL.md` returns only host-owned directories and the reviewed prohibition in `poteto-mode`.
- [ ] `python scripts/scan-host-boundary.py` still exits 0 with the tightened exemption list.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Add a link-and-contact test that fails when a README names a skill path that does not exist, and run `.venv/bin/python -m pytest -q tests/test_architecture_documentation.py tests/test_verify_harness_guides.py tests/test_scan_host_boundary.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Render the router decision for `reflect` at trunk and head with a fixture profile set. Save `reflect-route.log`. Pass when the head resolves the active host and the trunk names Grok.
- [ ] Lane 2. Grep the shared skill tree for the Grok display name. Save `grok-grep.log`. Pass when every hit is inside a host-owned directory or the reviewed prohibition.
- [ ] Lane 3. Open the authoring playbook path named by `reflect`. Save `authoring-playbook.log`. Pass when the file exists and the path resolves from the skill directory.
- [ ] Lane 4. Resolve `references/<host>-transcript.md` for each declared host. Save `transcript-pattern.log`. Pass when the text names a pattern and states which hosts have one.
- [ ] Lane 5. Follow one model reference from `skills/how/SKILL.md` to its target. Save `how-model-ref.log`. Pass when the target contains the named toml key.
- [ ] Lane 6. Follow the same for `skills/arena/SKILL.md` and `skills/interrogate/SKILL.md`. Save `arena-interrogate-ref.log`. Pass when both resolve.
- [ ] Lane 7. Run the tightened scanner with `skills/setup-pstack/**` no longer exempt. Save `setup-exemption.log`. Pass when the shared entry is scanned and clean.
- [ ] Lane 8. Delete a guide file a README names and run the documentation test. Save `dead-link.log`. Pass when the test fails.
- [ ] Lane 9. Restore the file and rerun. Save `dead-link-restored.log`. Pass when the test passes.
- [ ] Lane 10. Load each edited SKILL.md frontmatter through the skill frontmatter test. Save `frontmatter.log`. Pass when every file parses and keeps its name.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Skills-tree byte count and scanner wall time.
- [ ] Probe. `du -sb skills` and five scanner runs at trunk and head, interleaved.
- [ ] Baseline. Record the trunk byte count and median wall time first.
- [ ] Rule. Head byte count must not grow more than 1 percent, and scanner wall time within 25 percent of trunk.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges.

## Make every gate result independent of the machine (hermetic-doctor)

**Depends on.** `evidence-truth`

**Files.**

- [ ] Edit `scripts/verify-portable.py`.
- [ ] Edit `tests/test_verify_portable.py`, `tests/test_omp_native_package.py`, `tests/test_sync_antigravity_plugin.py`.
- [ ] Edit `.github/workflows/portability-offline.yml`.

**Build.**

- [ ] Base this branch on `fix/709-hermetic-doctor` (PR #717), which already rewrites `scripts/verify-portable.py` and `tests/test_verify_portable.py`. Do not open a parallel portable change against main.
- [ ] Land the #717 fixture-home work, then fix the remaining ambient read at `tests/test_verify_portable.py:301` by providing a fake `openspec` on PATH that answers only from the repository root.
- [ ] Make the OMP native package tests independent of suite order by allocating a unique disposable directory per run and by refusing to read an ambient plugin mirror.
- [ ] Localize the OMP failure that the full offline selection reproduces, since the same file passes alone and in the portable pair.
- [ ] Remove the live antigravity mirror read in `tests/test_sync_antigravity_plugin.py`, which fails when paired with the OMP file because the repository carries skills the installed mirror lacks.
- [ ] Add the order probe to CI so the interaction cannot return silently.

**You see.**

- [ ] The full offline gate selection run twice gives the same pass set.
- [ ] `PATH=/usr/bin:/bin .venv/bin/python -m pytest -q tests/test_verify_portable.py` passes with no developer tooling.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Add a test that changes a fixture home between two runs and asserts the scenario verdict is identical, and a test that runs the OMP package file both alone and after `tests/test_verify_portable.py`. Run `.venv/bin/python -m pytest -q tests/test_verify_portable.py tests/test_omp_native_package.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the CI selection at trunk and head with a fixture HOME. Save `ci-selection.log`. Pass when the head result equals the trunk result for every test not named in this PR.
- [ ] Lane 2. Run the CI selection twice at head. Save `ci-twice.log`. Pass when the two pass sets are identical.
- [ ] Lane 3. Run with `PATH=/usr/bin:/bin`. Save `bare-path.log`. Pass when the portable tests pass.
- [ ] Lane 4. Point the fixture home at a stale plugin mirror. Save `stale-mirror.log`. Pass when the doctor verdict is unchanged.
- [ ] Lane 5. Point it at a fresh mirror. Save `fresh-mirror.log`. Pass when the doctor verdict is unchanged again.
- [ ] Lane 6. Run the OMP package file alone. Save `omp-alone.log`. Pass when it reports 5 passed and 2 skipped or all passed.
- [ ] Lane 7. Run the OMP package file after the portable file in the same pytest process. Save `omp-after-portable.log`. Pass when the result matches lane 6.
- [ ] Lane 8. Run the full offline selection with a read-only ambient home. Save `readonly-home.log`. Pass when nothing attempts a write and the result matches lane 2.
- [ ] Lane 9. Run the antigravity sync test with a fixture home. Save `agy-fixture.log`. Pass when no live install is read.
- [ ] Lane 10. Inspect the CI workflow for a machine-dependent step. Save `workflow-audit.log`. Pass when every doctor scenario runs under the fixture home.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of the offline gate selection.
- [ ] Probe. Run `python -m pytest -q` over the CI selection three times at trunk and three at head, interleaved.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Head median within 15 percent of trunk, and the two head runs must not differ by more than 5 percent.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges.

## Make the declared setup projection the one the writers obey (setup-projection)

**Depends on.** `host-authority-sweep`

**Files.**

- [ ] Edit `profiles/*.json`.
- [ ] Edit `scripts/setup_pstack.py`, `scripts/project-package.py`, `scripts/adapt-harness.py`, `scripts/portability_types.py`.
- [ ] Edit `tests/test_setup_projection.py` and `tests/test_portability_schemas.py`.

**Build.**

- [ ] Give `resolve_setup_projection` a real production caller in the dispatch path, or delete it and read the projection where the write happens.
- [ ] Derive the install-path table and the projection targets in `project-package.py` from `profiles/*/setup`, and delete the four literal sites.
- [ ] Delete the `GOLDEN` copy in `tests/test_setup_projection.py` and replace it with cross-field invariants, including host-catalog requiring a host-specific catalog file and inherit requiring an inherited default model.
- [ ] Validate the host argument against the profile's declared host and reject path traversal.
- [ ] Coerce the three boundary exceptions into `ValidationError`.
- [ ] Drop the `effort` field where it is a pure function of `source`, or state why it stays.
- [ ] Register `tests/test_setup_projection.py` in `.github/workflows/portability-offline.yml`, because a green gate currently says nothing about the new type.
- [ ] Restamp every durable receipt this PR invalidates, or land after `evidence-truth` and restamp once, since the PR edits `portability_types.py` and the profiles that are hashed into `package_driver_revision`, `profile_hash`, and `skills_tree_hash`.

**You see.**

- [ ] `python -c "from scripts.setup_pstack import resolve_setup_projection; print(resolve_setup_projection('acme'))"` raises a named error for an unknown host and traverses nothing.
- [ ] Changing one profile's catalog path changes the projection output with no code edit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Replace the golden comparisons with the invariant tests and one explicit Grok case, and add negative cases for a non-dict block, an unknown key, and a traversal host. Run `.venv/bin/python -m pytest -q tests/test_setup_projection.py tests/test_portability_schemas.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Render the projection for all six hosts at trunk and head. Save `projection-six.log`. Pass when the head adds the declared paths and changes no existing field.
- [ ] Lane 2. Change `profiles/grok.json#setup.catalog` in a fixture tree and render. Save `catalog-follow.log`. Pass when the rendered target follows the profile.
- [ ] Lane 3. Request a host whose profile declares `source: none`. Save `none-host.log`. Pass when the result is a named BLOCKED, not a fallback.
- [ ] Lane 4. Request `../profiles/grok`. Save `traversal.log`. Pass when it is rejected.
- [ ] Lane 5. Request `github:copilot`. Save `alias-host.log`. Pass when it resolves through the declared host name.
- [ ] Lane 6. Declare `host-cli` on a candidate host in a fixture. Save `candidate-cli.log`. Pass when validation fails.
- [ ] Lane 7. Supply a non-dict setup block. Save `non-dict.log`. Pass when it raises `ValidationError`.
- [ ] Lane 8. Run the package projection for every host and diff it against trunk. Save `package-projection.log`. Pass when only the intended paths change.
- [ ] Lane 9. Run `python -m pytest -q tests/test_project_package.py tests/test_setup_projection.py`. Save `package-tests.log`. Pass when both are green.
- [ ] Lane 10. Read the `settlement` cache the projection emits for each host. Save `projection-cache.log`. Pass when no host re-emits a stale catalog hash.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `scripts/project-package.py` across all hosts, and the number of hardcoded host path literals under `scripts/`.
- [ ] Probe. Run the projection five times at trunk and head, interleaved, and count literals with `git grep -c`.
- [ ] Baseline. Record the trunk median and the trunk literal count first.
- [ ] Rule. Head wall time within 15 percent of trunk, and the literal count must drop by at least four.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges.

## Reconcile the epic graph against what merged (gate-reconcile)

**Depends on.** `evidence-truth`, `boundary-gate`, `host-authority-sweep`, `hermetic-doctor`, `setup-projection`

**Files.**

- [ ] Edit `docs/audit/thermo-nuclear-695/*`.
- [ ] Edit `todo.md` and `openspec/` records for #695.
- [ ] Edit the issue bodies through `gh issue edit`.

**Build.**

- [ ] Record in #706 that the audited heads and the merged heads differ for #700, #702, and #705, and that the merged commits were verified after the fact by this program with named run ids.
- [ ] Close #706 with the contiguous-run evidence, or restate it as the open verification item for the next stack.
- [ ] Close #709, #703, and #707 against the merges that satisfy them, and link each to its PR.
- [ ] Leave #699 open with its dependency on `version-identity`, and add the new child issues this review produced.
- [ ] Add each accepted finding to the epic as a checklist row with its PR id, so the plan and the graph cannot diverge.

**You see.**

- [ ] `gh issue view 706` shows the merged heads, the verification ids, and a disposition that matches the repository state.
- [ ] Every open child issue of #695 names a plan identifier.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `node skills/poteto-mode/scripts/check-plan.mjs docs/audit/thermo-nuclear-695/program-plan.md` and assert it exits 0 with the expected section count.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Fetch every issue and PR named in the plan at trunk and head. Save `graph-fetch.log`. Pass when every identifier resolves to a live object.
- [ ] Lane 2. Read #706 and compare its frozen heads to `gh pr view` merged heads. Save `head-compare.log`. Pass when the discrepancy is stated.
- [ ] Lane 3. Read each closed issue and confirm its closing evidence exists. Save `closure-evidence.log`. Pass when every closure names a merged commit.
- [ ] Lane 4. Confirm no open issue duplicates a closed one by title and scope. Save `duplicate-scan.log`. Pass when the set is disjoint.
- [ ] Lane 5. Confirm the plan identifiers match the issue checklist rows one to one. Save `id-crosswalk.log`. Pass when both directions resolve.
- [ ] Lane 6. Confirm `check-plan.mjs` output lists every section with a dependency depth. Save `plan-check.log`. Pass when depths match Appendix A.
- [ ] Lane 7. Confirm the audit directory links resolve on disk. Save `link-check.log`. Pass when every relative link exists.
- [ ] Lane 8. Confirm the epic body lists no finding without a PR id. Save `epic-rows.log`. Pass when every row has one.
- [ ] Lane 9. Confirm `todo.md` reflects the merged state. Save `todo-state.log`. Pass when no merged unit is unchecked.
- [ ] Lane 10. Confirm the verified run order in the plan matches the merge order in `git log`. Save `merge-order.log`. Pass when the two sequences agree.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. The count of open child issues with no plan identifier, and the count of plan identifiers with no issue.
- [ ] Probe. Enumerate both sets with `gh issue list --state open` and the plan section titles, then compare.
- [ ] Baseline. Record the trunk counts from `main` before this PR touches issues.
- [ ] Rule. Both counts must be zero at head.

**Review gate.** None.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Root squash-merges.

## Migrate the release suffix without breaking adapters (version-identity)

**Depends on.** `setup-projection`

**Files.**

- [ ] Edit `pstack.package.json` and every `host_adapters[*].version`.
- [ ] Edit the projected manifests and `scripts/project-package.py` inputs.
- [ ] Edit `.audit/evidence/*.json` surface revisions and `tests/test_package_lifecycle*.py`.

**Build.**

- [ ] Enumerate every consumer of the current suffix and record the list in the PR body.
- [ ] Choose a neutral SemVer pre-release label and preserve the upstream pin.
- [ ] Define the compatibility alias or the explicit breaking upgrade, and state which one applies.
- [ ] Regenerate every projection and invalidate the receipts that hash the descriptor.
- [ ] Prove install, update, and uninstall on each host with a declared lifecycle.

**You see.**

- [ ] `python -m scripts.package_lifecycle version` reports the neutral label on every host adapter.
- [ ] A receipt generated before the change fails its surface check with a named reason.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Add the version-consumer enumeration as a test input and run `.venv/bin/python -m pytest -q tests/test_package_lifecycle.py tests/test_package_lifecycle_safety.py tests/test_project_package.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `the omp profile default model` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `package-lifecycle install` for grok at trunk and head. Save `install-grok.log`. Pass when the head installs a package whose version is the new label and the trunk installs the old one.
- [ ] Lane 2. Run `package-lifecycle update` from the old label to the new one. Save `update-path.log`. Pass when the update succeeds without uninstall.
- [ ] Lane 3. Run `package-lifecycle uninstall` and confirm no user file is removed. Save `uninstall.log`. Pass when only package-owned files disappear.
- [ ] Lane 4. Read every projected manifest and confirm the version matches the descriptor. Save `manifest-versions.log`. Pass when all six agree.
- [ ] Lane 5. Run the version command for each host. Save `version-all.log`. Pass when every host reports the neutral label.
- [ ] Lane 6. Feed a pre-change receipt to the durability check. Save `stale-receipt.log`. Pass when it fails with a named surface reason.
- [ ] Lane 7. Confirm the upstream pin is byte-identical to trunk. Save `upstream-pin.log`. Pass when it is unchanged.
- [ ] Lane 8. Confirm the compatibility alias resolves the old label if one is declared. Save `alias-resolve.log`. Pass when the alias resolves or the breaking notice is printed.
- [ ] Lane 9. Confirm the OMP native package lever still passes. Save `omp-lever.log`. Pass when the lever reports PASS.
- [ ] Lane 10. Confirm no test asserts the old suffix as a literal. Save `suffix-literals.log`. Pass when the grep is empty or every hit is a fixture.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Package projection wall time and projected manifest byte count.
- [ ] Probe. Run `python scripts/project-package.py` five times at trunk and head, interleaved, and measure manifest bytes.
- [ ] Baseline. Record the trunk median and the trunk byte count first.
- [ ] Rule. Wall time within 15 percent of trunk, and manifest bytes must change only by the length delta of the version string.

**Review gate.** The operator reviews before merge.

- [ ] Copy the lane 1 and lane 2 terminal screenshots into `docs/audit/thermo-nuclear-695/review-version-identity-install.log` and `review-version-identity-update.log`.
- [ ] Record a 30 to 60 second video of install then update on the worktree child's real surface. Save it as `docs/audit/thermo-nuclear-695/review-version-identity.cast`.
- [ ] Post the screenshots and the video in chat and stop at merge-ready. Wait for the operator decision on the breaking SemVer question.

**Merge.**

- [ ] Root clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] Operator approves the SemVer decision, then the root squash-merges.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Report the queue table, every verdict, what merged, the remaining operator gate, and the open risks from Appendix C.
- [ ] Confirm the epic #695 graph matches the plan identifiers in both directions.

## Appendix A. Prototype evidence

The arena ran on the boundary gate at `1002590` with two candidates in separate worktrees, `arena/bnd-a` and `arena/bnd-b`, and one cross-judge. Base is candidate A. A holds detection best, with 10 of 10 routing phrasings caught against 8 of 10, and 2 of 8 false positives on legal verb-bearing mentions against 7 of 8. Candidate B had the smaller surface, 385 lines against A's 446, and my first read picked B. The cross-judge picked A and the disagreement resolved on detection, which the rubric ranks first.

Two grafts from B into A. B's per-occurrence allowance accounting, because A's allowance shelters the whole line and lets `Hand the loop to Grok Build.` pass beside the sanctioned sentence. B's CLI leak test, because A's suite never proves a non-zero exit.

Neither candidate met two rubric criteria, so both are build steps rather than grafts. Fail closed on an unparsable profile and an unreadable file. Narrow or delete the `skills/setup-pstack/**` exemption.

Both candidates independently found and fixed the same two real directives, `skills/reflect/SKILL.md:56` and `skills/automate-me/SKILL.md:67`. Two independent attempts converging on the same leak is corroboration that the old gate was blind to it.

The omp native package probe is the other prototype. `tests/test_omp_native_package.py` failed inside the full offline selection, passed twice alone, and passed when paired with `tests/test_verify_portable.py`. The pair with `tests/test_sync_antigravity_plugin.py` failed one test instead, and its dump shows repository skills missing from the live antigravity mirror. So there are two ambient defects, not one, and the OMP one is not yet localized. `hermetic-doctor` owns both.

Unproven and carried as open. Whether the harness accepts a per-child model override, because this host rejected the field, which is why arena and panel family diversity is `DEGRADED`. Whether the six-host runtime claims survive a live run on this machine, because none was attempted.

## Appendix B. Alternatives rejected

Keeping the line-numbered carve-out and adding a second reviewed prohibition was rejected because the failure mode is a traceback on an unrelated edit, and the reviewer cannot see which sentence is protected from the source.

Adding a per-host exemption for each new shared path was rejected because the exemption list then encodes the current tree, which is how the `setup-pstack` hole appeared.

Recording the vacuous openspec row as PASS with a note was rejected because a row that executed nothing is not evidence, and the canonical plane reduces to PASS without it.

Deferring the evidence guard to the next epic was rejected because a guard that cannot record bad news converts every later verdict into a claim.

## Appendix C. Risks

The `evidence-truth` change touches the one file that decides what the receipts mean. Risk of a wrong refusal that blocks a legitimate refresh. The owner watches for a live run that succeeds but is refused, and the lane 2 and lane 3 cases cover both directions.

The `hermetic-doctor` change alters where tests read plugin mirrors. Risk of hiding a real mirror defect behind a fixture. The owner watches lane 4 and lane 5, which must produce the same verdict from a stale and a fresh mirror.

`version-identity` is a published-identity change. Risk that a consumer keyed on the old suffix breaks without a migration path. The owner watches lane 2 and lane 8 and stops for the operator.

The program depends on GitHub issue edits being reversible. Risk that a wrong closure hides work. The owner records the previous body in the PR description before editing.

## Appendix D. Links and reading list

Read `docs/audit/thermo-nuclear-695/summary.md` and its seven detail files before editing anything in this program. The summary states the verdict and the remediation order. The detail files carry the commands.

Read `openspec/specs/pstack-recursive-plan-validation/spec.md` before editing this plan, and run `node skills/poteto-mode/scripts/check-plan.mjs docs/audit/thermo-nuclear-695/program-plan.md` after any edit.

`boundary-gate` and `evidence-truth` both get the `how` and `interrogate` skills before their verdict. The rest get `interrogate` only.

The decision trail for this program is the audit directory itself, with the swarm and arena run identifiers recorded in the program log.
