---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
disable-model-invocation: true
---

# Arena

Open a todolist with one entry per phase (Frame, Fan out, Cross-judge, Pick, Graft, Verify) before launching anything. The arena runs autonomously and the list keeps phases from silently disappearing.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract. Get it right before spawning anything.

1. State the artifact each candidate is producing.
2. Derive the rubric, 3-6 concrete gradeable criteria for what success looks like on *this* task. Concrete: `Adds a --dry-run flag that skips writes`. Vague: `code is correct`. The rubric is the picker's tool in Phase D; candidates only see the task.
3. Pick the runners from canonical role key `arena-runners` in the host's setup projection per [`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md) §5. If the catalog or key is absent, spawn **one** runner using the host default model resolved from the active profile (omit if rejected). Spawn more only when the projection lists more detected slugs, or when the arena covers multiple design directions on the **same** named-or-omitted slug. Same model N times when the work is generation-bound rather than judgment-sensitive. Every candidate seat maps to a real tracked child agent and discrete worktree; never claim N independent models from one repeated alias or without verified spawn. When multiple seats use the same model family, record generation diversity only; never claim cross-family independence without verified diverse model families. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **poteto-mode** skill.
4. Give each candidate its own output location: a project worktree under `.worktrees/` for repo-backed work (per using-git-worktrees, `fix/<slug>` leaves, removed after the run), otherwise `/tmp/arena-<slug>/candidate-<n>/` only for scratch with no repo checkout. N candidates writing to the same path is shared mutable state and fails the the **separate-before-serializing-shared-state** principle skill test.
5. Freeze the task and the rubric before any candidate spawns: a rubric rewritten after a candidate returned invalidates the comparison, so the run re-runs instead of scoring the old candidates against the new rubric.

## Phase B: Fan out

Spawn all N subagents in one message using the host's `agent.spawn` primitive (per active harness profile and host references), background/async execution, role/type `pstack:arena-runners` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md)), each with the brief, the path to the shared grounding, its own output path, and instructions to produce the artifact and a short rationale naming the alternatives it considered and what it rejected. Do not send `reasoning_effort` unless supported. Architect passes role key `architect-runners` and `pstack:architect-runners` instead.

The rationale is mandatory. Without it, the parent cannot tell whether a candidate's structure is principled or accidental, which makes Phase E grafting unreliable.

If a candidate fails to produce output, proceed with N-1 and note the dropout in the synthesis record. Join under a bounded join deadline named before spawn (e.g. `join deadline: 10m`); a candidate that has not returned by the deadline is a reported dropout, not silence. A candidate you cancel, or that the host kills in flight, is the same reported dropout, never a pass.

Dispatch the candidates through the fan-out route the active harness profile binds (its host reference names the concrete mechanism). Each candidate runs in a fresh context: a warm or keep-alive worker reused across candidates carries the previous candidate's context, so a run that reuses one reports that reuse as an adaptation or a gap rather than an independent attempt. A dropped or cancelled candidate keeps its gap in the synthesis record, and synthesis never grades or backfills it.

## Phase C: Cross-judge

After all Phase B candidates complete, resolve the **coordinator's own model family** from active-host evidence, not a guessed slug prefix. Consult canonical role key `arena-cross-judge-pool` in the active host's setup projection per [`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md) §5. Walk candidate judge entries in pool order. An `auto` or `inherit-parent` alias resolves to the coordinator and **never judges**. Select only a model whose observed family differs from the coordinator's. If the host rejects a configured judge, try a confirmed runnable model **of that same different family** from host discovery, then the next eligible pool entry; do not silently reuse the parent or a candidate seat. Do not substitute a model solely by guessing its family from a slug.

If no different-family judge is runnable, **skip Phase C**, record `SKIPPED: no evidence-backed cross-family judge` and let the coordinator pick alone in Phase D. Do not present an unknown-family or same-family invocation as independent judgment. If the requested acceptance contract requires an independent judge, mark that gate `BLOCKED`; otherwise the candidate comparison may continue with a clearly degraded review-strength label. When an eligible judge exists, spawn it using the active host's native spawn capability and canonical `arena-cross-judge-pool` role mapping, operating read-only where the host actually enforces it; report advisory-only read-only as `DEGRADED`. Do not send `reasoning_effort` unless supported. The judge sees the frozen rubric and candidate artifacts and runs in parallel with the coordinator's independent reading.

## Phase D: Pick a base

Read every candidate end to end before picking. Skimming N candidates surfaces only the candidate whose surface looks most familiar. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the cross-judge **only if Phase C actually ran an eligible judge**. Agreement on the base confirms the pick; disagreement calls for checking both rationales. When Phase C was skipped, select a base from the frozen rubric yourself and record the missing cross-family check rather than fabricating a judge verdict.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller surface area, per the Laziness Protocol.

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the **redesign-from-first-principles** principle skill, so the result stays coherent under one mental model. Don't paste mechanically.

The rejection notes are the highest-signal part of the record. Future readers learn from what you considered and dropped, not just what you kept.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per the **prove-it-works** principle skill. The arena does not earn you a pass. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the cross-judge's verdict **or the explicit Phase C skip reason**, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result. Name each candidate and judge model with its evidence-backed family. When the harness cannot identify a family from live discovery, record it as `unknown` and mark the run degraded. Never derive a family from a slug or an inferred provider. A single-family run stays degraded and never counts as multi-model proof. The note binds to evidence: the receipt scenario id, file hash, or PR head SHA the artifact was verified against. A prose-only verdict fails. When the arena claims host parity, name the declared census read from `pstack.package.json#host_targets` via `get_declared_hosts` in `scripts/verify_portable.py`, with each host's evidence tier; a missing host is a stated gap, not silence.
