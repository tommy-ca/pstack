# Verify the result and open a PR

"It compiles" is not evidence. The [Prove It Works principle](../../skills/principle-prove-it-works/SKILL.md) makes the agent check the real artifact before it reports success, and your job is to make "the real artifact" checkable.

This page has three planes. State a finish condition first. Then prove an application, prove this plugin, or open a PR and land it.

![A prototype plane flies a real test course while she times it with a stopwatch and robots film and checklist the run; the terminal reads verify: pass, evidence: captured.](./images/verification.jpg)

## State the finish condition up front

Put what done means in the first prompt, in whatever words fit:

```text
/poteto-mode add json output to this command. text output stays byte-identical, the json parses, both run against the sample project. show me the evidence.
```

Now the agent has three checks it can run, not a mood to satisfy. When the reply comes back, it should carry the exact commands and outputs. If a check couldn't run, a good reply says "inconclusive". A confident reply without evidence is a warning sign.

Match the check to the change:

- A CLI change runs the real command.
- A UI change walks the changed flow in the running app.
- A parser or migration replays a saved input.
- A perf change compares before and after profiles.
- A storage change reads back the written value.

For a small diff you don't fully trust, [`/blast-radius`](../../skills/blast-radius/SKILL.md) finds what it could break elsewhere. It finds the one fact that makes the change safe and proves that fact by running code, not by arguing for it.

## Application plane

Use this plane when the checkout is an application repo, not this plugin.

The UI bullet above hides a real requirement. The agent needs a scripted way to drive your app. If your project has one, great. If not, run:

```text
/create-verification-skill
```

[`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md) interviews the repository, not you. It works out what a user touches, how the app launches locally, what can drive it (an existing harness first, otherwise browser and CDP, a PTY, or plain HTTP), what evidence proves behavior, and whether two instances can run side by side. It asks you only what the code can't answer.

For an application repo it writes `.grok/skills/verify-<app>/`, agent-facing instructions with Launch, Doctor, Drive, Proof bar, Evidence, and Cleanup, plus a feature map under `features/` with a Full sweep README. The skill ships a [worked feature-map example](../../skills/create-verification-skill/references/feature-map-example/). Before handing it over, the generator proves the skill once: launch, doctor, drive one feature, capture evidence, clean up. That smoke is not a Full sweep. If that proof fails, don't use the output.

From then on, "verify it in the app" is a step any agent can execute, in that repo, with no setup conversation.

Once the verify skill works, a [`/swarm`](../../skills/swarm/SKILL.md) can split a full pass by feature-map entry and aggregate the results.

Apps change and feature maps rot. When yours drifts, run:

```text
/maintain-verification-skill
```

[`/maintain-verification-skill`](../../skills/maintain-verification-skill/SKILL.md) audits the generated skill: one read-only source reader per feature in parallel, then one live pass that drives every mapped feature. It ends in exactly one of three outcomes. `clean` means full coverage and nothing to ship. `changed` means one PR of proven corrections, confined to the verification skill's own directory. `blocked` names the blocker. It never edits product code. If the live pass catches a product regression, it reports the regression instead of papering over it in docs.

## Formally verify a property with `/create-formal-verification-skill`

Some properties are hard to trust from tests alone: distributed state that depends on message order, auth boundaries where one missing check leaks data, financial math that must not round incorrectly, or migrations that must invert cleanly.

When the property matters more than whether a particular test suite passes, run:

```text
/create-formal-verification-skill
```

[`/create-formal-verification-skill`](../../skills/create-formal-verification-skill/SKILL.md) picks the lightweight formal tool for the job (such as Alloy, TLA+, Kani, or Z3) and sets up a bounded, executable model against the code. It insists on seeing that property failing on a broken variant of the code, because a check you've never seen fail proves nothing. When the current code already breaks the property, you get the counterexample as a short sequence of steps in your code's terms. The property stays as stated, so the finding stays a finding. Product code doesn't change unless you ask.

It writes a project-local skill that tells the next agent whether a change touches the verified code, how to run the check with one command, and how to tell a real bug from a modeling error. Before handing it over, the generator follows that skill once on a scratch change that breaks the property, and the check must catch it. The handoff says what was verified, with which tool and bounds, what the check found, and what it doesn't cover. A pass covers the model or the bound, not the whole system.

The skill also records which code each check covers and the commit where the check last matched it. Merges and refactors that skip the skill can leave the check passing on a description of code that's gone. After them, run [`/maintain-formal-verification-skill`](../../skills/maintain-formal-verification-skill/SKILL.md). It updates the verification from the code, reruns it, shows that each updated check can still fail, and tells you whether each failure is drift in the verification or a bug in the code.

Do not treat this plane as the recipe for **this** plugin checkout. This plugin has no CDP, no `--checkout`, and keeps verify-pstack as a checkout-local meta skill.

## Plugin plane

This repository is the pstack Grok plugin. Checkout-local [`/verify-pstack`](../../.grok/skills/verify-pstack/SKILL.md) lives at `.grok/skills/verify-pstack/`. Plugin doctor lives at `.grok/skills/verify-pstack/`. Do not ship it under `skills/`. `plugin.json` lists `./skills/` and must not list `.grok/skills`. Isolation is `--run-id`. There is no CDP checkout flag. Do not write `.claude/skills`. Do not write `~/.grok/skills`.

Doctor is leftover scanner, then `grok plugin validate .` as companion only. `verify.py doctor` is that pair. Two processes without the same `--run-id` each mint a new run-id, and Full sweep drive then misses leftover `PASS`. Full sweep is one process:

```bash
python3 .grok/skills/verify-pstack/scripts/verify.py run --root .
```

That is leftover doctor, then leftover-scanner, upstream-pin, absorbed-intent, upstream-recipe, refresh-hygiene, and release-tag, then cleanup. Evidence survives. Leftover stdout must start with `PASS` and include `playbooks: 22 named + opening-a-pr`, `principles: 24`, and `plugin.json name: pstack`.

`grok inspect --json` proves enable and trust. It is not leftover scanner. Leftover PASS is checkout token cleanliness, not catalog identity. Plugin-agents uses inspect to require `pstack:swarm-workers` from https://github.com/tommy-ca/pstack. The widened enable check fails on a marketplace `plugins[].path`, a `~/.grok/plugins/pstack` bind, and pstack `collidesWith`. `grok plugin validate` alone is not leftover scanner. `pytest` and `tests/test_verify_harness.py` are not leftover scanner.

Pin proof is `python3 scripts/sync-from-upstream.py --pin`. Recipe proof is `--recipe` stdout needles plus argv without `--log`. Hygiene uses tmp `--skills` and never `--apply-skills`. Release proof is `python3 tests/test_release.py`. Do not run `scripts/release.sh` to completion from nested grok.

Keep the map honest with [`/maintain-verification-skill`](../../skills/maintain-verification-skill/SKILL.md). The map stays leftover-scanner, upstream-pin, absorbed-intent, upstream-recipe, refresh-hygiene, and release-tag.

## Ship plane

Open the PR, drive it to merge-ready, then land the stack. This plane does not replace leftover doctor.

```text
/poteto-mode open the pr. small ordered commits, evidence in the description.
```

The [Opening a PR playbook](../../skills/poteto-mode/playbooks/opening-a-pr.md) works from a worktree, rebases the work into small ordered commits, cleans the diff, unslops the prose, and returns the PR link. Five narrow PRs beat one fat one, and stacked follow-ups beat a growing branch.

An open PR starts collecting blockers immediately. Checks fail, reviewers comment, trunk moves. Hand that churn to the [Babysit playbook](../../skills/poteto-mode/playbooks/babysit.md):

```text
/poteto-mode babysit this pr. get it green.
```

Babysit watches the PR, using the host `monitor` capability (on GitHub or the Origin CLI when available), and takes blockers in order: conflicts, then review threads, then CI. Every known fix batches into one push, so the checks restart once instead of after every fix. The comment triage is skeptical, because humans and bots file real catches and noise in the same list. A real finding gets a fix, and noise gets dismissed with the disproof posted on the thread. When all you want is status, ask smaller and Babysit answers without starting the loop:

```text
/poteto-mode check on pr 123. anything outstanding?
```

Babysit stops at merge-ready. It never merges, even with everything green, because merging is a different decision.

Green is not the same as safe. When you're ready to land, say so:

```text
/poteto-mode land the stack.
```

The [Shipping playbook](../../skills/poteto-mode/playbooks/shipping.md) verifies each PR independently before it arms anything. One fresh agent per PR proves the behavior live, and the agent that judges a change is never the one that wrote it. Then Shipping lands only the contiguous verified run from the bottom, one PR at a time through `gh` by default or Origin when its CLI is available, and reports the first PR that breaks the chain. A verified PR sitting above an unverified one waits, because merging it would pull the gap in underneath.

Next: [Run work while you sleep](./07-overnight.md).
