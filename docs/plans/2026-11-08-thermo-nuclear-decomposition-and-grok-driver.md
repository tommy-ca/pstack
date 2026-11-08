# Thermo-nuclear decomposition and Grok verification driver plan

Four PRs decompose Antigravity command projection, unify Grok verification driver execution, automate CI offline checks, and qualify the full 6-host verification matrix.
Order is antigravity-command-projection, grok-verification-driver, ci-driver-wiring, gate-verification-close.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-thermo-nuclear-decomposition-and-grok-driver.md, PR ids in order antigravity-command-projection, grok-verification-driver, ci-driver-wiring, gate-verification-close, the verification rule, the root merges, and the done condition is every box checked with its evidence."
- [x] Read these from trunk at program start. Re-read them at every tick.
  - [x] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [x] `git show origin/main:skills/swarm/SKILL.md`
  - [x] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [x] `git show origin/main:skills/poteto-mode/playbooks/shipping.md`
- [x] Arm the 30-minute audit tick with the host schedule capability. Never leave the cadence to memory.
- [x] Use this tick prompt. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [x] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [x] From this parent session, spawn one owner per PR using the host spawn primitive. Depth is 1.
- [x] Follow this dependency graph.
  - [x] antigravity-command-projection is first and branches from main.
  - [x] grok-verification-driver after antigravity-command-projection.
  - [x] ci-driver-wiring after grok-verification-driver.
  - [x] gate-verification-close after ci-driver-wiring.
- [x] Hold the file boundaries strictly per task files list.
- [x] Hold the review gate for every PR before merge.

### PR mechanics, for every PR

- [x] Resolve the forge once. Default to `gh`.
- [x] Open each PR ready with `gh pr create --base <parent-branch>`.
- [x] Run unslop before each commit and no-comments before review.
- [x] Rebase onto current trunk before babysit and again before merge.

### Verdict and merge, for every PR

- [x] A full swarm runs once at the code-ready head.
- [x] Ten live lanes verify the real surface.
- [x] Four perf lanes verify timings against baseline.
- [x] Clean only when every lane is PASS.
- [x] The root merges verified PRs bottom-up.

### Boot recipe, for every live lane

Each live lane runs in its own worktree child at the PR head. Drive the real surface.

- [x] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [x] Run `python3 scripts/verify_portable.py doctor --host <host>`.
- [x] Record output and exit codes.
- [x] Save reports to `/tmp/swarm-<pr-id>/worker-<n>/receipt.json`.

## Extract Antigravity command projection into dedicated module (antigravity-command-projection)

**Depends on.** None.

**Files.**

- [x] Create `scripts/antigravity_command_projection.py`.
- [x] Create `tests/test_antigravity_command_projection.py`.
- [x] Edit `scripts/package_projection.py`.

**Build.**

- [x] Extract generate_antigravity_commands to scripts/antigravity_command_projection.py.
- [x] Extract project_antigravity_auxiliary and check_antigravity_auxiliary.
- [x] Re-export and delegate from scripts/package_projection.py.
- [x] Add unit tests verifying 21 commands and auxiliary projection in tests/test_antigravity_command_projection.py.

**You see.**

- [x] scripts/package_projection.py decomposes below 600 lines while all 21 commands remain in sync.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_antigravity_command_projection.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify package projection sync. Save `/tmp/swarm-antigravity-command-projection/worker-1/trunk.png`. Pass when package projection passes.
- [x] Lane 2. Command file generation probe. Save `/tmp/swarm-antigravity-command-projection/worker-2/commands.png`. Pass when 21 commands generate.
- [x] Lane 3. Command content fidelity probe. Save `/tmp/swarm-antigravity-command-projection/worker-3/fidelity.png`. Pass when toml contents match.
- [x] Lane 4. Models manifest projection probe. Save `/tmp/swarm-antigravity-command-projection/worker-4/models.png`. Pass when models match.
- [x] Lane 5. Auxiliary check pass probe. Save `/tmp/swarm-antigravity-command-projection/worker-5/check.png`. Pass when check reports PASS.
- [x] Lane 6. Missing commands directory refusal probe. Save `/tmp/swarm-antigravity-command-projection/worker-6/missing.png`. Pass when missing dir reports error.
- [x] Lane 7. Drifted command content refusal probe. Save `/tmp/swarm-antigravity-command-projection/worker-7/drift.png`. Pass when drifted content reports error.
- [x] Lane 8. Package projection module line limit probe. Save `/tmp/swarm-antigravity-command-projection/worker-8/lines.png`. Pass when lines are under 600.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-antigravity-command-projection/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-antigravity-command-projection/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Package projection duration in milliseconds.
- [x] Probe. Time python3 scripts/package_projection.py --check.
- [x] Baseline. Record trunk duration of package projection check.
- [x] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/antigravity-command-projection-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/antigravity-command-projection-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to main branch.

## Add reproducible driver to verify-pstack and require driver in scaffolder (grok-verification-driver)

**Depends on.** antigravity-command-projection

**Files.**

- [x] Create `.grok/skills/verify-pstack/scripts/driver.sh`.
- [x] Edit `scripts/scaffold_verification_skill.py`.

**Build.**

- [x] Author executable .grok/skills/verify-pstack/scripts/driver.sh implementing launch, doctor, drive, and cleanup.
- [x] Implement 60-second timeout bounding and reproducible uv run python / bun runtime resolution.
- [x] Update scripts/scaffold_verification_skill.py to require driver.sh in all verification skills.

**You see.**

- [x] All 10 verification skills in repository feature executable driver.sh scripts and pass audit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scaffold_verification_skill.py --check --target-dir .grok/skills/verify-pstack`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full scaffolder audit. Save `/tmp/swarm-grok-verification-driver/worker-1/trunk.png`. Pass when 10 skills pass.
- [x] Lane 2. Grok driver executable mode probe. Save `/tmp/swarm-grok-verification-driver/worker-2/mode.png`. Pass when executable bit is set.
- [x] Lane 3. Grok driver launch mode probe. Save `/tmp/swarm-grok-verification-driver/worker-3/launch.png`. Pass when launch returns 0.
- [x] Lane 4. Grok driver doctor mode probe. Save `/tmp/swarm-grok-verification-driver/worker-4/doctor.png`. Pass when doctor returns 0.
- [x] Lane 5. Grok driver drive mode probe. Save `/tmp/swarm-grok-verification-driver/worker-5/drive.png`. Pass when drive returns 0.
- [x] Lane 6. Grok driver cleanup mode probe. Save `/tmp/swarm-grok-verification-driver/worker-6/cleanup.png`. Pass when cleanup returns 0.
- [x] Lane 7. Scaffolder driver presence enforcement probe. Save `/tmp/swarm-grok-verification-driver/worker-7/require.png`. Pass when missing driver is rejected.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-grok-verification-driver/worker-8/runtime.png`. Pass when uv run python resolution is used.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-grok-verification-driver/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-grok-verification-driver/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Grok verification skill check duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .grok/skills/verify-pstack.
- [x] Baseline. Record trunk duration of skill check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/grok-verification-driver-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/grok-verification-driver-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Wire Grok verification driver into portability-offline CI workflow (ci-driver-wiring)

**Depends on.** grok-verification-driver

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Wire Grok verification skill driver checks into portability-offline.yml workflow.
- [x] Update tests in test_scaffold_verification_skill.py asserting driver.sh requirement.

**You see.**

- [x] CI offline workflow executes and validates drivers for all declared hosts including Grok.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full pytest suite. Save `/tmp/swarm-ci-driver-wiring/worker-1/trunk.png`. Pass when all tests pass.
- [x] Lane 2. Grok CI driver step probe. Save `/tmp/swarm-ci-driver-wiring/worker-2/grok-step.png`. Pass when workflow syntax validates.
- [x] Lane 3. Scaffolder driver presence test probe. Save `/tmp/swarm-ci-driver-wiring/worker-3/driver-test.png`. Pass when test passes.
- [x] Lane 4. Ten skills audit probe. Save `/tmp/swarm-ci-driver-wiring/worker-4/ten-skills.png`. Pass when 10/10 skills pass.
- [x] Lane 5. Scaffolder list probe. Save `/tmp/swarm-ci-driver-wiring/worker-5/list.png`. Pass when 10 skills are listed.
- [x] Lane 6. Package projection probe. Save `/tmp/swarm-ci-driver-wiring/worker-6/projection.png`. Pass when all manifests match.
- [x] Lane 7. Driver reproducible runtime probe. Save `/tmp/swarm-ci-driver-wiring/worker-7/runtime.png`. Pass when uv and bun run.
- [x] Lane 8. Worktree protocol probe. Save `/tmp/swarm-ci-driver-wiring/worker-8/worktree.png`. Pass when confinement passes.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-ci-driver-wiring/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-ci-driver-wiring/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Scaffolder audit duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --audit --json.
- [x] Baseline. Record trunk duration of audit.
- [x] Rule. Head duration must not exceed trunk duration plus 50 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/ci-driver-wiring-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/ci-driver-wiring-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Run multi-harness verification gate, reconcile plan, and close Epic 1087 (gate-verification-close)

**Depends on.** ci-driver-wiring

**Files.**

- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.
- [x] Edit `docs/plans/2026-11-08-thermo-nuclear-decomposition-and-grok-driver.md`.

**Build.**

- [x] Run full 6-host doctor and verify matrix verdict is PASS.
- [x] Validate evidence freshness across all 6 hosts.
- [x] Update changelog with entries for Antigravity projection decomposition and Grok verification driver.
- [x] Update todo.md and close Epic #1087.

**You see.**

- [x] Complete 6-harness verification matrix passes and 10 verification skills with drivers are active.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/verify_portable.py doctor --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify 6-harness doctor matrix. Save `/tmp/swarm-gate-verification-close/worker-1/trunk.png`. Pass when matrix verdict is PASS.
- [x] Lane 2. Worktree protocol check probe. Save `/tmp/swarm-gate-verification-close/worker-2/worktree.png`. Pass when worktree protocol passes.
- [x] Lane 3. Staleness report probe. Save `/tmp/swarm-gate-verification-close/worker-3/staleness.png`. Pass when matrix evidence is ALL FRESH.
- [x] Lane 4. Evidence durability probe. Save `/tmp/swarm-gate-verification-close/worker-4/durability.png`. Pass when all hosts report PASS.
- [x] Lane 5. Package projection probe. Save `/tmp/swarm-gate-verification-close/worker-5/projection.png`. Pass when all manifests match.
- [x] Lane 6. Verification scaffolder audit probe. Save `/tmp/swarm-gate-verification-close/worker-6/scaffold.png`. Pass when all 10 skills pass audit.
- [x] Lane 7. Plan validation probe. Save `/tmp/swarm-gate-verification-close/worker-7/plan.png`. Pass when check-plan reports 4 sections and 0 problems.
- [x] Lane 8. Full pytest suite probe. Save `/tmp/swarm-gate-verification-close/worker-8/pytest.png`. Pass when all tests pass.
- [x] Lane 9. Full bun test suite probe. Save `/tmp/swarm-gate-verification-close/worker-9/bun.png`. Pass when 102 tests pass.
- [x] Lane 10. Python size limit probe. Save `/tmp/swarm-gate-verification-close/worker-10/size.png`. Pass when all python modules remain under 1000 lines.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Multi-harness doctor duration in seconds.
- [x] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [x] Baseline. Record trunk duration of doctor across all hosts.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/gate-verification-close-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/gate-verification-close-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every box above is checked with its evidence.
- [x] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated package projection decomposition in scripts/antigravity_command_projection.py.
- Evaluated Grok driver requirements in .grok/skills/verify-pstack/scripts/driver.sh.
- Evaluated CI workflow integration in .github/workflows/portability-offline.yml.

## Appendix B. Alternatives rejected

- Leaving package_projection.py above 700 lines rejected per Single Responsibility Principle.
- Leaving Grok verification skill without driver.sh rejected per complete verification skill contract.

## Appendix C. Risks

- Risk of command drift during decomposition. Mitigated by comprehensive unit tests and projection check.
- Risk of timeout in driver commands. Mitigated by strict 60s execution bounds.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
