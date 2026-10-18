# OMC + OMX orchestration reference audit (2026-10-18)

Status: source inspection; no execution or independent multi-model reviewer runs.

## Immutable revisions

- OMC: `Yeachan-Heo/oh-my-claudecode@6688a30e90d7285ff336af2dc5ab4b9709f1a8bc`
- OMX: `Yeachan-Heo/oh-my-codex@b4a0817e8ce2ec735ed154caeb6569c1be047419`
- pstack: `tommy-ca/pstack@4d41cc3c28d3048663a8cd740ac4a16d9728a9f2`
- official Cursor pstack observed: `0b8e952052d482ee6de06deebf14d590d77b1b34`, target normative `UPSTREAM` pin remains `1dcc2bacde73ddd284803b7af28164d0436198fc`.

## Audit verdict

OMC supplies a more expressive, sealed graph contract than the earlier OmO scheduling-only DAG: typed agent/command/human-approval/join nodes, explicit effect policies, fanout, conditional, bounded back edges, a deterministic projection reducer and journal-owned recovery. Its graph runner and contained filesystem are an optional host implementation; never assume a graph runner automatically owns the parent pstack program.

OMX supplies a CLI-owned task mutation contract, claim/version tokens, bounded team plan/PRD/execute/verify/fix transitions, goal ledger/steering and a structured completion report. The documented completion report format does NOT prove commands executed. Native `/goal` and shell ledger state differ.

Both sources show the need for authority scopes. OMC and OMX are MIT at the top-level LICENSE, with independent license audit needed for copied assets/dependencies.

## Matrix of behavior, gaps and transfer

| Dimension | OMC code anchor | OMX code anchor | Recomposition decision | Runtime proof |
| --- | --- | --- | --- | --- |
| Plan identity | `src/graph/descriptor.ts` | `src/team/dag-schema.ts` | validated then sealed graph revision | untested |
| Conditional/fanout/loop | `src/graph/types.ts` | `src/team/orchestrator.ts` | typed control edges; bounded back edges | untested |
| Recovery authority | `src/graph/runtime/{journal,store,fence}.ts` | `src/state/workflow-transition-reconcile.ts` | owner epoch, one journal authority, projections secondary | untested |
| Team mutation | `src/team/api-interop.ts` | `docs/interop-team-mutation-contract.md`, `src/team/state/tasks.ts` | call native mutation API, not direct private file writes | untested |
| Native session goal | `docs/ultragoal.md` | `skills/ultragoal/SKILL.md` | model-facing session directive separate from ledger | untested |
| Artifact verification | `src/graph/types.ts` | `src/team/completion-evidence.ts` | exact artifact + real verifier, not structured self-report | untested |
| Delivery/integration | `src/team/merge-coordinator.ts` | `src/team/worktree.ts` | exclusive integrator; reverify changed patch | untested |
| Portability | OMC Claude-specific hooks | OMX Codex/tmux-specific CLI | stable host-neutral postconditions, native adapter differences | untested |

## pstack method mapping

- Principles: Boundary Discipline, Model the Domain, Idempotency, Separate Before Serializing Shared State, Prove It Works, Guard the Context Window, Type System Discipline, Subtract Before You Add.
- Leaf skills: how, why, architect, blast-radius, create-verification-skill, show-me-your-work.
- Compositions: swarm (complete coverage), arena (frozen rubric, isolated candidates, graft and post-check), interrogate (independent read-only findings, no auto-fix).
- Playbooks: multi-phase-plan, orchestrate, autonomous-run, session-pickup, shipping.
- Host semantics: existing 17 capabilities; model-plan policy remains proposal-stage in ADR-0021. Do not introduce a competing role catalog.

## Blocking questions and test observations

1. Is the native OMC graph runner tested as an independently surviving external controller, or only as bounded child? Source proves primitives, not deployment equivalence.
2. Does the authoritative host support artifact-typed inputs? Neither team task `depends_on` nor graph control edges alone prove transfer.
3. Does a model plan actually bind the chosen native model? Static planning cannot substitute for native child settlement.
4. Do OMX structured evidence files correspond to commands actually run? Independent driver/receipt required.
5. Do OMC POSIX contained-filesystem guarantees cover the target platform? Explicit capability gate; do not assume Windows parity.
6. Can agent review contexts be proven independent? Fresh identity/workspace and read-only enforcement required.
7. Is a goal LEDGER report synchronized with native /goal? Need explicit session observation; do not equate the two.

## Analytical methodology result

Swarm: seven review partitions covered in source; all runtime partitions UNTESTED. Arena: choose existing host + bounded OMC/OMX child execution over copying both runtimes; standalone graph-core-host remains optional and mutually exclusive. Interrogate: blocking flaws are duplicate owners, graph-digest drift, unsupported effect retries, unsupported native /goal claim, review-context leakage, unverifiable evidence, and stale patch acceptance. No live multi-agent Swarm, Arena, or Interrogate was performed.

## Proposed acceptance criteria

All OpenSpec change tasks G0–G7 remain open until executable checks and four-plane pstack receipts prove native behavior. Maintain source-at-commit traceability and reconcile #502 rather than clone its 24-block catalog.
