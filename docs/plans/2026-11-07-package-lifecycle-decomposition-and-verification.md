# Package lifecycle decomposition and verification levers plan

Four PRs decompose package lifecycle logic and harden verification tooling.
The program extracts installation staging out of package lifecycle into a dedicated module.
Order is package-staging, verification-tools, quality-reconcile, multi-harness-gate.
Each unit proves itself through unit, live, and perf verification.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR section has a unique parenthesized identifier and a `Depends on.` list naming direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The root merges the verified run bottom-up. All four PRs stop at merge-ready for the operator.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on an explicit go.
- [ ] On that go, persist the plan path on disk with this exact text. "docs/plans/2026-11-07-package-lifecycle-decomposition-and-verification.md, PR ids in order package-staging, verification-tools, quality-reconcile, multi-harness-gate, the verification rule, the root merges, and the done condition is every box checked with its evidence."
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
  - [ ] package-staging is first and branches from main.
  - [ ] verification-tools after package-staging.
  - [ ] quality-reconcile after verification-tools.
  - [ ] multi-harness-gate after quality-reconcile.
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

## Decompose package lifecycle staging logic (package-staging)

**Depends on.** None.

**Files.**

- [ ] Create `scripts/package_install_staging.py`.
- [ ] Edit `scripts/package_lifecycle.py`.
- [ ] Edit `scripts/surface_revisions.py`.
- [ ] Edit `tests/test_package_lifecycle.py`.
- [ ] Edit `tests/test_package_lifecycle_safety.py`.

**Build.**

- [ ] Extract host installation staging and file copying from package lifecycle into package install staging.

**You see.**

- [ ] Package lifecycle line count is reduced under 500 lines.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_package_lifecycle.py tests/test_package_lifecycle_safety.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify package installation on grok. Save `/tmp/swarm-package-staging/worker-1/grok.png`. Pass when grok install succeeds.
- [ ] Lane 2. Package install on codex probe. Save `/tmp/swarm-package-staging/worker-2/codex.png`. Pass when codex install succeeds.
- [ ] Lane 3. Package install on omp probe. Save `/tmp/swarm-package-staging/worker-3/omp.png`. Pass when omp install succeeds.
- [ ] Lane 4. Package install on opencode probe. Save `/tmp/swarm-package-staging/worker-4/opencode.png`. Pass when opencode install succeeds.
- [ ] Lane 5. Package install on antigravity probe. Save `/tmp/swarm-package-staging/worker-5/antigravity.png`. Pass when antigravity install succeeds.
- [ ] Lane 6. Package install on droid probe. Save `/tmp/swarm-package-staging/worker-6/droid.png`. Pass when droid install succeeds.
- [ ] Lane 7. Safe scan plugin tree without following symlink loops probe. Save `/tmp/swarm-package-staging/worker-7/safe-scan.png`. Pass when scan ignores loops.
- [ ] Lane 8. Preserved unmanaged user authored files probe. Save `/tmp/swarm-package-staging/worker-8/unmanaged.png`. Pass when unmanaged files persist.
- [ ] Lane 9. Managed manifest ledger creation probe. Save `/tmp/swarm-package-staging/worker-9/manifest.png`. Pass when managed ledger is written.
- [ ] Lane 10. Line count audit across package lifecycle scripts. Save `/tmp/swarm-package-staging/worker-10/lines.png`. Pass when scripts remain under 500 lines.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Plugin install dry run duration in milliseconds.
- [ ] Probe. Time python3 -c "import scripts.package_lifecycle as pl; pl.compute_managed_files('antigravity', pl.load_package_descriptor()[0])".
- [ ] Baseline. Record trunk duration of compute managed files.
- [ ] Rule. Head duration must not exceed trunk duration plus 20 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/package-staging-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/package-staging-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Harden verification tooling with structured audit levers (verification-tools)

**Depends on.** package-staging

**Files.**

- [ ] Edit `scripts/scaffold_verification_skill.py`.
- [ ] Edit `tests/test_scaffold_verification_skill.py`.

**Build.**

- [ ] Add structured JSON flag support for audit and list commands in scaffold verification skill.

**You see.**

- [ ] Scaffold verification skill outputs structured JSON on audit and list requests.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_scaffold_verification_skill.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Built-in host scaffolding audit check. Save `/tmp/swarm-verification-tools/worker-1/trunk.png`. Pass when audit validates.
- [ ] Lane 2. Audit json format probe. Save `/tmp/swarm-verification-tools/worker-2/audit-json.png`. Pass when audit emits valid json.
- [ ] Lane 3. List json format probe. Save `/tmp/swarm-verification-tools/worker-3/list-json.png`. Pass when list emits valid json.
- [ ] Lane 4. Candidate skills directory resolution probe. Save `/tmp/swarm-verification-tools/worker-4/candidate-dir.png`. Pass when candidate directories parse.
- [ ] Lane 5. Driver script validation probe. Save `/tmp/swarm-verification-tools/worker-5/driver.png`. Pass when driver script exists and is executable.
- [ ] Lane 6. Feature map heading validation probe. Save `/tmp/swarm-verification-tools/worker-6/feature-h2.png`. Pass when required H2 headings exist.
- [ ] Lane 7. App naming validation probe. Save `/tmp/swarm-verification-tools/worker-7/naming.png`. Pass when kebab-case naming is enforced.
- [ ] Lane 8. Skill byte size limit probe. Save `/tmp/swarm-verification-tools/worker-8/byte-limit.png`. Pass when skill bodies stay under 24000 bytes.
- [ ] Lane 9. Formal verification mode probe. Save `/tmp/swarm-verification-tools/worker-9/formal-mode.png`. Pass when formal mode generates formal map.
- [ ] Lane 10. Audit exit code validation probe. Save `/tmp/swarm-verification-tools/worker-10/audit-exit.png`. Pass when audit returns zero on clean skills.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Audit run time in milliseconds.
- [ ] Probe. Time python3 scripts/scaffold_verification_skill.py --audit --json.
- [ ] Baseline. Record trunk duration of audit run.
- [ ] Rule. Head duration must not exceed trunk duration plus 50 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/verification-tools-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/verification-tools-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Complete quality review and reconcile change tasks (quality-reconcile)

**Depends on.** verification-tools

**Files.**

- [ ] Edit `docs/plans/2026-11-07-package-lifecycle-decomposition-and-verification.md`.
- [ ] Edit `todo.md`.
- [ ] Edit `CHANGELOG.md`.

**Build.**

- [ ] Record Thermo-Nuclear review findings, refresh evidence receipts, and update project tracking.

**You see.**

- [ ] Tracking documents and receipts reflect clean status.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `uv run pytest tests/test_evidence_durability.py tests/test_verify_portable.py -v`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `gemini-pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify clean working tree. Save `/tmp/swarm-quality-reconcile/worker-1/trunk.png`. Pass when git status is clean.
- [ ] Lane 2. Evidence durability static receipts probe. Save `/tmp/swarm-quality-reconcile/worker-2/durability.png`. Pass when receipts match current code.
- [ ] Lane 3. Line count audit across python files. Save `/tmp/swarm-quality-reconcile/worker-3/lines.png`. Pass when all files are under 850 lines.
- [ ] Lane 4. Thousand line ceiling audit. Save `/tmp/swarm-quality-reconcile/worker-4/ceiling.png`. Pass when zero files exceed 1000 lines.
- [ ] Lane 5. Dead imports and dangling reference check. Save `/tmp/swarm-quality-reconcile/worker-5/imports.png`. Pass when imports resolve cleanly.
- [ ] Lane 6. Tracking file reconciliation probe. Save `/tmp/swarm-quality-reconcile/worker-6/todo.png`. Pass when todo.md reflects current epic.
- [ ] Lane 7. Git worktree protocol check probe. Save `/tmp/swarm-quality-reconcile/worker-7/worktree-protocol.png`. Pass when worktree protocol passes.
- [ ] Lane 8. Worktree audit script probe. Save `/tmp/swarm-quality-reconcile/worker-8/worktree-audit.png`. Pass when zero worktrees leak.
- [ ] Lane 9. Staleness matrix check probe. Save `/tmp/swarm-quality-reconcile/worker-9/staleness.png`. Pass when matrix is fresh.
- [ ] Lane 10. DSH candidate table scoring probe. Save `/tmp/swarm-quality-reconcile/worker-10/dsh.png`. Pass when table hash matches candidate.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Freshness check duration in milliseconds.
- [ ] Probe. Time python3 scripts/verify_portable.py check-staleness --host all.
- [ ] Baseline. Record trunk duration of freshness check.
- [ ] Rule. Head duration must not exceed trunk duration plus 200 milliseconds.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane screenshots into `/tmp/quality-reconcile-review-gate.png`.
- [ ] Record a 30 second video of the change and save as `/tmp/quality-reconcile-review.mp4`.
- [ ] Post the screenshot and video in chat for operator review.

**Merge.**

- [ ] Root clean verdict at head SHA.
- [ ] Squash merge to parent branch.

## Multi-harness verification and gate (multi-harness-gate)

**Depends on.** quality-reconcile

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

- Evaluated package lifecycle module decomposition.
- Confirmed separation of host asset staging and file preservation logic.
- Verified test suite execution with 1525 passed tests.

## Appendix B. Alternatives rejected

- Inlining staging logic in one giant file rejected because it breaks the file size ceiling.
- Untracked unstructured output for audit rejected because structured tools need JSON.

## Appendix C. Risks

- Risk of breaking existing plugin installations. Mitigated by retaining exact helper signatures and backwards compatibility.
- Risk of evidence hash mismatch. Mitigated by tracking new file in surface revisions.

## Appendix D. Links and reading list

- Package lifecycle in scripts/package_lifecycle.py
- Scaffolding lever in scripts/scaffold_verification_skill.py
- Poteto mode playbooks in skills/poteto-mode/playbooks/
