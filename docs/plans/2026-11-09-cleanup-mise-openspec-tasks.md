# Clean Up Mise OpenSpec Tasks, Harden Verification Scaffolding, and Reconcile Intent Flows

The goal is to clean up OpenSpec tasks in mise.toml to eliminate redundant duplicate tasks.
Operational tasks under openspec namespace are streamlined to status and list.
Validation tasks under validate namespace follow qstack conventions without redundant aliases.
Verification skill scaffolding is hardened with OpenSpec audit checks.
Living specifications and active change proposals are validated with dual-mode checks.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-09-cleanup-mise-openspec-tasks.md, PR ids in order cleanup-mise-tasks, harden-verification-scaffold, reconcile-intent-flows, gate-close-1251, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] cleanup-mise-tasks is first and branches from main.
  - [ ] harden-verification-scaffold after cleanup-mise-tasks.
  - [ ] reconcile-intent-flows after harden-verification-scaffold.
  - [ ] gate-close-1251 after reconcile-intent-flows.
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

## Clean up mise OpenSpec tasks and eliminate redundant duplicate tasks (cleanup-mise-tasks)

**Depends on.** None.

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `tests/test_runtime_toolchain.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Remove redundant `verify:openspec`, `verify:openspec:all`, and `verify:openspec:changes` tasks from `mise.toml`.
- [x] Remove redundant alias `openspec:validate` in favor of canonical `validate:openspec:changes`.
- [x] Retain canonical operational tasks `openspec:status` and `openspec:list`.
- [x] Retain canonical validation tasks `validate:openspec`, `validate:openspec:all`, and `validate:openspec:changes`.
- [x] Update `tests/test_runtime_toolchain.py` assertions to verify the clean task set.
- [x] Update `todo.md` with Epic 1251 task tracking.

**You see.**

- [x] Clean, deduplicated task list in `mise.toml`.
- [x] Green test suite in `tests/test_runtime_toolchain.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py tests/test_openspec_direct.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Dual validation probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-1/dual.png`. Pass when mise run validate:openspec passes.
- [ ] Lane 2. All specs validation probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-2/all.png`. Pass when mise run validate:openspec:all passes.
- [ ] Lane 3. Changes validation probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-3/changes.png`. Pass when mise run validate:openspec:changes passes.
- [ ] Lane 4. OpenSpec list probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-4/list.png`. Pass when mise run openspec:list passes.
- [ ] Lane 5. OpenSpec status probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-5/status.png`. Pass when mise run openspec:status passes.
- [ ] Lane 6. Toolchain test suite probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-6/toolchain.png`. Pass when test_runtime_toolchain passes.
- [ ] Lane 7. Direct openspec test probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-7/direct.png`. Pass when test_openspec_direct passes.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-cleanup-mise-tasks/worker-10/hygiene.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Toolchain test execution duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_runtime_toolchain.py.
- [ ] Baseline. Record trunk duration of toolchain test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/cleanup-mise-tasks-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/cleanup-mise-tasks-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Harden verification skill scaffolding and templates with OpenSpec audit checks (harden-verification-scaffold)

**Depends on.** cleanup-mise-tasks

**Files.**

- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Add OpenSpec change audit validation checks to `scripts/scaffold_verification_skill.py`.
- [x] Expand `tests/test_scaffold_verification_skill.py` with OpenSpec validation audit test cases.
- [x] Verify all 10 verification skill drivers and formal drivers are validated.

**You see.**

- [x] Structured OpenSpec audit capabilities in verification skill scaffolding.
- [x] Green test suite in `tests/test_scaffold_verification_skill.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Scaffolder audit probe. Save `/tmp/swarm-harden-verification-scaffold/worker-1/audit.png`. Pass when scaffolder audit passes.
- [ ] Lane 2. Driver orchestrator probe. Save `/tmp/swarm-harden-verification-scaffold/worker-2/drivers.png`. Pass when drive-all passes.
- [ ] Lane 3. Doctor orchestrator probe. Save `/tmp/swarm-harden-verification-scaffold/worker-3/doctor.png`. Pass when doctor-all passes.
- [ ] Lane 4. Cleanup orchestrator probe. Save `/tmp/swarm-harden-verification-scaffold/worker-4/cleanup.png`. Pass when cleanup-all passes.
- [ ] Lane 5. Scaffolder test suite probe. Save `/tmp/swarm-harden-verification-scaffold/worker-5/tests.png`. Pass when test_scaffold_verification_skill passes.
- [ ] Lane 6. Package projection probe. Save `/tmp/swarm-harden-verification-scaffold/worker-6/projection.png`. Pass when package projection passes.
- [ ] Lane 7. Evidence staleness probe. Save `/tmp/swarm-harden-verification-scaffold/worker-7/staleness.png`. Pass when check-staleness reports fresh.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-harden-verification-scaffold/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-harden-verification-scaffold/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-harden-verification-scaffold/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scaffolder test execution duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_scaffold_verification_skill.py.
- [ ] Baseline. Record trunk duration of scaffolder test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/harden-verification-scaffold-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/harden-verification-scaffold-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Reconcile OpenSpec intent-driven flows and update test tiers documentation (reconcile-intent-flows)

**Depends on.** harden-verification-scaffold

**Files.**

- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `tests/test_verify_docs_sync.py`.
- [x] Edit `todo.md`.

**Build.**

- [x] Update `docs/verification-test-tiers.md` with the clean, deduplicated mise OpenSpec tasks.
- [x] Document the canonical separation between operational commands and validation commands.
- [x] Verify docs sync test suite passes cleanly.

**You see.**

- [x] Accurate and concise verification test tiers documentation.
- [x] Green test suite in `tests/test_verify_docs_sync.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_verify_docs_sync.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Docs sync test probe. Save `/tmp/swarm-reconcile-intent-flows/worker-1/sync.png`. Pass when test_verify_docs_sync passes.
- [ ] Lane 2. OpenSpec list probe. Save `/tmp/swarm-reconcile-intent-flows/worker-2/list.png`. Pass when openspec list runs.
- [ ] Lane 3. OpenSpec status probe. Save `/tmp/swarm-reconcile-intent-flows/worker-3/status.png`. Pass when openspec status runs.
- [ ] Lane 4. Dual validation probe. Save `/tmp/swarm-reconcile-intent-flows/worker-4/validate.png`. Pass when validate:openspec runs.
- [ ] Lane 5. Driver orchestrator probe. Save `/tmp/swarm-reconcile-intent-flows/worker-5/drivers.png`. Pass when drive-all passes.
- [ ] Lane 6. Worktree confinement probe. Save `/tmp/swarm-reconcile-intent-flows/worker-6/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 7. Evidence staleness probe. Save `/tmp/swarm-reconcile-intent-flows/worker-7/staleness.png`. Pass when check-staleness reports fresh.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-reconcile-intent-flows/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-reconcile-intent-flows/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-reconcile-intent-flows/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Docs sync test duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_verify_docs_sync.py.
- [ ] Baseline. Record trunk duration of docs sync test.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/reconcile-intent-flows-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/reconcile-intent-flows-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1251 (gate-close-1251)

**Depends on.** reconcile-intent-flows

**Files.**

- [x] Edit `docs/plans/2026-11-09-cleanup-mise-openspec-tasks.md`.
- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Run full 6-harness verification matrix doctor across all declared hosts.
- [x] Run driver orchestrator across all 10 verification skills.
- [x] Update CHANGELOG.md with Epic 1251 deliverables.
- [x] Reconcile `todo.md` and close Epic #1251 on GitHub.

**You see.**

- [x] 6-Harness Matrix Verdict PASS in doctor output.
- [x] 10 of 10 verification skill drivers pass in drive-all output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-09-cleanup-mise-openspec-tasks.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Driver orchestrator probe. Save `/tmp/swarm-gate-close-1251/worker-1/drivers.png`. Pass when drive-all exits 0.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1251/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1251/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1251/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1251/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1251/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1251/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1251/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Pinned bunx dual validation probe. Save `/tmp/swarm-gate-close-1251/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1251/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1251-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1251-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated deduplication of mise OpenSpec tasks.
- Evaluated removal of redundant verify:openspec duplicate tasks.
- Evaluated canonical task execution with dual-mode validation.

## Appendix B. Alternatives rejected

- Keeping redundant verify:openspec duplicate tasks rejected per principle-subtract-before-you-add and DRY.
- Ad-hoc bash wrapper tasks rejected per principle-laziness-protocol.

