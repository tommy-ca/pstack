## Context

Cross-harness portability has historically been treated as a set of translation notes rather than an explicit boundary contract. Official pstack remains pinned at `cursor/plugins/pstack@UPSTREAM`.

## Goals / Non-Goals

**Goals:**
- Provide a small, typed capability and binding model.
- Separate pin conformance from upstream freshness.
- Retain composed skills (Swarm, Arena, Interrogate) without inventing new primitives.
- Retain Grok as a strong reference adapter without imposing its fields on other hosts.

**Non-Goals:**
- Introducing a runtime engine, workflow DSL, scheduler, or session database.
- Rewriting playbooks into an intermediate language.

## Decisions

- **Boundary Discipline**: Host-specific vocabulary stops at the adapter.
- **Model the Domain**: Define typed states for capability, binding, adaptation, evidence, and support.
- **Laziness Protocol**: Smallest specification that accurately reflects reality.
- **Build the Lever**: Verification must be executable and rerunnable.

## Risks / Trade-offs

- Specifying dynamic discovery before the discovery lever lands requires backward-compatible wording during the transition.

## Migration Plan

1. Formalize the spec and porting documentation.
2. Build the foundation index lever (Issue #49).
3. Validate schemas and run architecture gates before pilot scaling.

## Open Questions

- None for this spec phase.
