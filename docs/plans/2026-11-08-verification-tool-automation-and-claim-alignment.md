# Verification Tool Automation and Claim Alignment

This program implements automated verification driver orchestration, streamlines mise tasks, and aligns verifier claims with declared harnesses.
Work proceeds in four stacked pull requests under Epic 1134.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-verification-tool-automation-and-claim-alignment.md, PR ids in order scaffold-driver-orchestrator, streamline-mise-drivers, align-verifier-claim, gate-close-1134, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] scaffold-driver-orchestrator is first and branches from main.
  - [ ] streamline-mise-drivers after scaffold-driver-orchestrator.
  - [ ] align-verifier-claim after streamline-mise-drivers.
  - [ ] gate-close-1134 after align-verifier-claim.
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

## Add drive-all command to scaffold_verification_skill.py and update test suite (scaffold-driver-orchestrator)

**Depends on.** None.

**Files.**

- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Implement `drive_verification_skill` and `drive_all_verification_skills` in scaffolder script.
- [x] Support `--drive-all` and `--drive` CLI options with optional `--json` output.
- [x] Add unit tests for driving individual skills and driving all skills with timeouts.
- [x] Verify test suite passes cleanly with zero errors.

**You see.**

- [x] Clean executable CLI command `python3 scripts/scaffold_verification_skill.py --drive-all`.
- [x] Detailed JSON summary with driver duration, exit codes, and status.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Scaffolder audit probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-1/audit.png`. Pass when audit passes.
- [x] Lane 2. Drive-all execution probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-2/drive-all.png`. Pass when drive-all exits 0.
- [x] Lane 3. Drive-all JSON output probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-3/json.png`. Pass when JSON matches schema.
- [x] Lane 4. Single skill drive probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-4/drive-single.png`. Pass when single drive passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Package projection probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-6/projection.png`. Pass when package_projection check passes.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-scaffold-driver-orchestrator/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Drive-all execution duration in seconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --drive-all.
- [x] Baseline. Record trunk duration of manual driver bash chain.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/scaffold-driver-orchestrator-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/scaffold-driver-orchestrator-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Streamline mise.toml verify:drivers task to use the new driver orchestrator lever (streamline-mise-drivers)

**Depends on.** scaffold-driver-orchestrator

**Files.**

- [ ] Edit `mise.toml`.
- [ ] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [ ] Update `mise.toml` `verify:drivers` task to call `uv run python scripts/scaffold_verification_skill.py --drive-all`.
- [ ] Update `tests/test_runtime_toolchain.py` assertions for streamlined task definition.
- [ ] Run test suite to verify toolchain consistency.

**You see.**

- [ ] Simplified `mise.toml` with clean task invocation.
- [ ] Passing toolchain tests across all tasks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_runtime_toolchain.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Mise tasks list probe. Save `/tmp/swarm-streamline-mise-drivers/worker-1/mise-tasks.png`. Pass when verify:drivers appears.
- [ ] Lane 2. Mise verify:drivers execution probe. Save `/tmp/swarm-streamline-mise-drivers/worker-2/run-drivers.png`. Pass when task exits 0.
- [ ] Lane 3. Toolchain test suite probe. Save `/tmp/swarm-streamline-mise-drivers/worker-3/toolchain.png`. Pass when toolchain tests pass.
- [ ] Lane 4. Worktree confinement probe. Save `/tmp/swarm-streamline-mise-drivers/worker-4/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 5. Package projection probe. Save `/tmp/swarm-streamline-mise-drivers/worker-5/projection.png`. Pass when projection check passes.
- [ ] Lane 6. Verification skills audit probe. Save `/tmp/swarm-streamline-mise-drivers/worker-6/audit.png`. Pass when 10 skills pass.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-streamline-mise-drivers/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-streamline-mise-drivers/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-streamline-mise-drivers/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-streamline-mise-drivers/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Mise verify:drivers task duration in seconds.
- [ ] Probe. Time mise run verify:drivers.
- [ ] Baseline. Record trunk duration of verify:drivers.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/streamline-mise-drivers-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/streamline-mise-drivers-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Align verifier claim to 6 declared harnesses and prune stale test cache (align-verifier-claim)

**Depends on.** streamline-mise-drivers

**Files.**

- [ ] Edit `scripts/portable_verifier.py`.
- [ ] Edit `tests/test_verify_portable.py`.

**Build.**

- [ ] Update verifier claim from 5-harness to 6-harness in `scripts/portable_verifier.py`.
- [ ] Add unit test assertions in `tests/test_verify_portable.py` validating claim formatting.
- [ ] Ensure stale test caches in subdirectories are pruned.

**You see.**

- [ ] Updated claim string matching the 6 declared harnesses.
- [ ] Passing portable verifier tests.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_verify_portable.py -k test_proof_bar`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Claim verification probe. Save `/tmp/swarm-align-verifier-claim/worker-1/claim.png`. Pass when claim contains 6-harness.
- [ ] Lane 2. Portable verifier test probe. Save `/tmp/swarm-align-verifier-claim/worker-2/portable-tests.png`. Pass when tests pass.
- [ ] Lane 3. Evidence staleness probe. Save `/tmp/swarm-align-verifier-claim/worker-3/staleness.png`. Pass when evidence remains fresh.
- [ ] Lane 4. Worktree confinement probe. Save `/tmp/swarm-align-verifier-claim/worker-4/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 5. Package projection probe. Save `/tmp/swarm-align-verifier-claim/worker-5/projection.png`. Pass when projection passes.
- [ ] Lane 6. Verification skills audit probe. Save `/tmp/swarm-align-verifier-claim/worker-6/audit.png`. Pass when 10 skills pass.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-align-verifier-claim/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-align-verifier-claim/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-align-verifier-claim/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-align-verifier-claim/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Proof bar computation duration in seconds.
- [ ] Probe. Time python3 -c "import scripts.portable_verifier".
- [ ] Baseline. Record trunk import duration.
- [ ] Rule. Head duration must not exceed trunk duration plus 0.2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/align-verifier-claim-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/align-verifier-claim-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix and close Epic 1134 (gate-close-1134)

**Depends on.** align-verifier-claim

**Files.**

- [ ] Edit `CHANGELOG.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `docs/plans/2026-11-08-verification-tool-automation-and-claim-alignment.md`.

**Build.**

- [ ] Update changelog with Epic 1134 entries.
- [ ] Update todo with Epic 1134 units.
- [ ] Mark all checkboxes in multi-phase plan.
- [ ] Verify plan schema with check-plan script.

**You see.**

- [ ] Complete reconciliation across ledger, todo, and plan.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-verification-tool-automation-and-claim-alignment.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1134/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1134/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1134/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1134/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1134/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1134/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1134/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1134/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Ephemeral prune probe. Save `/tmp/swarm-gate-close-1134/worker-9/prune.png`. Pass when prune-ephemeral exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1134/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1134-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1134-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated automated driver discovery in scaffold_verification_skill.py.
- Evaluated drive-all command execution across all 10 verification skills.
- Evaluated mise task simplification and error handling.
- Evaluated 6-harness receipt claim consistency.

## Appendix B. Alternatives rejected

- Leaving a 1000-character inline bash chain in mise.toml rejected per SOLID and DRY principles.
- Leaving claim as 5-harness rejected because 6 declared harnesses exist in pstack.
- Writing a separate driver runner script rejected per YAGNI since scaffolder already owns skills lifecycle.
- Manual execution of individual drivers rejected per automation and reproducibility principles.
