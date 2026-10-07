# Gemini audit and multi-harness verification plan

This program delivers the audit findings and repairs for the Gemini Antigravity plugin.
It restores driver shim preservation across version managers, enforces plugin hygiene, and verifies skill frontmatter.
The work is partitioned into four verifiable PR slices.
The PR identifiers in order are fix-driver-shims, antigravity-plugin-hygiene, kebab-case-verification, and swarm-matrix-receipts.

## How to read this

One box is one unit of work.
Every box names the evidence that checks it.
A nested box is a sub-step of the box above it.
Each PR section has a unique parenthesized identifier and a Depends on list.
Check a box only when its evidence exists.
Evidence can be a file, a log line, a screenshot, a test run, or a commit SHA.
The body is a how-to guide.
The appendices explain and record choices.

The program runs skills/poteto-mode/playbooks/autopilot-stack.md.
The root coordinator appends verified commits to the branch stack and the operator lands them.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on her explicit go.
- [ ] On her go, persist the plan path on disk with this exact text. "docs/delivery/2026-10-gemini-audit-and-verification-stack.md, PRs fix-driver-shims, antigravity-plugin-hygiene, kebab-case-verification, swarm-matrix-receipts, verification rule all checked, operator lands, done when all green."
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:skills/swarm/SKILL.md`
  - [ ] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
- [ ] Arm the 30-minute audit tick with the host schedule capability. Use interval 30m with immediate fire and monitor for wakes.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message, whether or not anything changed, with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] From this parent session, spawn one owner per PR using the host agent spawn primitive. Depth is 1.
- [ ] Follow this dependency graph.
  - [ ] fix-driver-shims is independent and first. It branches from main.
  - [ ] antigravity-plugin-hygiene after fix-driver-shims.
  - [ ] kebab-case-verification after antigravity-plugin-hygiene.
  - [ ] swarm-matrix-receipts after kebab-case-verification.
- [ ] Hold the file boundaries. Each slice touches only its declared files.
- [ ] Hold the review gate. Each slice waits for the operator review in chat before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to gh and record any fallback.
- [ ] Open the PR ready, never draft. A stack child targets its parent branch.
- [ ] Run unslop before each commit and no-comments before review.
- [ ] Triage every Bugbot and security reviewer comment.
- [ ] Rebase onto current trunk before babysit and again before the merge report.

### Verdict and merge, for every PR

- [ ] At the merge-ready head SHA, run the swarm per skills/swarm/SKILL.md. Run one gates lane, ten live lanes, one perf lane, and one audit lane.
- [ ] Clean only when every lane is PASS. Findings go back to the owner.
- [ ] The root appends the verified slice to the base branch stack and the operator lands it bottom up.

### Boot recipe, for every live lane

Each live lane runs in its own isolated worktree child at the PR head.

- [ ] Fetch origin and checkout head SHA.
- [ ] Run the test or verifier command. Wait for completion.
- [ ] Verify output and check exit codes.
- [ ] Save every screenshot to `/tmp/swarm-audit/worker/screen.png` and return paths.

## Preserve executable shims in harness drivers (fix-driver-shims)

**Depends on.** None.

**Files.**

- [ ] Edit `scripts/drivers/base.py`.

**Build.**

- [ ] Remove resolve calls on which_path in find_executable in scripts/drivers/base.py.

**You see.**

- [ ] Codex and Droid drivers resolve to their respective shims instead of the mise binary.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run driver scenario unit tests. Run `/home/tommyk/projects/dev-env/.venv/bin/pytest tests/test_harness_drivers.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run discover scenario on trunk and head. Save `/tmp/swarm-audit/lane1.png`. Pass when codex and droid pass discover.
- [ ] Lane 2. Run grok discover scenario. Save `/tmp/swarm-audit/lane2.png`. Pass when verdict is PASS.
- [ ] Lane 3. Run antigravity discover scenario. Save `/tmp/swarm-audit/lane3.png`. Pass when verdict is PASS.
- [ ] Lane 4. Run codex doctor discover scenario. Save `/tmp/swarm-audit/lane4.png`. Pass when verdict is PASS.
- [ ] Lane 5. Run omp discover scenario. Save `/tmp/swarm-audit/lane5.png`. Pass when verdict is PASS.
- [ ] Lane 6. Run opencode discover scenario. Save `/tmp/swarm-audit/lane6.png`. Pass when verdict is PASS.
- [ ] Lane 7. Run droid discover scenario with json flag. Save `/tmp/swarm-audit/lane7.png`. Pass when verdict is PASS.
- [ ] Lane 8. Run droid isolation check for worktree flag. Save `/tmp/swarm-audit/lane8.png`. Pass when verdict is PASS.
- [ ] Lane 9. Run droid child spawn contract check. Save `/tmp/swarm-audit/lane9.png`. Pass when verdict is PASS.
- [ ] Lane 10. Run droid route playbook advisory check. Save `/tmp/swarm-audit/lane10.png`. Pass when verdict is PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Execution duration of tests/test_harness_drivers.py.
- [ ] Probe. Time pytest test_harness_drivers.py execution.
- [ ] Baseline. Record trunk execution time of 30 seconds.
- [ ] Rule. Head execution time must remain under 40 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Capture lane screenshot in media.
- [ ] Record a video walkthrough for the operator.
- [ ] Post evidence in chat and wait for operator approval.

**Merge.**

- [ ] Root verdict is clean at head SHA.
- [ ] Append slice to stack for operator landing.

## Enforce Antigravity plugin zero-drift hygiene (antigravity-plugin-hygiene)

**Depends on.** fix-driver-shims

**Files.**

- [ ] Edit `scripts/sync-antigravity-plugin.py`.

**Build.**

- [ ] Add foreign directory detection and cleanup in scripts/sync-antigravity-plugin.py.

**You see.**

- [ ] Audit command reports foreign_directories none and agy plugin validate passes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run sync check command. Run `/home/tommyk/projects/dev-env/.venv/bin/python3 scripts/sync-antigravity-plugin.py --check`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Verify foreign directory check on trunk and head. Save `/tmp/swarm-audit/lane2-1.png`. Pass when foreign directories are purged.
- [ ] Lane 2. Run sync audit mode. Save `/tmp/swarm-audit/lane2-2.png`. Pass when foreign_directories reports none.
- [ ] Lane 3. Run sync dry-run mode. Save `/tmp/swarm-audit/lane2-3.png`. Pass when exit code is 0.
- [ ] Lane 4. Run agy plugin validate directly. Save `/tmp/swarm-audit/lane2-4.png`. Pass when all components pass.
- [ ] Lane 5. Validate plugin.json skills array. Save `/tmp/swarm-audit/lane2-5.png`. Pass when skills directory is valid.
- [ ] Lane 6. Validate models.json mappings. Save `/tmp/swarm-audit/lane2-6.png`. Pass when roles map to tiers.
- [ ] Lane 7. Validate agents directory count. Save `/tmp/swarm-audit/lane2-7.png`. Pass when 22 agents exist.
- [ ] Lane 8. Validate commands directory count. Save `/tmp/swarm-audit/lane2-8.png`. Pass when 19 commands exist.
- [ ] Lane 9. Validate rules AGENTS.md content. Save `/tmp/swarm-audit/lane2-9.png`. Pass when rules file is present.
- [ ] Lane 10. Verify live plugin directory exists. Save `/tmp/swarm-audit/lane2-10.png`. Pass when directory is present.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Duration of sync-antigravity-plugin.py check.
- [ ] Probe. Time sync-antigravity-plugin.py --check execution.
- [ ] Baseline. Record baseline check time of 0.2 seconds.
- [ ] Rule. Check execution must remain under 0.5 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Capture lane screenshot in media.
- [ ] Record a video walkthrough for the operator.
- [ ] Post evidence in chat and wait for operator approval.

**Merge.**

- [ ] Root verdict is clean at head SHA.
- [ ] Append slice to stack for operator landing.

## Verify skill frontmatter kebab-case naming (kebab-case-verification)

**Depends on.** antigravity-plugin-hygiene

**Files.**

- [ ] Edit `scripts/verify-harness.py`.
- [ ] Edit `scripts/adapt-harness.py`.
- [ ] Edit `tests/test_verify_harness.py`.
- [ ] Edit `openspec/changes/pstack-portability-contract/specs/pstack-portability/spec.md`.
- [ ] Edit `TEST-PLAN.md`.

**Build.**

- [ ] Add verify_skills_frontmatter in scripts/verify-harness.py and test in tests/test_verify_harness.py.

**You see.**

- [ ] All 54 skills conform to kebab-case naming and pass frontmatter checks.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run verify harness tests. Run `/home/tommyk/projects/dev-env/.venv/bin/pytest tests/test_verify_harness.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run verify-harness on trunk and head. Save `/tmp/swarm-audit/lane3-1.png`. Pass when kebab-case passes.
- [ ] Lane 2. Validate poteto-mode skill frontmatter name. Save `/tmp/swarm-audit/lane3-2.png`. Pass when name is poteto-mode.
- [ ] Lane 3. Validate make-pr-easy-to-review frontmatter name. Save `/tmp/swarm-audit/lane3-3.png`. Pass when name is kebab-case.
- [ ] Lane 4. Verify no Cursor-only mode true exists. Save `/tmp/swarm-audit/lane3-4.png`. Pass when zero files have mode true.
- [ ] Lane 5. Run adapt-harness string replacements check. Save `/tmp/swarm-audit/lane3-5.png`. Pass when replacements succeed.
- [ ] Lane 6. Run scan-host-boundary check. Save `/tmp/swarm-audit/lane3-6.png`. Pass when zero boundary leaks found.
- [ ] Lane 7. Run project-package check. Save `/tmp/swarm-audit/lane3-7.png`. Pass when all projected manifests match.
- [ ] Lane 8. Run canonical-index check. Save `/tmp/swarm-audit/lane3-8.png`. Pass when conformance is PASS.
- [ ] Lane 9. Run openspec change validation. Save `/tmp/swarm-audit/lane3-9.png`. Pass when change is valid.
- [ ] Lane 10. Run full test_verify_harness suite. Save `/tmp/swarm-audit/lane3-10.png`. Pass when all 37 tests pass.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Execution time of verify-harness.py.
- [ ] Probe. Time verify-harness.py script execution.
- [ ] Baseline. Record baseline execution time of 1.0 second.
- [ ] Rule. Execution must complete in under 2.0 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Capture lane screenshot in media.
- [ ] Record a video walkthrough for the operator.
- [ ] Post evidence in chat and wait for operator approval.

**Merge.**

- [ ] Root verdict is clean at head SHA.
- [ ] Append slice to stack for operator landing.

## Refresh multi-harness durable receipts (swarm-matrix-receipts)

**Depends on.** kebab-case-verification

**Files.**

- [ ] Edit `.audit/evidence/antigravity-receipt.json`.
- [ ] Edit `.audit/evidence/codex-receipt.json`.
- [ ] Edit `.audit/evidence/grok-receipt.json`.
- [ ] Edit `.audit/evidence/omp-receipt.json`.
- [ ] Edit `.audit/evidence/opencode-receipt.json`.
- [ ] Edit `.audit/evidence/index.json`.

**Build.**

- [ ] Regenerate all five durable receipts via verify-portable run.

**You see.**

- [ ] Doctor and verify-portable pass across all five harnesses with current revisions.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run evidence durability tests. Run `/home/tommyk/projects/dev-env/.venv/bin/pytest tests/test_evidence_durability.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `pro` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run doctor check across all five hosts. Save `/tmp/swarm-audit/lane4-1.png`. Pass when all five hosts report PASS.
- [ ] Lane 2. Verify grok receipt durable bindings. Save `/tmp/swarm-audit/lane4-2.png`. Pass when verdict is PASS.
- [ ] Lane 3. Verify codex receipt durable bindings. Save `/tmp/swarm-audit/lane4-3.png`. Pass when verdict is PASS.
- [ ] Lane 4. Verify omp receipt durable bindings. Save `/tmp/swarm-audit/lane4-4.png`. Pass when verdict is PASS.
- [ ] Lane 5. Verify opencode receipt durable bindings. Save `/tmp/swarm-audit/lane4-5.png`. Pass when verdict is PASS.
- [ ] Lane 6. Verify antigravity receipt durable bindings. Save `/tmp/swarm-audit/lane4-6.png`. Pass when verdict is PASS.
- [ ] Lane 7. Run check-evidence on all hosts. Save `/tmp/swarm-audit/lane4-7.png`. Pass when zero stale errors occur.
- [ ] Lane 8. Verify surface revisions driver_revision consistency. Save `/tmp/swarm-audit/lane4-8.png`. Pass when all receipts share revision.
- [ ] Lane 9. Verify package_driver_revision consistency. Save `/tmp/swarm-audit/lane4-9.png`. Pass when receipts match current code.
- [ ] Lane 10. Run test_verify_portable suite. Save `/tmp/swarm-audit/lane4-10.png`. Pass when all six tests pass.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Execution time of doctor --host all.
- [ ] Probe. Time verify-portable.py doctor --host all.
- [ ] Baseline. Record baseline execution time of 20 seconds.
- [ ] Rule. Doctor run must complete in under 30 seconds.

**Review gate.** The operator reviews before merge.

- [ ] Capture lane screenshot in media.
- [ ] Record a video walkthrough for the operator.
- [ ] Post evidence in chat and wait for operator approval.

**Merge.**

- [ ] Root verdict is clean at head SHA.
- [ ] Append slice to stack for operator landing.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

Open questions settled by probe:

1. Codex shim execution.
   Probed by running codex --version through unresolved shim path versus realpath.
   Unresolved returned codex-cli 0.160.1. Realpath returned mise 2026.10.3.
   Settled that shims must not be resolved with resolve() in find_executable.

2. Droid worktree flag discovery.
   Probed by running droid --help through unresolved shim path versus realpath.
   Unresolved returned -w, --worktree flag. Realpath returned mise help without worktree flag.
   Settled that Droid requires unresolved shim path to discover runtime arguments.

3. Foreign directory pollution.
   Probed by inspecting ~/.gemini/config/plugins/pstack/ for .codex-plugin and .claude-plugin.
   Found both foreign folders present.
   Settled that sync-antigravity-plugin.py must explicitly purge foreign directories.

## Appendix B. Alternatives rejected

1. Environment path prepend workaround.
   Rejected. Prepending mise binary paths to PATH worked around the symptom in earlier runs but left the root cause in find_executable, which broke any standard developer environment.

2. Monolithic delivery PR.
   Rejected. Combining driver fixes, plugin sync changes, skill frontmatter lints, and receipt regenerations into one diff obscures blame and complicates independent verification.

## Appendix C. Risks

1. Driver path resolution risk in fix-driver-shims.
   If an executable path is a broken symlink, checking is_file() on the unresolved path still traverses the link safely on Linux without mutating argv[0].

2. Receipt revision invalidation in swarm-matrix-receipts.
   Any subsequent edit to scripts or profiles invalidates the durable receipt hashes, requiring careful atomic ordering.

## Appendix D. Links and reading list

- `adr/0013-antigravity-harness-architecture.md`
- `skills/poteto-mode/references/antigravity-tools.md`
- `skills/poteto-mode/playbooks/autopilot-stack.md`
- `skills/swarm/SKILL.md`
- `skills/interrogate/SKILL.md`
