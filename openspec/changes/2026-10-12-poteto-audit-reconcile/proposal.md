## Why

Two programs are open at the same head with no shared execution contract: the OMP native
adapter epic (#288) and the DeepSeek skill-portability program (#305, carrier PR #317).
Each has its own plan, its own vocabulary and its own idea of what "done" means. Ten OMP
leaves and eleven DSH nodes are open, four of them provably finished or nearly finished,
and four more are gated behind a vertical slice nobody has written down as a PR sequence.
A reader cannot tell which issue is a real gap, which is a stale claim, and which is
finished work waiting for a verdict.

## What Changes

- Adds the pilot unit of program `pstack-poteto-audit-20261012`: one recursive,
  depth-first execution graph covering the OMP leaves (#289, #291, #292, #293, #294), the
  DSH carrier merge (#317 → #305–#315) and the verification parity gaps in
  `swarm`/`arena`/`interrogate` (bounded join timeout, evidence binding, declared-host
  census).
- Adds one section per future PR, each naming the files it touches, its build step, its
  observable result, and unit/live/perf verify boxes.
- Adds a per-issue verdict table over all 21 open issues with a pointer to the artifact
  that settles each verdict: OPEN-correct, SHOULD-CLOSE with residual, or NEEDS-WORK.
- Records the offline gate subset output and its exit code.

No code, no skill, no profile, no schema changes. This change is the plan and the
reconciliation; implementation lands in the PRs the plan names.

## Capabilities

### New Capabilities

None. This change introduces no behavior. `skip_specs: true` in `.openspec.yaml` records
that deliberately: the intent-driven schema requires a spec capability for behavior
changes, and there are none.

### Modified Capabilities

None. No existing requirement changes. Both programs already carry their own formal
deltas (OMP: `openspec/changes/2026-10-11-omp-native-adapter/specs/`; DSH: PR #317
`specs/pstack-reusable-skill-patterns/spec.md`).

## Impact

- Docs only: this change directory and the reconciliation section of `todo.md`.
- Issue tracker: a verdict and, for #296, a closure; no code path changes.
- Baselines read, not written: pstack `main` `40382c9516e7b4a19838eb29a2d9629b90d3df2e`;
  canonical `UPSTREAM` pin `df581122cde17e6e27686b5a448bde23e4ad4318`; OMP doc pin
  `can1357/oh-my-pi@0affc77e41c357bb33f8bf056c3ea3cf50fd408b`; DSH source pin
  `deepseek-ai/deepseek-harness@d743267388641bc76f17c45ce8b4c231aed1d32c`.
- Sequencing: this change is the pilot. It must land before the coordinator opens the
  stacked PRs it describes, because their unit size and verify recipes come from here.
