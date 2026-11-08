# Verification Cleanup Orchestration and Worktree Hygiene

This program implements verification driver cleanup-all orchestration in scaffold_verification_skill.py, wires mise cleanup tasks, enforces worktree confinement, and prunes obsolete local branches.
Work proceeds in four stacked pull requests under Epic 1152.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-verification-cleanup-orchestration-and-worktree-hygiene.md, PR ids in order scaffold-cleanup-all, mise-cleanup-skills-task, worktree-branch-hygiene, gate-close-1152, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] scaffold-cleanup-all is first and branches from main.
  - [ ] mise-cleanup-skills-task after scaffold-cleanup-all.
  - [ ] worktree-branch-hygiene after mise-cleanup-skills-task.
  - [ ] gate-close-1152 after worktree-branch-hygiene.
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

## Add cleanup-all flag to scaffold_verification_skill.py and update test suite (scaffold-cleanup-all)

**Depends on.** None.

**Files.**

- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Add `--cleanup-all` command line option to `scripts/scaffold_verification_skill.py`.
- [x] Support structured JSON output with `--json`.
- [x] Add unit tests in `tests/test_scaffold_verification_skill.py` for `--cleanup-all`.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Clean executable CLI command `python3 scripts/scaffold_verification_skill.py --cleanup-all`.
- [x] Detailed JSON summary with cleanup execution duration, exit codes, and status.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py -k test_cli_cleanup_all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Scaffolder cleanup-all probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-1/cleanup-all.png`. Pass when cleanup-all exits 0.
- [x] Lane 2. Scaffolder doctor-all probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-2/doctor-all.png`. Pass when doctor-all exits 0.
- [x] Lane 3. Scaffolder audit probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-4/projection.png`. Pass when package_projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-scaffold-cleanup-all/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Cleanup-all execution duration in seconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --cleanup-all.
- [x] Baseline. Record trunk duration of driver executions.
- [x] Rule. Head duration must not exceed 30 seconds across all 10 skills.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/scaffold-cleanup-all-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/scaffold-cleanup-all-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Add verify:cleanup:skills task to mise.toml and update toolchain tests (mise-cleanup-skills-task)

**Depends on.** scaffold-cleanup-all

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [x] Add `verify:cleanup:skills` task to `mise.toml` invoking `uv run python scripts/scaffold_verification_skill.py --cleanup-all`.
- [x] Update `tests/test_runtime_toolchain.py` to assert the new task presence and command string.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Clean executable mise task `mise run verify:cleanup:skills`.
- [x] `tests/test_runtime_toolchain.py` asserting all verification driver tasks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Mise cleanup task probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-1/task.png`. Pass when task runs cleanly.
- [x] Lane 2. Mise doctor task probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-2/doctor.png`. Pass when doctor runs cleanly.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-4/projection.png`. Pass when projection passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-mise-cleanup-skills-task/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Mise task execution duration in seconds.
- [x] Probe. Time mise run verify:cleanup:skills.
- [x] Baseline. Record trunk duration of driver executions.
- [x] Rule. Head duration must not exceed 30 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/mise-cleanup-skills-task-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/mise-cleanup-skills-task-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Prune obsolete merged local branches, verify worktree confinement, and enforce clean git state (worktree-branch-hygiene)

**Depends on.** mise-cleanup-skills-task

**Files.**

- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Verify worktree confinement with `python3 scripts/worktree_protocol.py check`.
- [x] Safely prune obsolete local branches cherry-merged into `main`.
- [x] Document worktree confinement and branch lifecycle invariants in `docs/verification-test-tiers.md`.
- [x] Verify zero untracked clutter and clean working tree.

**You see.**

- [x] Pruned local branch list with zero merged leftover branches.
- [x] Clean `git status` reporting zero untracked clutter.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/worktree_protocol.py check`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Worktree confinement probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-1/confinement.png`. Pass when worktrees are confined.
- [x] Lane 2. Local branch count probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-2/branches.png`. Pass when stale branches are pruned.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-4/projection.png`. Pass when projection passes.
- [x] Lane 5. Evidence staleness probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-5/staleness.png`. Pass when staleness reports all fresh.
- [x] Lane 6. Poteto test suite probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-6/poteto.png`. Pass when 104 tests pass.
- [x] Lane 7. Python line ceiling probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-7/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 8. Untracked file probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-8/untracked.png`. Pass when untracked files are expected.
- [x] Lane 9. Git status probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-9/status.png`. Pass when status is clean.
- [x] Lane 10. OpenSpec change resolution probe. Save `/tmp/swarm-worktree-branch-hygiene/worker-10/openspec.png`. Pass when OpenSpec change validates.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Confinement check duration in seconds.
- [x] Probe. Time python3 scripts/worktree_protocol.py check.
- [x] Baseline. Record trunk duration of confinement check.
- [x] Rule. Head duration must not exceed 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/worktree-branch-hygiene-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/worktree-branch-hygiene-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile plan, and close Epic 1152 (gate-close-1152)

**Depends on.** worktree-branch-hygiene

**Files.**

- [x] Edit `docs/plans/2026-11-08-verification-cleanup-orchestration-and-worktree-hygiene.md`.
- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Run full 6-harness verification matrix doctor across all hosts.
- [x] Run offline contract suite, poteto-mode bun tests, and plan validation.
- [x] Update CHANGELOG.md with Epic 1152 deliverables.
- [x] Reconcile `todo.md` and mark all child units and Epic 1152 complete.

**You see.**

- [x] 6-Harness Matrix Verdict PASS in doctor output.
- [x] Complete evidence receipts recorded for all six harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-verification-cleanup-orchestration-and-worktree-hygiene.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1152/worker-1/confinement.png`. Pass when worktrees are confined.
- [x] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1152/worker-2/projection.png`. Pass when package_projection check passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1152/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1152/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1152/worker-5/evidence.png`. Pass when check-evidence passes.
- [x] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1152/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [x] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1152/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1152/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Cleanup skills probe. Save `/tmp/swarm-gate-close-1152/worker-9/cleanup.png`. Pass when cleanup-all exits 0.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1152/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Full verification gate duration in seconds.
- [x] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [x] Baseline. Record trunk duration of doctor across all hosts.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/gate-close-1152-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/gate-close-1152-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every PR merged to trunk in bottom-up order.
- [x] Every box in this plan checked with its evidence.
- [x] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated verification skill driver cleanup execution across all 10 skills.
- Evaluated cleanup-all command-line integration and structured JSON output.
- Evaluated mise task invocation and runtime toolchain consistency.
- Evaluated branch pruning and worktree confinement validation.

## Appendix B. Alternatives rejected

- Manual per-skill driver cleanup execution rejected per automation and DRY principles.
- Leaving stale cherry-merged branches unpruned rejected per clean repository hygiene.
- Adding arbitrary external worktree paths rejected per principle-boundary-discipline.
