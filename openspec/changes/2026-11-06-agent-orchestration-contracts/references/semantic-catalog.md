# Source-backed atomic semantic catalog

**Purpose:** atomic reusable concepts for PStack orchestration; these are *concepts*, not imported dependencies. Each link is pinned to the observed commit.

| Atomic concept | Source anchor | Semantic contract | Disposition for PStack |
| --- | --- | --- | --- |
| Workstream scope | [Mu workstream](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/src/workstream.ts) | Partition tasks and agent ownership by explicit scope | Adopt contract, existing orch owner |
| Dependency edge | [Mu DAG](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/dag.md) | One unambiguous `blocks` edge; derive readiness; reject cycles | Adopt invariant, no parallel DAG engine |
| Atomic claim | [Mu DAG](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/dag.md) | Exclusive assignment under concurrent claim | Conditional adapter test |
| Task note / evidence | [Mu DAG](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/dag.md) | Durable, append-only observations independent of LLM context | Adopt evidence principle |
| Operation history | [Mu ops log](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/ops-log.md) | Same-transaction mutation/history and rebuildable projections | Reference only; do not import DB |
| Replay and drift | [Mu ops log](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/ops-log.md) | Recompute expected state and compare against materialization | Adopt verifier idea, not storage |
| Causal sync | [Mu sync](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/sync.md) | Single-writer JSONL segments; HLC, watermarks, integrity check | Exclude until multi-host state needed |
| Mux adapter | [Mu architecture](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/ARCHITECTURE.md) | Branch on capabilities, not backend names | Adopt boundary discipline |
| Agent control | [Mu control socket](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/ARCHITECTURE.md) | Explicit send/state/wait/abort, no silent TTY fallback | Conditional opt-in adapter |
| Bounded wait | [Mu wait](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/src/wait.ts) | One correlated event; deadline, cancellation and resumption | Adopt invariant in existing join |
| Resource admission | [Dogsled admission](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/src/admissions.rs) | Queue or reserve before execution, never hide saturation | Conditional opt-in placement |
| Resource quota | [Dogsled quota](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/src/quota.rs) | Explicit bounded host capacity | Optional future, not a core scheduler |
| Execution identity | [Dogsled unit requests](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/unit-requests.md) | Owner + origin + invocation ID + request ID remain stable | Adopt typed contract |
| Prepare/commit/observe | [Dogsled unit requests](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/unit-requests.md) | Prepared is not launched; observe must not dispatch; unresolved is not success | Adopt formal safety conditions |
| Agent lifecycle | [Dogsled lifecycle](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/lifecycle.md) | Turn stopped is not task completed; explicit terminal evidence needed | Adopt invariant |
| Ownership / custody | [Dogsled custody](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/src/custody.rs) | Children retain an accountable owner until settled/released | Adopt contract; runtime host-owned |
| Crash-safe launch | [Dogsled jobs](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/README.md) | Non-executable intent precedes executable claim; uncertain launch cannot be blindly retried | Adopt negative checks |
| Worktree preservation | [Dogsled lifecycle](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/lifecycle.md) | Uncommitted work preserved before cleaning orphan checkout; no proof means no deletion | Adopt safety invariant |
| Owner inbox | [Dogsled inbox](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/src/inbox.rs) | Route ask/blocked signals to accountable parent | Reuse native host transport |
| Repair/reconciliation | [Dogsled lifecycle](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/lifecycle.md) | Observed unknown/lost states remain visible until evidence resolves them | Adopt status vocabulary |
| Isolated review | [Cursor Arena](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/arena/SKILL.md) | Same frozen brief, isolated outputs, evidence-backed selection/grafting | Reuse existing skill |
| Independent coverage | [Cursor Swarm](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/swarm/SKILL.md) | Partition or declare race; account for every worker/dropout | Reuse existing skill |
| Falsification | [Cursor Interrogate](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/interrogate/SKILL.md) | Independent reviewer challenges and reproduced findings | Reuse existing skill |
| Simplification lens | [Thermos code quality](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-code-quality-review/SKILL.md) | Simplify layers, discourage spaghetti, avoid false abstractions | Reuse at review gate |
| Correctness lens | [Thermos review](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/thermos/skills/thermo-nuclear-review/SKILL.md) | Scope to changed diff, prove security/correctness concerns | Reuse at review gate |

## Recomposition

`Intent -> WorkUnit -> ExecutionRequest -> HostAdapter/Executor -> ExecutionReceipt -> Evidence -> Verdict -> (accept | rework | ask)`

- **Principles:** separate policy from execution; explicit authority; idempotent transitions; visible uncertainty; fail-closed safety; evidence before PASS; preserve outputs before cleanup.
- **Skills:** reuse existing `swarm`, `arena`, `interrogate`, `create-verification-skill`, `create-formal-verification-skill`; don't mint redundant leaves.
- **Playbooks:** plan a dependency DAG; dispatch independent bounded units; join all; challenge outputs; verify against acceptance; synthesize; ship via existing PStack shipping playbook.
- **QStack:** import *conceptual* invariants as optional quant-domain overlays only; never add reverse imports or another software-development task store.

## Audit risks (hypotheses, not verified defects)

- Unknown or stale host evidence treated as a successful end state.
- Retry of an unproven launch creating a second worker.
- Worktree cleanup after an aborted child discarding untracked/dirty files.
- Reviewers with duplicated contexts or model aliases presented as independent.
- Static check or source narrative presented as live execution proof.
- Feature additions that accidentally import Mu task policy or Dogsled admission policy as PStack core dependencies.

Each requires a reproducible mutation or live observation before it is a confirmed finding.
