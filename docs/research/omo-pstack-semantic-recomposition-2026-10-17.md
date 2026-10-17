# OmO semantic blocks recomposed with canonical pstack

Status: source-level analytical audit; NOT an independently run Swarm, Arena or Interrogate; no runtime conformance claim.

## Source manifest

- OmO: `code-yeongyu/oh-my-openagent` `dev` at `90eaba6e93a4fbfdb342bd001e6b512e852bdc04`.
- Official pstack `main` seen at `101b274dd991f694e1f7024be2157e5f3adf07de`; normative target pin remains the port's `UPSTREAM` `1dcc2bacde73ddd284803b7af28164d0436198fc`.
- Portable target base: `tommy-ca/pstack` `ce05650c3825a00b5d7efcbb1458188c05c72913`.

The concepts below can be independently specified; borrowing implementation code requires a separate license review. OmO is not the canonical source for pstack principles, roles or workflow intent.

## 24 source blocks → eight semantic contracts

| ID | OmO source concept | Proposed internal contract | pstack source/decision |
| --- | --- | --- | --- |
| SB-01 | Intent / agent routing | AC-01 | poteto-mode intent router; no new role authority |
| SB-02 | Model resolver / delegate-core | AC-01 | proposed model-role-policy, ModelPlan and actual native availability |
| SB-03 | Rule / skill resolution | AC-01 | pinned principle and skill inventory, declared fallback order |
| SB-04 | Execution brief builder | AC-01 | orchestrate brief, standing orders |
| SB-05 | DAG graph compiler | AC-02 | model-the-domain, type-system-discipline |
| SB-06 | DAG fingerprint / amendment | AC-02 | sequence-verifiable-units, source revision guard |
| SB-07 | Dependency-frontier scheduler | AC-02 | host schedule/monitor; not portable scheduler |
| SB-08 | Residency / resource governor | AC-03 | bounded worker concurrency and admission |
| SB-09 | Run generation / fence | AC-03, AC-06 | make-operations-idempotent; one owner shared by both |
| SB-10 | Child runner | AC-03 | agent.spawn/join/cancel/resume native mapping |
| SB-11 | Workpool keyed items | AC-03 | internal dispatch mechanism, optional |
| SB-12 | Team registry | AC-04 | collaboration topology, not durable program ownership |
| SB-13 | Mailbox reservations | AC-04 | agent.message + durable inbox receipts |
| SB-14 | Result persistence / artifacts | AC-05 | exact-revision evidence.capture |
| SB-15 | isolation-core / worktrees | AC-05 | separate-before-serializing-shared-state |
| SB-16 | memory-core context | AC-05 | guard-the-context-window; committed revisions |
| SB-17 | DAG journal / checkpoints | AC-06 | host-owned durable state |
| SB-18 | DAG recovery | AC-06 | reconcile-before-retry; no blind effect replay |
| SB-19 | Workpool completion aggregation | AC-04 | swarm join coverage and missing-result gap |
| SB-20 | Validation / QA | AC-07 | prove-it-works, create-verification-skill |
| SB-21 | Integration / merge-back | AC-07 | shipping, verified integration frontier |
| SB-22 | Budgets / retries | AC-01 | autonomous-run/figure-it-out and escalation |
| SB-23 | Human decision gate | AC-01 | human.ask / human.gate, never-block-on-the-human |
| SB-24 | Evidence/conformance | AC-08 | pstack four-plane receipt and native adapter proof |

These SB names are a *reference-analysis index*. AC names are *design ownership boundaries*. Neither set is a new portable capability enum.

## Original source anchors and observed behavior

- `packages/senpi-task/src/dag/graph.ts`: deterministic compiler; dependencies order execution **only**, not artifact transport.
- `packages/senpi-task/src/dag/AGENTS.md`, `scheduler.ts`: dependency-frontier admission, node recovery and conservative launch boundary.
- `packages/senpi-task/src/workpool/{types,reconcile,schema}.ts`: keyed yield records, delivery phases, `delivery_uncertain` handling; no blind replay.
- `packages/senpi-task/src/state/run-fence.ts`: live/superseded/legacy/unknown epoch distinctions; not a remote API side-effect fence.
- `packages/team-core/src/types.ts`, `team-tasklist/claim.ts`, `team-mailbox/reservation.ts`: collaboration state/claims/mailbox; one execution scope, not authoritative program scheduler.
- `packages/model-core/src/model-resolution-pipeline.ts`: explicit override precedence can return a requested slug without testing current availability; final pstack-bound native dispatch must validate constraints.
- `packages/omo-config-core/AGENTS.md`: harness-neutral config core with adapter projections, no replacement pstack role registry.
- `packages/memory-core/AGENTS.md`, `src/git/commit-outcome.ts`, `src/git/repo-lock-sweep.ts`: git-committed memory, lock discipline, outcome-based resolution of timed-out Git commits.
- `packages/isolation-core/AGENTS.md`: owned workspace and conservative cleanup.

OmO `dev` has changed substantially between 2026-10-17 source snapshots. A refreshed extraction must identify the commit and compare the files it uses, not assume old prose is current.

## Canonical methodology flow

```text
requirement / issue
  -> how / why / blast-radius (ground system and boundaries)
  -> architect + optional arena (design candidates, freeze rubric)
  -> multi-phase-plan / orchestrate (verifiable units and dependency graph)
  -> feature / refactoring / tdd where useful (bounded implementation)
  -> swarm for parallel coverage or declared race (complete join)
  -> interrogate for independent challenge (no automatic edits)
  -> create-verification-skill / prove-it-works (real artifact)
  -> shipping (fresh patch/revision evidence and contiguous integration)
  -> show-me-your-work + session-pickup (decision trail and rollover)
```

The playbook is chosen by intent and scale; this is a menu of eligible compositions, not a mandatory giant workflow for every trivial task.

## Normalized source-level conclusion

The most valuable OmO patterns are graph validation, admission readiness, durable run identities, Workpool delivery uncertainty, context-safe recovery and owned isolation. The most valuable pstack contribution is not another runtime: it is policy constraints, method selection, independent evaluation and verifiable acceptance. Recompose by mapping OmO mechanics to host-native postconditions, not by copying its orchestration database, model catalog and session manager into portable pstack.
