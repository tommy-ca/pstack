## Why

Earlier OmO-derived orchestration drafts treat 24 extracted semantic building blocks as if they were potential portable execution primitives. Official Cursor pstack instead separates cross-cutting principle skills, focused leaf skills, composed playbooks, and existing host capabilities. The implementation already defines 17 portable capability IDs; ADR-0006 requires durable work state to remain host-owned. The model/role policy work (ADR-0021, proposed) also already provides a typed planner seam. Without explicit ownership, porting OmO's DAG, Workpool, recovery and model routing risks duplicate controllers, registries, and unverifiable runtime claims.

## What changes

- Formalize a four-kind classification: canonical principle skills, leaf skills, workflow compositions, and runtime semantic blocks.
- Retain the existing 17 portable capabilities; define eight cohesive domain contracts as *internal specification organization*, not new capability IDs or services.
- Map all 24 OmO reference blocks to those contracts and to canonical pstack principles and workflow compositions, with source revision and parity state.
- Make control dependencies distinct from typed artifact/data dependencies; identify graph, session, attempt, artifact and verification authorities.
- Define conservative external-effect recovery, independent review, model-policy final authorization, exact-revision evidence, and a depth-first conformance graph.
- Reuse the four-plane receipt format (canonical, adapter, package, runtime), without asserting live parity.

## Modified capabilities

- `pstack-portability`: source-to-host traceability, model/role authority, recovery honesty, artifact proof semantics.
- `pstack-playbooks`: method compositions and their evidence-sensitive postconditions.
- `pstack-omo-orchestration`: reference-source learning and host-neutral contracts (new proposal).

## Scope and non-goals

This change proposes specifications and source-grounded research; it does not implement an agent engine, add host tools, modify the 17 capability IDs, copy OmO source, change accepted ADRs, or claim observed-live multi-agent runs. OmO is a reference implementation, not a new normative methodology authority. Licenses must be checked before any future implementation reuse.
