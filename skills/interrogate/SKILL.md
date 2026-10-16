---
name: interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Multiple LLM reviewers challenge changes from independent angles."
disable-model-invocation: true
---

# Interrogate

This is the pstack multi-model adversarial review. Use it first. Do not start with `/review`. `/review` is the bundled single-reviewer fallback after this skill.

Spawn one reviewer per configured model to adversarially review code changes. The adversarial signal comes from model diversity, not assigned personas. Models differ in blind spots, priors, and reasoning patterns. Agreement across models is high-confidence signal; lone-model findings are worth reading but lower confidence. The deliverable is a synthesized verdict. Do NOT auto-apply changes.

## Step 1, Scope

Identify what to review from context:

- If the user points at specific files or a diff, use that.
- If on a feature branch, run `git diff main...HEAD` (or the appropriate base branch) for the full changeset.
- If the user's message references recent work, gather the relevant files.

Package the diff or file contents with any surrounding context files the reviewers need to understand the code.

## Step 2, Intent

Before spawning reviewers, state the intent in one clear paragraph from the user's message, commit messages, the PR description if one exists, and the code. What is this code trying to accomplish? Reviewers challenge whether the work achieves the intent well, not whether the intent itself is correct. If you're unsure about the intent, ask the user before proceeding.

## Step 3, Spawn Reviewers

Launch all reviewers in a single message using the host's `agent.spawn` primitive (per active harness profile and host references). Use toml array `interrogate-reviewers` per `../setup-pstack/references/resolve-model.md` (or active profile model configuration), one reviewer per entry. If the configuration is absent, spawn **one** reviewer with the host default model resolved from the active profile.

For each reviewer:
- role / `subagent_type`: `pstack:interrogate-reviewers` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md))
- `model`: that entry when it is a detected slug; omit when the entry is `inherit-parent`/`auto`. Configuration absent: host default model resolved from active profile. Do not send `reasoning_effort` on spawn.

If the host rejects a slug, omit `model` or retry only with a slug the error text named that is already in this session's detected set. Do not pick a closest family equivalent. If the configured value is `inherit-parent` or `auto`, omit `model`; never treat those aliases as broken slugs.

Fill the reviewer prompt with `skills/interrogate/scripts/pack.py --intent` plus exactly one of `--range` or `--diff-file` (`references/rubric.md`, `references/code-quality-review.md`). Do not hand-fill the template. Point reviewers at the packed `prompt.md` rather than inlining dumps. The same packed prompt goes to all reviewers, so every model applies the code-quality lens. Name each reviewer model with its evidence-backed family. When the harness cannot identify a family from live discovery, record it as `unknown` and mark the panel degraded. Never derive a family from a slug or an inferred provider. When the reviewer panel resolves to one model family, record reduced family diversity per the change design instead of claiming multi-model proof.

Join the reviewers under a bounded join deadline named before spawn (e.g. `join deadline: 10m`). A reviewer that has not returned by the deadline is a reported dropout, not a pass. A reviewer you cancel, or that the host kills in flight, is the same reported dropout, never a pass and never silently omitted.

The pack is frozen before spawn: every reviewer receives the identical packed prompt, and a pack rebuilt mid-run is a new review. Dispatch the reviewers through the fan-out route the active harness profile binds (its host reference names the concrete mechanism). Each reviewer runs in a fresh, independent context: a warm or keep-alive worker reused across reviewers carries the previous arm's context, so a run that reuses one reports an adaptation or a gap, never a blinded multi-model review. Reviewers are read-only: the prompt forbids edits, and the run states whether the host enforced that boundary or the restriction stayed advisory.

Each reviewer produces structured findings as described in the prompt template.

## Step 4, Synthesize

As results come back, build a unified picture. Parse every reviewer's findings. Merge findings that describe the same issue differently, and note which models raised each one. Findings two or more models raised independently are the highest signal. Read a lone model's finding, but weight it accordingly. Note disagreements: if one model flags something and another explicitly says the opposite, that is context for the verdict. Keep the gaps: a dropped or cancelled reviewer keeps its gap, the verdict names the arm as absent, its missing findings are never inferred or backfilled, and the Agreement Map states which arms actually reported.

## Step 5, Lead Judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator. Read `references/lead-judgment.md` for the full framework. Reviewers only see a slice of the codebase. You have the full context (the goal, the constraints, the timeline, which tradeoffs were already considered). Use that context aggressively. Put every finding in one of four buckets, with the model(s) that raised it and a one-line rationale.

- **Act on**. Real issues affecting correctness, security, or maintainability given the actual goals. They would block a real PR.
- **Consider**. Legitimate, but you're not sure they outweigh the cost of addressing them now. Worth the user's attention.
- **Noted**. Technically valid but not actionable. Context-dependent, premature optimization, or low-impact at this stage.
- **Dismissed**. Wrong, nitpicky, or missing context, with a brief reason.

The verdict binds to evidence: every finding cites the receipt scenario id, file hash, or PR head SHA it rests on. A prose-only verdict fails and is re-run, not shipped. When the verdict claims host parity, name the declared census read from `pstack.package.json#host_targets` via `get_declared_hosts` in `scripts/verify-portable.py`, with each host's evidence tier; a missing host is a stated gap, not silence.

## Effect Ownership and Finding Contract

The verdict is a review artifact, and these hold for every finding in it:

- **Exact revision.** Name the resolved base and the head commit the verdict reviewed, and
  cite the revision (commit SHA, file hash, or receipt scenario id) each finding rests on.
  A verdict bound only to a patch title, an old PR description, or a stale checkout is not a
  verdict on this change, and a retarget or a rebase that changes the patch identity makes
  the affected findings re-derive rather than re-date.
- **Typed failure identity and effect status.** An expected operational error keeps its
  typed identity and cause, and its effect is stated as one of
  `none | partial | committed | unknown`. Only the state owner declares recovery, rollback,
  or retry safety. While an effect is `partial` or `unknown`, a blind retry is forbidden,
  and the review MUST NOT report success or a completed rollback.
- **Order findings by observable impact** — what a user or operator can observe:
  correctness, data and security effects, lifecycle and consumer breakage, then structure.
  Give each finding a disposition and the recheck that would settle it; structure comes
  before style. A list of style, naming, or formatting nits MUST NOT stand in for the
  lifecycle, consumer, and security review.
- **Consumers and lifecycle.** A finding that asks for code to be deleted, moved, or
  collapsed names the consumers it searched (in-repo call sites, tests, docs, registry or
  dynamic lookup, published API, plugin and config seams) and the behavior pin that says the
  observable behavior survives. Absence of in-repo references is not evidence of
  deletability, and it is not consumer reachability.
- **User-safe report.** The verdict states impact, uncertainty, the current disposition, and
  the safe next step, with no credential or secret values in the text.

## Output Format

Present the verdict in this structure:

### Intent
> [The stated intent paragraph from Step 2]

### Reviewers
- Reviewer [label]: [model name], [N findings] (one bullet per reviewer)

### Act On
[Each: description, which models raised it, why it matters.]

### Consider
[Each: description, which models raised it, the tradeoff.]

### Noted
[Brief list.]

### Dismissed
[Each with a brief rationale. This shows the user what was filtered out and why, so they can override your judgment if they disagree.]

### Agreement Map
[Where models agreed and diverged, and what that pattern tells us.]
