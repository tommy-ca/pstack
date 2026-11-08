# Thermonuclear quality and verification tools plan

Four PRs decompose giant projection modules, harden driver executable guards, and scaffold Antigravity verification skill.
The program brings architectural decomposition, driver hardening, and verification skill coverage for the active host.
Order is droid-decomposition, driver-hardening, antigravity-verification-skill, quality-gate.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-thermonuclear-quality-and-verification.md, PR ids in order droid-decomposition, driver-hardening, antigravity-verification-skill, quality-gate, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] droid-decomposition is first and branches from main.
  - [x] driver-hardening after droid-decomposition.
  - [x] antigravity-verification-skill after driver-hardening.
  - [x] quality-gate after antigravity-verification-skill.
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

## Decompose package projection and extract Droid role module (droid-decomposition)

**Depends on.** None.

**Files.**

- [x] Create `scripts/droid_role_projection.py`.
- [x] Edit `scripts/package_projection.py`.
- [x] Edit `tests/test_droid_projection.py`.

**Build.**

- [x] Extract Droid role generation and validation from package_projection to droid_role_projection.
- [x] Re-export all public symbols in package_projection for backward compatibility.
- [x] Add direct unit tests in test_droid_projection.py for the extracted module.

**You see.**

- [x] package_projection.py decreases in length from 841 lines to under 720 lines.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_droid_projection.py tests/test_project_package.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify package projection check. Save `/tmp/swarm-droid-decomposition/worker-1/trunk.png`. Pass when package projection reports in sync.
- [x] Lane 2. Droid role count probe. Save `/tmp/swarm-droid-decomposition/worker-2/roles.png`. Pass when 22 droid roles are generated.
- [x] Lane 3. Droid marketplace probe. Save `/tmp/swarm-droid-decomposition/worker-3/marketplace.png`. Pass when marketplace manifest matches.
- [x] Lane 4. Droid manifest probe. Save `/tmp/swarm-droid-decomposition/worker-4/manifest.png`. Pass when plugin.json matches.
- [x] Lane 5. Caller count invariant probe. Save `/tmp/swarm-droid-decomposition/worker-5/callers.png`. Pass when test_model_role_profiles passes.
- [x] Lane 6. File size ceiling probe. Save `/tmp/swarm-droid-decomposition/worker-6/size.png`. Pass when package_projection is under 720 lines.
- [x] Lane 7. Extracted module size probe. Save `/tmp/swarm-droid-decomposition/worker-7/extracted-size.png`. Pass when droid_role_projection is under 200 lines.
- [x] Lane 8. Re-export compatibility probe. Save `/tmp/swarm-droid-decomposition/worker-8/re-export.png`. Pass when all legacy imports resolve.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-droid-decomposition/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-droid-decomposition/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Package projection execution duration in milliseconds.
- [x] Probe. Time python3 scripts/package_projection.py --check.
- [x] Baseline. Record trunk duration of package projection check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/droid-decomposition-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/droid-decomposition-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to main branch.

## Harden verification drivers and add formal driver (driver-hardening)

**Depends on.** droid-decomposition

**Files.**

- [x] Create `.codex/skills/verify-llm-wiki-formal/scripts/driver.sh`.
- [x] Edit `scripts/scaffold_verification_skill.py`.
- [x] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [x] Add executable driver script to .codex/skills/verify-llm-wiki-formal.
- [x] Wire driver branches to scripts/verify_llm_wiki_model.py and tests/test_llm_wiki_bounded_model.py.
- [x] Add check_skill rule in scaffolder verifying driver.sh is non-symlink and executable when present.
- [x] Add regression test in test_scaffold_verification_skill.py.

**You see.**

- [x] .codex/skills/verify-llm-wiki-formal/scripts/driver.sh passes doctor, launch, drive, and cleanup commands.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify scaffolder audit. Save `/tmp/swarm-driver-hardening/worker-1/trunk.png`. Pass when audit passes.
- [x] Lane 2. Driver doctor command probe. Save `/tmp/swarm-driver-hardening/worker-2/doctor.png`. Pass when driver doctor returns 0.
- [x] Lane 3. Driver launch command probe. Save `/tmp/swarm-driver-hardening/worker-3/launch.png`. Pass when driver launch returns 0.
- [x] Lane 4. Driver drive command probe. Save `/tmp/swarm-driver-hardening/worker-4/drive.png`. Pass when driver drive runs model checks and tests.
- [x] Lane 5. Driver cleanup command probe. Save `/tmp/swarm-driver-hardening/worker-5/cleanup.png`. Pass when driver cleanup returns 0.
- [x] Lane 6. Executable driver check probe. Save `/tmp/swarm-driver-hardening/worker-6/exec-check.png`. Pass when non-executable driver is flagged.
- [x] Lane 7. LLM wiki bounded model probe. Save `/tmp/swarm-driver-hardening/worker-7/wiki-model.png`. Pass when 39 traces and mutant pass.
- [x] Lane 8. Driver timeout handling probe. Save `/tmp/swarm-driver-hardening/worker-8/timeout.png`. Pass when 60s bounding is present.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-driver-hardening/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-driver-hardening/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Scaffolder audit execution duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --audit --json.
- [x] Baseline. Record trunk duration of scaffolder audit.
- [x] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/driver-hardening-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/driver-hardening-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Build Antigravity verification skill (antigravity-verification-skill)

**Depends on.** driver-hardening

**Files.**

- [x] Create `.agents/skills/verify-antigravity-pstack/SKILL.md`.
- [x] Create `.agents/skills/verify-antigravity-pstack/features/features.json`.
- [x] Create `.agents/skills/verify-antigravity-pstack/scripts/driver.sh`.

**Build.**

- [x] Scaffold and tailor verify-antigravity-pstack skill in .agents/skills/.
- [x] Implement doctor, launch, drive, proof bar, evidence, and cleanup sections.
- [x] Provide features.json and executable driver.sh running doctor checks and contracts.

**You see.**

- [x] python3 scripts/scaffold_verification_skill.py --audit --json discovers and passes 7 verification skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scaffold_verification_skill.py --check --target-dir .agents/skills/verify-antigravity-pstack`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full scaffolder audit. Save `/tmp/swarm-antigravity-verification-skill/worker-1/trunk.png`. Pass when 7 skills pass.
- [x] Lane 2. Antigravity skill structure probe. Save `/tmp/swarm-antigravity-verification-skill/worker-2/structure.png`. Pass when all 7 required sections exist.
- [x] Lane 3. Antigravity skill byte limit probe. Save `/tmp/swarm-antigravity-verification-skill/worker-3/bytes.png`. Pass when body is under 24000 bytes.
- [x] Lane 4. Features manifest probe. Save `/tmp/swarm-antigravity-verification-skill/worker-4/features.png`. Pass when features.json validates.
- [x] Lane 5. Driver doctor probe. Save `/tmp/swarm-antigravity-verification-skill/worker-5/driver-doctor.png`. Pass when driver doctor returns 0.
- [x] Lane 6. Driver drive probe. Save `/tmp/swarm-antigravity-verification-skill/worker-6/driver-drive.png`. Pass when driver drive returns 0.
- [x] Lane 7. Driver cleanup probe. Save `/tmp/swarm-antigravity-verification-skill/worker-7/driver-cleanup.png`. Pass when driver cleanup returns 0.
- [x] Lane 8. Reproducible runtime probe. Save `/tmp/swarm-antigravity-verification-skill/worker-8/runtime.png`. Pass when uv run python resolution is used.
- [x] Lane 9. Evidence freshness probe. Save `/tmp/swarm-antigravity-verification-skill/worker-9/freshness.png`. Pass when receipts are fresh.
- [x] Lane 10. Evidence durability probe. Save `/tmp/swarm-antigravity-verification-skill/worker-10/durability.png`. Pass when all hosts report PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Antigravity verification skill check duration in milliseconds.
- [x] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .agents/skills/verify-antigravity-pstack.
- [x] Baseline. Record trunk duration of skill check.
- [x] Rule. Head duration must not exceed trunk duration plus 15 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/antigravity-verification-skill-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/antigravity-verification-skill-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Update CI offline contracts, reconcile docs, and gate proof (quality-gate)

**Depends on.** antigravity-verification-skill

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `docs/plans/2026-11-07-thermonuclear-quality-and-verification.md`.
- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Add CI execution steps for verify-llm-wiki-formal and verify-antigravity-pstack drivers.
- [x] Update changelog with entries for decomposition, driver hardening, and Antigravity skill.
- [x] Update todo.md tracking and close Epic #1054.

**You see.**

- [x] Full matrix verdict is PASS and all python and bun tests pass.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/verify_portable.py doctor --host all`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify 6-harness doctor matrix. Save `/tmp/swarm-quality-gate/worker-1/trunk.png`. Pass when matrix verdict is PASS.
- [x] Lane 2. Worktree protocol check probe. Save `/tmp/swarm-quality-gate/worker-2/worktree.png`. Pass when worktree protocol passes.
- [x] Lane 3. Staleness report probe. Save `/tmp/swarm-quality-gate/worker-3/staleness.png`. Pass when matrix evidence is ALL FRESH.
- [x] Lane 4. Evidence durability probe. Save `/tmp/swarm-quality-gate/worker-4/durability.png`. Pass when all hosts report PASS.
- [x] Lane 5. Package projection probe. Save `/tmp/swarm-quality-gate/worker-5/projection.png`. Pass when all manifests match.
- [x] Lane 6. Verification scaffolder audit probe. Save `/tmp/swarm-quality-gate/worker-6/scaffold.png`. Pass when all 7 skills pass audit.
- [x] Lane 7. Plan validation probe. Save `/tmp/swarm-quality-gate/worker-7/plan.png`. Pass when check-plan reports 4 sections and 0 problems.
- [x] Lane 8. Full pytest suite probe. Save `/tmp/swarm-quality-gate/worker-8/pytest.png`. Pass when all tests pass.
- [x] Lane 9. Full bun test suite probe. Save `/tmp/swarm-quality-gate/worker-9/bun.png`. Pass when 102 tests pass.
- [x] Lane 10. Python size limit probe. Save `/tmp/swarm-quality-gate/worker-10/size.png`. Pass when all python modules remain under 1000 lines.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Multi-harness doctor duration in seconds.
- [x] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [x] Baseline. Record trunk duration of doctor across all hosts.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/quality-gate-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/quality-gate-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every box above is checked with its evidence.
- [x] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated decomposition of scripts/package_projection.py into scripts/droid_role_projection.py.
- Evaluated missing driver.sh in .codex/skills/verify-llm-wiki-formal.
- Evaluated missing verification skill in .agents/skills/ for the active Antigravity host.

## Appendix B. Alternatives rejected

- Leaving package_projection.py as a monolithic 841-line module rejected per thermonuclear review rule #1 and #6.
- Manually invoking scripts without executable driver scripts rejected to ensure consistent CI execution.

## Appendix C. Risks

- Risk of breaking re-exports in package_projection.py. Mitigated by explicit symbol re-exports and comprehensive test suite.
- Risk of skill audit failure on Antigravity skill. Mitigated by strict frontmatter and section conformance.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Scaffolder in scripts/scaffold_verification_skill.py
- Offline contracts workflow in .github/workflows/portability-offline.yml
