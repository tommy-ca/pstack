# Schema flattening and clutter pruning plan

Four PRs flatten schemas directory from portability subfolder to root schemas, prune stale cache clutter, update verification skill templates, and qualify the 6-host verification matrix.
Order is flatten-schemas, prune-clutter, verification-tools, gate-close-1116.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-08-schema-flattening-and-clutter-pruning.md, PR ids in order flatten-schemas, prune-clutter, verification-tools, gate-close-1116, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] flatten-schemas is first and branches from main.
  - [ ] prune-clutter after flatten-schemas.
  - [ ] verification-tools after prune-clutter.
  - [ ] gate-close-1116 after verification-tools.
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
- [ ] Execute commands and verify side effects.
- [ ] Save output logs and screenshots for the report.

## Flatten schemas portability directory to schemas (flatten-schemas)

**Depends on.** None.

**Files.**

- [x] Move `schemas/portability/*.schema.json` to `schemas/`.
- [x] Edit `pstack.package.json`.
- [x] Edit `scripts/model_role_policy.py`.
- [x] Edit `scripts/surface_revisions.py`.
- [x] Edit `tests/test_portability_schemas.py`.
- [x] Edit `tests/test_host_identity.py`.
- [x] Edit `tests/test_model_role_schema.py`.
- [x] Edit `tests/test_model_role_profiles.py`.
- [x] Edit `tests/test_surface_cache.py`.
- [x] Edit `tests/test_scan_host_boundary.py`.
- [x] Edit `tests/model_role_helpers.py`.
- [x] Edit `.audit/evidence/*.json`.

**Build.**

- [x] Move all 13 schema files from schemas/portability to schemas.
- [x] Remove empty directory schemas/portability.
- [x] Update schema IDs to remove portability path segment.
- [x] Update import and filesystem references across scripts and tests.

**You see.**

- [x] Schemas reside directly under schemas without portability nesting.
- [x] All schema test assertions pass cleanly.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_portability_schemas.py tests/test_host_identity.py tests/test_model_role_schema.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Schema load probe. Save `/tmp/swarm-flatten-schemas/worker-1/schemas.png`. Pass when schema validation passes.
- [x] Lane 2. Host identity probe. Save `/tmp/swarm-flatten-schemas/worker-2/host-id.png`. Pass when test_host_identity passes.
- [x] Lane 3. Model role schema probe. Save `/tmp/swarm-flatten-schemas/worker-3/model-role.png`. Pass when model role tests pass.
- [x] Lane 4. Surface cache probe. Save `/tmp/swarm-flatten-schemas/worker-4/surface-cache.png`. Pass when surface cache passes.
- [x] Lane 5. Boundary scan probe. Save `/tmp/swarm-flatten-schemas/worker-5/boundary.png`. Pass when scan_host_boundary passes.
- [x] Lane 6. Evidence durability probe. Save `/tmp/swarm-flatten-schemas/worker-6/durability.png`. Pass when check-evidence passes.
- [x] Lane 7. Evidence staleness probe. Save `/tmp/swarm-flatten-schemas/worker-7/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 8. Package projection probe. Save `/tmp/swarm-flatten-schemas/worker-8/projection.png`. Pass when package_projection check passes.
- [x] Lane 9. Confinement check probe. Save `/tmp/swarm-flatten-schemas/worker-9/confinement.png`. Pass when worktrees are confined.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-flatten-schemas/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Schema test suite duration in seconds.
- [x] Probe. Time uv run pytest tests/test_portability_schemas.py.
- [x] Baseline. Record trunk duration of schema tests.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/flatten-schemas-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/flatten-schemas-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Prune stale cache clutter and enforce style rules (prune-clutter)

**Depends on.** flatten-schemas

**Files.**

- [x] Delete stale `.atl/` directory.
- [x] Edit `.gitignore`.
- [x] Edit documentation referencing old schema paths.

**Build.**

- [x] Remove obsolete cache artifacts.
- [x] Enforce clean ignore rules for workspace scratch directories.
- [x] Cleanse references to old schema paths across docs and guides.
- [x] Confirm zero long dashes across the repository.

**You see.**

- [x] Clean working tree with zero untracked scratch files.
- [x] Repository boundary scanner reports zero violations.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `python3 scripts/scan_host_boundary.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Boundary scan probe. Save `/tmp/swarm-prune-clutter/worker-1/boundary.png`. Pass when scan_host_boundary passes.
- [x] Lane 2. Git status probe. Save `/tmp/swarm-prune-clutter/worker-2/status.png`. Pass when git status is clean.
- [x] Lane 3. Worktree protocol probe. Save `/tmp/swarm-prune-clutter/worker-3/confinement.png`. Pass when worktrees are confined.
- [x] Lane 4. Package projection probe. Save `/tmp/swarm-prune-clutter/worker-4/projection.png`. Pass when package_projection check passes.
- [x] Lane 5. Evidence staleness probe. Save `/tmp/swarm-prune-clutter/worker-5/staleness.png`. Pass when check-staleness reports all fresh.
- [x] Lane 6. Evidence durability probe. Save `/tmp/swarm-prune-clutter/worker-6/durability.png`. Pass when check-evidence passes.
- [x] Lane 7. Thermos skill frontmatter probe. Save `/tmp/swarm-prune-clutter/worker-7/thermo.png`. Pass when test_thermos_skills passes.
- [x] Lane 8. Offline checks selection probe. Save `/tmp/swarm-prune-clutter/worker-8/select.png`. Pass when test_select_checks passes.
- [x] Lane 9. Line ceiling probe. Save `/tmp/swarm-prune-clutter/worker-9/ceiling.png`. Pass when zero Python files exceed 1000 lines.
- [x] Lane 10. Status hygiene probe. Save `/tmp/swarm-prune-clutter/worker-10/status-clean.png`. Pass when working tree has zero untracked files.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Boundary scan execution duration in seconds.
- [x] Probe. Time python3 scripts/scan_host_boundary.py.
- [x] Baseline. Record trunk duration of boundary scan.
- [x] Rule. Head duration must not exceed trunk duration plus 2 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/prune-clutter-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/prune-clutter-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Update verification skill templates and audit drivers (verification-tools)

**Depends on.** prune-clutter

**Files.**

- [ ] Edit `scripts/verification_skill_templates.py`.
- [ ] Edit `scripts/scaffold_verification_skill.py`.
- [ ] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [ ] Update verification skill templates to reference flattened schemas.
- [ ] Ensure scaffold verification tests validate updated schema locations.
- [ ] Audit all ten verification skill drivers across all hosts.

**You see.**

- [ ] Verification scaffold audit reports 10 passed and 0 failed.
- [ ] All verification skill drivers execute successfully.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `python3 scripts/scaffold_verification_skill.py --audit --json`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Grok driver probe. Save `/tmp/swarm-verification-tools/worker-1/grok.png`. Pass when Grok driver passes.
- [ ] Lane 2. Codex driver probe. Save `/tmp/swarm-verification-tools/worker-2/codex.png`. Pass when Codex driver passes.
- [ ] Lane 3. Codex LLM wiki driver probe. Save `/tmp/swarm-verification-tools/worker-3/wiki.png`. Pass when LLM wiki driver passes.
- [ ] Lane 4. OMP driver probe. Save `/tmp/swarm-verification-tools/worker-4/omp.png`. Pass when OMP driver passes.
- [ ] Lane 5. OpenCode driver probe. Save `/tmp/swarm-verification-tools/worker-5/opencode.png`. Pass when OpenCode driver passes.
- [ ] Lane 6. Antigravity driver probe. Save `/tmp/swarm-verification-tools/worker-6/antigravity.png`. Pass when Antigravity driver passes.
- [ ] Lane 7. Droid driver probe. Save `/tmp/swarm-verification-tools/worker-7/droid.png`. Pass when Droid driver passes.
- [ ] Lane 8. Pi driver probe. Save `/tmp/swarm-verification-tools/worker-8/pi.png`. Pass when Pi driver passes.
- [ ] Lane 9. Pi formal driver probe. Save `/tmp/swarm-verification-tools/worker-9/pi-formal.png`. Pass when Pi formal driver passes.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-verification-tools/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scaffold audit duration in seconds.
- [ ] Probe. Time python3 scripts/scaffold_verification_skill.py --audit --json.
- [ ] Baseline. Record trunk duration of scaffold audit.
- [ ] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verification-tools-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/verification-tools-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Qualify 6-harness verification matrix and close Epic 1116 (gate-close-1116)

**Depends on.** verification-tools

**Files.**

- [ ] Edit `CHANGELOG.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `docs/plans/2026-11-08-schema-flattening-and-clutter-pruning.md`.

**Build.**

- [ ] Update changelog with Epic 1116 entries.
- [ ] Update todo with Epic 1116 units.
- [ ] Mark all checkboxes in multi-phase plan.
- [ ] Verify plan schema with check-plan script.

**You see.**

- [ ] Complete reconciliation across ledger, todo, and plan.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `bun skills/poteto-mode/scripts/check-plan.mjs docs/plans/2026-11-08-schema-flattening-and-clutter-pruning.md`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Confinement check probe. Save `/tmp/swarm-gate-close-1116/worker-1/confinement.png`. Pass when worktrees are confined.
- [ ] Lane 2. Package projection probe. Save `/tmp/swarm-gate-close-1116/worker-2/projection.png`. Pass when package_projection check passes.
- [ ] Lane 3. Verification skills audit probe. Save `/tmp/swarm-gate-close-1116/worker-3/audit.png`. Pass when 10 skills pass.
- [ ] Lane 4. Evidence staleness probe. Save `/tmp/swarm-gate-close-1116/worker-4/staleness.png`. Pass when check-staleness reports all fresh.
- [ ] Lane 5. Evidence durability probe. Save `/tmp/swarm-gate-close-1116/worker-5/evidence.png`. Pass when check-evidence passes.
- [ ] Lane 6. Portable doctor probe. Save `/tmp/swarm-gate-close-1116/worker-6/doctor.png`. Pass when 6-harness matrix verdict is PASS.
- [ ] Lane 7. Poteto script tests probe. Save `/tmp/swarm-gate-close-1116/worker-7/poteto-tests.png`. Pass when 102 tests pass.
- [ ] Lane 8. Python line ceiling probe. Save `/tmp/swarm-gate-close-1116/worker-8/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 9. Ephemeral prune probe. Save `/tmp/swarm-gate-close-1116/worker-9/prune.png`. Pass when prune-ephemeral exits 0.
- [ ] Lane 10. Status hygiene probe. Save `/tmp/swarm-gate-close-1116/worker-10/status.png`. Pass when git status is clean.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full verification gate duration in seconds.
- [ ] Probe. Time python3 scripts/verify_portable.py doctor --host all.
- [ ] Baseline. Record trunk duration of doctor across all hosts.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/gate-close-1116-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/gate-close-1116-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every PR merged to trunk in bottom-up order.
- [ ] Every box in this plan checked with its evidence.
- [ ] Post final status message to operator.

## Appendix A. Prototype evidence

- Evaluated schema movement from schemas/portability to schemas.
- Evaluated relative ref resolution across schemas in jsonschema Draft 2020-12.
- Evaluated stale cache directory pruning and ignore rules.
- Evaluated verification skill drivers and template generation.

## Appendix B. Alternatives rejected

- Retaining schemas/portability nesting rejected per KISS and DRY principles.
- Retaining stale cache directories rejected per workspace hygiene principle.
- Modifying verification skill interfaces rejected to preserve backwards compatibility.
- Skipping multi-harness doctor matrix rejected per strict verification protocol.

## Appendix C. Risks

- Risk of schema URI mismatch. Mitigated by updating all schemas and test references together.
- Risk of evidence receipt hash drift. Mitigated by updating package driver revisions in static receipts.

## Appendix D. Links and reading list

- Poteto mode check-plan in skills/poteto-mode/scripts/check-plan.mjs
- Portable verifier in scripts/portable_verifier.py
- Package projection in scripts/package_projection.py
- Verification skill templates in scripts/verification_skill_templates.py
