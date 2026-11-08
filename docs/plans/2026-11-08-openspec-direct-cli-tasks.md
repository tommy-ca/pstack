# OpenSpec Direct CLI Task Execution and Toolchain Verification Harmonization

This program updates OpenSpec tasks in mise.toml to invoke openspec CLI commands directly rather than relying on another Python wrapper, matching qstack/mise.toml task conventions. It harmonizes toolchain test assertions, updates verification documentation, and qualifies the 6-harness verification matrix across all declared harnesses.
Work proceeds in four stacked pull requests under Epic 1191.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-openspec-direct-cli-tasks.md, PR ids in order direct-mise-tasks, toolchain-tests-harmonization, verification-docs-parity, gate-close-1191, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] direct-mise-tasks is first and branches from main.
  - [ ] toolchain-tests-harmonization after direct-mise-tasks.
  - [ ] verification-docs-parity after toolchain-tests-harmonization.
  - [ ] gate-close-1191 after verification-docs-parity.
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

## Update OpenSpec tasks in mise.toml to invoke openspec CLI directly per qstack/mise.toml (direct-mise-tasks)

**Depends on.** None.

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [x] Replace Python wrapper in `openspec:status` with direct `openspec status --all`.
- [x] Replace Python wrapper in `verify:openspec` with dual-mode `openspec validate --all && openspec validate --changes --strict`.
- [x] Add `verify:openspec:changes` running `openspec validate --changes --strict`.
- [x] Add `validate:openspec`, `validate:openspec:all`, and `validate:openspec:changes` matching `qstack/mise.toml`.

**You see.**

- [x] Clean executable tasks in `mise.toml` invoking `openspec` directly without Python indirection.
- [x] Full parity with `qstack/mise.toml` task definitions.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py -k test_mise_toml_configuration`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Direct status probe. Save `/tmp/swarm-direct-mise-tasks/worker-1/status.png`. Pass when openspec:status exits 0.
- [ ] Lane 2. Direct dual validate probe. Save `/tmp/swarm-direct-mise-tasks/worker-2/validate.png`. Pass when verify:openspec exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-direct-mise-tasks/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-direct-mise-tasks/worker-4/projection.png`. Pass when package_projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-direct-mise-tasks/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-direct-mise-tasks/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-direct-mise-tasks/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-direct-mise-tasks/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-direct-mise-tasks/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-direct-mise-tasks/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Mise configuration check duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py.
- [ ] Baseline. Record trunk duration of runtime toolchain test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/direct-mise-tasks-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/direct-mise-tasks-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Harmonize runtime toolchain and OpenSpec test suites with direct CLI contracts (toolchain-tests-harmonization)

**Depends on.** direct-mise-tasks

**Files.**

- [x] Edit `tests/test_runtime_toolchain.py`.
- [x] Edit `tests/test_openspec_change.py`.

**Build.**

- [x] Update `tests/test_runtime_toolchain.py` assertions for direct CLI commands across all openspec tasks.
- [x] Ensure `tests/test_openspec_change.py` passes completely without regressions.
- [x] Validate both `verify:openspec` and `validate:openspec` task definitions in toolchain tests.
- [x] Verify zero unnecessary wrappers per SOLID, KISS, DRY, and YAGNI.

**You see.**

- [x] Green test suites for both `tests/test_runtime_toolchain.py` and `tests/test_openspec_change.py`.
- [x] Direct validation contracts verified against actual `mise.toml` contents.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py tests/test_openspec_change.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Toolchain suite probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-1/toolchain.png`. Pass when toolchain tests pass.
- [ ] Lane 2. OpenSpec change suite probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-2/openspec.png`. Pass when openspec tests pass.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-toolchain-tests-harmonization/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Test suite execution duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py tests/test_openspec_change.py.
- [ ] Baseline. Record trunk duration of test suites.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/toolchain-tests-harmonization-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/toolchain-tests-harmonization-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Update verification documentation with direct OpenSpec CLI tasks and qstack parity (verification-docs-parity)

**Depends on.** toolchain-tests-harmonization

**Files.**

- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Document direct OpenSpec CLI tasks in `docs/verification-test-tiers.md`.
- [x] Document qstack task parity (`validate:openspec`, `validate:openspec:all`, `validate:openspec:changes`).
- [x] Remove outdated references to Python wrapper task implementations.
- [x] Update todo.md with completed tasks under Epic 1191.

**You see.**

- [x] Accurate documentation of direct OpenSpec CLI tasks in `docs/verification-test-tiers.md`.
- [x] Updated execution plan and task ledger in `todo.md`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `openspec status --all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Direct openspec status probe. Save `/tmp/swarm-verification-docs-parity/worker-1/status.png`. Pass when status exits 0.
- [ ] Lane 2. Direct dual validate probe. Save `/tmp/swarm-verification-docs-parity/worker-2/validate.png`. Pass when dual validate exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-verification-docs-parity/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-verification-docs-parity/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-verification-docs-parity/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-verification-docs-parity/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-verification-docs-parity/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-verification-docs-parity/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-verification-docs-parity/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-verification-docs-parity/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec direct status duration in seconds.
- [ ] Probe. Time openspec status --all.
- [ ] Baseline. Record trunk duration of direct status execution.
- [ ] Rule. Head duration must not exceed 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verification-docs-parity-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/verification-docs-parity-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1191 (gate-close-1191)

**Depends on.** verification-docs-parity

**Files.**

- [ ] Edit `docs/plans/2026-11-08-openspec-direct-cli-tasks.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Run full 6-harness verification matrix doctor across all hosts.
- [ ] Run plan check, offline test suites, and direct OpenSpec validations.
- [ ] Update CHANGELOG.md with Epic 1191 deliverables.
- [ ] Reconcile `todo.md` and close Epic #1191 on GitHub.

**You see.**

- [ ] 6-Harness Matrix Verdict PASS in doctor output.
- [ ] Complete evidence receipts recorded for all six harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-openspec-direct-cli-tasks.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1191/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1191/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1191/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1191/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1191/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1191/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1191/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1191/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. OpenSpec direct dual validation probe. Save `/tmp/swarm-gate-close-1191/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1191/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1191-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1191-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated direct `openspec status --all` execution with native formatting and exit code 0.
- Evaluated direct `openspec validate --all` and `openspec validate --changes --strict` with 0 failures.
- Evaluated `qstack/mise.toml` task naming and direct CLI execution conventions.
- Evaluated 6-harness doctor matrix across all declared hosts.

## Appendix B. Alternatives rejected

- Adding another custom Python wrapper rejected per principle-laziness-protocol and principle-subtract-before-you-add.
- Modifying hardened living schemas rejected per principle-boundary-discipline.
- Skipping live harness matrix verification rejected per principle-prove-it-works.
