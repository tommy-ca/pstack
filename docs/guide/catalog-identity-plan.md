# Catalog identity plan

This program makes the grok pstack enable check prove catalog identity. Operators who run `python3 scripts/check-plugin-agents.py` must see FAIL when inspect loads a marketplace tree, a home plugins bind, or a pstack `collidesWith` overlay. Docs and skill gotchas follow that lever. The grok-build-plugins catalog pin is a separate repo. PR ids in order are plugin-agents-identity, enable-docs, skill-order-gotchas, then catalog-pin.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Each PR/task section also has a unique parenthesized identifier and a `Depends on.` list that names direct parents or `None.`. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/autopilot-stack.md`. The operator reviews and lands every PR. Nothing auto-merges.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] State the protocol and this plan to the operator, then stop. Start execution only on her explicit go.
- [x] On her go, persist the plan path on disk with this exact text. "docs/guide/catalog-identity-plan.md, plugin-agents-identity then enable-docs then skill-order-gotchas then catalog-pin, the verification rule, the operator lands, done when the four PRs are STACK-READY with swarm PASS."
- [x] Read these from trunk at program start. Re-read them at every tick.
  - [x] `git show origin/main:skills/poteto-mode/playbooks/autopilot-stack.md`
  - [x] `git show origin/main:skills/swarm/SKILL.md`
  - [x] `git show origin/main:scripts/check-plugin-agents.py`
  - [x] `git show origin/main:skills/poteto-mode/playbooks/opening-a-pr.md`
  - [x] `git show origin/main:skills/interrogate/SKILL.md`
  - [x] `git show origin/main:skills/arena/SKILL.md`
  - [x] `git show origin/main:.grok/skills/verify-pstack/SKILL.md`
- [x] Arm the 30-minute audit tick with `scheduler_create` (`interval: "30m"`, `fire_immediately: true`) and `monitor` for event wakes. Never leave the cadence to memory.
- [x] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk and the persisted plan. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then send the operator a status message, whether or not anything changed, with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] From this parent session, spawn one owner per PR with `spawn_subagent` (`isolation: "worktree"`). Depth is 1. Owners do not spawn.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
  - [x] plugin-agents-identity and catalog-pin are independent and first. plugin-agents-identity branches from `main`. catalog-pin lives in tommy-ca/grok-build-plugins and branches from that `main`.
  - [ ] enable-docs after plugin-agents-identity.
  - [ ] skill-order-gotchas after enable-docs.
- [ ] Hold the file boundaries. plugin-agents-identity touches only `scripts/check-plugin-agents.py`, `tests/test_plugin_agents.py`, and `tests/fixtures/*`. enable-docs touches leftover-scanner.md, verify-pstack SKILL.md, 01-setup.md, HARNESS.md, and 06-verify-and-ship.md. skill-order-gotchas touches poteto-mode, how, and figure-it-out SKILL.md files. catalog-pin touches grok-build-plugins marketplace.json only.
- [ ] Hold the review gate. No PR in this program changes an interaction that needs a video. Review gate is None.

### PR mechanics, for every PR

- [x] Resolve the forge once. Default to `gh`; if `command -v origin` succeeds and Origin can resolve the repository, use `origin pr` for every PR operation. Record any fallback to `gh`. Never require `gt`. Origin CLI is absent. Forge is `gh` for tommy-ca/pstack and tommy-ca/grok-build-plugins.
- [ ] Open the PR ready, never draft, with `origin pr create --status open --base <base-branch>` or `gh pr create --base <base-branch>` according to the resolved forge. A stack child targets its parent branch.
- [ ] Run `/unslop` before each commit and `/no-comments` before review.
- [ ] Triage every Bugbot and security-reviewer comment per `../references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before babysit and again before the merge-ready report.

### Verdict and merge, for every PR

- [ ] At the merge-ready head SHA, run the swarm per `skills/swarm/SKILL.md`. One gates lane. The ten live lanes from the PR's **Verify, live** block. The perf lane from its **Verify, perf** block. One audit lane that reads the diff and the receipts and distrusts the PR body.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner. A new head gets a fresh swarm and a fresh verdict.
- [ ] The root appends a clean verdict to the linear base-branch stack. The operator lands bottom-up. No owner squash-merges.

### Boot recipe, for every live lane

Each live lane runs in its own `isolation: "worktree"` child at the PR head. Drive the real surface (running app, CLI, tests, or Grok browser tools).

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Run `python3 scripts/check-plugin-agents.py --inspect-json <fixture>` or live `grok inspect --json` piped to the script. Wait for exit.
- [ ] Deliver the inspect JSON or live inspect. Name stdout and stderr as the read-only diagnostics.
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return the paths with the report.

## Widen the enable check (plugin-agents-identity)

**Depends on.** None.

**Files.**

- [ ] Edit `scripts/check-plugin-agents.py`.
- [ ] Edit `tests/test_plugin_agents.py`.
- [ ] Create `tests/fixtures/` payloads for marketplace path, home plugins bind, and pstack `collidesWith`.

**Build.**

- [ ] Keep the dual gate. Add path identity FAIL for `/marketplaces/` trees and `~/.grok/plugins/pstack` binds without resolving symlinks. Add FAIL on inspect `skills[]` `collidesWith` when `plugin_name` is pstack. Graft the parts-based marketplace matcher from arena candidate 3. Track [issue 31](https://github.com/tommy-ca/pstack/issues/31).

**You see.**

- [ ] `uv run --with pytest pytest tests/test_plugin_agents.py` prints the new FAIL literals on the injected marketplace, bind, and collision payloads, and still prints `PASS plugin-agents pstack:swarm-workers` for a clean checkout payload.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_plugin_agents.py` gains marketplace, bind, and collision cases. Run `uv run --with pytest pytest tests/test_plugin_agents.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.6` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `uv run --with pytest pytest tests/test_plugin_agents.py` at trunk and head. If trunk lacks the feature, record that and gate the new FAIL literals plus the PASS line on a clean checkout. Save `plugin-agents-regression.txt`. Pass when head is green and trunk is red on the new cases.
- [ ] Lane 2. Marketplace fixture with `agents/swarm-workers.md` present. Save `marketplace-fail.txt`. Pass when stderr starts with `FAIL plugin-agents marketplace path`.
- [ ] Lane 3. Home plugins bind fixture with swarm-workers.md present. Save `bind-fail.txt`. Pass when stderr names the `~/.grok/plugins/pstack` bind.
- [ ] Lane 4. Clean checkout fixture. Save `checkout-pass.txt`. Pass when stdout first line is `PASS plugin-agents pstack:swarm-workers`.
- [ ] Lane 5. Clean installed-plugins fixture using a tmp tree that is not a marketplace path. Save `install-pass.txt`. Pass when the PASS line prints.
- [ ] Lane 6. Name-only fixture `tests/fixtures/inspect-name-only.json`. Save `name-only-fail.txt`. Pass when stderr contains `no enabled pstack plugin path`.
- [ ] Lane 7. Collision fixture on a clean tree. Save `collision-fail.txt`. Pass when stderr contains `FAIL plugin-agents collidesWith`.
- [ ] Lane 8. Mixed enabled marketplace path plus a good path. Save `mixed-fail.txt`. Pass when the run exits 1.
- [ ] Lane 9. Live `grok inspect --json` piped through `--inspect-json` at this host. Save `live-inspect.txt`. Pass when the script exits 1 while this host still has `user:poteto-mode` `collidesWith`.
- [ ] Lane 10. `python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .` still prints leftover `PASS`. Save `leftover-doctor.txt`. Pass when leftover-scanner is unchanged and still PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `python3 scripts/check-plugin-agents.py --inspect-json` on a 200-skill inspect blob at trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.
- [ ] Probe. `TIMEFORMAT=%R; time python3 scripts/check-plugin-agents.py --inspect-json /tmp/swarm-plugin-agents/inspect-200.json` at trunk and at the head, interleaved. Both sides must produce the metric.
- [ ] Baseline. Record the trunk seconds first.
- [ ] Rule. Head must stay under 2x trunk and under 2 seconds. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.

**Review gate.** None.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root appends it to the base-branch stack and the operator lands it bottom-up.

## Document the enable check (enable-docs)

**Depends on.** plugin-agents-identity

**Files.**

- [ ] Edit `.grok/skills/verify-pstack/features/leftover-scanner.md`.
- [ ] Edit `.grok/skills/verify-pstack/SKILL.md`.
- [ ] Edit `docs/guide/01-setup.md`.
- [ ] Edit `HARNESS.md`.
- [ ] Edit `docs/guide/06-verify-and-ship.md`.

**Build.**

- [ ] State leftover PASS is checkout token cleanliness, not catalog identity. State Claude-compat off does not hide `~/.grok/skills`. State `marketplace add` is catalog-only. Track [issue 32](https://github.com/tommy-ca/pstack/issues/32).

**You see.**

- [ ] `rg "collidesWith" docs/guide/01-setup.md HARNESS.md .grok/skills/verify-pstack/features/leftover-scanner.md` prints hits, and leftover-scanner skip dirs still omit `$HOME`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_verify_docs_sync.py` still PASSes. Run `uv run --with pytest pytest tests/test_verify_docs_sync.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.6` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `uv run --with pytest pytest tests/test_verify_docs_sync.py` at trunk and head. If trunk lacks the feature, record that and gate the new gotcha sentences plus the old leftover PASS contract. Save `docs-sync-regression.txt`. Pass when head pytest is green.
- [ ] Lane 2. leftover-scanner.md names inspect `plugins[].path`. Save `leftover-gotcha.txt`. Pass when the gotcha line exists.
- [ ] Lane 3. 01-setup First session names `collidesWith`. Save `setup-gotcha.txt`. Pass when the sentence exists.
- [ ] Lane 4. HARNESS Marketplace add names catalog-only `marketplace add`. Save `harness-gotcha.txt`. Pass when the sentence exists.
- [ ] Lane 5. leftover-scanner skip dirs still exclude `$HOME`. Save `skip-dirs.txt`. Pass when `$HOME` is not a walk root.
- [ ] Lane 6. `python3 scripts/verify-harness.py` still first line PASS. Save `verify-harness.txt`. Pass when first stdout line is PASS.
- [ ] Lane 7. verify-pstack SKILL.md still says the script is not leftover scanner. Save `verify-skill.txt`. Pass when that sentence remains.
- [ ] Lane 8. 06-verify-and-ship.md names the widened enable check. Save `ship-docs.txt`. Pass when the path identity sentence exists.
- [ ] Lane 9. `rg "Do not write .~/.grok/skills" docs/guide/01-setup.md` still hits. Save `no-write-home.txt`. Pass when the ban remains.
- [ ] Lane 10. Live leftover doctor. Save `doctor-live.txt`. Pass when doctor leftover PASS is unchanged.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Word count of leftover-scanner.md at trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.
- [ ] Probe. `wc -w .grok/skills/verify-pstack/features/leftover-scanner.md` at trunk and at the head, interleaved. Both sides must produce the metric.
- [ ] Baseline. Record the trunk word count first.
- [ ] Rule. Head must not grow more than 80 words over trunk. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.

**Review gate.** None.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root appends it to the base-branch stack and the operator lands it bottom-up.

## Record skill-order collisions (skill-order-gotchas)

**Depends on.** enable-docs

**Files.**

- [ ] Edit `skills/poteto-mode/SKILL.md`.
- [ ] Edit `skills/how/SKILL.md`.
- [ ] Edit `skills/figure-it-out/SKILL.md`.

**Build.**

- [ ] Skill order says plugin vs native keep two inspect rows. how Gotchas say resolve the symlink before calling a path personal. figure-it-out Phase A includes `collidesWith` in the predicate. Track [issue 33](https://github.com/tommy-ca/pstack/issues/33).

**You see.**

- [ ] `rg "collidesWith" skills/poteto-mode/SKILL.md skills/how/SKILL.md skills/figure-it-out/SKILL.md` prints a hit in each file.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Skill markdown still has valid frontmatter. Run `python3 scripts/verify-harness.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.6` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `python3 scripts/verify-harness.py` at trunk and head. If trunk lacks the feature, record that and gate leftover PASS plus the new gotcha strings. Save `harness-regression.txt`. Pass when both sides leftover PASS and head contains the new strings.
- [ ] Lane 2. poteto-mode Skill order names `/pstack:<name>`. Save `poteto-order.txt`. Pass when that token exists.
- [ ] Lane 3. how Gotchas name inspect `source.path`. Save `how-gotcha.txt`. Pass when that token exists.
- [ ] Lane 4. figure-it-out Phase A names `collidesWith`. Save `fio-predicate.txt`. Pass when that token exists.
- [ ] Lane 5. No copy into `~/.grok/skills` remains banned. Save `no-copy.txt`. Pass when the ban remains.
- [ ] Lane 6. `disable-model-invocation` on plugin poteto-mode is still true. Save `dmi.txt`. Pass when frontmatter still has it.
- [ ] Lane 7. Playbook count still 22 plus opening-a-pr. Save `playbooks.txt`. Pass when leftover-playbooks still PASS.
- [ ] Lane 8. Principle count still 23. Save `principles.txt`. Pass when leftover-principles still PASS.
- [ ] Lane 9. Live inspect still lists both poteto-mode rows until the host overlay is removed. Save `live-collision.txt`. Pass when the gotcha matches the live inspect, not a guessed path.
- [ ] Lane 10. Interrogate packed prompt on the three SKILL.md diffs. Save `interrogate.txt`. Pass when the lead verdict has no Act on leftover Cursor call sites.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Line count of `skills/poteto-mode/SKILL.md` at trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.
- [ ] Probe. `wc -l skills/poteto-mode/SKILL.md` at trunk and at the head, interleaved. Both sides must produce the metric.
- [ ] Baseline. Record the trunk line count first.
- [ ] Rule. Head must not grow more than 40 lines over trunk. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.

**Review gate.** None.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root appends it to the base-branch stack and the operator lands it bottom-up.

## Refresh the catalog pin (catalog-pin)

**Depends on.** None.

**Files.**

- [ ] Edit `.grok-plugin/marketplace.json` in tommy-ca/grok-build-plugins.

**Build.**

- [ ] Set catalog `pstack` version and sha to the current tommy-ca/pstack release that matches the live git install. Track [grok-build-plugins issue 31](https://github.com/tommy-ca/grok-build-plugins/issues/31).

**You see.**

- [ ] `gh api repos/tommy-ca/grok-build-plugins/contents/.grok-plugin/marketplace.json` after merge shows a pstack version that is not `0.14.7-grokbuild.1`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] JSON parses. Run `python3 -c 'import json,pathlib; json.loads(pathlib.Path(".grok-plugin/marketplace.json").read_text())'`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.6` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `python3 -c 'import json,pathlib; print(json.loads(pathlib.Path(".grok-plugin/marketplace.json").read_text())["plugins"][0]["version"])'` at trunk and head. If trunk lacks the feature, record that and gate the new version string plus parse success. Save `pin-regression.txt`. Pass when head version is newer than trunk `0.14.7-grokbuild.1`.
- [ ] Lane 2. marketplace.json `pstack` source url is tommy-ca/pstack.git. Save `pin-url.txt`. Pass when the url matches.
- [ ] Lane 3. sha is a 40-char hex. Save `pin-sha.txt`. Pass when the sha matches `git ls-remote` for that tag or commit.
- [ ] Lane 4. Other catalog plugins still parse. Save `other-plugins.txt`. Pass when agent-compatibility still exists.
- [ ] Lane 5. `grok plugin marketplace update grok-build-plugins` after land would refresh. Save `update-cmd.txt`. Pass when the command is documented in the PR body.
- [ ] Lane 6. Bare install warning stays in pstack 01-setup. Save `bare-install.txt`. Pass when pstack docs still forbid bare `grok plugin install pstack`.
- [ ] Lane 7. Live list still shows installed git pstack as marketplace null until someone reinstalls from catalog. Save `list-null.txt`. Pass when that split is described.
- [ ] Lane 8. No pstack nested as `plugins/pstack`. Save `nest.txt`. Pass when source is the git url, not a nested folder.
- [ ] Lane 9. Homepage still tommy-ca/pstack. Save `homepage.txt`. Pass when homepage matches.
- [ ] Lane 10. JSON schema name remains grok-build-plugins. Save `catalog-name.txt`. Pass when name is grok-build-plugins.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Byte size of marketplace.json at trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.
- [ ] Probe. `wc -c .grok-plugin/marketplace.json` at trunk and at the head, interleaved. Both sides must produce the metric.
- [ ] Baseline. Record the trunk byte size first.
- [ ] Rule. Head must stay within 2 kilobytes of trunk. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.

**Review gate.** None.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Bugbot triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The operator lands the grok-build-plugins PR on that repo. It is not stacked on pstack.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

Current `scripts/check-plugin-agents.py` PASSed on a real `installed-plugins/pstack-6ff43f58` inspect that also listed `user:poteto-mode` `collidesWith`. Receipt `/tmp/proto-plugin-agents/real-install-plus-collision.json`. A marketplace path without swarm-workers.md already failed for the missing file, which hid the identity hole. Arena candidate 1 is the base. Candidate 3 donated the parts-based marketplace matcher. Candidate 2 dropped out with an empty output dir.

## Appendix B. Alternatives rejected

Fail only on path and warn on collisions. That keeps the false PASS on this host. leftover-scanner walk of `$HOME`. Issue 31 forbids it. Allow-list only installed-plugins hashes. That rejects git checkout enable.

## Appendix C. Risks

plugin-agents-identity will FAIL live inspect on this host until the overlay links are removed. That is the lever working. catalog-pin is another repo and can stall without blocking the pstack stack. Skill gotchas can drift into leftover Cursor tokens. leftover-scanner still walks skills markdown.

## Appendix D. Links and reading list

[issue 31](https://github.com/tommy-ca/pstack/issues/31). [issue 32](https://github.com/tommy-ca/pstack/issues/32). [issue 33](https://github.com/tommy-ca/pstack/issues/33). [grok-build-plugins issue 31](https://github.com/tommy-ca/grok-build-plugins/issues/31). `skills/how/SKILL.md` on plugin-agents-identity. `skills/interrogate/SKILL.md` on skill-order-gotchas. Trail `~/.grok/pstack-catalog-identity-decisions.tsv`. Arena notes `/tmp/arena-plugin-agents/candidate-1/rationale.md`.
