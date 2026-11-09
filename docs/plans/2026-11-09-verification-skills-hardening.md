# Verification Skills Hardening and Live Settlements

This program aligns OpenSpec spec delta headers for reusable skill patterns, updates durable OMP live driver settlements with current surface revisions, documents the 10-skill verification driver matrix in test tiers documentation, and qualifies the 6-harness verification matrix.
Work proceeds in four stacked pull requests under Epic 1215.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-09-verification-skills-hardening.md, PR ids in order openspec-delta-align, omp-live-settlements, verify-skills-docs, gate-close-1215, the verification rule, the root merges, and the done condition is every box checked with its evidence."
- [x] Read these from trunk at program start. Re-read them at every tick.
  - [x] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [x] `git show origin/main:skills/swarm/SKILL.md`
  - [x] `git show origin/main:profiles/antigravity.json`
  - [x] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [x] `git show origin/main:skills/poteto-mode/playbooks/shipping.md`
- [x] Arm the 30-minute audit tick with the host schedule capability. Never leave the cadence to memory.
- [x] Use this tick prompt. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [x] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [x] From this parent session, spawn one owner per PR using the host spawn primitive. Depth is 1.
- [x] Follow this dependency graph.
  - [x] openspec-delta-align is first and branches from main.
  - [x] omp-live-settlements after openspec-delta-align.
  - [x] verify-skills-docs after omp-live-settlements.
  - [x] gate-close-1215 after verify-skills-docs.
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
- [x] Start the environment and verify toolchains.
- [x] Execute the live test and save evidence screenshots.


## Reconcile OpenSpec spec delta headers and align reusable skill pattern requirements (openspec-delta-align)

**Depends on.** None.

**Files.**

- [x] Edit `openspec/changes/2026-11-07-deepseek-skills-22-source-refresh/specs/pstack-reusable-skill-patterns/spec.md`.
- [x] Edit `tests/test_openspec_change.py`.

**Build.**

- [x] Change `## ADDED Requirements` to `## MODIFIED Requirements` in deepseek skills spec delta.
- [x] Verify validation passes with zero archive refusal warnings.
- [x] Add test assertion verifying active change spec deltas align with base specs.
- [x] Enforce SOLID, KISS, DRY, and YAGNI architectural principles.

**You see.**

- [x] Clean OpenSpec validation with zero warnings about refused deltas.
- [x] Passing test suite in `tests/test_openspec_change.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bunx --yes @fission-ai/openspec@1.16.1 validate --all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Dual validation probe. Save `/tmp/swarm-openspec-delta-align/worker-1/validate.png`. Pass when validate:openspec exits 0.
- [x] Lane 2. OpenSpec change suite probe. Save `/tmp/swarm-openspec-delta-align/worker-2/openspec.png`. Pass when test_openspec_change passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-openspec-delta-align/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-openspec-delta-align/worker-4/projection.png`. Pass when projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-openspec-delta-align/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-openspec-delta-align/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-openspec-delta-align/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-openspec-delta-align/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-openspec-delta-align/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-openspec-delta-align/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. OpenSpec validate duration in seconds.
- [x] Probe. Time bunx --yes @fission-ai/openspec@1.16.1 validate --all.
- [x] Baseline. Record trunk duration of OpenSpec validation.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/openspec-delta-align-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/openspec-delta-align-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Harmonize durable OMP live driver settlements and update evidence index (omp-live-settlements)

**Depends on.** openspec-delta-align

**Files.**

- [x] Edit `.audit/evidence/omp-receipt.json`.
- [x] Edit `.audit/evidence/index.json`.
- [x] Edit `tests/test_evidence_durability.py`.

**Build.**

- [x] Commit verified live OMP RPC settlements matching current driver revision.
- [x] Synchronize `.audit/evidence/index.json` OMP entry timestamp and revision.
- [x] Add test asserting driver revision uniformity across declared packaged hosts in index.
- [x] Verify zero regressions in durability and receipt test suites.

**You see.**

- [x] Synchronized driver revisions in `index.json` and durable receipts.
- [x] Green test suite in `tests/test_evidence_durability.py`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run python scripts/verify_portable.py check-staleness --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Staleness check probe. Save `/tmp/swarm-omp-live-settlements/worker-1/staleness.png`. Pass when staleness reports ALL FRESH.
- [x] Lane 2. Evidence durability probe. Save `/tmp/swarm-omp-live-settlements/worker-2/durability.png`. Pass when check-evidence passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-omp-live-settlements/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-omp-live-settlements/worker-4/projection.png`. Pass when projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-omp-live-settlements/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence test suite probe. Save `/tmp/swarm-omp-live-settlements/worker-6/evidence-tests.png`. Pass when durability tests pass.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-omp-live-settlements/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-omp-live-settlements/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-omp-live-settlements/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-omp-live-settlements/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Staleness check duration in seconds.
- [x] Probe. Time uv run python scripts/verify_portable.py check-staleness --host all.
- [x] Baseline. Record trunk duration of staleness check.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/omp-live-settlements-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/omp-live-settlements-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Update verification test tiers documentation and harmonize plugin synchronization lifecycle (verify-skills-docs)

**Depends on.** omp-live-settlements

**Files.**

- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Document the 10-skill verification driver matrix in `docs/verification-test-tiers.md`.
- [x] Document live Antigravity plugin synchronization and lifecycle update contracts.
- [x] Document live settlement retention semantics across portable verifiers.
- [x] Update `todo.md` with completed tasks under Epic 1215.

**You see.**

- [x] Comprehensive verification test tiers documentation covering driver matrix.
- [x] Accurate task tracking in `todo.md`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run python scripts/sync_antigravity_plugin.py --check`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Plugin sync probe. Save `/tmp/swarm-verify-skills-docs/worker-1/sync.png`. Pass when sync check exits 0.
- [x] Lane 2. Lifecycle verify probe. Save `/tmp/swarm-verify-skills-docs/worker-2/lifecycle.png`. Pass when package_lifecycle verify exits 0.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-verify-skills-docs/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-verify-skills-docs/worker-4/projection.png`. Pass when projection check passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-verify-skills-docs/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Evidence staleness probe. Save `/tmp/swarm-verify-skills-docs/worker-6/staleness.png`. Pass when staleness reports ALL FRESH.
- [x] Lane 7. Poteto test suite probe. Save `/tmp/swarm-verify-skills-docs/worker-7/poteto.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-verify-skills-docs/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Untracked file probe. Save `/tmp/swarm-verify-skills-docs/worker-9/untracked.png`. Pass when untracked files are expected.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-verify-skills-docs/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Plugin sync check duration in seconds.
- [x] Probe. Time uv run python scripts/sync_antigravity_plugin.py --check.
- [x] Baseline. Record trunk duration of plugin sync check.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/verify-skills-docs-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/verify-skills-docs-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile issue graph, and close Epic 1215 (gate-close-1215)

**Depends on.** verify-skills-docs

**Files.**

- [x] Edit `docs/plans/2026-11-09-verification-skills-hardening.md`.
- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Run full 6-harness verification matrix doctor across all declared hosts.
- [x] Run driver orchestrator across all 10 verification skills.
- [x] Update CHANGELOG.md with Epic 1215 deliverables.
- [x] Reconcile `todo.md` and close Epic #1215 on GitHub.

**You see.**

- [x] 6-Harness Matrix Verdict PASS in doctor output.
- [x] 10 of 10 verification skill drivers pass in drive-all output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-09-verification-skills-hardening.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Driver orchestrator probe. Save `/tmp/swarm-gate-close-1215/worker-1/drivers.png`. Pass when drive-all exits 0.
- [x] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1215/worker-2/projection.png`. Pass when package_projection check passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1215/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1215/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1215/worker-5/evidence.png`. Pass when check-evidence passes.
- [x] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1215/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [x] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1215/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1215/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Pinned bunx dual validation probe. Save `/tmp/swarm-gate-close-1215/worker-9/dual.png`. Pass when dual validation exits 0.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1215/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Full verification gate duration in seconds.
- [x] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [x] Baseline. Record trunk duration of doctor across all hosts.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/gate-close-1215-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/gate-close-1215-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every PR merged to trunk in bottom-up order.
- [x] Every box in this plan checked with its evidence.
- [x] Post final status message to operator.


## Appendix A. Prototype evidence

- Evaluated live OMP RPC v2 subagent operations with real model openai-codex/gpt-6-luna.
- Evaluated scaffold_verification_skill.py --drive-all across all 10 verification skills with 10/10 PASS.
- Evaluated sync_antigravity_plugin.py --force --sync and package_lifecycle.py update --host all convergence.
- Evaluated check-staleness --host all with ALL FRESH.

## Appendix B. Alternatives rejected

- Leaving OMP receipt stale rejected per principle-prove-it-works.
- Leaving duplicate ADDED delta headers in OpenSpec rejected per principle-boundary-discipline.
- Skipping live harness matrix verification rejected per principle-make-operations-idempotent.
