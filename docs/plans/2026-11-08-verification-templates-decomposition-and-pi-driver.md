# Verification templates decomposition and Pi driver plan

Four PRs decompose verification skill templates, fix OpenSpec strict validation warnings, unify Pi verification driver execution, automate CI offline checks, and qualify the full 6-host verification matrix.
Order is verification-skill-templates, openspec-and-pi-driver, ci-pi-driver-wiring, gate-verification-close.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-verification-templates-decomposition-and-pi-driver.md, PR ids in order verification-skill-templates, openspec-and-pi-driver, ci-pi-driver-wiring, gate-verification-close, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] verification-skill-templates is first and branches from main.
  - [x] openspec-and-pi-driver after verification-skill-templates.
  - [x] ci-pi-driver-wiring after openspec-and-pi-driver.
  - [x] gate-verification-close after ci-pi-driver-wiring.
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

## Extract verification skill templates into dedicated module (verification-skill-templates)

**Depends on.** None.

**Files.**

- [x] Create `scripts/verification_skill_templates.py`.
- [x] Create `tests/test_verification_skill_templates.py`.
- [x] Edit `scripts/scaffold_verification_skill.py`.

**Build.**

- [x] Extract generate_driver_script, generate_skill_content, generate_features_readme, generate_feature_content to scripts/verification_skill_templates.py.
- [x] Re-export and delegate from scripts/scaffold_verification_skill.py.
- [x] Add unit tests verifying template generation in tests/test_verification_skill_templates.py.
- [x] Verify scripts/scaffold_verification_skill.py decomposes below 430 lines while all 10 verification skills remain in sync.

**You see.**

- [x] scripts/scaffold_verification_skill.py decomposes below 430 lines while audit command reports PASS on all 10 skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_verification_skill_templates.py tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify verification skill audit. Save `/tmp/swarm-verification-skill-templates/worker-1/trunk.png`. Pass when audit reports 10 passed.
- [x] Lane 2. Driver script template generation probe. Save `/tmp/swarm-verification-skill-templates/worker-2/driver.png`. Pass when template generates with uv run and bun.
- [x] Lane 3. SKILL.md template generation probe. Save `/tmp/swarm-verification-skill-templates/worker-3/skill.png`. Pass when frontmatter and sections match.
- [x] Lane 4. Features readme template probe. Save `/tmp/swarm-verification-skill-templates/worker-4/readme.png`. Pass when features readme generates.
- [x] Lane 5. Feature file template probe. Save `/tmp/swarm-verification-skill-templates/worker-5/feature.png`. Pass when feature content generates.
- [x] Lane 6. Re-export delegation probe. Save `/tmp/swarm-verification-skill-templates/worker-6/reexport.png`. Pass when legacy imports still succeed.
- [x] Lane 7. Scaffolder module line limit probe. Save `/tmp/swarm-verification-skill-templates/worker-7/lines.png`. Pass when lines are under 430.
- [x] Lane 8. Verification skill list probe. Save `/tmp/swarm-verification-skill-templates/worker-8/list.png`. Pass when 10 skills are listed.
- [x] Lane 9. Verification skill check probe. Save `/tmp/swarm-verification-skill-templates/worker-9/check.png`. Pass when checking an existing skill passes.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-verification-skill-templates/worker-10/durability.png`. Pass when receipts are durable.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Template generation duration in seconds.
- [x] Probe. Time uv run pytest tests/test_verification_skill_templates.py.
- [x] Baseline. Record trunk duration of scaffolder tests.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/verification-skill-templates-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/verification-skill-templates-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Fix OpenSpec strict validation and unify Pi verification driver (openspec-and-pi-driver)

**Depends on.** verification-skill-templates

**Files.**

- [x] Edit `openspec/changes/2026-11-07-deepseek-skills-22-source-refresh/specs/pstack-reusable-skill-patterns/spec.md`.
- [x] Edit `.pi/skills/verify-pi-pstack/scripts/driver.sh`.
- [x] Edit `scripts/evidence_index.py`.
- [x] Edit `scripts/verify_portable.py`.

**Build.**

- [x] Remove text above first header and tighten long requirement description in pstack-reusable-skill-patterns/spec.md.
- [x] Tailor .pi/skills/verify-pi-pstack/scripts/driver.sh with standard 60s timeout bounded launch and drive verbs.
- [x] Add prune-ephemeral helper function to scripts/evidence_index.py and wire prune command into scripts/verify_portable.py.
- [x] Verify openspec validate --changes --strict and tests/test_verify_harness.py pass with 0 exit code.

**You see.**

- [x] openspec validate passes in strict mode and .pi/skills/verify-pi-pstack/scripts/driver.sh passes launch and drive.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `openspec validate --changes --strict && uv run pytest tests/test_verify_harness.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify openspec strict validation. Save `/tmp/swarm-openspec-and-pi-driver/worker-1/trunk.png`. Pass when strict validation passes.
- [x] Lane 2. Test verify harness probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-2/harness.png`. Pass when test_verify_harness passes.
- [x] Lane 3. Pi driver launch probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-3/launch.png`. Pass when launch reports environment ready.
- [x] Lane 4. Pi driver drive probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-4/drive.png`. Pass when drive reports PASS.
- [x] Lane 5. Pi driver doctor probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-5/doctor.png`. Pass when doctor reports PASS.
- [x] Lane 6. Pi formal driver probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-6/formal.png`. Pass when formal driver passes all verbs.
- [x] Lane 7. Prune ephemeral probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-7/prune.png`. Pass when prune leaves tracked receipts intact.
- [x] Lane 8. Candidate profile contract probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-8/profile.png`. Pass when verify_pi_candidate check passes.
- [x] Lane 9. Bounded negative controls probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-9/controls.png`. Pass when 59 mutants are rejected.
- [x] Lane 10. Verification scaffolder audit probe. Save `/tmp/swarm-openspec-and-pi-driver/worker-10/scaffold.png`. Pass when 10 skills pass audit.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. OpenSpec strict validation duration in seconds.
- [x] Probe. Time openspec validate --changes --strict.
- [x] Baseline. Record trunk duration of openspec validation.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/openspec-and-pi-driver-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/openspec-and-pi-driver-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Wire Pi verification drivers and projection tests into CI (ci-pi-driver-wiring)

**Depends on.** openspec-and-pi-driver

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `scripts/select_checks.py`.

**Build.**

- [x] Add Pi verification driver launch and drive steps to .github/workflows/portability-offline.yml.
- [x] Add offline tests to portability-offline.yml including antigravity projection, droid projection, thermos skills, worktree cleanup, verification templates, and verify harness.
- [x] Update scripts/select_checks.py mapping rules for new projection and template modules.
- [x] Verify offline contracts workflow syntax and run select-checks.

**You see.**

- [x] GitHub Actions offline workflow executes Pi verification driver and expanded offline test suite.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_select_checks.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify workflow syntax and parse. Save `/tmp/swarm-ci-pi-driver-wiring/worker-1/trunk.png`. Pass when workflow is valid yaml.
- [x] Lane 2. Offline contract test list probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-2/list.png`. Pass when all new tests are discovered.
- [x] Lane 3. Check selection mapping probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-3/mapping.png`. Pass when select_checks maps templates.
- [x] Lane 4. Antigravity projection mapping probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-4/ag_map.png`. Pass when antigravity projection maps.
- [x] Lane 5. Droid projection mapping probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-5/droid_map.png`. Pass when droid projection maps.
- [x] Lane 6. Worktree cleanup mapping probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-6/wt_map.png`. Pass when worktree cleanup maps.
- [x] Lane 7. Thermos skills mapping probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-7/thermos_map.png`. Pass when thermos skills map.
- [x] Lane 8. Pi driver CI step probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-8/pi_step.png`. Pass when Pi driver steps execute cleanly.
- [x] Lane 9. Verification scaffolder audit probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-9/scaffold.png`. Pass when 10 skills pass audit.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-ci-pi-driver-wiring/worker-10/durability.png`. Pass when all receipts are durable.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Select checks duration in seconds.
- [x] Probe. Time uv run python scripts/select_checks.py.
- [x] Baseline. Record trunk duration of select_checks.
- [x] Rule. Head duration must not exceed trunk duration plus 5 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/ci-pi-driver-wiring-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/ci-pi-driver-wiring-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Run multi-harness verification gate, reconcile plan, and close Epic 1096 (gate-verification-close)

**Depends on.** ci-pi-driver-wiring

**Files.**

- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.
- [x] Edit `docs/plans/2026-11-08-verification-templates-decomposition-and-pi-driver.md`.

**Build.**

- [x] Run full 6-host doctor and verify matrix verdict is PASS.
- [x] Validate evidence freshness across all 6 hosts.
- [x] Update changelog with entries for templates decomposition, OpenSpec fix, Pi driver unification, and CI expansion.
- [x] Update todo.md and close Epic #1096.

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

- Evaluated template decomposition in scripts/verification_skill_templates.py.
- Evaluated OpenSpec strict validation in openspec validate --changes --strict.
- Evaluated Pi driver execution in .pi/skills/verify-pi-pstack/scripts/driver.sh.
- Evaluated CI workflow offline contract tests in .github/workflows/portability-offline.yml.

## Appendix B. Alternatives rejected

- Leaving scaffold_verification_skill.py above 680 lines rejected per Single Responsibility Principle.
- Leaving OpenSpec strict validation warnings rejected per strict quality gate.
- Leaving Pi driver untested in CI rejected per complete driver contract.

## Appendix C. Risks

- Risk of template drift during decomposition. Mitigated by comprehensive unit tests and scaffolder audit.
- Risk of timeout in driver commands. Mitigated by strict 60s execution bounds.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
