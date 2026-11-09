# Reconcile Active OpenSpec Intent-Driven Flows, Archive Completed Changes, and Harden Verification Tooling

The goal is to reconcile all active OpenSpec intent-driven changes across the repository.
Completed changes that have merged to main are archived into living specifications.
Verification tooling and select-checks mappings are hardened.
All living specifications and active changes are validated with dual-mode checks.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-09-reconcile-openspec-flows-and-archive.md, PR ids in order openspec-select-checks, archive-openspec-batch1, archive-openspec-batch2, gate-close-1239, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] openspec-select-checks is first and branches from main.
  - [ ] archive-openspec-batch1 after openspec-select-checks.
  - [ ] archive-openspec-batch2 after archive-openspec-batch1.
  - [ ] gate-close-1239 after archive-openspec-batch2.
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

## Update select-checks OpenSpec mappings and harden verification skill scaffolding (openspec-select-checks)

**Depends on.** None.

**Files.**

- [x] Edit `scripts/select_checks.py`.
- [x] Edit `tests/test_select_checks.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Map openspec pattern in `scripts/select_checks.py` to `tests/test_openspec_direct.py`.
- [x] Update `tests/test_select_checks.py` with direct openspec test assertions.
- [x] Verify select-checks plan correctly resolves direct openspec tests.
- [x] Update `todo.md` with Epic 1239 task tracking.

**You see.**

- [x] Accurate check selection when modifying openspec files.
- [x] Green test suite in `tests/test_select_checks.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_select_checks.py tests/test_openspec_direct.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Select checks test probe. Save `/tmp/swarm-openspec-select-checks/worker-1/select.png`. Pass when test_select_checks passes.
- [ ] Lane 2. Direct openspec test probe. Save `/tmp/swarm-openspec-select-checks/worker-2/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-openspec-select-checks/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-openspec-select-checks/worker-4/projection.png`. Pass when projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-openspec-select-checks/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-openspec-select-checks/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-openspec-select-checks/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-openspec-select-checks/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-openspec-select-checks/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-openspec-select-checks/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Select checks duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_select_checks.py.
- [ ] Baseline. Record trunk duration of select checks test.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/openspec-select-checks-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/openspec-select-checks-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Reconcile and archive completed active changes into living specifications Batch 1 October changes (archive-openspec-batch1)

**Depends on.** openspec-select-checks

**Files.**

- [x] Edit `openspec/specs/pstack-portability/spec.md`.
- [x] Edit `openspec/specs/pstack-quickstart/spec.md`.
- [x] Edit `openspec/specs/pstack-harness-map/spec.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Archive `2026-10-15-harness-neutral-role-policy` into `openspec/changes/archive/`.
- [x] Archive `2026-10-20-cross-port-semantic-delta` into `openspec/changes/archive/`.
- [x] Archive `2026-10-21-fast-role-task-fit` into `openspec/changes/archive/`.
- [x] Archive `2026-10-31-llm-wiki-reference-contracts` into `openspec/changes/archive/`.

**You see.**

- [x] Four completed October changes archived with complete planning chains preserved.
- [x] Living specifications updated cleanly in `openspec/specs/`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `mise run validate:openspec`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Dual validation probe. Save `/tmp/swarm-archive-openspec-batch1/worker-1/validate.png`. Pass when validate:openspec exits 0.
- [ ] Lane 2. Direct openspec test probe. Save `/tmp/swarm-archive-openspec-batch1/worker-2/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-archive-openspec-batch1/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-archive-openspec-batch1/worker-4/projection.png`. Pass when projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-archive-openspec-batch1/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-archive-openspec-batch1/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-archive-openspec-batch1/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-archive-openspec-batch1/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-archive-openspec-batch1/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-archive-openspec-batch1/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec dual validation duration in seconds.
- [ ] Probe. Time mise run validate:openspec.
- [ ] Baseline. Record trunk duration of dual validation.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/archive-openspec-batch1-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/archive-openspec-batch1-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Reconcile and archive completed active changes into living specifications Batch 2 November changes (archive-openspec-batch2)

**Depends on.** archive-openspec-batch1

**Files.**

- [x] Edit `openspec/specs/pstack-portability/spec.md`.
- [x] Edit `openspec/specs/pstack-reusable-skill-patterns/spec.md`.
- [x] Edit `openspec/specs/pstack-setup-overlays/spec.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Archive `2026-11-05-pi-standalone-candidate` into `openspec/changes/archive/`.
- [x] Archive `2026-11-06-cross-port-parity` into `openspec/changes/archive/`.
- [x] Archive `2026-11-06-cross-port-semantic-parity` into `openspec/changes/archive/`.
- [x] Archive `2026-11-06-single-entry-setup-pstack` into `openspec/changes/archive/`.
- [x] Archive `2026-11-06-upstream-semantic-boundary` into `openspec/changes/archive/`.
- [x] Archive `2026-11-07-deepseek-skills-22-source-refresh` into `openspec/changes/archive/`.

**You see.**

- [x] Six completed November changes archived with complete planning chains preserved.
- [x] Living specifications updated cleanly in `openspec/specs/`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `mise run validate:openspec`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Dual validation probe. Save `/tmp/swarm-archive-openspec-batch2/worker-1/validate.png`. Pass when validate:openspec exits 0.
- [ ] Lane 2. Direct openspec test probe. Save `/tmp/swarm-archive-openspec-batch2/worker-2/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-archive-openspec-batch2/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-archive-openspec-batch2/worker-4/projection.png`. Pass when projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-archive-openspec-batch2/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-archive-openspec-batch2/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-archive-openspec-batch2/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-archive-openspec-batch2/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-archive-openspec-batch2/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-archive-openspec-batch2/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec dual validation duration in seconds.
- [ ] Probe. Time mise run validate:openspec.
- [ ] Baseline. Record trunk duration of dual validation.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/archive-openspec-batch2-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/archive-openspec-batch2-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1239 (gate-close-1239)

**Depends on.** archive-openspec-batch2

**Files.**

- [ ] Edit `docs/plans/2026-11-09-reconcile-openspec-flows-and-archive.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Run full 6-harness verification matrix doctor across all declared hosts.
- [ ] Run driver orchestrator across all 10 verification skills.
- [ ] Update CHANGELOG.md with Epic 1239 deliverables.
- [ ] Reconcile `todo.md` and close Epic #1239 on GitHub.

**You see.**

- [ ] 6-Harness Matrix Verdict PASS in doctor output.
- [ ] 10 of 10 verification skill drivers pass in drive-all output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-09-reconcile-openspec-flows-and-archive.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Driver orchestrator probe. Save `/tmp/swarm-gate-close-1239/worker-1/drivers.png`. Pass when drive-all exits 0.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1239/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1239/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1239/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1239/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1239/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1239/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1239/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Pinned bunx dual validation probe. Save `/tmp/swarm-gate-close-1239/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1239/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1239-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1239-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated direct bunx openspec archive of 2026-10-15-harness-neutral-role-policy.
- Evaluated spec integration with 11 added requirements.
- Evaluated dual-mode validation after archive with PASS.

## Appendix B. Alternatives rejected

- Archiving all changes in one monolithic PR rejected per principle-sequence-verifiable-units.
- Bespoke Python archive scripts rejected per principle-laziness-protocol.
- Archiving incomplete change 2026-11-07-pi-extension-package-proof rejected per openspec-git-discipline.
