# Proposal: OMC + OMX reference semantics for long-horizon pstack

## Why

The current OmO extraction in draft PR #502 classifies 24 reference blocks under eight design contracts. OMC and OMX have stronger reference implementations for graph sealing and effect policies, mode-transition policy, owner fencing, team mutation APIs, goal ledgers, and completion evidence. Directly importing either runtime would violate accepted ADR-0006 (host-owned durable orchestration) and risk duplicating the existing 17 portable capabilities or the proposed model-role planner (ADR-0021).

## What changes

- Review OMC and OMX against immutable heads, canonical Cursor pstack methodology, and #502.
- Extend the *semantic reference* catalog, not the public portable capability enum; keep pstack principles, leaf skills, playbooks and runtime mechanisms distinct.
- Introduce **proposed, host-neutral** schema contracts for a sealed graph revision and bounded execution handoff with explicit control and artifact dependencies.
- Specify effect policy (side-effect-free, idempotent, reconcile), bounded back edges, authoritative mutation ports, attempt fencing, checkpoint/goal ledgers, independent evidence and revision-bound acceptance.
- Add explicit crosswalks, data/code flow, Swarm/Arena/Interrogate review, fault-injection acceptance tests and a depth-first execution graph.
- Preserve one authoritative host per namespace; bounded OMC/OMX execution may be nested under a host work unit without sharing scheduler authority.

## Scope

Documentation, OpenSpec proposed deltas, and JSON Schema exemplars only; no runtime code or native harness behavior claims. This PR should be reviewed alongside #502 before either change is accepted. No upstream code is copied. Both inspected top-level LICENSE files state MIT, but transitive assets/dependencies require their own review if future copying is contemplated.

## Source pins

- OMC `Yeachan-Heo/oh-my-claudecode` `main`: `6688a30e90d7285ff336af2dc5ab4b9709f1a8bc`
- OMX `Yeachan-Heo/oh-my-codex` `main`: `b4a0817e8ce2ec735ed154caeb6569c1be047419`
- Port `tommy-ca/pstack`: `4d41cc3c28d3048663a8cd740ac4a16d9728a9f2`
- Official pstack observed head: `0b8e952052d482ee6de06deebf14d590d77b1b34`; normative port pin stays `1dcc2bacde73ddd284803b7af28164d0436198fc`.
