# Multi-harness verification skills for OpenCode and Droid plan

Four PRs complete native verification skills for OpenCode and Droid, wire CI verification drivers, and qualify full multi-harness conformance.
The program brings complete coverage across all six declared hosts and reinforces reproducible runtime execution.
Order is opencode-verification-skill, droid-verification-skill, ci-driver-wiring, gate-verification-close.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-opencode-and-droid-verification-skills.md, PR ids in order opencode-verification-skill, droid-verification-skill, ci-driver-wiring, gate-verification-close, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] opencode-verification-skill is first and branches from main.
  - [x] droid-verification-skill after opencode-verification-skill.
  - [x] ci-driver-wiring after droid-verification-skill.
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

## Scaffold and tailor OpenCode verification skill with reproducible driver (opencode-verification-skill)

**Depends on.** None.

**Files.**

- [x] Create `.opencode/skills/verify-opencode-pstack/SKILL.md`.
- [x] Create `.opencode/skills/verify-opencode-pstack/features/README.md`.
- [x] Create `.opencode/skills/verify-opencode-pstack/features/core.md`.
- [x] Create `.opencode/skills/verify-opencode-pstack/features/features.json`.
- [x] Create `.opencode/skills/verify-opencode-pstack/scripts/driver.sh`.

**Build.**

- [x] Scaffold verify-opencode-pstack skill in .opencode/skills/verify-opencode-pstack/.
- [x] Tailor SKILL.md with Launch, Doctor, Drive, Proof bar, Evidence, Cleanup, and Helpers.
- [x] Provide features map covering OpenCode manifest projection and 4-plane doctor checks.
- [x] Provide executable driver.sh running projection checks, doctor checks, and 60s timeout bounding.
- [x] Validate skill structure with scaffold_verification_skill.py --check.

**You see.**

- [x] python3 scripts/scaffold_verification_skill.py --audit --json discovers and passes 9 verification skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scaffold_verification_skill.py --check --target-dir .opencode/skills/verify-opencode-pstack`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full scaffolder audit. Save `/tmp/swarm-opencode-verification-skill/worker-1/trunk.png`. Pass when 9 skills pass.
- [x] Lane 2. OpenCode skill structure probe. Save `/tmp/swarm-opencode-verification-skill/worker-2/structure.png`. Pass when all 7 required sections exist.
- [x] Lane 3. OpenCode skill byte limit probe. Save `/tmp/swarm-opencode-verification-skill/worker-3/bytes.png`. Pass when body is under 24000 bytes.
- [x] Lane 4. Features manifest probe. Save `/tmp/swarm-opencode-verification-skill/worker-4/features.png`. Pass when features.json validates.
- [x] Lane 5. Driver doctor probe. Save `/tmp/swarm-opencode-verification-skill/worker-5/driver-doctor.png`. Pass when driver doctor returns 0.
- [x] Lane 6. Driver drive probe. Save `/tmp/swarm-opencode-verification-skill/worker-6/driver-drive.png`. Pass when driver drive returns 0.
- [x] Lane 7. Driver cleanup probe. Save `/tmp/swarm-opencode-verification-skill/worker-7/driver-cleanup.png`. Pass when driver cleanup returns 0.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-opencode-verification-skill/worker-8/runtime.png`. Pass when uv run python resolution is used.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-opencode-verification-skill/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-opencode-verification-skill/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. OpenCode verification skill check duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .opencode/skills/verify-opencode-pstack.
- [x] Baseline. Record trunk duration of skill check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/opencode-verification-skill-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/opencode-verification-skill-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to main branch.

## Scaffold and tailor Droid verification skill with reproducible driver (droid-verification-skill)

**Depends on.** opencode-verification-skill

**Files.**

- [x] Create `.factory/skills/verify-droid-pstack/SKILL.md`.
- [x] Create `.factory/skills/verify-droid-pstack/features/README.md`.
- [x] Create `.factory/skills/verify-droid-pstack/features/core.md`.
- [x] Create `.factory/skills/verify-droid-pstack/features/features.json`.
- [x] Create `.factory/skills/verify-droid-pstack/scripts/driver.sh`.

**Build.**

- [x] Scaffold verify-droid-pstack skill in .factory/skills/verify-droid-pstack/.
- [x] Tailor SKILL.md with Launch, Doctor, Drive, Proof bar, Evidence, Cleanup, and Helpers.
- [x] Provide features map covering Droid manifest, marketplace, and role projection.
- [x] Provide executable driver.sh running projection checks, doctor checks, and 60s timeout bounding.
- [x] Validate skill structure with scaffold_verification_skill.py --check.

**You see.**

- [x] python3 scripts/scaffold_verification_skill.py --audit --json discovers and passes 10 verification skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scaffold_verification_skill.py --check --target-dir .factory/skills/verify-droid-pstack`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full scaffolder audit. Save `/tmp/swarm-droid-verification-skill/worker-1/trunk.png`. Pass when 10 skills pass.
- [x] Lane 2. Droid skill structure probe. Save `/tmp/swarm-droid-verification-skill/worker-2/structure.png`. Pass when all 7 required sections exist.
- [x] Lane 3. Droid skill byte limit probe. Save `/tmp/swarm-droid-verification-skill/worker-3/bytes.png`. Pass when body is under 24000 bytes.
- [x] Lane 4. Features manifest probe. Save `/tmp/swarm-droid-verification-skill/worker-4/features.png`. Pass when features.json validates.
- [x] Lane 5. Driver doctor probe. Save `/tmp/swarm-droid-verification-skill/worker-5/driver-doctor.png`. Pass when driver doctor returns 0.
- [x] Lane 6. Driver drive probe. Save `/tmp/swarm-droid-verification-skill/worker-6/driver-drive.png`. Pass when driver drive returns 0.
- [x] Lane 7. Driver cleanup probe. Save `/tmp/swarm-droid-verification-skill/worker-7/driver-cleanup.png`. Pass when driver cleanup returns 0.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-droid-verification-skill/worker-8/runtime.png`. Pass when uv run python resolution is used.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-droid-verification-skill/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-droid-verification-skill/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Droid verification skill check duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .factory/skills/verify-droid-pstack.
- [x] Baseline. Record trunk duration of skill check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/droid-verification-skill-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/droid-verification-skill-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Wire OMP, OpenCode, and Droid verification drivers into CI workflow (ci-driver-wiring)

**Depends on.** droid-verification-skill

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Wire OMP verification skill driver checks into portability-offline.yml workflow.
- [x] Wire OpenCode verification skill driver checks into portability-offline.yml workflow.
- [x] Wire Droid verification skill driver checks into portability-offline.yml workflow.
- [x] Add unit test assertions in test_scaffold_verification_skill.py for 10 total skills.

**You see.**

- [x] CI offline workflow executes and validates drivers for all declared hosts.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full pytest suite. Save `/tmp/swarm-ci-driver-wiring/worker-1/trunk.png`. Pass when all tests pass.
- [x] Lane 2. OMP CI driver step probe. Save `/tmp/swarm-ci-driver-wiring/worker-2/omp-step.png`. Pass when workflow syntax validates.
- [x] Lane 3. OpenCode CI driver step probe. Save `/tmp/swarm-ci-driver-wiring/worker-3/opencode-step.png`. Pass when workflow syntax validates.
- [x] Lane 4. Droid CI driver step probe. Save `/tmp/swarm-ci-driver-wiring/worker-4/droid-step.png`. Pass when workflow syntax validates.
- [x] Lane 5. Ten skills audit probe. Save `/tmp/swarm-ci-driver-wiring/worker-5/ten-skills.png`. Pass when 10/10 skills pass.
- [x] Lane 6. Scaffolder list probe. Save `/tmp/swarm-ci-driver-wiring/worker-6/list.png`. Pass when 10 skills are listed.
- [x] Lane 7. Driver reproducible runtime probe. Save `/tmp/swarm-ci-driver-wiring/worker-7/runtime.png`. Pass when uv and bun run.
- [x] Lane 8. Package projection probe. Save `/tmp/swarm-ci-driver-wiring/worker-8/projection.png`. Pass when all manifests match.
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

## Run multi-harness verification gate, reconcile plan, and close Epic 1078 (gate-verification-close)

**Depends on.** ci-driver-wiring

**Files.**

- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.
- [x] Edit `docs/plans/2026-11-08-opencode-and-droid-verification-skills.md`.

**Build.**

- [x] Run full 6-host doctor and verify matrix verdict is PASS.
- [x] Validate evidence freshness across all 6 hosts.
- [x] Update changelog with entries for OpenCode and Droid verification skills and CI wiring.
- [x] Update todo.md and close Epic #1078.

**You see.**

- [x] Complete 6-harness verification matrix passes and 10 verification skills are active.

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

- Evaluated OpenCode harness verification requirements in .opencode/skills/verify-opencode-pstack/.
- Evaluated Droid harness verification requirements in .factory/skills/verify-droid-pstack/.
- Evaluated CI workflow integration in .github/workflows/portability-offline.yml.

## Appendix B. Alternatives rejected

- Leaving OpenCode and Droid without verification skills rejected per complete multi-harness contract.
- Hardcoded shell commands rejected in favor of reproducible uv run and bun drivers.

## Appendix C. Risks

- Risk of receipt staleness. Mitigated by refreshing static receipts and verifying freshness.
- Risk of timeout in driver commands. Mitigated by strict 60s execution bounds.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
