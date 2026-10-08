## Why

pstack already has a strong router/playbook/skill architecture. TypeSafe Jev can improve a narrow class of fast bounded decisions, but a broad integration would violate pstack's Laziness Protocol and portability boundary.

This change formalizes Jev as an optional advisory decision primitive, not an agent role or workflow runtime. It preserves baseline pstack behavior and requires shadow evidence before any controlling route.

Program: #193.

## What Changes

- Add the `pstack-jev-decisions` formal capability spec.
- Define decision precedence, correlated typed outcomes, strict egress, revision-bound receipts, and provider fallback.
- Specify one future canonical mapping while leaving its runtime artifact to a later review unit.
- Restrict phase one to shadow playbook classification. Skill suggestion remains unavailable until its taxonomy and caller are grounded.
- Require the accepted-spec and refreshed-baseline gates before implementation.
- Require blinded Eval, fresh evidence, exact-head Swarm and Interrogate review, and rollback proof before promotion.
- Keep Jev out of code generation, architecture synthesis, exact computation, tool execution, irreversible approval, shipping authority, and human preference decisions.

## Capabilities

### New Capabilities

- `pstack-jev-decisions`: optional bounded semantic decision support with evidence-gated promotion.

## Impact

Specification and planning only. No runtime behavior changes in this change.
