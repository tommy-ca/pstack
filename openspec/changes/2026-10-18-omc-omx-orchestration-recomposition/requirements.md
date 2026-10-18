# Requirements baseline — AO-OMCX-001

Status: Proposed. Normative MUST/SHOULD statements apply to the recomposed design; they do not assert existing OMC/OMX runtime conformance.

## Functional and recovery requirements

| ID | Priority | Requirement | Acceptance scenario |
| --- | --- | --- | --- |
| AO-01 | P0 | Only the selected external host MUST own program graph revision, work claim, retries, acceptance and verified integration for one namespace. | Host + native team simultaneously attempt same parent mutation; only host transition accepted |
| AO-02 | P0 | A draft graph MUST undergo deterministic structural validation and integrity sealing before execution; digests MUST be checked when read. | GRAPH-01 |
| AO-03 | P0 | Graph node kinds MUST be explicit: agent, command, approval or join; unsupported native kinds MUST map to adaptations or gaps. | GRAPH-01 |
| AO-04 | P0 | Control flow MAY contain conditional/fanout/bounded-backedge semantics; unconstrained cycles MUST be refused. | GRAPH-02 |
| AO-05 | P0 | Every executable node MUST declare side-effect-free, idempotent or reconcile retry policy; idempotent effects require stable external identity. | EFFECT-01 |
| AO-06 | P0 | The scheduler MUST distinguish control dependencies from typed, validated artifact/data dependencies. | DATA-01 |
| AO-07 | P0 | Work, attempts, native sessions and goal ledgers MUST have separate identities and lifecycle states. | GOAL-01 |
| AO-08 | P0 | Each dispatch MUST retain work ID, attempt ID, generation, identity key, graph revision and authorized model plan. | OWN-01 |
| AO-09 | P0 | The adapter MUST enforce actual native model/tool/permission eligibility against its approved plan. | POLICY-01 |
| AO-10 | P0 | Native task mutation MUST use the owning runtime's supported API, including claim/version/lease preconditions. | OWN-01 |
| AO-11 | P0 | Recovery MUST reconcile native session/process and effect observations before retry; unknown MUST remain nonterminal. | OWNER-02, EFFECT-01 |
| AO-12 | P0 | Native /goal directives and repo-persisted goal/Ultragoal records MUST NOT be represented as identical authority. | GOAL-01 |
| AO-13 | P0 | Completion report shape, path confinement and claim association MUST NOT be represented as attestation that commands ran. | EVID-01 |
| AO-14 | P0 | Verification MUST check the real artifact and bind evidence to exact digest/source revision. | EVID-01, EVID-02 |
| AO-15 | P0 | Swarm MUST account for declared partition/race rules; a missing required result MUST remain a gap. | SWARM-01 |
| AO-16 | P0 | Arena MUST freeze its rubric, isolate candidates and reverify the selected graft. | ARENA-01 |
| AO-17 | P0 | Interrogate MUST preserve independent reviewer contexts and dispositions; reviewer agents MUST NOT auto-edit the target. | INT-01 |
| AO-18 | P0 | Portable conformance MUST retain existing 17 capability IDs and four receipt planes; static source inspection MUST NOT satisfy runtime claims. | PORT-01 |
| AO-19 | P1 | Context rollover MUST rehydrate exact standing orders, accepted artifacts and current work ownership. | LONG-01 |
| AO-20 | P1 | A verified work item MAY enter the integration frontier only when all relevant ancestors/base changes remain accepted. | EVID-02, LONG-01 |
| AO-21 | P1 | Host-specific filesystem containment MUST be declared by platform; POSIX-only guards MUST NOT imply Windows support. | FS-01 |
| AO-22 | P1 | Goal steering / graph amendments MUST be versioned, authorized and unable to silently weaken active acceptance criteria. | STEER-01 |

## Nonfunctional requirements

- **Security**: Enforce writable workspace ownership, native permissions, side-effect authorization, symlink/path containment appropriate to the host, and secret redaction in traces; do not rely on prompt text as an access-control mechanism.
- **Reliability**: Use single-owner commits, attempt fencing, idempotent internal transitions, conservative ambiguous-external-effect handling and deterministic state reconciliation.
- **Portability**: Depend on observable semantic postconditions; never import Claude Code or Codex SDK types into the portable policy layer.
- **Maintainability**: Preserve one canonical role registry, one portable evidence schema and one authoritative durable state owner; prefer pure domain reducers and thin native adapters.
- **Performance**: Use bounded ready frontier and rolling worker windows; measure capacity and cost before tuning; context summaries are pointers, never substitutes for immutable artifacts.

## Explicit non-goals

Do not copy either complete OMC or OMX runtime, create a generic provider gateway, introduce a second pstack-local scheduler or database, add 22 portable capability IDs, claim native multi-agent execution based on documents, or assume all harnesses support nested agent delegation.

## Evidence and release gate

G0/G1 can be proved with pinned-source audits and offline checks. G2–G7 require executable fixtures and observed-live native adapter receipts. A draft PR may be accepted as a specification without claiming those runtime gates passed, but must retain them as open acceptance work.
