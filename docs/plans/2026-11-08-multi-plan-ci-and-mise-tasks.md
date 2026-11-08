# Multi-Plan CI Validation and Mise Task Synchronization

This program enhances plan validation tooling, synchronizes mise tasks, and enforces verification driver automation.
Work proceeds in four stacked pull requests under Epic 1125.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-multi-plan-ci-and-mise-tasks.md, PR ids in order multi-plan-ci, mise-tasks-sync, prune-ephemeral-clutter, gate-close-1125, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] multi-plan-ci is first and branches from main.
  - [ ] mise-tasks-sync after multi-plan-ci.
  - [ ] prune-ephemeral-clutter after mise-tasks-sync.
  - [ ] gate-close-1125 after prune-ephemeral-clutter.
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
- [ ] Execute commands and verify side effects.
- [ ] Save output logs and screenshots for the report.

## Support multi-file plan validation and wire into CI (multi-plan-ci)

**Depends on.** None.

**Files.**

- [x] Edit `skills/poteto-mode/scripts/check-plan.mjs`.
- [x] Edit `skills/poteto-mode/scripts/check-plan.test.mjs`.
- [x] Edit `.github/workflows/portability-offline.yml`.

**Build.**

- [x] Accept multiple plan file arguments in check-plan script.
- [x] Validate each plan file and aggregate problem reports across files.
- [x] Add unit tests for multiple file validation in check-plan test suite.
- [x] Update offline CI workflow to validate all plans in docs/plans directory.

**You see.**

- [x] Command bun check-plan.mjs docs/plans/*.md passes with zero problems reported.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun test skills/poteto-mode/scripts/check-plan.test.mjs`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Single plan validation probe. Save `/tmp/swarm-multi-plan-ci/worker-1/single.png`. Pass when single plan passes.
- [x] Lane 2. Multi-plan validation probe. Save `/tmp/swarm-multi-plan-ci/worker-2/multi.png`. Pass when multiple plans pass.
- [x] Lane 3. Error reporting probe. Save `/tmp/swarm-multi-plan-ci/worker-3/error.png`. Pass when bad plan exits non-zero.
- [x] Lane 4. Check-plan test suite probe. Save `/tmp/swarm-multi-plan-ci/worker-4/suite.png`. Pass when all tests pass.
- [x] Lane 5. All plans sweep probe. Save `/tmp/swarm-multi-plan-ci/worker-5/sweep.png`. Pass when all 13 plans pass.
- [x] Lane 6. Worktree confinement probe. Save `/tmp/swarm-multi-plan-ci/worker-6/confinement.png`. Pass when worktrees are confined.
- [x] Lane 7. Package projection probe. Save `/tmp/swarm-multi-plan-ci/worker-7/projection.png`. Pass when projection check passes.
- [x] Lane 8. Verification skills audit probe. Save `/tmp/swarm-multi-plan-ci/worker-8/audit.png`. Pass when 10 skills pass.
- [x] Lane 9. Python line ceiling probe. Save `/tmp/swarm-multi-plan-ci/worker-9/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-multi-plan-ci/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Multi-plan audit duration across all plans in milliseconds.
- [x] Probe. Time bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/*.md.
- [x] Baseline. Record single plan execution duration.
- [x] Rule. Sweep duration across all plans must not exceed 1000 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/multi-plan-ci-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/multi-plan-ci-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Synchronize mise offline test suite and add driver tasks (mise-tasks-sync)

**Depends on.** multi-plan-ci

**Files.**

- [ ] Edit `mise.toml`.

**Build.**

- [ ] Update test:offline task in mise.toml to include all 54 offline tests.
- [ ] Add plan:check task to validate all plans via check-plan script.
- [ ] Add verify:drivers task to execute launch and drive across all 10 drivers.

**You see.**

- [ ] Task configuration in mise.toml includes updated offline test lists and driver commands.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `python3 -m pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Mise plan check probe. Save `/tmp/swarm-mise-tasks-sync/worker-1/plan.png`. Pass when plan:check succeeds.
- [ ] Lane 2. Mise offline test suite probe. Save `/tmp/swarm-mise-tasks-sync/worker-2/offline.png`. Pass when test:offline succeeds.
- [ ] Lane 3. Verification skill audit probe. Save `/tmp/swarm-mise-tasks-sync/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-mise-tasks-sync/worker-4/projection.png`. Pass when projection check passes.
- [ ] Lane 5. Evidence staleness probe. Save `/tmp/swarm-mise-tasks-sync/worker-5/staleness.png`. Pass when staleness is fresh.
- [ ] Lane 6. Evidence durability probe. Save `/tmp/swarm-mise-tasks-sync/worker-6/durability.png`. Pass when check-evidence passes.
- [ ] Lane 7. Worktree confinement probe. Save `/tmp/swarm-mise-tasks-sync/worker-7/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-mise-tasks-sync/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Mise config validation probe. Save `/tmp/swarm-mise-tasks-sync/worker-9/mise.png`. Pass when mise.toml is valid.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-mise-tasks-sync/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Mise offline test task execution duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py.
- [ ] Baseline. Record execution duration of toolchain test.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/mise-tasks-sync-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/mise-tasks-sync-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Prune ephemeral evidence runs and audit clutter (prune-ephemeral-clutter)

**Depends on.** mise-tasks-sync

**Files.**

- [ ] Edit `todo.md`.

**Build.**

- [ ] Prune stale ephemeral evidence directories keeping only active receipts.
- [ ] Verify zero unnecessary files and enforce style rules.

**You see.**

- [ ] Workspace free of untracked temporary runs.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `python3 scripts/portable_verifier.py prune-ephemeral --keep-last 1`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Ephemeral prune probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-1/prune.png`. Pass when prune exits 0.
- [ ] Lane 2. Evidence durability probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-2/durability.png`. Pass when receipts survive.
- [ ] Lane 3. Evidence staleness probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-3/staleness.png`. Pass when evidence remains fresh.
- [ ] Lane 4. Worktree confinement probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-4/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 5. Package projection probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-5/projection.png`. Pass when projection passes.
- [ ] Lane 6. Verification skills audit probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-6/audit.png`. Pass when 10 skills pass.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-7/poteto.png`. Pass when 102 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-prune-ephemeral-clutter/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Prune script duration in seconds.
- [ ] Probe. Time python3 scripts/portable_verifier.py prune-ephemeral --keep-last 1.
- [ ] Baseline. Record trunk duration of prune-ephemeral.
- [ ] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/prune-ephemeral-clutter-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/prune-ephemeral-clutter-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix and close Epic 1125 (gate-close-1125)

**Depends on.** prune-ephemeral-clutter

**Files.**

- [ ] Edit `CHANGELOG.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `docs/plans/2026-11-08-multi-plan-ci-and-mise-tasks.md`.

**Build.**

- [ ] Update changelog with Epic 1125 entries.
- [ ] Update todo with Epic 1125 units.
- [ ] Mark all checkboxes in multi-phase plan.
- [ ] Verify plan schema with check-plan script.

**You see.**

- [ ] Complete reconciliation across ledger, todo, and plan.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-multi-plan-ci-and-mise-tasks.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1125/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1125/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1125/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1125/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1125/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1125/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1125/worker-7/poteto-tests.png`. Pass when 102 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1125/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Ephemeral prune probe. Save `/tmp/swarm-gate-close-1125/worker-9/prune.png`. Pass when prune-ephemeral exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1125/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1125-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1125-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated multi-file support in check-plan script.
- Evaluated offline CI execution time and coverage.
- Evaluated mise task definitions and execution consistency.
- Evaluated verification driver determinism across all 10 skills.

## Appendix B. Alternatives rejected

- Leaving check-plan single-file only rejected per DRY and continuous validation principles.
- Leaving mise test:offline out of sync with CI rejected per reproducible environment principle.
- Deleting upstream reference cache rejected because active scripts rely on it.
- Skipping multi-harness doctor matrix rejected per strict verification protocol.
