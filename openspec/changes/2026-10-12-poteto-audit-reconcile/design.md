# Design — plan carrier and issue-graph reconciliation

## Context

Two open programs share one head (`main` `40382c95`) and no shared contract:

- **OMP epic #288** with ten open children (#289–#294, #296–#298). Its formal spec is
  merged (`openspec/changes/2026-10-11-omp-native-adapter`, PR #295). The merged
  `tasks.md` carries an appended "Implementation status (2026-10-12 stack)" section
  because the plan above it describes what was believed before the stack landed.
- **DSH program #305** with sub-epics #306/#307 and leaves #308–#315. Its formal spec is
  an **open draft PR #317** on branch `spec/deepseek-portable-skill-patterns-20261011`,
  nine files, documentation only.

Observed state at `40382c95`, from artifacts rather than from issue prose:

- `.audit/evidence/omp-receipt.json` carries `runtime-child-spawn-omp` as `observed_live`
  (child `ChildOk`, model `opencode-go/deepseek-v4.1-flash`, typed settlement) and
  `runtime-isolation-omp` as `static` — inside a runtime plane that still reduces to
  `PASS`. That pair is what #289/#291 are actually about.
- `profiles/omp.json` lists `agent.cancel`, `agent.resume`, `session.resume`, `monitor`
  and `schedule` as `verification_status: verified` with `evidence_ref` pointing at that
  receipt, and no scenario in that receipt exercises any of them.
  `schemas/portability/binding.schema.json` types `evidence_ref` as a free string, so
  nothing ties a binding to the scenario that proves it; only a dangling path fails
  (`tests/test_evidence_durability.py::test_dangling_evidence_path_fails`).
- `skills/swarm`, `skills/arena`, `skills/interrogate` specify spawn, join and reporting,
  but no bounded join deadline, no receipt/evidence binding and no reference to the
  declared six-host census (`scripts/verify-portable.py::get_declared_hosts`). That is the
  verification parity gap this program closes wherever those playbooks run.
- PR #317 is `MERGEABLE` and `draft=true`; DSH leaves #311 and #312 already have merged
  implementation PRs (#331, #321/#332) while their own issues stay open on purpose.

## Goals / Non-Goals

**Goals**

1. One depth-first execution graph over both programs: what lands, in what order, gated by
   what.
2. One section per future PR with files, build step, observable result and unit/live/perf
   verify boxes, so the coordinator can size and stack without re-deriving scope.
3. A per-issue verdict for every open issue in the range, each with an artifact pointer.
4. An honest closure policy: close only what an artifact settles, name the residual in the
   close comment, never close gated work.

**Non-Goals**

- No implementation. No `skills/`, `scripts/`, `profiles/`, `schemas/` edit in this unit.
- No new capability, schema, enum, scheduler, router or state store.
- No reopening of closed history (#320, #322, #62/#66/#67/#68, #235/#238/#247/#248).
- No re-litigation of the merged OMP spec (PR #295) or of the DSH draft (#317).

## Decisions

**D1 — This change carries a plan, not behavior; `skip_specs: true`.** The intent-driven
schema demands a `specs/<capability>/` delta for behavior changes and errors out without
one. This change changes no behavior, so the honest flag is `skip_specs: true` beside
`schema: intent-driven`, rather than inventing a capability to satisfy a validator.
*Alternative rejected:* manufacturing an empty capability folder — that is a fake contract.

**D2 — Verdict vocabulary is three-valued, not binary.** `OPEN-correct` (the issue still
describes real work), `SHOULD-CLOSE with residual` (an artifact settles the acceptance and
only minor, named leftovers remain) and `NEEDS-WORK` (an acceptance item is provably
unmet). A binary open/closed call forces either premature closure or a stale backlog.
*Alternative rejected:* leaving every issue open until its epic closes — that is what
produced the current "cannot tell finished from unfinished" problem.

**D3 — Closure policy for #296 and #298 is evidence-driven and asymmetric.** #296 is
closed with an evidence comment: the enum is already closed at
`schemas/portability/receipt.schema.json`, the merged spec forbids invented `live`/
`documented` values (`design.md:52`, `specs/pstack-omp-native-adapter/spec.md:76`), and
`tests/test_evidence_durability.py` plus `tests/test_verdict_reduction.py` cover legacy
non-promotion, FAIL-over-BLOCKED and staleness. The one residual is a negative fixture
asserting the schema rejects `live` and `documented` — a guard over an enum that already
rejects them. #298 is **kept open**: its acceptance names a disabled-plugin case, a
deeply-nested-skill case and a missing/invalid `omp`-key case, none of which has a
recorded observation. Those are named negative tests, not cosmetic leftovers.

**D4 — Verify boxes are three-tiered per PR: unit, live, perf.** The repo already
separates offline contract checks, host-dependent smoke and observed model-backed runtime
(`docs/verification-test-tiers.md`). A per-PR "verified" claim that does not say which
tier ran is exactly the false PASS both programs are trying to eliminate. Perf is a box
only where the PR can move a measurable number (join deadline, doctor wall clock, context
cost); where it cannot, the box records the bounded budget instead of inventing a metric.

**D5 — Ordering is bottom-up, one PR per unit, no carrier before its leaves are shaped.**
The DSH carrier (#317) merges first in its own track because every DSH leaf cites its
files; the OMP track runs in dependency order #289 → #296/#297 → #290 → #291 → #292 →
#293 → #294, with the verification-parity unit (P9) parallel to #289 because it touches
only host-neutral playbooks.

## Risks / Trade-offs

- **Plan rot.** A graph pinned to `40382c95` misleads once the tree moves. *Mitigation:*
  every verdict row names a file plus an id (receipt scenario, test name, profile row), not
  a narrative; a reader re-runs `python scripts/verify-portable.py check-evidence --host
  all` and `python -m pytest -q tests/test_evidence_durability.py` to re-derive them.
- **Closing #296 with a residual hides work.** *Mitigation:* the residual is named in the
  close comment and carried as a task in P2; the verdict table records the same pointer.
- **A plan that duplicates the OMP spec's own tasks.md.** *Mitigation:* this file is the
  cross-program sequence and verdict layer only. Where OMP already has a graph (merged
  `tasks.md`), the section references it instead of restating its checklists.
- **Perf boxes become vanity metrics.** *Mitigation:* D4 — a perf box must name the counter
  and the budget, or say "bounded by the join deadline" and nothing else.

## Migration Plan

Docs only, and reversible: revert the merge commit. No rollback strategy beyond that,
because no runtime artifact changes. The only external state change is one issue closure
(#296), which a reopen reverses.

## Open Questions

- Does the DSH carrier branch (#317) pass `openspec validate --type change --strict`
  without an `adr.md`? The change directory has no `adr` artifact today. P10 runs the
  validator before the carrier is marked ready; if it demands `adr.md`, the carrier PR adds
  a manifest stating that no durable decision was introduced.
- Should the #296 residual fixture live in `tests/test_portability_schemas.py` (schema
  rejection) or `tests/test_evidence_durability.py` (receipt-shaped fixture)? P2 decides;
  both already import the receipt schema.
- Does `agent.resume` mean cold parent `--resume` or child handle revival? The profile row
  conflates them today; P1 splits the row or records the conflation as a gap.
