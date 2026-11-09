# Eliminate OpenSpec Python Wrappers and Migrate to Direct Bunx Execution

This program eliminates all OpenSpec Python wrappers across the repository.
It migrates OpenSpec execution entirely to direct pinned bunx commands and mise tasks.
Work proceeds in four stacked pull requests under Epic 1227.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-09-eliminate-openspec-python-wrappers.md, PR ids in order rm-openspec-python-wrapper, direct-openspec-tests, openspec-direct-docs, gate-close-1227, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] rm-openspec-python-wrapper is first and branches from main.
  - [ ] direct-openspec-tests after rm-openspec-python-wrapper.
  - [ ] openspec-direct-docs after direct-openspec-tests.
  - [ ] gate-close-1227 after openspec-direct-docs.
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

## Eliminate scripts/openspec_change.py and migrate portable verifier doctor to direct bunx execution (rm-openspec-python-wrapper)

**Depends on.** None.

**Files.**

- [x] Delete `scripts/openspec_change.py`.
- [x] Edit `scripts/portable_verifier.py`.
- [x] Edit `scripts/verify_portable.py`.
- [x] Edit `scripts/select_checks.py`.

**Build.**

- [x] Remove `scripts/openspec_change.py` from repository.
- [x] Migrate portable verifier doctor canonical plane check to direct bunx openspec validate command.
- [x] Remove wrapper imports from `scripts/portable_verifier.py` and `scripts/verify_portable.py`.
- [x] Remove wrapper mapping from `scripts/select_checks.py`.

**You see.**

- [x] Absence of `scripts/openspec_change.py` in git status.
- [x] Direct bunx execution in doctor canonical plane checks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bunx --yes @fission-ai/openspec@1.16.1 validate --changes --strict`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Direct validation probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-1/validate.png`. Pass when bunx validate exits 0.
- [x] Lane 2. Doctor canonical plane probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-2/doctor.png`. Pass when doctor canonical plane passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-4/projection.png`. Pass when projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-rm-openspec-python-wrapper/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Direct validation duration in seconds.
- [x] Probe. Time bunx --yes @fission-ai/openspec@1.16.1 validate --changes --strict.
- [x] Baseline. Record trunk duration of strict change validation.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/rm-openspec-python-wrapper-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/rm-openspec-python-wrapper-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Harmonize test suites, select-checks mappings, and toolchain tests with direct bunx/mise execution (direct-openspec-tests)

**Depends on.** rm-openspec-python-wrapper

**Files.**

- [x] Delete `tests/test_openspec_change.py`.
- [x] Create `tests/test_openspec_direct.py`.
- [x] Edit `tests/test_verify_portable.py`.
- [x] Edit `tests/test_select_checks.py`.

**Build.**

- [x] Replace wrapper test file with direct openspec test suite.
- [x] Add assertions proving absence of openspec python wrappers.
- [x] Add assertions proving direct bunx and mise execution contracts.
- [x] Remove wrapper dependencies from verify_portable and select_checks tests.

**You see.**

- [x] Green test suite in `tests/test_openspec_direct.py`.
- [x] Clean test execution across full offline test suite.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_openspec_direct.py tests/test_verify_portable.py tests/test_select_checks.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Direct openspec test probe. Save `/tmp/swarm-direct-openspec-tests/worker-1/direct-tests.png`. Pass when test_openspec_direct passes.
- [x] Lane 2. Select checks test probe. Save `/tmp/swarm-direct-openspec-tests/worker-2/select-tests.png`. Pass when test_select_checks passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-direct-openspec-tests/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-direct-openspec-tests/worker-4/projection.png`. Pass when projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-direct-openspec-tests/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-direct-openspec-tests/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-direct-openspec-tests/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-direct-openspec-tests/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-direct-openspec-tests/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-direct-openspec-tests/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Direct test suite duration in seconds.
- [x] Probe. Time uv run pytest tests/test_openspec_direct.py.
- [x] Baseline. Record trunk duration of direct openspec test suite.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/direct-openspec-tests-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/direct-openspec-tests-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Update verification documentation, mise tasks, and intent-driven flow guidance with direct bunx/mise execution (openspec-direct-docs)

**Depends on.** direct-openspec-tests

**Files.**

- [ ] Edit `docs/verification-test-tiers.md`.
- [ ] Edit `mise.toml`.
- [ ] Edit `todo.md`.

**Build.**

- [ ] Document complete elimination of OpenSpec Python wrappers in `docs/verification-test-tiers.md`.
- [ ] Add direct intent-driven OpenSpec helper tasks to `mise.toml`.
- [ ] Document active change reconciliation and planning flow status.
- [ ] Update `todo.md` with Epic 1227 progress.

**You see.**

- [ ] Comprehensive documentation of direct bunx and mise OpenSpec execution.
- [ ] Pinned mise tasks for intent-driven flows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Runtime toolchain test probe. Save `/tmp/swarm-openspec-direct-docs/worker-1/toolchain.png`. Pass when test_runtime_toolchain passes.
- [ ] Lane 2. Dual validation probe. Save `/tmp/swarm-openspec-direct-docs/worker-2/validate.png`. Pass when validate:openspec exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-openspec-direct-docs/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-openspec-direct-docs/worker-4/projection.png`. Pass when projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-openspec-direct-docs/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-openspec-direct-docs/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-openspec-direct-docs/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-openspec-direct-docs/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-openspec-direct-docs/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-openspec-direct-docs/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Toolchain test duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py.
- [ ] Baseline. Record trunk duration of runtime toolchain test.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/openspec-direct-docs-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/openspec-direct-docs-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1227 (gate-close-1227)

**Depends on.** openspec-direct-docs

**Files.**

- [ ] Edit `docs/plans/2026-11-09-eliminate-openspec-python-wrappers.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Run full 6-harness verification matrix doctor across all declared hosts.
- [ ] Run driver orchestrator across all 10 verification skills.
- [ ] Update CHANGELOG.md with Epic 1227 deliverables.
- [ ] Reconcile `todo.md` and close Epic #1227 on GitHub.

**You see.**

- [ ] 6-Harness Matrix Verdict PASS in doctor output.
- [ ] 10 of 10 verification skill drivers pass in drive-all output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-09-eliminate-openspec-python-wrappers.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Driver orchestrator probe. Save `/tmp/swarm-gate-close-1227/worker-1/drivers.png`. Pass when drive-all exits 0.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1227/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1227/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1227/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1227/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1227/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1227/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1227/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Pinned bunx dual validation probe. Save `/tmp/swarm-gate-close-1227/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1227/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1227-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1227-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated direct bunx openspec validate --changes --strict with 11/11 PASS.
- Evaluated direct bunx openspec validate 2026-11-07-pi-extension-package-proof --type change --strict with PASS.
- Evaluated removal of scripts/openspec_change.py in favor of direct execution.
- Evaluated 6-harness doctor with direct bunx command execution.

## Appendix B. Alternatives rejected

- Keeping Python wrapper scripts rejected per principle-laziness-protocol.
- Silently bypassing openspec validation in doctor rejected per principle-prove-it-works.
- Creating bespoke wrapper classes in Python rejected per principle-subtract-before-you-add.
