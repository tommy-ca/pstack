# Reproducible runtime and verification levers plan

Four PRs unify Python uv run and Bun runtime workflows and harden verification drivers.
The program brings reproducible test execution, driver hardening, and CI consistency.
Order is bun-runtime, reproducible-drivers, ci-runtime-reconcile, multi-harness-gate.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-reproducible-runtime-and-verification.md, PR ids in order bun-runtime, reproducible-drivers, ci-runtime-reconcile, multi-harness-gate, the verification rule, the root merges, and the done condition is every box checked with its evidence."
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:skills/swarm/SKILL.md`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/shipping.md`
- [ ] Arm the 30-minute audit tick with the host schedule capability. Never leave the cadence to memory.
- [ ] Use this tick prompt. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] From this parent session, spawn one owner per PR using the host spawn primitive. Depth is 1.
- [ ] Follow this dependency graph.
  - [ ] bun-runtime is first and branches from main.
  - [ ] reproducible-drivers after bun-runtime.
  - [ ] ci-runtime-reconcile after reproducible-drivers.
  - [ ] multi-harness-gate after ci-runtime-reconcile.
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
- [ ] Run `python3 scripts/verify_portable.py doctor --host <host>`.
- [ ] Record output and exit codes.
- [ ] Save reports to `/tmp/swarm-<pr-id>/worker-<n>/receipt.json`.

## Configure root bunfig and bun test execution (bun-runtime)

**Depends on.** None.

**Files.**

- [ ] Create `bunfig.toml`.
- [ ] Edit `skills/poteto-mode/scripts/check-plan.mjs`.

**Build.**

- [ ] Configure root bunfig.toml with 15000ms test timeout for reliable worktree test execution.
- [ ] Update check-plan.mjs shebang and runtime support for bun.

**You see.**

- [ ] Running bun test skills/poteto-mode/scripts/ passes 102/102 tests with zero timeouts.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun test skills/poteto-mode/scripts/`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify bun test suite passes. Save `/tmp/swarm-bun-runtime/worker-1/trunk.png`. Pass when bun test succeeds.
- [ ] Lane 2. Root bunfig existence probe. Save `/tmp/swarm-bun-runtime/worker-2/bunfig.png`. Pass when bunfig.toml exists and configures timeout.
- [ ] Lane 3. Check-plan execution probe. Save `/tmp/swarm-bun-runtime/worker-3/check-plan.png`. Pass when check-plan validates with bun.
- [ ] Lane 4. Worktree audit test probe. Save `/tmp/swarm-bun-runtime/worker-4/worktree-audit.png`. Pass when worktree-audit.test.ts passes.
- [ ] Lane 5. Worktree drop test probe. Save `/tmp/swarm-bun-runtime/worker-5/worktree-drop.png`. Pass when worktree-drop.test.ts passes.
- [ ] Lane 6. Watch PR policy test probe. Save `/tmp/swarm-bun-runtime/worker-6/watch-pr.png`. Pass when policy.test.ts passes.
- [ ] Lane 7. Watch PR github test probe. Save `/tmp/swarm-bun-runtime/worker-7/github.png`. Pass when github.test.ts passes.
- [ ] Lane 8. Watch PR cli test probe. Save `/tmp/swarm-bun-runtime/worker-8/cli.png`. Pass when cli.test.ts passes.
- [ ] Lane 9. Orch store test probe. Save `/tmp/swarm-bun-runtime/worker-9/orch.png`. Pass when orch.test.ts passes.
- [ ] Lane 10. Check-plan test probe. Save `/tmp/swarm-bun-runtime/worker-10/plan-test.png`. Pass when check-plan.test.mjs passes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Bun test execution duration in seconds.
- [ ] Probe. Time bun test skills/poteto-mode/scripts/.
- [ ] Baseline. Record trunk duration of bun test execution.
- [ ] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/bun-runtime-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/bun-runtime-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Harden verification drivers and scaffolder for reproducible runtimes (reproducible-drivers)

**Depends on.** bun-runtime

**Files.**

- [ ] Edit `scripts/scaffold_verification_skill.py`.
- [ ] Edit `.codex/skills/verify-llm-wiki/scripts/driver.sh`.
- [ ] Edit `.codex/skills/verify-decision-contract/scripts/driver.sh`.
- [ ] Edit `.pi/skills/verify-pi-pstack/scripts/driver.sh`.
- [ ] Edit `.pi/skills/verify-pi-pstack-formal/scripts/driver.sh`.
- [ ] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [ ] Update driver templates and scripts to resolve uv run and bun runtimes reproducibly.
- [ ] Add unit tests asserting driver script template generation and runtime resolution.

**You see.**

- [ ] Driver scripts detect uv and bun to run hermetic environments, falling back gracefully to python3 when uv is absent.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_scaffold_verification_skill.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify scaffolder audit passes. Save `/tmp/swarm-reproducible-drivers/worker-1/trunk.png`. Pass when audit is clean.
- [ ] Lane 2. Driver template generation probe. Save `/tmp/swarm-reproducible-drivers/worker-2/driver-gen.png`. Pass when generated driver includes runtime resolution.
- [ ] Lane 3. LLM wiki driver launch probe. Save `/tmp/swarm-reproducible-drivers/worker-3/wiki-launch.png`. Pass when driver launch exits 0.
- [ ] Lane 4. LLM wiki driver doctor probe. Save `/tmp/swarm-reproducible-drivers/worker-4/wiki-doctor.png`. Pass when driver doctor exits 0.
- [ ] Lane 5. Decision contract driver launch probe. Save `/tmp/swarm-reproducible-drivers/worker-5/decision-launch.png`. Pass when launch exits 0.
- [ ] Lane 6. Decision contract driver doctor probe. Save `/tmp/swarm-reproducible-drivers/worker-6/decision-doctor.png`. Pass when doctor exits 0.
- [ ] Lane 7. Pi candidate driver doctor probe. Save `/tmp/swarm-reproducible-drivers/worker-7/pi-doctor.png`. Pass when doctor exits 0.
- [ ] Lane 8. Pi formal driver doctor probe. Save `/tmp/swarm-reproducible-drivers/worker-8/pi-formal.png`. Pass when doctor exits 0.
- [ ] Lane 9. Python module size discipline probe. Save `/tmp/swarm-reproducible-drivers/worker-9/size.png`. Pass when python files remain under 1000 lines.
- [ ] Lane 10. Scaffolder check probe. Save `/tmp/swarm-reproducible-drivers/worker-10/scaffold-check.png`. Pass when check exits 0 across all skills.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scaffolder audit run time in milliseconds.
- [ ] Probe. Time python3 scripts/scaffold_verification_skill.py --audit --json.
- [ ] Baseline. Record trunk duration of scaffolder audit.
- [ ] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/reproducible-drivers-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/reproducible-drivers-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Update CI workflows and documentation for reproducible execution (ci-runtime-reconcile)

**Depends on.** reproducible-drivers

**Files.**

- [ ] Edit `.github/workflows/portability-offline.yml`.
- [ ] Edit `docs/plans/2026-11-07-reproducible-runtime-and-verification.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Add setup-bun action and bun test execution steps to GitHub Actions workflow.
- [ ] Update bare python3 commands to uv run python in CI workflow.
- [ ] Reconcile execution plan, todo tracking, and changelog.

**You see.**

- [ ] CI workflow executes bun test and uv run python deterministically.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `python3 scripts/verify_portable.py check-staleness --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify workflow yaml syntax. Save `/tmp/swarm-ci-runtime-reconcile/worker-1/trunk.png`. Pass when yaml is valid.
- [ ] Lane 2. Bun setup step probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-2/bun-step.png`. Pass when setup-bun is declared.
- [ ] Lane 3. Bun test step probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-3/bun-test.png`. Pass when bun test step is present.
- [ ] Lane 4. Check-plan step probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-4/check-plan.png`. Pass when check-plan step is present.
- [ ] Lane 5. UV run step probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-5/uv-step.png`. Pass when uv run python is used for pi candidate and worktree protocol.
- [ ] Lane 6. Evidence freshness probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-6/freshness.png`. Pass when all receipts are fresh.
- [ ] Lane 7. Evidence durability probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-7/durability.png`. Pass when all 6 harnesses report PASS.
- [ ] Lane 8. Plan validation probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-8/plan-check.png`. Pass when check-plan reports zero problems.
- [ ] Lane 9. Changelog sync probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-9/changelog.png`. Pass when unreleased entries are recorded.
- [ ] Lane 10. Todo sync probe. Save `/tmp/swarm-ci-runtime-reconcile/worker-10/todo.png`. Pass when todo reflects completed units.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Evidence staleness check duration in milliseconds.
- [ ] Probe. Time python3 scripts/verify_portable.py check-staleness --host all.
- [ ] Baseline. Record trunk duration of evidence staleness check.
- [ ] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/ci-runtime-reconcile-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/ci-runtime-reconcile-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Multi-harness verification and gate (multi-harness-gate)

**Depends on.** ci-runtime-reconcile

**Files.**

- [ ] Edit `docs/plans/2026-11-07-reproducible-runtime-and-verification.md`.
- [ ] Edit `todo.md`.

**Build.**

- [ ] Execute full multi-harness doctor, staleness, and durability matrix.
- [ ] Execute complete full test suite across python and bun runtimes.

**You see.**

- [ ] Full matrix verdict is PASS and all 1531 python tests and 102 bun tests pass.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `python3 scripts/verify_portable.py doctor --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify 6-harness doctor matrix. Save `/tmp/swarm-multi-harness-gate/worker-1/trunk.png`. Pass when matrix verdict is PASS.
- [ ] Lane 2. Worktree protocol check probe. Save `/tmp/swarm-multi-harness-gate/worker-2/worktree.png`. Pass when worktree protocol passes.
- [ ] Lane 3. Staleness report probe. Save `/tmp/swarm-multi-harness-gate/worker-3/staleness.png`. Pass when matrix evidence is ALL FRESH.
- [ ] Lane 4. Evidence durability probe. Save `/tmp/swarm-multi-harness-gate/worker-4/durability.png`. Pass when all hosts report PASS.
- [ ] Lane 5. Package projection probe. Save `/tmp/swarm-multi-harness-gate/worker-5/projection.png`. Pass when 21 commands and all manifests match.
- [ ] Lane 6. Verification scaffolder audit probe. Save `/tmp/swarm-multi-harness-gate/worker-6/scaffold.png`. Pass when all 6 skills pass audit.
- [ ] Lane 7. Plan validation probe. Save `/tmp/swarm-multi-harness-gate/worker-7/plan.png`. Pass when check-plan reports 4 sections and 0 problems.
- [ ] Lane 8. Full pytest suite probe. Save `/tmp/swarm-multi-harness-gate/worker-8/pytest.png`. Pass when all tests pass.
- [ ] Lane 9. Full bun test suite probe. Save `/tmp/swarm-multi-harness-gate/worker-9/bun.png`. Pass when 102 tests pass.
- [ ] Lane 10. Python size limit probe. Save `/tmp/swarm-multi-harness-gate/worker-10/size.png`. Pass when all python modules remain under 1000 lines.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Multi-harness doctor duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/multi-harness-gate-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/multi-harness-gate-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated Python execution across CI and driver scripts.
- Evaluated Bun test runner across skills/poteto-mode/scripts/ with 102 tests.
- Confirmed bunfig.toml timeout parameter eliminates integration test flakiness.

## Appendix B. Alternatives rejected

- Unpinned bare system python execution rejected due to environment drift and missing packages.
- Uncoordinated test timeouts rejected to maintain deterministic CI execution.

## Appendix C. Risks

- Risk of missing bun in environments where only node is present. Mitigated by keeping check-plan node compatible.
- Risk of virtual environment path discrepancies. Mitigated by checking .venv/bin presence and uv run fallback.

## Appendix D. Links and reading list

- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
- Offline contracts workflow in .github/workflows/portability-offline.yml
