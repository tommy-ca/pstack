# Verification Doctor Orchestration and Workspace Hygiene

This program harmonizes verification driver doctor execution, implements doctor-all orchestration, streamlines mise tasks, and enforces clean workspace hygiene.
Work proceeds in four stacked pull requests under Epic 1143.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-verification-doctor-orchestration-and-workspace-hygiene.md, PR ids in order omp-driver-doctor-hygiene, scaffold-doctor-all, mise-doctor-skills-task, gate-close-1143, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] omp-driver-doctor-hygiene is first and branches from main.
  - [ ] scaffold-doctor-all after omp-driver-doctor-hygiene.
  - [ ] mise-doctor-skills-task after scaffold-doctor-all.
  - [ ] gate-close-1143 after mise-doctor-skills-task.
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

## Harmonize OMP verification driver doctor command and prune stale pycache (omp-driver-doctor-hygiene)

**Depends on.** None.

**Files.**

- [x] Edit `.omp/skills/verify-omp-pstack/scripts/driver.sh`.

**Build.**

- [x] Harmonize `.omp/skills/verify-omp-pstack/scripts/driver.sh` doctor command with grok, opencode, and droid patterns.
- [x] Remove heavy 85-second prove_omp_native_package script from quick doctor check to avoid 60-second timeouts.
- [x] Prune untracked `.pyc` cache files in `.grok/skills/verify-pstack/scripts/__pycache__/`.
- [x] Verify that doctor completes within 10 seconds.

**You see.**

- [x] Clean executable doctor command in `.omp/skills/verify-omp-pstack/scripts/driver.sh`.
- [x] Doctor exits 0 in under 10 seconds.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bash .omp/skills/verify-omp-pstack/scripts/driver.sh doctor`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. OMP doctor execution probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-1/doctor.png`. Pass when doctor exits 0.
- [x] Lane 2. OMP drive execution probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-2/drive.png`. Pass when drive exits 0.
- [x] Lane 3. Worktree confinement probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-3/confinement.png`. Pass when worktrees are confined.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-4/projection.png`. Pass when projection passes.
- [x] Lane 5. Verification skills audit probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-5/audit.png`. Pass when 10 skills pass.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-omp-driver-doctor-hygiene/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. OMP doctor execution duration in seconds.
- [x] Probe. Time bash .omp/skills/verify-omp-pstack/scripts/driver.sh doctor.
- [x] Baseline. Record trunk duration of OMP doctor check.
- [x] Rule. Head duration must not exceed 15 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/omp-driver-doctor-hygiene-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/omp-driver-doctor-hygiene-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Add doctor-all flag to scaffold_verification_skill.py and update test suite (scaffold-doctor-all)

**Depends on.** omp-driver-doctor-hygiene

**Files.**

- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Add `--doctor-all` command line option to `scripts/scaffold_verification_skill.py`.
- [x] Support structured JSON output with `--json`.
- [x] Add unit tests in `tests/test_scaffold_verification_skill.py` for `--doctor-all`.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Clean executable CLI command `python3 scripts/scaffold_verification_skill.py --doctor-all`.
- [x] Detailed JSON summary with doctor execution duration, exit codes, and status.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py -k test_cli_doctor_all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Scaffolder doctor-all probe. Save `/tmp/swarm-scaffold-doctor-all/worker-1/doctor-all.png`. Pass when doctor-all exits 0.
- [x] Lane 2. Doctor-all JSON output probe. Save `/tmp/swarm-scaffold-doctor-all/worker-2/json.png`. Pass when JSON matches schema.
- [x] Lane 3. Single skill drive probe. Save `/tmp/swarm-scaffold-doctor-all/worker-3/single.png`. Pass when single drive passes.
- [x] Lane 4. Worktree confinement probe. Save `/tmp/swarm-scaffold-doctor-all/worker-4/confinement.png`. Pass when worktrees are confined.
- [x] Lane 5. Package projection probe. Save `/tmp/swarm-scaffold-doctor-all/worker-5/projection.png`. Pass when projection check passes.
- [x] Lane 6. Verification skills audit probe. Save `/tmp/swarm-scaffold-doctor-all/worker-6/audit.png`. Pass when 10 skills pass.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-scaffold-doctor-all/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-scaffold-doctor-all/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-scaffold-doctor-all/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-scaffold-doctor-all/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Doctor-all execution duration in seconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --doctor-all.
- [x] Baseline. Record trunk duration of doctor-all execution.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/scaffold-doctor-all-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/scaffold-doctor-all-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Add verify:doctor:skills task to mise.toml and update toolchain tests (mise-doctor-skills-task)

**Depends on.** scaffold-doctor-all

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [x] Add `verify:doctor:skills` task to `mise.toml` executing `uv run python scripts/scaffold_verification_skill.py --doctor-all`.
- [x] Update `tests/test_runtime_toolchain.py` assertions for new task contract.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Updated `mise.toml` with new verify:doctor:skills task.
- [x] Passing toolchain tests asserting task definition.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Mise tasks list probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-1/tasks.png`. Pass when verify:doctor:skills appears.
- [x] Lane 2. Mise verify:doctor:skills execution probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-2/run-doctor.png`. Pass when task exits 0.
- [x] Lane 3. Toolchain test suite probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-3/toolchain.png`. Pass when toolchain tests pass.
- [x] Lane 4. Worktree confinement probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-4/confinement.png`. Pass when worktrees are confined.
- [x] Lane 5. Package projection probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-5/projection.png`. Pass when projection check passes.
- [x] Lane 6. Verification skills audit probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-6/audit.png`. Pass when 10 skills pass.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-mise-doctor-skills-task/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Mise verify:doctor:skills task duration in seconds.
- [x] Probe. Time mise run verify:doctor:skills.
- [x] Baseline. Record trunk duration of doctor execution.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/mise-doctor-skills-task-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/mise-doctor-skills-task-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Qualify 6-harness verification matrix and close Epic 1143 (gate-close-1143)

**Depends on.** mise-doctor-skills-task

**Files.**

- [ ] Edit `CHANGELOG.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `docs/plans/2026-11-08-verification-doctor-orchestration-and-workspace-hygiene.md`.

**Build.**

- [ ] Update changelog with Epic 1143 entries.
- [ ] Update todo with Epic 1143 units.
- [ ] Mark all checkboxes in multi-phase plan.
- [ ] Verify plan schema with check-plan script.

**You see.**

- [ ] Complete reconciliation across ledger, todo, and plan.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-verification-doctor-orchestration-and-workspace-hygiene.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1143/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1143/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1143/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1143/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1143/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1143/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1143/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1143/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Ephemeral prune probe. Save `/tmp/swarm-gate-close-1143/worker-9/prune.png`. Pass when prune-ephemeral exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1143/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1143-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1143-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated OMP verification driver doctor command execution and isolated timeout cause.
- Evaluated doctor-all execution across all 10 verification skills.
- Evaluated mise task invocation and toolchain consistency.
- Evaluated workspace hygiene and cache directory pruning.

## Appendix B. Alternatives rejected

- Keeping heavy 85-second prove_omp_native_package script inside quick doctor check rejected because doctor is intended as a rapid health check.
- Increasing timeout to 120s across all skills rejected per KISS and responsiveness principles.
- Leaving doctor orchestration unautomated rejected per DRY and automation principles.
- Manual execution of individual driver doctor commands rejected per reproducibility principles.
