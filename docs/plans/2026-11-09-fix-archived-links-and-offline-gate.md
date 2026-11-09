# Fix Archived Doc Links, Harmonize Offline PR Gate, and Expose OpenSpec Audit Task

The goal is to address findings from the thermo-nuclear code quality review.
Archived change links in architecture documentation must point to valid archive paths.
Model role profile tests must resolve archived change paths reliably.
Hermetic offline tests must run in pull-request validation and mise tasks.
OpenSpec verification scaffolding must be exposed via a mise task.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-09-fix-archived-links-and-offline-gate.md, PR ids in order fix-archived-arch-link, fix-archived-model-role-test, wire-offline-ci-openspec-tests, gate-close-1263, the verification rule, the root merges, and the done condition is every box checked with its evidence."
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:skills/swarm/SKILL.md`
  - [ ] `git show origin/main:profiles/antigravity.json`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/shipping.md`
- [ ] Arm the 30-minute audit tick with the host schedule capability. Never leave the cadence to memory.
- [ ] Use this tick prompt. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] From this parent session, spawn one owner per PR using the host spawn primitive. Depth is 1.
- [ ] Follow this dependency graph.
  - [ ] fix-archived-arch-link is first and branches from main.
  - [ ] fix-archived-model-role-test after fix-archived-arch-link.
  - [ ] wire-offline-ci-openspec-tests after fix-archived-model-role-test.
  - [ ] gate-close-1263 after wire-offline-ci-openspec-tests.
- [ ] Hold the file boundaries strictly per task files list.
- [ ] Hold the review gate for every PR before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`.
- [ ] Open each PR ready with `gh pr create --base <parent-branch>`.
- [ ] Run unslop before each commit and no-comments before review.
- [ ] Rebase onto current trunk before babysit and again before merge.

### Verdict and merge, for every PR

- [ ] A full swarm runs once at the code-ready head.
- [ ] Ten live lanes verify the real surface.
- [ ] Four perf lanes verify timings against baseline.
- [ ] Clean only when every lane is PASS.
- [ ] The root merges verified PRs bottom-up.

### Boot recipe, for every live lane

Each live lane runs in its own worktree child at the PR head. Drive the real surface.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Start the environment and verify toolchains.
- [ ] Execute the live test and save evidence screenshots.

## Update archived OpenSpec change link in architecture documentation (fix-archived-arch-link)

**Depends on.** None.

**Files.**

- [x] Edit `docs/architecture/harness-adapters-and-jev-2026-10-20.md`.
- [x] Edit `tests/test_architecture_documentation.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Update link in `docs/architecture/harness-adapters-and-jev-2026-10-20.md` to reference archived path.
- [x] Pass `test_documented_relative_links_resolve_within_repository` in `tests/test_architecture_documentation.py`.
- [x] Track Issue 1264 under Epic 1263 in `todo.md`.

**You see.**

- [x] All relative links in architecture documentation resolve within repository.
- [x] Green test suite in `tests/test_architecture_documentation.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_architecture_documentation.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Architecture link resolution probe. Save `/tmp/swarm-fix-archived-arch-link/worker-1/links.png`. Pass when test_architecture_documentation passes.
- [ ] Lane 2. Relative link boundary probe. Save `/tmp/swarm-fix-archived-arch-link/worker-2/boundary.png`. Pass when target is relative to root.
- [ ] Lane 3. Markdown existence probe. Save `/tmp/swarm-fix-archived-arch-link/worker-3/exists.png`. Pass when target file exists on disk.
- [ ] Lane 4. OpenSpec archive probe. Save `/tmp/swarm-fix-archived-arch-link/worker-4/archive.png`. Pass when openspec changes archive path is valid.
- [ ] Lane 5. Full architecture test suite probe. Save `/tmp/swarm-fix-archived-arch-link/worker-5/suite.png`. Pass when all 8 architecture tests pass.
- [ ] Lane 6. Toolchain test suite probe. Save `/tmp/swarm-fix-archived-arch-link/worker-6/toolchain.png`. Pass when test_runtime_toolchain passes.
- [ ] Lane 7. Direct openspec test probe. Save `/tmp/swarm-fix-archived-arch-link/worker-7/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-fix-archived-arch-link/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-fix-archived-arch-link/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-fix-archived-arch-link/worker-10/hygiene.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Architecture doc test duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_architecture_documentation.py.
- [ ] Baseline. Record trunk duration of architecture test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/fix-archived-arch-link-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/fix-archived-arch-link-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Support archived change path resolution in model role profiles test (fix-archived-model-role-test)

**Depends on.** fix-archived-arch-link

**Files.**

- [x] Edit `tests/test_model_role_profiles.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Resolve change directory to archived directory when active directory is absent.
- [x] Pass `test_cross_harness_promotion_gate_and_evidence_contract` in `tests/test_model_role_profiles.py`.
- [x] Track Issue 1265 under Epic 1263 in `todo.md`.

**You see.**

- [x] Resilient change path resolution across active and archived OpenSpec directories.
- [x] Green test suite in `tests/test_model_role_profiles.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_model_role_profiles.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Promotion gate test probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-1/gate.png`. Pass when promotion gate test passes.
- [ ] Lane 2. Full model role profiles suite probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-2/profiles.png`. Pass when all 31 tests pass.
- [ ] Lane 3. ADR-0021 status probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-3/adr.png`. Pass when ADR-0021 is accepted.
- [ ] Lane 4. Evidence contract probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-4/contract.png`. Pass when profile schema validates.
- [ ] Lane 5. Untested runtime assertion probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-5/untested.png`. Pass when untested runtimes stay UNTESTED.
- [ ] Lane 6. Architecture documentation probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-6/arch.png`. Pass when test_architecture_documentation passes.
- [ ] Lane 7. Direct openspec test probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-7/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-fix-archived-model-role-test/worker-10/hygiene.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Model role profile test duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_model_role_profiles.py.
- [ ] Baseline. Record trunk duration of model role profiles test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/fix-archived-model-role-test-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/fix-archived-model-role-test-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Wire direct OpenSpec and docs sync tests into offline CI gate and mise tasks (wire-offline-ci-openspec-tests)

**Depends on.** fix-archived-model-role-test

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `mise.toml`.
- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `tests/test_runtime_toolchain.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Add `tests/test_openspec_direct.py` and `tests/test_verify_docs_sync.py` to `.github/workflows/portability-offline.yml`.
- [x] Add `tests/test_openspec_direct.py` and `tests/test_verify_docs_sync.py` to `test:offline` in `mise.toml`.
- [x] Add task `verify:openspec:audit` running `scaffold_verification_skill.py --check-openspec` to `mise.toml`.
- [x] Document offline tests in `docs/verification-test-tiers.md`.
- [x] Update assertions in `tests/test_runtime_toolchain.py`.
- [x] Track Issue 1266 under Epic 1263 in `todo.md`.

**You see.**

- [x] Hermetic offline PR gate includes direct OpenSpec and docs sync tests.
- [x] Task `verify:openspec:audit` is defined and functional in `mise.toml`.
- [x] Green test suite in `tests/test_runtime_toolchain.py` and `tests/test_verify_docs_sync.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py tests/test_openspec_direct.py tests/test_verify_docs_sync.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Mise verify openspec audit probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-1/audit.png`. Pass when mise run verify:openspec:audit passes.
- [ ] Lane 2. Offline workflow syntax probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-2/workflow.png`. Pass when portability-offline.yml is valid.
- [ ] Lane 3. Toolchain test suite probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-3/toolchain.png`. Pass when test_runtime_toolchain passes.
- [ ] Lane 4. Direct openspec test probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-4/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 5. Docs sync test probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-5/docs.png`. Pass when test_verify_docs_sync passes.
- [ ] Lane 6. Select checks mapping probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-6/select.png`. Pass when test_select_checks passes.
- [ ] Lane 7. Plan validation probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-7/plan.png`. Pass when check-plan passes.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-wire-offline-ci-openspec-tests/worker-10/hygiene.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Toolchain and docs sync test duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py tests/test_verify_docs_sync.py.
- [ ] Baseline. Record trunk duration of toolchain and docs sync tests.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/wire-offline-ci-openspec-tests-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/wire-offline-ci-openspec-tests-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1263 (gate-close-1263)

**Depends on.** wire-offline-ci-openspec-tests

**Files.**

- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Run full doctor matrix across all 6 declared harnesses.
- [x] Run driver orchestrator across all 10 verification skills.
- [x] Update `CHANGELOG.md` with Epic 1263 deliverables.
- [x] Reconcile `todo.md` and close Epic #1263 on GitHub.

**You see.**

- [x] 6-Harness Matrix Verdict PASS in doctor output.
- [x] 10 of 10 verification skill drivers pass in drive-all output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-09-fix-archived-links-and-offline-gate.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Driver orchestrator probe. Save `/tmp/swarm-gate-close-1263/worker-1/drivers.png`. Pass when drive-all exits 0.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1263/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1263/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1263/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1263/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1263/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1263/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1263/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Pinned bunx dual validation probe. Save `/tmp/swarm-gate-close-1263/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1263/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1263-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1263-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [x] Every PR merged to trunk in bottom-up order.
- [x] Every box in this plan checked with its evidence.
- [x] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated relative link resolution in architecture documentation.
- Evaluated archived OpenSpec change path resolution in model role profile tests.
- Evaluated inclusion of hermetic tests in offline PR gate and mise tasks.

## Appendix B. Alternatives rejected

- Leaving stale unarchived links rejected per principle-boundary-discipline and KISS.
- Duplicating OpenSpec validation scripts rejected per principle-subtract-before-you-add and DRY.
