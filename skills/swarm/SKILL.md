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
4. Pick the worker model from toml key `swarm-workers` per `../setup-pstack/references/resolve-model.md`. Absent file: send the host default model resolved from the active profile (omit if rejected). Missing key, `inherit-parent`, or `auto`: omit `model`. For a model race, name each arm from this session's detected slugs only.
5. Give each worker its own writable output when it writes. Use a worktree, branch, or `/tmp/swarm-<slug>/worker-<n>/`. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method: sample count, what one sample is, and order. The worker records both in its result.

When the work is an upstream refresh, `port` and `new-skill-lever` are shared-intent labels, not a write permit. Seed with `scripts/partition.py seed --cache .worktrees/upstream-cursor-plugins --out /tmp/pstack-refresh/overlay.tsv`. Seed pin and tip are the UPSTREAM tree and cache `origin/main`, not the prior table comments. `apply-check ok` plus dry-run copy=0 is not overlay-seeded. Overlay identity is skip `idempotent-equal`. Dest-adapted is copy-bucket rows refused `already-remapped` or `host-keep`. Relative `--cache` is resolved on the primary checkout. Coverage is name-status only (`print --coverage` on that overlay). Workers fill unclassified fragments and do not rewrite the canonical TSV. Skip, host-owned, and audit stay fences. Reopen audit rows whose notes only record skipped density. After classify, copy with `scripts/apply.py` on that overlay. Remap proof is apply refuse (`already-remapped`, `host-keep` via `dest_looks_raw_cursor`), not dest-equals-source. Prove dest with `apply-check`. Pass the same `--cache` primary-checkout path to seed, coverage, apply, and apply-check. Nested overlay caches under linked worktrees are leftovers. `python3 skills/swarm/scripts/refresh-hygiene.py` reports them. `--apply` deletes only those clones. Coverage CLI uses `resolve_cache`.

## Phase B: Fan out

`mkdir` each worker output dir before spawn `cwd`. Spawn all N workers in one parent turn using the host's `agent.spawn` primitive (per active harness profile and host references): role/type `pstack:swarm-workers` ([`../setup-pstack/references/resolve-effort.md`](../setup-pstack/references/resolve-effort.md)), isolated workspace (`workspace.isolated`), background/async execution, and the configured `model`. Use shared workspace (`workspace.shared`) only when the worker needs this machine's cwd. Do not send `reasoning_effort` unless supported. Join with the host's `agent.join` primitive (per active harness profile).

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and rerun that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
