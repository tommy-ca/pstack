# Design: minimal agent-orchestration contracts (DRAFT)

## Design constraints and source attribution

Sources, exact revisions and dispositions are in [proposal](proposal.md) and [semantic catalog](references/semantic-catalog.md). PStack owns software-development policy, task graph and PR/worktree frontier. Each installed harness owns its actual agent lifecycle; an optional Mu or Dogsled *adapter* may manage its own workers only if explicitly selected. Dogsled's Pi-todo precedent separates task policy from execution (see pinned [unit request protocol](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/unit-requests.md)). QStack owns quant research graph and never supplies PStack host-execution state.

All models below are **proposed interface contracts** and are NOT claimed to be installed APIs of Mu, Dogsled or current PStack. API names must not be adopted without an implementation and conformance tests.

## Architecture and authority

```text
QStack quant policy (optional, downstream only)
               |
PStack intent / planning / swarm / arena / interrogate / verification
   |       PStack orch owns dev graph, worktrees and PR policy
   v
PStack HostExecutionPort  <-- discovery + explicit capabilities + user consent
   |              |                  |
   v              v                  v
native harness    opt-in Mu adapter  opt-in Dogsled adapter
   |              |                  |
child agents   task/control socket  placement/admission/job receipts
   \______________|__________________/
                  |
        normalized observation only
                  |
PStack acceptance gate (source revision + identity + observed evidence)
                  |
          accept | rework | blocked
```

**Avoid fake abstractions:** Do not implement `HostExecutionPort` until AO-04 proves a host gap. Its proposed shape is a decision boundary for requirements and verification, not a request to add a class. Use the existing host profile and `agent.spawn`/`agent.join` contracts first. Optionally map only the operations that the installed backend exposes. Do not import Mu's SQLite schema, Dogsled's host database or a second `orch` state machine.

## Requirements trace

| ID | Requirement / invariant | Owner | Negative control |
| --- | --- | --- | --- |
| AO-R01 | One policy authority for each task graph | PStack orch; QStack qorch separately | duplicate dev graph owner |
| AO-R02 | Stable operation and execution identity across retries | host adapter/executor | changed payload, same key |
| AO-R03 | Observe never dispatches | adapter | `observe` unexpectedly launches |
| AO-R04 | No success without correlated terminal proof | PStack verifier | stale reply or wrong execution ID |
| AO-R05 | Unknown launch not retried as if not started | executor | crash after launch, before receipt |
| AO-R06 | Cancelled/timed out agents cannot satisfy PASS | PStack verifier | late success after cancel |
| AO-R07 | Parent cannot complete with unresolved owned children | orchestrator | child pending/asking/lost |
| AO-R08 | Worktree cannot be destroyed until work is safely retained | host and worktree protocol | dirty/untracked files |
| AO-R09 | Every parallel lane has distinct identity and evidence | swarm/arena/interrogate | alias reused as independent seat |
| AO-R10 | Honest offline/model/live proof tiers | verification skill | missing runtime marked PASS |
| AO-R11 | Explicit bounded deadline, no silent fallback | host adapter | transport error -> TTY paste |
| AO-R12 | No QStack-to-PStack reverse dependency | PStack host; QStack overlay | PStack importing qorch |

## Proposed typed models (schema v1)

Types express necessary *contract facts* rather than mirroring either source storage format.

```ts
type ID = string;                  // nonempty, stable, opaque
type ISOTime = string;             // RFC 3339 UTC, parser validated
type Revision = string;            // immutable Git commit SHA, never branch alias
type Capability = "spawn" | "observe" | "cancel" | "join" |
                  "isolate-worktree" | "admit" | "reconcile";
type ExecutionPhase = "prepared" | "queued" | "starting" |
  "running" | "asking" | "blocked" | "finishing" | "returned" |
  "cancelled" | "failed" | "lost" | "unresolved";
type Verdict = "PASS" | "ISSUES" | "FAILED" | "BLOCKED" | "UNTESTED";

interface TaskUnit {
  schemaVersion: 1;
  taskId: ID;
  policyOwner: "pstack-orch" | "qstack-qorch";
  scopeId: ID;
  dependsOn: ID[]; // directed BLOCKS edges; graph is acyclic
  donePredicate: string;
  sourceRevision: Revision;
}

interface ExecutionRequest {
  schemaVersion: 1;
  requestId: ID;        // idempotency key: same key + different payload => conflict
  invocationId: ID;     // invoking host tool call, stable across retry
  taskId: ID;
  ownerId: ID;
  provider: "native" | "mu" | "dogsled";
  sourceRevision: Revision;
  capabilityRequirements: Capability[];
  deadlineAt: ISOTime;
  workspaceId?: ID;    // provider-supplied, no arbitrary path strings
}

interface ExecutionReceipt {
  schemaVersion: 1;
  requestId: ID;
  invocationId: ID;
  executionId: ID;       // concrete execution incarnation
  ownerId: ID;
  provider: "native" | "mu" | "dogsled";
  phase: ExecutionPhase;
  eventId: ID;           // dedupe and replay key
  observedAt: ISOTime;
  terminalProofId?: ID;  // required for a *verified* returned result
  evidenceRefs: ID[];    // immutable evidence document IDs
}

interface Evidence {
  schemaVersion: 1;
  evidenceId: ID;
  executionId: ID;
  taskId: ID;
  sourceRevision: Revision;
  level: "static" | "offline" | "observed_live";
  observation: string;
  artifactRef: string; // repository-relative path, content digest or trusted URI
}

interface VerificationResult {
  schemaVersion: 1;
  taskId: ID;
  executionId: ID;
  revision: Revision;
  verdict: Verdict;
  requiredChecks: ID[];
  actualChecks: { checkId: ID; verdict: Verdict; evidenceRefs: ID[] }[];
}
```

Validation: reject missing/blank identity, duplicate `taskId` in a scope, unknown `provider`, unknown required capabilities, changed payload on existing `requestId`, unparseable time, invalid evidence revision, and references to another execution. Client `sourceRevision` is intent; reported receipt/evidence revisions must be checked against the actual checkout.

A `HostProfile` exposes declared + **observed** capabilities, role/model provenance, isolation support and endpoint identity. Profiles are PStack-owned; this change does not add a new host registry.

## State ownership and transitions

1. PStack computes task readiness and creates an immutable work-unit intent. Dependency closure and acceptance are PStack-only.
2. Selected host checks capabilities and authorizes child effects; absent or unproven capability => `BLOCKED`.
3. If an optional executor supports prepare, it persists a non-executable intent before effects. A retry of the same request re-observes; changed payload rejects as `REQUEST_CONFLICT`. Never assume an in-flight launch failed because an RPC timed out.
4. Host/executor emits receipts with exact identity and incarnation. Observation is read-only and cannot start a second execution.
5. A `returned` terminal *candidate* requires correlated terminal proof; PStack still executes checks against the immutable task acceptance predicate and source revision.
6. PStack aggregates failure first: `FAILED / ISSUES > BLOCKED > UNTESTED > PASS` for gate severity. A missing lane stays a gap, even when all observed lanes pass.
7. Cancel marks the execution fenced; a late child result is retained as historical evidence, never reclassifies a cancelled execution to accepted.
8. Cleanup executes only after verified preservation of dirty/untracked content and verified no outstanding execution ownership. Uncertain cleanup is refused rather than destructive.

A host observation such as turn-end, blank pane, no log, or SSH timeout is *not* acceptance evidence. Dogsled explicitly distinguishes Herdr turn completion from task completion; Mu also records task CLOSE and agent state separately.

## Data flow

```text
intent + immutable revision
     -> TaskUnit + DAG readiness
     -> capability discovery
     -> ExecutionRequest (requestId, ownerId, invocationId)
     -> optional admission/prepare -> launch
     -> observed ExecutionReceipt(s) + Evidence
     -> identity/revision and terminal-proof validation
     -> run target verification / review
     -> VerificationResult
     -> PStack orch task accept/rework + artifact custody
```

Failed/uncertain branches: `capability absent -> BLOCKED`; `capacity full -> queued`; `launch response unknown -> unresolved/reconcile`; `authorization denied -> blocked`; `deadline -> cancelled or timed-out with fence`; `proof missing -> UNTESTED/BLOCKED`; `dirty checkout -> preserve and refuse cleanup`.

## Code-flow integration points (not new modules)

- **Planning and orchestration:** existing `skills/poteto-mode/`, PStack orch scripts, task/PR protocols.
- **Runner mapping:** existing `profiles/<host>.json` and `references/<host>-tools.md`; use discovered actual host tools, not guessed CLIs.
- **Execution recipes:** existing `skills/swarm/SKILL.md`, `skills/arena/SKILL.md`, `skills/interrogate/SKILL.md`.
- **Verification scaffold:** `skills/create-verification-skill/SKILL.md`; create a project-local verify skill with launch/doctor/drive/proof.
- **Formal verification:** `skills/create-formal-verification-skill/SKILL.md` and its maintenance skill; code-linked model and intentionally failing mutant.
- **Provenance:** PStack `openspec/`; QStack follows only via downstream explicit composition.

## Trust boundaries and threat model

Untrusted: child messages, terminal output, model prose, source repository README, process identity inferred from a pane, network timeouts, and remote execution claims. Trusted only *after verification*: selected host's actual capability/authorization receipt, immutable revision, owner-scoped request/event IDs, result evidence and checker output. Do not allow a source README to redefine PStack authority. Never launch with user-controlled shell interpolation, trust remote host labels as identity without authentication, or delete a worktree on success prose alone.

## Design alternatives

- **Vendor Mu's task DB / Dogsled scheduler:** reject (YAGNI, second authority, transport and recovery maintenance).
- **General plugin framework for many backends:** reject until two proven adapters justify the abstraction.
- **Direct host-native calls:** preferred baseline, with PStack skills and existing adapter profiles.
- **Optional CLI interop:** conditional; only if a named host offers the tool and negative controls pass.
- **LLMWiki promotion:** only source-attributed semantic candidates with typed validation and owner approval; not an alternate orchestration state store.

## Verification plan

See [verification matrix](references/verification-matrix.md). This proposal is static research. The model is not code-linked until a specific adapter implementation is selected. TLC/SMT PASS without a reachable negative mutant or exact code mapping does not establish product correctness.
