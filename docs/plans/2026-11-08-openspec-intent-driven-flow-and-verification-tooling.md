# OpenSpec Intent-Driven Flow Inspection and Verification Tooling

This program implements intent-driven OpenSpec planning flow inspection in scripts/openspec_change.py, wires mise tasks, audits artifact chains, and qualifies the 6-harness verification matrix.
Work proceeds in four stacked pull requests under Epic 1164.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-openspec-intent-driven-flow-and-verification-tooling.md, PR ids in order openspec-flow-status, mise-openspec-tasks, openspec-chain-audit, gate-close-1164, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] openspec-flow-status is first and branches from main.
  - [ ] mise-openspec-tasks after openspec-flow-status.
  - [ ] openspec-chain-audit after mise-openspec-tasks.
  - [ ] gate-close-1164 after openspec-chain-audit.
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

## Add intent-driven flow status inspection to scripts/openspec_change.py and update test suite (openspec-flow-status)

**Depends on.** None.

**Files.**

- [x] Edit `scripts/openspec_change.py`.
- [x] Edit `tests/test_openspec_change.py`.

**Build.**

- [x] Add `inspect_intent_driven_change` function to `scripts/openspec_change.py`.
- [x] Support `--status` and `--json` flags in CLI invocation.
- [x] Add unit tests in `tests/test_openspec_change.py` for status inspection and JSON reporting.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Clean executable CLI command `python3 scripts/openspec_change.py --status`.
- [x] Detailed JSON summary with artifact completion states across proposal, specs, design, adr, and tasks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_openspec_change.py -k test_intent_driven_status`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. OpenSpec status inspection probe. Save `/tmp/swarm-openspec-flow-status/worker-1/status.png`. Pass when status exits 0.
- [ ] Lane 2. OpenSpec JSON output probe. Save `/tmp/swarm-openspec-flow-status/worker-2/json.png`. Pass when JSON contains artifacts.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-openspec-flow-status/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-openspec-flow-status/worker-4/projection.png`. Pass when package_projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-openspec-flow-status/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-openspec-flow-status/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-openspec-flow-status/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-openspec-flow-status/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-openspec-flow-status/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-openspec-flow-status/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec status execution duration in seconds.
- [ ] Probe. Time python3 scripts/openspec_change.py --status.
- [ ] Baseline. Record trunk duration of OpenSpec list.
- [ ] Rule. Head duration must not exceed 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/openspec-flow-status-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/openspec-flow-status-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Add verify:openspec and openspec:status tasks to mise.toml and update toolchain tests (mise-openspec-tasks)

**Depends on.** openspec-flow-status

**Files.**

- [ ] Edit `mise.toml`.
- [ ] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [ ] Add `openspec:status` task to `mise.toml` executing `uv run python scripts/openspec_change.py --status`.
- [ ] Add `verify:openspec` task to `mise.toml` executing `uv run python scripts/openspec_change.py validate`.
- [ ] Update `tests/test_runtime_toolchain.py` to assert both tasks are defined.
- [ ] Verify test suite passes cleanly with zero errors.

**You see.**

- [ ] Clean executable mise tasks `mise run openspec:status` and `mise run verify:openspec`.
- [ ] `tests/test_runtime_toolchain.py` asserting all OpenSpec tasks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Mise status task probe. Save `/tmp/swarm-mise-openspec-tasks/worker-1/status.png`. Pass when status task exits 0.
- [ ] Lane 2. Mise verify task probe. Save `/tmp/swarm-mise-openspec-tasks/worker-2/verify.png`. Pass when verify task exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-mise-openspec-tasks/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-mise-openspec-tasks/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-mise-openspec-tasks/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-mise-openspec-tasks/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-mise-openspec-tasks/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-mise-openspec-tasks/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-mise-openspec-tasks/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-mise-openspec-tasks/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Mise task execution duration in seconds.
- [ ] Probe. Time mise run openspec:status.
- [ ] Baseline. Record trunk duration of OpenSpec commands.
- [ ] Rule. Head duration must not exceed 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/mise-openspec-tasks-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/mise-openspec-tasks-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Audit intent-driven artifact chains across all changes and document flow contracts (openspec-chain-audit)

**Depends on.** mise-openspec-tasks

**Files.**

- [ ] Edit `docs/verification-test-tiers.md`.
- [ ] Edit `todo.md`.

**Build.**

- [ ] Audit intent-driven artifact chains across all active and archived changes in `openspec/`.
- [ ] Document the 5-artifact planning lifecycle (proposal, specs, design, adr, tasks) in `docs/verification-test-tiers.md`.
- [ ] Ensure strict compliance with `archive-chain-integrity` specification.
- [ ] Verify zero untracked clutter and clean working tree.

**You see.**

- [ ] Verified intent-driven artifact chains across all changes.
- [ ] Clear documentation of OpenSpec intent-driven flows in `docs/verification-test-tiers.md`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run python scripts/openspec_change.py 2026-11-07-pi-extension-package-proof`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Change validation probe. Save `/tmp/swarm-openspec-chain-audit/worker-1/validation.png`. Pass when active change is valid.
- [ ] Lane 2. Archive chain probe. Save `/tmp/swarm-openspec-chain-audit/worker-2/archive.png`. Pass when archived chains are intact.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-openspec-chain-audit/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-openspec-chain-audit/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-openspec-chain-audit/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-openspec-chain-audit/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-openspec-chain-audit/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-openspec-chain-audit/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-openspec-chain-audit/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-openspec-chain-audit/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec validation duration in seconds.
- [ ] Probe. Time uv run python scripts/openspec_change.py 2026-11-07-pi-extension-package-proof.
- [ ] Baseline. Record trunk duration of change validation.
- [ ] Rule. Head duration must not exceed 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/openspec-chain-audit-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/openspec-chain-audit-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile plan, and close Epic 1164 (gate-close-1164)

**Depends on.** openspec-chain-audit

**Files.**

- [ ] Edit `docs/plans/2026-11-08-openspec-intent-driven-flow-and-verification-tooling.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Run full 6-harness verification matrix doctor across all hosts.
- [ ] Run offline contract suite, poteto-mode bun tests, and plan validation.
- [ ] Update CHANGELOG.md with Epic 1164 deliverables.
- [ ] Reconcile `todo.md` and mark all child units and Epic 1164 complete.

**You see.**

- [ ] 6-Harness Matrix Verdict PASS in doctor output.
- [ ] Complete evidence receipts recorded for all six harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-openspec-intent-driven-flow-and-verification-tooling.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1164/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1164/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1164/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1164/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1164/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1164/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1164/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1164/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. OpenSpec status probe. Save `/tmp/swarm-gate-close-1164/worker-9/status.png`. Pass when status exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1164/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1164-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1164-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated OpenSpec status reporting across all active intent-driven changes.
- Evaluated JSON serialization of artifact completion states.
- Evaluated mise task integration and toolchain consistency.
- Evaluated 6-harness verification matrix and evidence durability.

## Appendix B. Alternatives rejected

- Manual per-artifact checking rejected per automation and DRY principles.
- Removing intent-driven artifacts rejected per archive-chain-integrity specification.
- Inventing external feature formats rejected per OpenSpec markdown contract.
