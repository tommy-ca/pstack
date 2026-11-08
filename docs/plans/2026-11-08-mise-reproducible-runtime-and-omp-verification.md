# Mise reproducible runtime, OMP verification skill, and DSH-22 integration plan

Four PRs enforce reproducible runtime execution via mise, scaffold OMP verification skill, and reconcile DSH-22 OpenSpec.
The program brings reproducible environment management, OMP harness verification, and full DAG reconciliation.
Order is mise-runtime-hardening, omp-verification-skill, openspec-reconcile, gate-verification-close.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-mise-reproducible-runtime-and-omp-verification.md, PR ids in order mise-runtime-hardening, omp-verification-skill, openspec-reconcile, gate-verification-close, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] mise-runtime-hardening is first and branches from main.
  - [x] omp-verification-skill after mise-runtime-hardening.
  - [x] openspec-reconcile after omp-verification-skill.
  - [x] gate-verification-close after openspec-reconcile.
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

## Enforce reproducible uv and bun runtime via mise tasks and driver contracts (mise-runtime-hardening)

**Depends on.** None.

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `.github/workflows/release.yml`.
- [x] Edit `tests/test_runtime_toolchain.py`.

**Build.**

- [x] Add missing verification and worktree tasks to mise.toml.
- [x] Update driver script template in scaffold_verification_skill.py ensuring bun default and uv run python resolution.
- [x] Add driver runtime contract verification in check_skill.
- [x] Update release.yml workflow to use uv run python.
- [x] Add tests in test_runtime_toolchain.py for mise tasks and runtime contracts.

**You see.**

- [x] All mise tasks execute cleanly and drivers adhere to reproducible runtime contracts.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify mise test task. Save `/tmp/swarm-mise-runtime-hardening/worker-1/trunk.png`. Pass when test task passes.
- [x] Lane 2. Mise scripts task probe. Save `/tmp/swarm-mise-runtime-hardening/worker-2/scripts.png`. Pass when bun tests pass.
- [x] Lane 3. Mise verify portable probe. Save `/tmp/swarm-mise-runtime-hardening/worker-3/portable.png`. Pass when evidence passes.
- [x] Lane 4. Mise doctor task probe. Save `/tmp/swarm-mise-runtime-hardening/worker-4/doctor.png`. Pass when doctor passes across all hosts.
- [x] Lane 5. Mise staleness task probe. Save `/tmp/swarm-mise-runtime-hardening/worker-5/staleness.png`. Pass when evidence is all fresh.
- [x] Lane 6. Scaffolder audit runtime probe. Save `/tmp/swarm-mise-runtime-hardening/worker-6/audit.png`. Pass when all skills pass audit.
- [x] Lane 7. Release workflow syntax probe. Save `/tmp/swarm-mise-runtime-hardening/worker-7/release.png`. Pass when release.yml uses uv run.
- [x] Lane 8. Driver template bun default probe. Save `/tmp/swarm-mise-runtime-hardening/worker-8/bun-default.png`. Pass when BUN_EXEC defaults to bun.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-mise-runtime-hardening/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-mise-runtime-hardening/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Mise task execution duration in seconds.
- [x] Probe. Time mise run test:scripts.
- [x] Baseline. Record trunk duration of test:scripts.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/mise-runtime-hardening-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/mise-runtime-hardening-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to main branch.

## Scaffold and tailor OMP verification skill with reproducible driver (omp-verification-skill)

**Depends on.** mise-runtime-hardening

**Files.**

- [x] Create `.omp/skills/verify-omp-pstack/SKILL.md`.
- [x] Create `.omp/skills/verify-omp-pstack/features/README.md`.
- [x] Create `.omp/skills/verify-omp-pstack/features/core.md`.
- [x] Create `.omp/skills/verify-omp-pstack/features/features.json`.
- [x] Create `.omp/skills/verify-omp-pstack/scripts/driver.sh`.

**Build.**

- [x] Scaffold verify-omp-pstack skill in .omp/skills/verify-omp-pstack/.
- [x] Tailor SKILL.md with Launch, Doctor, Drive, Proof bar, Evidence, Cleanup, and Helpers.
- [x] Provide features map covering OMP manifest, RPC contracts, and native package proof.
- [x] Provide executable driver.sh running doctor checks, vertical slice tests, and 60s bounding.
- [x] Refresh static receipts across all six hosts.

**You see.**

- [x] python3 scripts/scaffold_verification_skill.py --audit --json discovers and passes 8 verification skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scaffold_verification_skill.py --check --target-dir .omp/skills/verify-omp-pstack`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full scaffolder audit. Save `/tmp/swarm-omp-verification-skill/worker-1/trunk.png`. Pass when 8 skills pass.
- [x] Lane 2. OMP skill structure probe. Save `/tmp/swarm-omp-verification-skill/worker-2/structure.png`. Pass when all 7 required sections exist.
- [x] Lane 3. OMP skill byte limit probe. Save `/tmp/swarm-omp-verification-skill/worker-3/bytes.png`. Pass when body is under 24000 bytes.
- [x] Lane 4. Features manifest probe. Save `/tmp/swarm-omp-verification-skill/worker-4/features.png`. Pass when features.json validates.
- [x] Lane 5. Driver doctor probe. Save `/tmp/swarm-omp-verification-skill/worker-5/driver-doctor.png`. Pass when driver doctor returns 0.
- [x] Lane 6. Driver drive probe. Save `/tmp/swarm-omp-verification-skill/worker-6/driver-drive.png`. Pass when driver drive returns 0.
- [x] Lane 7. Driver cleanup probe. Save `/tmp/swarm-omp-verification-skill/worker-7/driver-cleanup.png`. Pass when driver cleanup returns 0.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-omp-verification-skill/worker-8/runtime.png`. Pass when uv run python resolution is used.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-omp-verification-skill/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-omp-verification-skill/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. OMP verification skill check duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .omp/skills/verify-omp-pstack.
- [x] Baseline. Record trunk duration of skill check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/omp-verification-skill-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/omp-verification-skill-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Reconcile DSH-22 OpenSpec and integrate PR 1049 (openspec-reconcile)

**Depends on.** omp-verification-skill

**Files.**

- [x] Rebase `spec/deepseek-skills-22-source-refresh-20261107`.
- [x] Edit `openspec/changes/2026-11-07-deepseek-skills-22-source-refresh/source-crosswalk.md`.
- [x] Edit `openspec/changes/2026-11-07-deepseek-skills-22-source-refresh/issue-graph.md`.

**Build.**

- [x] Rebase PR #1049 onto current trunk.
- [x] Reconcile 22-source classification across general, conditional, and excluded skills.
- [x] Verify zero unsupported workflow imports and zero broken seams.
- [x] Mark PR #1049 ready for review.

**You see.**

- [x] PR #1049 passes all CI checks and provides complete OpenSpec specification.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_context_budget_contracts.py tests/test_context_overlays.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify offline contracts suite. Save `/tmp/swarm-openspec-reconcile/worker-1/trunk.png`. Pass when CI passes.
- [x] Lane 2. 22-source crosswalk census probe. Save `/tmp/swarm-openspec-reconcile/worker-2/census.png`. Pass when 22 sources are classified.
- [x] Lane 3. 12 general skills probe. Save `/tmp/swarm-openspec-reconcile/worker-3/general.png`. Pass when 12 general skills map to existing owners.
- [x] Lane 4. 5 conditional skills probe. Save `/tmp/swarm-openspec-reconcile/worker-4/conditional.png`. Pass when 5 conditional skills are gated.
- [x] Lane 5. 5 excluded skills probe. Save `/tmp/swarm-openspec-reconcile/worker-5/excluded.png`. Pass when 5 excluded skills have no runtime import.
- [x] Lane 6. Issue graph link probe. Save `/tmp/swarm-openspec-reconcile/worker-6/graph.png`. Pass when issue graph links match GitHub issues.
- [x] Lane 7. Requirement collision probe. Save `/tmp/swarm-openspec-reconcile/worker-7/collision.png`. Pass when no duplicate requirements exist.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-openspec-reconcile/worker-8/runtime.png`. Pass when uv and bun run cleanly.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-openspec-reconcile/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-openspec-reconcile/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Context budget contract test duration in seconds.
- [x] Probe. Time uv run pytest tests/test_context_budget_contracts.py.
- [x] Baseline. Record trunk duration of context budget tests.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/openspec-reconcile-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/openspec-reconcile-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Qualify PR 1065, full multi-harness gate, and close Epics 1060 and 1072 (gate-verification-close)

**Depends on.** openspec-reconcile

**Files.**

- [x] Rebase `skill/pr-evidence-integrity-20261107`.
- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.
- [x] Edit `docs/plans/2026-11-08-mise-reproducible-runtime-and-omp-verification.md`.

**Build.**

- [x] Rebase PR #1065 onto current trunk.
- [x] Validate 14-case candidate evaluation and 29/29 sensitive controls.
- [x] Mark PR #1065 ready for review and merge.
- [x] Update changelog with entries for mise tasks, OMP verification skill, and DSH-22 reconciliation.
- [x] Update todo.md and close Epic #1060 and Epic #1072.

**You see.**

- [x] Full matrix verdict is PASS and all 8 verification skills pass audit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/verify_portable.py doctor --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify 6-harness doctor matrix. Save `/tmp/swarm-gate-verification-close/worker-1/trunk.png`. Pass when matrix verdict is PASS.
- [x] Lane 2. Worktree protocol check probe. Save `/tmp/swarm-gate-verification-close/worker-2/worktree.png`. Pass when worktree protocol passes.
- [x] Lane 3. Staleness report probe. Save `/tmp/swarm-gate-verification-close/worker-3/staleness.png`. Pass when matrix evidence is ALL FRESH.
- [x] Lane 4. Evidence durability probe. Save `/tmp/swarm-gate-verification-close/worker-4/durability.png`. Pass when all hosts report PASS.
- [x] Lane 5. Package projection probe. Save `/tmp/swarm-gate-verification-close/worker-5/projection.png`. Pass when all manifests match.
- [x] Lane 6. Verification scaffolder audit probe. Save `/tmp/swarm-gate-verification-close/worker-6/scaffold.png`. Pass when all 8 skills pass audit.
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

- Evaluated mise tasks and toolchain configuration.
- Evaluated OMP verification skill requirements in .omp/skills/verify-omp-pstack/.
- Evaluated DSH-22 OpenSpec requirements in PR #1049 and PR #1065.

## Appendix B. Alternatives rejected

- Installing unmanaged runtime binaries rejected in favor of reproducible mise management.
- Importing vendor-specific DSH workflows rejected per OpenSpec classification.

## Appendix C. Risks

- Risk of lockfile drift. Mitigated by strict mise.lock and uv.lock validation.
- Risk of breaking existing OMP package validation. Mitigated by comprehensive RPC and lifecycle tests.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
- OpenSpec in openspec/changes/2026-11-07-deepseek-skills-22-source-refresh/
