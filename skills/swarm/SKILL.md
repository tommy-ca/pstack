---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
disable-model-invocation: true
---

# Swarm

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers.
4. Pick the worker model from canonical role key `swarm-workers` in the host's setup projection per [`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md) §5. No catalog or overlay: send the host default model resolved from the active profile (omit if rejected). Missing key, `inherit-parent`, or `auto`: omit `model`. For a model race, name each arm from this session's detected slugs only. Every worker lane maps to a real tracked child agent and isolated workspace; never claim N independent workers from one repeated alias without verified discrete spawn. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of the **poteto-mode** skill.
5. Give each worker its own writable output when it writes. Use a project worktree under `.worktrees/` for repo-backed work (per using-git-worktrees, `fix/<slug>` or `docs/<slug>` leaves), a bare branch only for branch-local edits with no checkout, or `/tmp/swarm-<slug>/worker-<n>/` only for scratch with no repo checkout. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method: sample count, what one sample is, and order. The worker records both in its result.
6. Freeze each brief before dispatch: the brief a lane receives is the brief it reports against, a rewritten brief is a new lane, and follow-up work is a fresh spawn rather than a resume with different scope. Dispatch through the fan-out route the active harness profile binds (its host reference names the concrete mechanism); a lane that reuses a warm or keep-alive worker context is not a fresh lane, and the run reports that reuse as an adaptation or a gap.

Exec route (waves 6 to 8 evidence): when scout lanes report BLOCKED on no-exec, retry as Task agents with command execution in isolated project worktrees at the pinned SHA (`.worktrees/fix/<lane>`, removed after the lane; TMPDIR stays test-private). Each lane creates its own project worktree, runs the three-step probe with real commands, records exits and outputs, then removes the worktree. Coordinator-run probes are evidence only, never Swarm verdicts.

When the work is an upstream refresh, `port` and `new-skill-lever` are shared-intent labels, not a write permit. Seed with `skills/swarm/scripts/partition.py seed --cache .worktrees/upstream-cursor-plugins --out /tmp/pstack-refresh/overlay.tsv`. Seed pin and tip are the UPSTREAM tree and cache `origin/main`, not the prior table comments. `apply-check ok` plus dry-run copy=0 is not overlay-seeded. Overlay identity is skip `idempotent-equal`. Dest-adapted is copy-bucket rows refused `already-remapped` or `host-keep`. Relative `--cache` is resolved on the primary checkout. Coverage is name-status only (`print --coverage` on that overlay). Workers fill unclassified fragments and do not rewrite the canonical TSV. Skip, host-owned, and audit stay fences. Reopen audit rows whose notes only record skipped density. After classify, copy with `skills/swarm/scripts/apply.py` on that overlay. Remap proof is apply refuse (`already-remapped`, `host-keep` via `dest_looks_raw_cursor`), not dest-equals-source. Prove dest with `apply-check`. Pass the same `--cache` primary-checkout path to seed, coverage, apply, and apply-check. Nested overlay caches under linked worktrees are leftovers. `python3 skills/swarm/scripts/refresh-hygiene.py` reports them. `--apply` deletes only those clones. Coverage CLI uses `resolve_cache`.

## Phase B: Fan out

`mkdir` each worker output dir before spawn `cwd`. Spawn all N workers in one parent turn using the host's `agent.spawn` primitive (per active harness profile and host references): role/type `pstack:swarm-workers` ([`../setup-pstack/SKILL.md`](../setup-pstack/SKILL.md)), isolated workspace (`workspace.isolated`), background/async execution, and the configured `model`. Use shared workspace (`workspace.shared`) only when the worker needs this machine's cwd. Do not send `reasoning_effort` unless supported. Join with the host's `agent.join` primitive (per active harness profile) under a bounded join deadline named before spawn (e.g. `join deadline: 10m`). A lane that has not returned by the deadline is a reported dropout, never a pass.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence bound to an artifact: a receipt scenario id, a file hash, or a commit SHA. A prose-only verdict is not a result. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

If a worker drops out, proceed with N-1 and note it. The report names the deadline it enforced and which lanes it dropped. A lane you cancel, or that the host kills while it is in flight, is the same reported dropout: it never becomes a pass and is never silently omitted.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and rerun that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts. Synthesis preserves gaps: a dropped or cancelled lane keeps its gap in the table and in the report, and the parent never backfills its slice or counts it as covered.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used. Name each worker model and its evidence-backed family. When the harness cannot identify a family from live discovery, record it as `unknown` and mark the run degraded. Never derive a family from a slug or an inferred provider. A single-family run stays degraded and never counts as multi-model proof. When the report claims host parity, name the declared census read from `pstack.package.json#host_targets` via `get_declared_hosts` in `scripts/verify-portable.py`, with each host's evidence tier. A missing host is a stated gap, not silence.
