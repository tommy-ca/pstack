# Pi native package and verification levers plan

Four PRs reconcile the Pi candidate package and harden verification tooling.
The program projects native Pi skills and roles without bundling extensions.
Order is pi-package, verify-levers, thermo-quality, multi-harness-gate.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-pi-package-and-verification-levers.md, PR ids in order pi-package, verify-levers, thermo-quality, multi-harness-gate, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] pi-package is first and branches from main.
  - [ ] verify-levers after pi-package.
  - [ ] thermo-quality after verify-levers.
  - [ ] multi-harness-gate after thermo-quality.
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

## Project opt-in Pi native package (pi-package)

**Depends on.** None.

**Files.**

- [ ] Edit `scripts/package_projection.py`.
- [ ] Create `.pi/package.json`.
- [ ] Edit `scripts/project_package.py`.
- [ ] Edit `scripts/verify_pi_candidate.py`.
- [ ] Edit `scripts/prove_pi_vertical_slice.py`.
- [ ] Edit `tests/test_pi_candidate_profile.py`.
- [ ] Edit `tests/test_pi_authorization_contracts.py`.

**Build.**

- [ ] Add `generate_pi_manifest` and `check_pi_package` to `scripts/package_projection.py`.

**You see.**

- [ ] Package projection check confirms `.pi/package.json` sync.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_pi_candidate_profile.py tests/test_pi_authorization_contracts.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify six built-in host package projections. Save `/tmp/swarm-pi-package/worker-1/trunk.png`. Pass when all six built-in manifests match.
- [ ] Lane 2. Package sync check probe. Save `/tmp/swarm-pi-package/worker-2/sync.png`. Pass when package check exits 0.
- [ ] Lane 3. Negative control on bundled extensions. Save `/tmp/swarm-pi-package/worker-3/neg-ext.png`. Pass when bundled extensions are rejected.
- [ ] Lane 4. Negative control on missing skills path. Save `/tmp/swarm-pi-package/worker-4/neg-skills.png`. Pass when missing skills path is rejected.
- [ ] Lane 5. Negative control on missing agents path. Save `/tmp/swarm-pi-package/worker-5/neg-agents.png`. Pass when missing agents path is rejected.
- [ ] Lane 6. Negative control on version mismatch. Save `/tmp/swarm-pi-package/worker-6/neg-version.png`. Pass when mismatched version is rejected.
- [ ] Lane 7. Offline vertical slice verification. Save `/tmp/swarm-pi-package/worker-7/slice.png`. Pass when offline slice verifies package presence.
- [ ] Lane 8. Project package target flag probe. Save `/tmp/swarm-pi-package/worker-8/project-target.png`. Pass when host pi target projects cleanly.
- [ ] Lane 9. Package descriptor schema validation. Save `/tmp/swarm-pi-package/worker-9/descriptor.png`. Pass when package descriptor validates.
- [ ] Lane 10. Settings discovery parity probe. Save `/tmp/swarm-pi-package/worker-10/settings.png`. Pass when settings resolution aligns with package.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Package generation run time in milliseconds.
- [ ] Probe. Time python3 scripts/package_projection.py --project.
- [ ] Baseline. Record trunk duration of package projection.
- [ ] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/pi-package-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/pi-package-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Extend verification skills and scaffolders (verify-levers)

**Depends on.** pi-package

**Files.**

- [ ] Edit `scripts/scaffold_verification_skill.py`.
- [ ] Edit `tests/test_scaffold_verification_skill.py`.
- [ ] Edit `skills/create-verification-skill/SKILL.md`.
- [ ] Edit `skills/maintain-verification-skill/SKILL.md`.
- [ ] Edit `.pi/skills/verify-pi-pstack/SKILL.md`.
- [ ] Edit `.pi/skills/verify-pi-pstack-formal/SKILL.md`.

**Build.**

- [ ] Allow candidate hosts in `scripts/scaffold_verification_skill.py` host argument.

**You see.**

- [ ] Structural validation passes for candidate skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_scaffold_verification_skill.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Built-in host scaffolding check. Save `/tmp/swarm-verify-levers/worker-1/trunk.png`. Pass when built-in host output matches.
- [ ] Lane 2. Scaffold skill dry-run for pi host. Save `/tmp/swarm-verify-levers/worker-2/pi-scaffold.png`. Pass when pi host resolves to .pi/skills.
- [ ] Lane 3. Candidate skills directory resolution probe. Save `/tmp/swarm-verify-levers/worker-3/candidate-dir.png`. Pass when candidate directories parse.
- [ ] Lane 4. Audit mode check across skills. Save `/tmp/swarm-verify-levers/worker-4/audit.png`. Pass when audit validates all skills.
- [ ] Lane 5. Driver script validation probe. Save `/tmp/swarm-verify-levers/worker-5/driver.png`. Pass when driver script exists and is executable.
- [ ] Lane 6. Feature map heading validation probe. Save `/tmp/swarm-verify-levers/worker-6/feature-h2.png`. Pass when required H2 headings exist.
- [ ] Lane 7. App naming validation probe. Save `/tmp/swarm-verify-levers/worker-7/naming.png`. Pass when kebab-case naming is enforced.
- [ ] Lane 8. Skill byte size limit probe. Save `/tmp/swarm-verify-levers/worker-8/byte-limit.png`. Pass when skill bodies stay under 24000 bytes.
- [ ] Lane 9. Formal verification mode probe. Save `/tmp/swarm-verify-levers/worker-9/formal-mode.png`. Pass when formal mode generates formal map.
- [ ] Lane 10. Formal driver model checking probe. Save `/tmp/swarm-verify-levers/worker-10/formal-driver.png`. Pass when driver includes model invocation.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scaffolder check run time in milliseconds.
- [ ] Probe. Time python3 scripts/scaffold_verification_skill.py --check --target-dir .pi/skills/verify-pi-pstack.
- [ ] Baseline. Record trunk duration of scaffolder check.
- [ ] Rule. Head duration must not exceed trunk duration plus 50 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verify-levers-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/verify-levers-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Complete thermo-nuclear quality audit and judo (thermo-quality)

**Depends on.** verify-levers

**Files.**

- [ ] Edit `openspec/changes/2026-11-07-pi-extension-package-proof/tasks.md`.
- [ ] Edit `docs/plans/2026-11-07-pi-package-and-verification-levers.md`.
- [ ] Edit `todo.md`.

**Build.**

- [ ] Record Thermo-Nuclear review findings and update project tracking.

**You see.**

- [ ] OpenSpec validation confirms change is valid.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_openspec_change.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify clean working tree. Save `/tmp/swarm-thermo-quality/worker-1/trunk.png`. Pass when git status is clean.
- [ ] Lane 2. OpenSpec change strict validation probe. Save `/tmp/swarm-thermo-quality/worker-2/openspec.png`. Pass when change is valid.
- [ ] Lane 3. Line count audit across python files. Save `/tmp/swarm-thermo-quality/worker-3/lines.png`. Pass when all files are under 850 lines.
- [ ] Lane 4. Thousand line ceiling audit. Save `/tmp/swarm-thermo-quality/worker-4/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 5. Dead imports and dangling reference check. Save `/tmp/swarm-thermo-quality/worker-5/imports.png`. Pass when imports resolve cleanly.
- [ ] Lane 6. Tracking file reconciliation probe. Save `/tmp/swarm-thermo-quality/worker-6/todo.png`. Pass when todo.md reflects current epic.
- [ ] Lane 7. Git worktree protocol check probe. Save `/tmp/swarm-thermo-quality/worker-7/worktree-protocol.png`. Pass when worktree protocol passes.
- [ ] Lane 8. Worktree audit script probe. Save `/tmp/swarm-thermo-quality/worker-8/worktree-audit.png`. Pass when zero worktrees leak.
- [ ] Lane 9. Detail review files presence probe. Save `/tmp/swarm-thermo-quality/worker-9/detail-files.png`. Pass when detail files exist.
- [ ] Lane 10. Summary review file presence probe. Save `/tmp/swarm-thermo-quality/worker-10/summary-file.png`. Pass when summary file exists.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. OpenSpec validation duration in milliseconds.
- [ ] Probe. Time openspec validate 2026-11-07-pi-extension-package-proof --type change --strict.
- [ ] Baseline. Record trunk duration of openspec validation.
- [ ] Rule. Head duration must not exceed trunk duration plus 500 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/thermo-quality-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/thermo-quality-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Multi-harness verification and gate (multi-harness-gate)

**Depends on.** thermo-quality

**Files.**

- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Verify multi-harness conformance and update documentation.

**You see.**

- [ ] Six-host verifier doctor outputs PASS for all declared harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run full test suite `uv run pytest`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify full test suite. Save `/tmp/swarm-multi-harness-gate/worker-1/trunk.png`. Pass when test count matches.
- [ ] Lane 2. Grok doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-2/grok.png`. Pass when grok doctor exits 0.
- [ ] Lane 3. Codex doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-3/codex.png`. Pass when codex doctor exits 0.
- [ ] Lane 4. OMP doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-4/omp.png`. Pass when omp doctor exits 0.
- [ ] Lane 5. OpenCode doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-5/opencode.png`. Pass when opencode doctor exits 0.
- [ ] Lane 6. Antigravity doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-6/antigravity.png`. Pass when antigravity doctor exits 0.
- [ ] Lane 7. Droid doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-7/droid.png`. Pass when droid doctor exits 0.
- [ ] Lane 8. Pi candidate check probe. Save `/tmp/swarm-multi-harness-gate/worker-8/pi-check.png`. Pass when pi check exits 0.
- [ ] Lane 9. Pi candidate model check probe. Save `/tmp/swarm-multi-harness-gate/worker-9/pi-model.png`. Pass when pi model exits 0.
- [ ] Lane 10. Pi candidate offline slice probe. Save `/tmp/swarm-multi-harness-gate/worker-10/pi-slice.png`. Pass when pi slice exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Full test suite execution duration in seconds.
- [ ] Probe. Time uv run pytest.
- [ ] Baseline. Record trunk execution duration of full test suite.
- [ ] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/multi-harness-gate-review-gate.png`.
- [ ] Record a 30 second video of 6-harness doctor verification and save as `/tmp/multi-harness-gate-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated Pi candidate package projection in .pi/package.json.
- Confirmed omission of third-party executable extensions from package manifest.
- Verified candidate host scaffolding resolution for .pi/skills.
- Verified test suite execution with 1521 passed tests.

## Appendix B. Alternatives rejected

- Bundling third-party executable extensions rejected because it introduces an unreviewed attack surface.
- Dynamic runtime loader hacks rejected because direct static declarations are simpler and more robust.
- Prematurely promoting candidate host to built-in rejected because native live runtime proof is pending.

## Appendix C. Risks

- Risk of breaking existing package projection checks. Mitigated by verifying six built-in host projections stay untouched.
- Risk of false runtime PASS. Mitigated by enforcing BLOCKED status for unobserved Pi runtime.
- Risk of file size sprawl. Mitigated by keeping all files under 850 lines.

## Appendix D. Links and reading list

- OpenSpec proposal in openspec/changes/2026-11-07-pi-extension-package-proof/
- Pi candidate profile in profiles/pstack-pi.json
- Scaffolding lever in scripts/scaffold_verification_skill.py
- Poteto mode playbooks in skills/poteto-mode/playbooks/
