# Upstream 0.15.36 sync and verification tooling plan

Four PRs bring this repository up to official Cursor PStack 0.15.36.
The program enforces host portability while absorbing canonical skills.
Order is orch-skills, statechart-ketchup, verify-levers, upstream-sync.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-upstream-0-15-36-sync-and-verification.md, PR ids in order orch-skills, statechart-ketchup, verify-levers, upstream-sync, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] orch-skills is first and branches from main.
  - [ ] statechart-ketchup after orch-skills.
  - [ ] verify-levers after statechart-ketchup.
  - [ ] upstream-sync after verify-levers.
- [ ] Hold the file boundaries strictly per task files list.
- [ ] Hold the review gate for every PR before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`.
- [ ] Open each PR ready with `gh pr create --base <parent-branch>`.
- [ ] Run unslop before each commit and no-comments before review.
- [ ] Rebase onto current trunk before babysit and again before merge.

### Verdict and merge, for every PR

- [ ] A full swarm runs once at the code-ready head.
- [ ] Clean only when every lane is PASS.
- [ ] Merge the verified run bottom-up with squash commits.

### Boot recipe, for every live lane

Each live lane runs in its own isolation worktree child at the PR head.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Run python3 scripts/verify_portable.py doctor --host antigravity.
- [ ] Run pytest on the targeted test module.
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return the paths with the report.

## Port agentic orchestrate and skill parity (orch-skills)

**Depends on.** None.

**Files.**

- [ ] Edit `skills/poteto-mode/playbooks/orchestrate.md`.
- [ ] Delete `skills/poteto-mode/scripts/orch/orch.ts`.
- [ ] Delete `skills/poteto-mode/scripts/orch/store.ts`.
- [ ] Delete `skills/poteto-mode/scripts/orch/orch.test.ts`.
- [ ] Edit `skills/arena/SKILL.md`.
- [ ] Edit `skills/interrogate/SKILL.md`.
- [ ] Edit `skills/swarm/SKILL.md`.
- [ ] Edit `skills/poteto-mode/scripts/watch-pr/watch-pr`.
- [ ] Edit `skills/poteto-mode/scripts/worktree-audit.sh`.

**Build.**

- [ ] Make Orchestrate agentic by removing legacy orch CLI calls and porting upstream skill enhancements.

**You see.**

- [ ] Orchestrate playbook describes agentic execution and legacy orch scripts are absent.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `pytest tests/test_shipping_safety.py tests/test_verify_harness.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run worktree audit and verify harness on trunk and head. Save `/tmp/swarm-orch-skills/worker-1/audit.png`. Pass when both exit 0.
- [ ] Lane 2. Swarm prompt verification. Save `/tmp/swarm-orch-skills/worker-2/swarm.png`. Pass when swarm skill syntax validates.
- [ ] Lane 3. Interrogate skill validation. Save `/tmp/swarm-orch-skills/worker-3/interrogate.png`. Pass when interrogate skill contains no obsolete references.
- [ ] Lane 4. Arena cross-model guidance check. Save `/tmp/swarm-orch-skills/worker-4/arena.png`. Pass when arena skill contains canonical judge fallbacks.
- [ ] Lane 5. Watch-pr sleep deadline probe. Save `/tmp/swarm-orch-skills/worker-5/watch-pr.png`. Pass when watch-pr caps sleep at deadline.
- [ ] Lane 6. Worktree-audit stat mtime probe. Save `/tmp/swarm-orch-skills/worker-6/worktree-audit.png`. Pass when worktree-audit parses GNU stat output cleanly.
- [ ] Lane 7. Orchestrate playbook structural check. Save `/tmp/swarm-orch-skills/worker-7/orchestrate.png`. Pass when orchestrate playbook references no orch script.
- [ ] Lane 8. Leftover scanner run. Save `/tmp/swarm-orch-skills/worker-8/leftovers.png`. Pass when leftover scanner reports clean status.
- [ ] Lane 9. Host boundary scanner run. Save `/tmp/swarm-orch-skills/worker-9/boundary.png`. Pass when scan_host_boundary.py exits 0.
- [ ] Lane 10. Portable verifier doctor on Grok. Save `/tmp/swarm-orch-skills/worker-10/grok-doctor.png`. Pass when grok doctor exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Worktree audit run time in seconds.
- [ ] Probe. Time execution of skills/poteto-mode/scripts/worktree-audit.sh.
- [ ] Baseline. Record trunk duration of worktree audit script.
- [ ] Rule. Head duration must not exceed trunk duration plus 1 second.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/orch-skills-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/orch-skills-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Ingest statechart and ketchup skills (statechart-ketchup)

**Depends on.** orch-skills

**Files.**

- [ ] Create `skills/statechart/SKILL.md`.
- [ ] Create `skills/statechart/scripts/render.ts`.
- [ ] Create `skills/statechart/scripts/compiler.ts`.
- [ ] Create `skills/ketchup-video/SKILL.md`.

**Build.**

- [ ] Ingest statechart skill and ketchup-video skill while excluding 356 static fixtures.

**You see.**

- [ ] `skills/statechart/SKILL.md` and `skills/ketchup-video/SKILL.md` register cleanly with zero corpus bloat.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `pytest tests/test_skill_frontmatter.py tests/test_refresh_hygiene.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify skill frontmatter on trunk and head. Save `/tmp/swarm-statechart/worker-1/frontmatter.png`. Pass when both exit 0.
- [ ] Lane 2. Statechart frontmatter check. Save `/tmp/swarm-statechart/worker-2/statechart-fm.png`. Pass when statechart frontmatter passes validation.
- [ ] Lane 3. Ketchup-video frontmatter check. Save `/tmp/swarm-statechart/worker-3/ketchup-fm.png`. Pass when ketchup-video frontmatter passes validation.
- [ ] Lane 4. Corpus exclusion check. Save `/tmp/swarm-statechart/worker-4/corpus-check.png`. Pass when corpus test folder is absent.
- [ ] Lane 5. Skill length validation. Save `/tmp/swarm-statechart/worker-5/length-check.png`. Pass when skill bodies remain under 24000 bytes.
- [ ] Lane 6. Leftover scanner check. Save `/tmp/swarm-statechart/worker-6/leftovers.png`. Pass when leftover scanner exits 0.
- [ ] Lane 7. Antigravity plugin manifest validation. Save `/tmp/swarm-statechart/worker-7/manifest.png`. Pass when sync_antigravity_plugin check passes.
- [ ] Lane 8. Codex skill list check. Save `/tmp/swarm-statechart/worker-8/codex.png`. Pass when codex package projection lists new skills.
- [ ] Lane 9. OMP skill list check. Save `/tmp/swarm-statechart/worker-9/omp.png`. Pass when omp package projection lists new skills.
- [ ] Lane 10. Portable verifier doctor on Antigravity. Save `/tmp/swarm-statechart/worker-10/doctor.png`. Pass when antigravity doctor exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Skill frontmatter check duration in milliseconds.
- [ ] Probe. Time pytest tests/test_skill_frontmatter.py.
- [ ] Baseline. Record trunk execution time for frontmatter tests.
- [ ] Rule. Head execution time must stay within 500 milliseconds of baseline.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/statechart-review-gate.png`.
- [ ] Record a 30 second video of the statechart skill review and save as `/tmp/statechart-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Upgrade verification skills and scaffolders (verify-levers)

**Depends on.** statechart-ketchup

**Files.**

- [ ] Edit `skills/create-formal-verification-skill/SKILL.md`.
- [ ] Edit `skills/maintain-formal-verification-skill/SKILL.md`.
- [ ] Edit `scripts/scaffold_verification_skill.py`.
- [ ] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [ ] Integrate formal verification skills with statechart visualization and extend scaffolder templates.

**You see.**

- [ ] Formal verification skills instruct agents to visualize models with statechart and driver generator produces clean templates.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `pytest tests/test_scaffold_verification_skill.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run test_scaffold_verification_skill on trunk and head. Save `/tmp/swarm-verify/worker-1/scaffold-tests.png`. Pass when both exit 0.
- [ ] Lane 2. Scaffold formal verification skill dry-run. Save `/tmp/swarm-verify/worker-2/scaffold-formal.png`. Pass when scaffold creates valid formal verify skill structure.
- [ ] Lane 3. Scaffold standard verification skill dry-run. Save `/tmp/swarm-verify/worker-3/scaffold-std.png`. Pass when standard verification skill template validates.
- [ ] Lane 4. Driver template statechart integration check. Save `/tmp/swarm-verify/worker-4/driver-statechart.png`. Pass when driver script includes statechart rendering hooks.
- [ ] Lane 5. Create-formal-verification-skill text validation. Save `/tmp/swarm-verify/worker-5/create-formal.png`. Pass when skill mentions statechart visualization.
- [ ] Lane 6. Maintain-formal-verification-skill text validation. Save `/tmp/swarm-verify/worker-6/maintain-formal.png`. Pass when skill mentions statechart maintenance.
- [ ] Lane 7. Scaffolder Tier 1 check validation. Save `/tmp/swarm-verify/worker-7/tier1-check.png`. Pass when scaffold_verification_skill check passes on all fixtures.
- [ ] Lane 8. Host boundary scanner run. Save `/tmp/swarm-verify/worker-8/boundary.png`. Pass when scan_host_boundary.py exits 0.
- [ ] Lane 9. Portable verifier doctor on Codex. Save `/tmp/swarm-verify/worker-9/codex-doctor.png`. Pass when codex doctor exits 0.
- [ ] Lane 10. Portable verifier doctor on Antigravity. Save `/tmp/swarm-verify/worker-10/agy-doctor.png`. Pass when antigravity doctor exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scaffolder execution time for 10 mock skills in milliseconds.
- [ ] Probe. Time python3 scripts/scaffold_verification_skill.py --formal --app demo --dry-run across 10 iterations.
- [ ] Baseline. Record trunk duration of dry-run scaffolding.
- [ ] Rule. Head execution time must not exceed baseline plus 100 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verify-levers-review-gate.png`.
- [ ] Record a 30 second video of scaffolded driver output and save as `/tmp/verify-levers-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Advance upstream pin and canonical sync (upstream-sync)

**Depends on.** verify-levers

**Files.**

- [ ] Edit `UPSTREAM`.
- [ ] Edit `pstack.package.json`.
- [ ] Edit `plugin.json`.
- [ ] Edit `scripts/sync_from_upstream.py`.
- [ ] Edit `scripts/canonical_index.py`.
- [ ] Edit `profiles/antigravity.json`.

**Build.**

- [ ] Advance UPSTREAM pin to c742dd61 and package version to 0.15.36 while refreshing canonical indices.

**You see.**

- [ ] `UPSTREAM` records tree 4719e1c4b4c43bac85d4206a8b41dd2899769c1c and package manifests report version 0.15.36.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `pytest tests/test_canonical_index.py tests/test_refresh_hygiene.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run test_canonical_index on trunk and head. Save `/tmp/swarm-sync/worker-1/canonical.png`. Pass when both exit 0.
- [ ] Lane 2. Upstream pin validation. Save `/tmp/swarm-sync/worker-2/pin.png`. Pass when sync_from_upstream.py --pin matches UPSTREAM tree.
- [ ] Lane 3. Package manifest version check. Save `/tmp/swarm-sync/worker-3/version.png`. Pass when pstack.package.json version matches 0.15.36.
- [ ] Lane 4. Plugin manifest check. Save `/tmp/swarm-sync/worker-4/plugin.png`. Pass when plugin.json version matches 0.15.36.
- [ ] Lane 5. Canonical index freshness check. Save `/tmp/swarm-sync/worker-5/index.png`. Pass when canonical_index.py reports 0 unclassified skills.
- [ ] Lane 6. Antigravity plugin synchronization check. Save `/tmp/swarm-sync/worker-6/agy-sync.png`. Pass when sync_antigravity_plugin.py --check exits 0.
- [ ] Lane 7. Host boundary scan across all profiles. Save `/tmp/swarm-sync/worker-7/boundary.png`. Pass when scan_host_boundary.py exits 0.
- [ ] Lane 8. Full 6-harness doctor matrix. Save `/tmp/swarm-sync/worker-8/doctor-all.png`. Pass when verify_portable.py doctor --host all exits 0.
- [ ] Lane 9. Full pytest test suite execution. Save `/tmp/swarm-sync/worker-9/full-suite.png`. Pass when all unit tests pass.
- [ ] Lane 10. Package lifecycle dry-run proof. Save `/tmp/swarm-sync/worker-10/lifecycle.png`. Pass when package_lifecycle.py check exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Canonical index verification duration in milliseconds.
- [ ] Probe. Time python3 scripts/canonical_index.py.
- [ ] Baseline. Record trunk execution time of canonical index check.
- [ ] Rule. Head execution time must stay within 200 milliseconds of baseline.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/upstream-sync-review-gate.png`.
- [ ] Record a 30 second video of 6-harness doctor verification and save as `/tmp/upstream-sync-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated upstream commit c742dd61706fbacc1b95f1a20b7b988cf096ce6c in local checkout at .worktrees/upstream-cursor-plugins.
- Confirmed removal of orch CLI scripts from official pstack.
- Confirmed statechart compiler and Pele renderer operate with Mermaid outputs.
- Proved 356 static corpus fixtures can be safely excluded without affecting skill discovery or runtime execution.

## Appendix B. Alternatives rejected

- Copying all 356 static statechart corpus fixtures rejected because it bloats git repository with 20000 lines of dead text.
- Retaining legacy scripts/orch CLI wrappers rejected because upstream Orchestrate is fully agentic and caller-free.
- Inventing proprietary scheduler primitives rejected because each host provides native schedule capabilities.

## Appendix C. Risks

- Risk of breaking existing custom workflows relying on orch CLI. Mitigated by verifying no internal scripts invoke orch CLI.
- Risk of Antigravity plugin size truncation. Mitigated by verifying every skill body stays strictly under 24000 bytes.
- Risk of multi-harness profile drift. Mitigated by running verify_portable doctor across all 6 harnesses.

## Appendix D. Links and reading list

- PStack upstream commit c742dd61706fbacc1b95f1a20b7b988cf096ce6c
- Upstream 0.15.36 audit in docs/research/upstream-pstack-0.15.36-audit-2026-10-31.md
- Poteto mode playbooks in skills/poteto-mode/playbooks/
- Scaffolding lever in scripts/scaffold_verification_skill.py
