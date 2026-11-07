# Thermos skills port and verification levers plan

Four PRs port the thermos skills from cursor/plugins and project commands.
The program brings thermo-nuclear review and thermos orchestration into pstack.
Order is thermos-port, project-thermos, reconcile-thermos, multi-harness-gate.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [x] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-thermos-skills-and-verification.md, PR ids in order thermos-port, project-thermos, reconcile-thermos, multi-harness-gate, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [x] thermos-port is first and branches from main.
  - [x] project-thermos after thermos-port.
  - [x] reconcile-thermos after project-thermos.
  - [x] multi-harness-gate after reconcile-thermos.
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

## Port thermos and thermo-nuclear-review skills (thermos-port)

**Depends on.** None.

**Files.**

- [x] Create `skills/thermo-nuclear-review/SKILL.md`.
- [x] Create `skills/thermos/SKILL.md`.
- [x] Create `tests/test_thermos_skills.py`.

**Build.**

- [x] Port thermo-nuclear-review and thermos skills with host-neutral portability.

**You see.**

- [x] Both skills parse valid frontmatter and pass structural tests.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_thermos_skills.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify existing skills pass frontmatter checks. Save `/tmp/swarm-thermos-port/worker-1/trunk.png`. Pass when existing skills validate.
- [x] Lane 2. Thermos skill frontmatter validation probe. Save `/tmp/swarm-thermos-port/worker-2/thermos-fm.png`. Pass when thermos frontmatter validates.
- [x] Lane 3. Thermo-nuclear-review skill frontmatter probe. Save `/tmp/swarm-thermos-port/worker-3/review-fm.png`. Pass when review frontmatter validates.
- [x] Lane 4. Banned long-dash character check probe. Save `/tmp/swarm-thermos-port/worker-4/no-dash.png`. Pass when zero long dashes are found.
- [x] Lane 5. Mid-sentence colon check probe. Save `/tmp/swarm-thermos-port/worker-5/no-colon.png`. Pass when zero mid-sentence colons are found.
- [x] Lane 6. Skill byte size limit probe. Save `/tmp/swarm-thermos-port/worker-6/byte-size.png`. Pass when files remain under 24000 bytes.
- [x] Lane 7. Subagent dispatch instruction probe. Save `/tmp/swarm-thermos-port/worker-7/dispatch.png`. Pass when subagent instructions are present.
- [x] Lane 8. Rubric section headers probe. Save `/tmp/swarm-thermos-port/worker-8/rubric.png`. Pass when required audit rubrics are declared.
- [x] Lane 9. Fresh eyes protocol probe. Save `/tmp/swarm-thermos-port/worker-9/fresh-eyes.png`. Pass when fresh eyes protocol is defined.
- [x] Lane 10. Report synthesis structure probe. Save `/tmp/swarm-thermos-port/worker-10/synthesis.png`. Pass when synthesis structure is defined.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Skill frontmatter parsing duration in milliseconds.
- [x] Probe. Time python3 -c "from scripts.skill_frontmatter import split_frontmatter; split_frontmatter(open('skills/thermos/SKILL.md').read())".
- [x] Baseline. Record trunk duration of frontmatter parsing.
- [x] Rule. Head duration must not exceed trunk duration plus 10 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/thermos-port-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/thermos-port-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Project thermos commands across host manifests (project-thermos)

**Depends on.** thermos-port

**Files.**

- [x] Edit `pstack.package.json`.
- [x] Create `.antigravity-plugin/commands/thermos.toml`.
- [x] Create `.antigravity-plugin/commands/thermo-nuclear-review.toml`.
- [x] Edit `tests/test_project_package.py`.

**Build.**

- [x] Register thermos commands in package descriptor and project to antigravity commands.

**You see.**

- [x] Package projection confirms commands are in sync.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_project_package.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify package descriptor schema. Save `/tmp/swarm-project-thermos/worker-1/trunk.png`. Pass when schema check succeeds.
- [x] Lane 2. Package projection check probe. Save `/tmp/swarm-project-thermos/worker-2/sync.png`. Pass when check exits 0.
- [x] Lane 3. Antigravity commands projection probe. Save `/tmp/swarm-project-thermos/worker-3/commands.png`. Pass when toml files exist.
- [x] Lane 4. Thermos command description probe. Save `/tmp/swarm-project-thermos/worker-4/cmd-desc.png`. Pass when command descriptions match.
- [x] Lane 5. Total commands count audit probe. Save `/tmp/swarm-project-thermos/worker-5/cmd-count.png`. Pass when commands count is 21.
- [x] Lane 6. Package descriptor hash change probe. Save `/tmp/swarm-project-thermos/worker-6/hash.png`. Pass when hash reflects updated descriptor.
- [x] Lane 7. Grok manifest synchronization probe. Save `/tmp/swarm-project-thermos/worker-7/grok.png`. Pass when grok manifest matches.
- [x] Lane 8. Codex manifest synchronization probe. Save `/tmp/swarm-project-thermos/worker-8/codex.png`. Pass when codex manifest matches.
- [x] Lane 9. OMP package synchronization probe. Save `/tmp/swarm-project-thermos/worker-9/omp.png`. Pass when omp package matches.
- [x] Lane 10. OpenCode package synchronization probe. Save `/tmp/swarm-project-thermos/worker-10/opencode.png`. Pass when opencode package matches.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Package projection run time in milliseconds.
- [x] Probe. Time python3 scripts/package_projection.py --check.
- [x] Baseline. Record trunk duration of package projection check.
- [x] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/project-thermos-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/project-thermos-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Reconcile receipts and evidence matrix (reconcile-thermos)

**Depends on.** project-thermos

**Files.**

- [x] Edit `docs/plans/2026-11-07-thermos-skills-and-verification.md`.
- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Refresh durable evidence receipts across all six harnesses and update tracking artifacts.

**You see.**

- [x] Evidence staleness report shows all fresh.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run `uv run pytest tests/test_evidence_durability.py tests/test_verify_portable.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify clean working tree. Save `/tmp/swarm-reconcile-thermos/worker-1/trunk.png`. Pass when git status is clean.
- [x] Lane 2. Evidence durability static receipts probe. Save `/tmp/swarm-reconcile-thermos/worker-2/durability.png`. Pass when receipts match current code.
- [x] Lane 3. Line count audit across python files. Save `/tmp/swarm-reconcile-thermos/worker-3/lines.png`. Pass when all files are under 850 lines.
- [x] Lane 4. Thousand line ceiling audit. Save `/tmp/swarm-reconcile-thermos/worker-4/ceiling.png`. Pass when zero files exceed 1000 lines.
- [x] Lane 5. Dead imports and dangling reference check. Save `/tmp/swarm-reconcile-thermos/worker-5/imports.png`. Pass when imports resolve cleanly.
- [x] Lane 6. Tracking file reconciliation probe. Save `/tmp/swarm-reconcile-thermos/worker-6/todo.png`. Pass when todo.md reflects current epic.
- [x] Lane 7. Git worktree protocol check probe. Save `/tmp/swarm-reconcile-thermos/worker-7/worktree-protocol.png`. Pass when worktree protocol passes.
- [x] Lane 8. Worktree audit script probe. Save `/tmp/swarm-reconcile-thermos/worker-8/worktree-audit.png`. Pass when zero worktrees leak.
- [x] Lane 9. Staleness matrix check probe. Save `/tmp/swarm-reconcile-thermos/worker-9/staleness.png`. Pass when matrix is fresh.
- [x] Lane 10. DSH candidate table scoring probe. Save `/tmp/swarm-reconcile-thermos/worker-10/dsh.png`. Pass when table hash matches candidate.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Freshness check duration in milliseconds.
- [x] Probe. Time python3 scripts/verify_portable.py check-staleness --host all.
- [x] Baseline. Record trunk duration of freshness check.
- [x] Rule. Head duration must not exceed trunk duration plus 200 milliseconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/reconcile-thermos-review-gate.png`.
- [x] Record a 30 second video of the change and save as `/tmp/reconcile-thermos-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Multi-harness verification and gate (multi-harness-gate)

**Depends on.** reconcile-thermos

**Files.**

- [x] Edit `todo.md`.
- [x] Edit `CHANGELOG.md`.

**Build.**

- [x] Verify multi-harness conformance and update documentation.

**You see.**

- [x] Six-host verifier doctor outputs PASS for all declared harnesses.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Run full test suite `uv run pytest`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [x] Lane 1. Regression lane against trunk. Verify full test suite. Save `/tmp/swarm-multi-harness-gate/worker-1/trunk.png`. Pass when test count matches.
- [x] Lane 2. Grok doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-2/grok.png`. Pass when grok doctor exits 0.
- [x] Lane 3. Codex doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-3/codex.png`. Pass when codex doctor exits 0.
- [x] Lane 4. OMP doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-4/omp.png`. Pass when omp doctor exits 0.
- [x] Lane 5. OpenCode doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-5/opencode.png`. Pass when opencode doctor exits 0.
- [x] Lane 6. Antigravity doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-6/antigravity.png`. Pass when antigravity doctor exits 0.
- [x] Lane 7. Droid doctor check probe. Save `/tmp/swarm-multi-harness-gate/worker-7/droid.png`. Pass when droid doctor exits 0.
- [x] Lane 8. Pi candidate check probe. Save `/tmp/swarm-multi-harness-gate/worker-8/pi-check.png`. Pass when pi check exits 0.
- [x] Lane 9. Pi candidate model check probe. Save `/tmp/swarm-multi-harness-gate/worker-9/pi-model.png`. Pass when pi model exits 0.
- [x] Lane 10. Pi candidate offline slice probe. Save `/tmp/swarm-multi-harness-gate/worker-10/pi-slice.png`. Pass when pi slice exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [x] Metric. Full test suite execution duration in seconds.
- [x] Probe. Time uv run pytest.
- [x] Baseline. Record trunk execution duration of full test suite.
- [x] Rule. Head duration must not exceed trunk duration plus 10 seconds.

**Review gate.** The operator reviews before merge.

- [x] Copy lane screenshots into `/tmp/multi-harness-gate-review-gate.png`.
- [x] Record a 30 second video of 6-harness doctor verification and save as `/tmp/multi-harness-gate-review.mp4`.
- [x] Post the screenshot and video in chat for operator review.

**Merge.**

- [x] Root clean verdict at head SHA.
- [x] Squash merge to parent branch.

## Close the program

- [x] Every box above is checked with its evidence.
- [x] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

- Evaluated thermos and thermo-nuclear-review skills in cursor/plugins.
- Confirmed dual review architecture with parallel subagent dispatch.
- Verified test suite execution with 1528 passed tests.

## Appendix B. Alternatives rejected

- Bundling arbitrary third-party extension packages rejected per pstack security model.
- Uncoordinated single-threaded review rejected because parallel dual audit provides higher signal.

## Appendix C. Risks

- Risk of command collision. Mitigated by checking package descriptor commands uniqueness.
- Risk of evidence staleness on skills tree changes. Mitigated by running refresh-static across all hosts.

## Appendix D. Links and reading list

- Thermos skills in skills/thermos/ and skills/thermo-nuclear-review/
- Package projection in scripts/package_projection.py
- Poteto mode playbooks in skills/poteto-mode/playbooks/
