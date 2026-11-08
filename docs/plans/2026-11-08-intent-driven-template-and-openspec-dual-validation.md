# Intent-Driven Template Ingestion and OpenSpec Dual-Mode Validation

This program implements intent-driven template configuration ingestion (opencode.json, AGENTS.md, openspec-git-discipline), harmonizes OpenSpec tasks in mise.toml with dual-mode validation from qstack/mise.toml, hardens verification skills, and qualifies the 6-harness verification matrix.
Work proceeds in four stacked pull requests under Epic 1178.

## How to read this

One box is one unit of work. Every box names the evidence that verifies it.
Check a box only when its evidence exists.
Follow procedures in playbooks/ when executing tasks.
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-intent-driven-template-and-openspec-dual-validation.md, PR ids in order template-ingest, mise-dual-validation, verification-conformance, gate-close-1178, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] template-ingest is first and branches from main.
  - [ ] mise-dual-validation after template-ingest.
  - [ ] verification-conformance after mise-dual-validation.
  - [ ] gate-close-1178 after verification-conformance.
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

## Ingest OpenSpec git discipline and install template configurations (template-ingest)

**Depends on.** None.

**Files.**

- [x] Edit `opencode.json`.
- [x] Edit `AGENTS.md`.
- [x] Edit `.agents/skills/openspec-git-discipline/SKILL.md`.
- [x] Edit `.opencode/skills/openspec-git-discipline/SKILL.md`.
- [x] Edit `tests/test_skill_frontmatter.py`.

**Build.**

- [x] Add `opencode.json` with official OpenCode schema declaration.
- [x] Add `AGENTS.md` with OpenSpec git discipline workflow instruction.
- [x] Ingest `openspec-git-discipline` skill into `.agents/skills` and `.opencode/skills`.
- [x] Validate skill frontmatter in `tests/test_skill_frontmatter.py`.

**You see.**

- [x] Valid `opencode.json` and `AGENTS.md` at repo root.
- [x] Working `openspec-git-discipline` skill across Antigravity and OpenCode skill roots.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_skill_frontmatter.py -k test_openspec_git_discipline`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. OpenCode JSON validation probe. Save `/tmp/swarm-template-ingest/worker-1/opencode.png`. Pass when opencode.json is valid JSON.
- [ ] Lane 2. AGENTS markdown probe. Save `/tmp/swarm-template-ingest/worker-2/agents.png`. Pass when AGENTS.md exists and is readable.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-template-ingest/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-template-ingest/worker-4/projection.png`. Pass when package_projection check passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-template-ingest/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-template-ingest/worker-6/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-template-ingest/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-template-ingest/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-template-ingest/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-template-ingest/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Skill frontmatter test execution duration in seconds.
- [ ] Probe. Time uv run pytest tests/test_skill_frontmatter.py.
- [ ] Baseline. Record trunk duration of frontmatter test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/template-ingest-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/template-ingest-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Harmonize OpenSpec mise tasks with dual-mode validation from qstack/mise.toml (mise-dual-validation)

**Depends on.** template-ingest

**Files.**

- [x] Edit `mise.toml`.
- [x] Edit `scripts/openspec_change.py`.
- [x] Edit `tests/test_runtime_toolchain.py`.
- [x] Edit `tests/test_openspec_change.py`.

**Build.**

- [x] Add `verify:openspec:all` task to `mise.toml` running `openspec validate --all`.
- [x] Add `--all` CLI flag support to `scripts/openspec_change.py`.
- [x] Update `tests/test_runtime_toolchain.py` to assert `verify:openspec:all`.
- [x] Update `tests/test_openspec_change.py` with `--all` tests.

**You see.**

- [x] Clean executable mise task `mise run verify:openspec:all`.
- [x] CLI command `python3 scripts/openspec_change.py --all` running all-spec validation.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_runtime_toolchain.py tests/test_openspec_change.py -k "test_mise_toml_configuration or test_all_flag"`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Dual-mode validation probe. Save `/tmp/swarm-mise-dual-validation/worker-1/dual.png`. Pass when verify:openspec:all exits 0.
- [ ] Lane 2. CLI all-flag probe. Save `/tmp/swarm-mise-dual-validation/worker-2/cli.png`. Pass when scripts/openspec_change.py --all exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-mise-dual-validation/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-mise-dual-validation/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-mise-dual-validation/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-mise-dual-validation/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-mise-dual-validation/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-mise-dual-validation/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-mise-dual-validation/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-mise-dual-validation/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec all validation duration in seconds.
- [ ] Probe. Time python3 scripts/openspec_change.py --all.
- [ ] Baseline. Record trunk duration of openspec validate --all.
- [ ] Rule. Head duration must not exceed 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/mise-dual-validation-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/mise-dual-validation-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Update verification skills and scaffolders with intent-driven template conformance (verification-conformance)

**Depends on.** mise-dual-validation

**Files.**

- [x] Edit `docs/verification-test-tiers.md`.
- [x] Edit `todo.md`.

**Build.**

- [x] Document intent-driven template files and git-discipline contracts in `docs/verification-test-tiers.md`.
- [x] Verify zero untracked clutter and clean worktree state across all 10 drivers.
- [x] Ensure strict adherence to SOLID, KISS, DRY, and YAGNI architectural principles.
- [x] Document dual-mode OpenSpec validation in test tier hierarchy.

**You see.**

- [x] Accurate documentation of intent-driven template integration in `docs/verification-test-tiers.md`.
- [x] Updated execution plan reflecting completed verification tasks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run python scripts/openspec_change.py --status`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Documentation structure probe. Save `/tmp/swarm-verification-conformance/worker-1/doc.png`. Pass when docs contain git-discipline.
- [ ] Lane 2. Status inspection probe. Save `/tmp/swarm-verification-conformance/worker-2/status.png`. Pass when status exits 0.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-verification-conformance/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Package projection probe. Save `/tmp/swarm-verification-conformance/worker-4/projection.png`. Pass when projection passes.
- [ ] Lane 5. Worktree confinement probe. Save `/tmp/swarm-verification-conformance/worker-5/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 6. Evidence staleness probe. Save `/tmp/swarm-verification-conformance/worker-6/staleness.png`. Pass when staleness reports all fresh.
- [ ] Lane 7. Poteto test suite probe. Save `/tmp/swarm-verification-conformance/worker-7/poteto.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-verification-conformance/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Untracked file probe. Save `/tmp/swarm-verification-conformance/worker-9/untracked.png`. Pass when untracked files are expected.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-verification-conformance/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec status inspection duration in seconds.
- [ ] Probe. Time uv run python scripts/openspec_change.py --status.
- [ ] Baseline. Record trunk duration of status inspection.
- [ ] Rule. Head duration must not exceed 5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verification-conformance-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/verification-conformance-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix, reconcile plan, and close Epic 1178 (gate-close-1178)

**Depends on.** verification-conformance

**Files.**

- [ ] Edit `docs/plans/2026-11-08-intent-driven-template-and-openspec-dual-validation.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Run full 6-harness verification matrix doctor across all hosts.
- [ ] Run offline contract suite, poteto-mode bun tests, and plan validation.
- [ ] Update CHANGELOG.md with Epic 1178 deliverables.
- [ ] Reconcile `todo.md` and mark all child units and Epic 1178 complete.

**You see.**

- [ ] 6-Harness Matrix Verdict PASS in doctor output.
- [ ] Complete evidence receipts recorded for all six harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-intent-driven-template-and-openspec-dual-validation.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1178/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1178/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1178/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1178/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1178/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1178/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1178/worker-7/poteto-tests.png`. Pass when 104 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1178/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. OpenSpec dual validation probe. Save `/tmp/swarm-gate-close-1178/worker-9/dual.png`. Pass when dual validation exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1178/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1178-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1178-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated intent-driven template configuration ingestion and skill layout.
- Evaluated dual-mode OpenSpec validation based on qstack/mise.toml.
- Evaluated 6-harness doctor matrix across all declared hosts.
- Evaluated plan validation and Bun test suite.

## Appendix B. Alternatives rejected

- Blindly overwriting existing hardened intent-driven schemas rejected per INSTALL_TEMPLATE.md.
- Hardcoding validation paths rejected per SOLID, KISS, and DRY principles.
- Skipping live harness matrix verification rejected per principle-prove-it-works.
