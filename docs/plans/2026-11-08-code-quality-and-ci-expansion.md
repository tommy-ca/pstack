# Code quality and offline CI expansion plan

Five PRs restore fail-closed Pi driver cleanup, cleanse thermo skill style rules, prune obsolete workspace clutter, expand offline CI with hermetic safety tests, and qualify the full 6-host verification matrix.
Order is pi-driver-cleanup, thermo-skills-hygiene, prune-clutter, ci-offline-expansion, gate-close-1105.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All five PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-code-quality-and-ci-expansion.md, PR ids in order pi-driver-cleanup, thermo-skills-hygiene, prune-clutter, ci-offline-expansion, gate-close-1105, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] pi-driver-cleanup is first and branches from main.
  - [x] thermo-skills-hygiene after pi-driver-cleanup.
  - [x] prune-clutter after thermo-skills-hygiene.
  - [x] ci-offline-expansion after prune-clutter.
  - [x] gate-close-1105 after ci-offline-expansion.
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

## Restore fail-closed Pi driver cleanup (pi-driver-cleanup)

**Depends on.** None.

**Files.**

- [x] Edit `.pi/skills/verify-pi-pstack/scripts/driver.sh`.
- [x] Edit `.pi/skills/verify-pi-pstack-formal/scripts/driver.sh`.

**Build.**

- [x] Restore fail-closed cleanup contract in `.pi/skills/verify-pi-pstack/scripts/driver.sh`.
- [x] Restore fail-closed cleanup contract in `.pi/skills/verify-pi-pstack-formal/scripts/driver.sh`.
- [x] Emit BLOCKED diagnostic message to standard error upon cleanup invocation.
- [x] Verify both driver scripts have executable permissions.

**You see.**

- [x] Cleanup verb fails closed with exit code 2 and diagnostic message.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_pi_authorization_contracts.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Driver cleanup exit code probe. Save `/tmp/swarm-pi-driver-cleanup/worker-1/cleanup.png`. Pass when cleanup exits 2.
- [x] Lane 2. Formal driver cleanup exit code probe. Save `/tmp/swarm-pi-driver-cleanup/worker-2/formal-cleanup.png`. Pass when cleanup exits 2.
- [x] Lane 3. Driver launch verb probe. Save `/tmp/swarm-pi-driver-cleanup/worker-3/launch.png`. Pass when launch exits 0.
- [x] Lane 4. Driver drive verb probe. Save `/tmp/swarm-pi-driver-cleanup/worker-4/drive.png`. Pass when drive exits 0.
- [x] Lane 5. Driver doctor verb probe. Save `/tmp/swarm-pi-driver-cleanup/worker-5/doctor.png`. Pass when doctor exits 0.
- [x] Lane 6. Pi candidate check script probe. Save `/tmp/swarm-pi-driver-cleanup/worker-6/check.png`. Pass when verify_pi_candidate check passes.
- [x] Lane 7. Pi candidate model script probe. Save `/tmp/swarm-pi-driver-cleanup/worker-7/model.png`. Pass when verify_pi_candidate model passes.
- [x] Lane 8. Pi candidate profile tests probe. Save `/tmp/swarm-pi-driver-cleanup/worker-8/profile.png`. Pass when test_pi_candidate_profile passes.
- [x] Lane 9. Verification skills audit probe. Save `/tmp/swarm-pi-driver-cleanup/worker-9/audit.png`. Pass when 10 skills pass.
- [x] Lane 10. Confinement check probe. Save `/tmp/swarm-pi-driver-cleanup/worker-10/confinement.png`. Pass when worktrees are confined.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Driver cleanup execution duration in seconds.
- [x] Probe. Time bash .pi/skills/verify-pi-pstack/scripts/driver.sh cleanup.
- [x] Baseline. Record trunk duration of driver commands.
- [x] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/pi-driver-cleanup-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/pi-driver-cleanup-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Cleanse thermo skill style rules and add frontmatter tests (thermo-skills-hygiene)

**Depends on.** pi-driver-cleanup

**Files.**

- [x] Edit `skills/thermo-nuclear-code-quality-review/SKILL.md`.
- [x] Edit `tests/test_thermos_skills.py`.
- [x] Create `docs/audit/thermo-nuclear-code-quality-review-2026-11-08.md`.

**Build.**

- [x] Cleanse long dashes and mid-sentence colons from skills/thermo-nuclear-code-quality-review/SKILL.md.
- [x] Add disable-model-invocation flag to frontmatter.
- [x] Add test_thermo_nuclear_code_quality_review_skill_frontmatter in tests/test_thermos_skills.py.
- [x] Add historical review record in docs/audit/thermo-nuclear-code-quality-review-2026-11-08.md.

**You see.**

- [x] All three thermo review skills pass frontmatter and style tests.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_thermos_skills.py tests/test_skill_frontmatter.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Style dashes probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-1/dashes.png`. Pass when zero long dashes found.
- [x] Lane 2. Style colons probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-2/colons.png`. Pass when zero mid-sentence colons found.
- [x] Lane 3. Frontmatter schema probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-3/frontmatter.png`. Pass when test_thermos_skills passes.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-4/projection.png`. Pass when package_projection check passes.
- [x] Lane 5. Antigravity plugin sync probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-5/sync.png`. Pass when sync check passes.
- [x] Lane 6. Skill inventory probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-6/inventory.png`. Pass when all skills discovered.
- [x] Lane 7. Historical audit record probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-7/audit-doc.png`. Pass when audit file exists.
- [x] Lane 8. Verification skills audit probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-8/audit.png`. Pass when 10 skills pass.
- [x] Lane 9. Confinement check probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-9/confinement.png`. Pass when worktrees are confined.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-thermo-skills-hygiene/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Skill frontmatter test duration in seconds.
- [x] Probe. Time uv run pytest tests/test_thermos_skills.py.
- [x] Baseline. Record trunk duration of frontmatter tests.
- [x] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/thermo-skills-hygiene-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/thermo-skills-hygiene-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Prune workspace clutter and non-evidence scratch files (prune-clutter)

**Depends on.** thermo-skills-hygiene

**Files.**

- [x] Edit `.gitignore`.
- [x] Edit `scripts/evidence_index.py`.

**Build.**

- [x] Add explicit ignore patterns for transient planning and command directories in `.gitignore`.
- [x] Enhance prune_ephemeral_evidence in scripts/evidence_index.py to purge stale non-evidence scratch files.
- [x] Remove obsolete .planning directory from workspace.
- [x] Remove obsolete .commandcode directory from workspace.

**You see.**

- [x] Workspace status is clean of historical scratch files.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_evidence_index_resilience.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Workspace status probe. Save `/tmp/swarm-prune-clutter/worker-1/status.png`. Pass when git status --ignored shows clean audit.
- [x] Lane 2. Ephemeral prune command probe. Save `/tmp/swarm-prune-clutter/worker-2/prune.png`. Pass when prune-ephemeral exits 0.
- [x] Lane 3. Evidence staleness probe. Save `/tmp/swarm-prune-clutter/worker-3/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 4. Evidence durable probe. Save `/tmp/swarm-prune-clutter/worker-4/evidence.png`. Pass when check-evidence passes.
- [x] Lane 5. Worktree confinement probe. Save `/tmp/swarm-prune-clutter/worker-5/confinement.png`. Pass when worktrees are confined.
- [x] Lane 6. Poteto script tests probe. Save `/tmp/swarm-prune-clutter/worker-6/poteto-tests.png`. Pass when 102 tests pass.
- [x] Lane 7. Verification skills audit probe. Save `/tmp/swarm-prune-clutter/worker-7/audit.png`. Pass when 10 skills pass.
- [x] Lane 8. Package projection probe. Save `/tmp/swarm-prune-clutter/worker-8/projection.png`. Pass when package_projection check passes.
- [x] Lane 9. Disk health probe. Save `/tmp/swarm-prune-clutter/worker-9/disk.png`. Pass when audit directory remains below 1 megabyte.
- [x] Lane 10. Confinement check probe. Save `/tmp/swarm-prune-clutter/worker-10/confinement.png`. Pass when worktrees are confined.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Prune command execution duration in seconds.
- [x] Probe. Time uv run python scripts/portable_verifier.py prune-ephemeral.
- [x] Baseline. Record trunk duration of prune command.
- [x] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/prune-clutter-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/prune-clutter-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Wire hermetic safety tests into offline CI (ci-offline-expansion)

**Depends on.** prune-clutter

**Files.**

- [x] Edit `.github/workflows/portability-offline.yml`.
- [x] Edit `scripts/select_checks.py`.
- [x] Edit `tests/test_select_checks.py`.

**Build.**

- [x] Add 11 hermetic test paths to .github/workflows/portability-offline.yml.
- [x] Update select_checks offline contract test list.
- [x] Update select_checks mapping rules for pi, profiles, interrogate, and swarm.
- [x] Update expected test counts in tests/test_select_checks.py.

**You see.**

- [x] All 11 newly wired tests run and pass in portability-offline CI.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_select_checks.py tests/test_pi_authorization_contracts.py tests/test_harness_profiles_sync.py tests/test_interrogate_pack.py tests/test_swarm_apply.py tests/test_swarm_partition.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Pi authorization test probe. Save `/tmp/swarm-ci-offline-expansion/worker-1/pi-auth.png`. Pass when test_pi_authorization_contracts passes.
- [x] Lane 2. Profile parity test probe. Save `/tmp/swarm-ci-offline-expansion/worker-2/profile-parity.png`. Pass when test_harness_profiles_sync passes.
- [x] Lane 3. Interrogate pack test probe. Save `/tmp/swarm-ci-offline-expansion/worker-3/interrogate.png`. Pass when test_interrogate_pack passes.
- [x] Lane 4. Swarm apply test probe. Save `/tmp/swarm-ci-offline-expansion/worker-4/swarm-apply.png`. Pass when test_swarm_apply passes.
- [x] Lane 5. Swarm partition test probe. Save `/tmp/swarm-ci-offline-expansion/worker-5/swarm-partition.png`. Pass when test_swarm_partition passes.
- [x] Lane 6. Select checks offline list probe. Save `/tmp/swarm-ci-offline-expansion/worker-6/offline-list.png`. Pass when 73 tests in offline selection.
- [x] Lane 7. Select checks mapping rules probe. Save `/tmp/swarm-ci-offline-expansion/worker-7/mappings.png`. Pass when test_select_checks passes.
- [x] Lane 8. Verification skills audit probe. Save `/tmp/swarm-ci-offline-expansion/worker-8/audit.png`. Pass when 10 skills pass.
- [x] Lane 9. Confinement check probe. Save `/tmp/swarm-ci-offline-expansion/worker-9/confinement.png`. Pass when worktrees are confined.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-ci-offline-expansion/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Select checks execution duration in seconds.
- [x] Probe. Time uv run pytest tests/test_select_checks.py.
- [x] Baseline. Record trunk duration of select checks tests.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/ci-offline-expansion-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/ci-offline-expansion-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Run multi-harness verification gate and close Epic 1105 (gate-close-1105)

**Depends on.** ci-offline-expansion

**Files.**

- [x] Edit `CHANGELOG.md`.
- [x] Edit `todo.md`.
- [x] Edit `docs/plans/2026-11-08-code-quality-and-ci-expansion.md`.

**Build.**

- [x] Update changelog with Epic 1105 entries.
- [x] Update todo with Epic 1105 units.
- [x] Mark all checkboxes in multi-phase plan.
- [x] Verify plan schema with check-plan script.

**You see.**

- [x] Complete reconciliation across ledger, todo, and plan.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-code-quality-and-ci-expansion.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1105/worker-1/confinement.png`. Pass when worktrees are confined.
- [x] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1105/worker-2/projection.png`. Pass when package_projection check passes.
- [x] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1105/worker-3/audit.png`. Pass when 10 skills pass.
- [x] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1105/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1105/worker-5/evidence.png`. Pass when check-evidence passes.
- [x] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1105/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [x] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1105/worker-7/poteto-tests.png`. Pass when 102 tests pass.
- [x] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1105/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 9. Ephemeral prune probe. Save `/tmp/swarm-gate-close-1105/worker-9/prune.png`. Pass when prune-ephemeral exits 0.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1105/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Full verification gate duration in seconds.
- [x] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [x] Baseline. Record trunk duration of doctor across all hosts.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/gate-close-1105-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/gate-close-1105-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every PR merged to trunk in bottom-up order.
- [x] Every box in this plan checked with its evidence.
- [x] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated Pi candidate cleanup fail-closed behavior in tests/test_pi_authorization_contracts.py.
- Evaluated thermo-nuclear-code-quality-review style rules and frontmatter schema.
- Evaluated ephemeral scratch file pruning and workspace cleanliness.
- Evaluated 11 hermetic test additions in .github/workflows/portability-offline.yml.

## Appendix B. Alternatives rejected

- Leaving Pi driver cleanup permissive rejected per strict fail-closed contract.
- Ignoring long dashes and mid-sentence colons rejected per style rules.
- Retaining stale non-evidence scratch files rejected per workspace hygiene principle.
- Leaving hermetic safety tests outside CI rejected per regression prevention gate.

## Appendix C. Risks

- Risk of test execution timeout in offline CI. Mitigated by selecting only fast hermetic unit tests.
- Risk of breaking downstream Pi callers. Mitigated by verifying check and model commands still succeed.

## Appendix D. Links and reading list

- Thermonuclear review in skills/thermo-nuclear-code-quality-review/SKILL.md
- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Pi candidate verification in scripts/verify_pi_candidate.py
- Portability offline workflow in .github/workflows/portability-offline.yml
