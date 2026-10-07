## Why

pstack already has a strong router/playbook/skill architecture. TypeSafe Jev can improve a narrow class of fast bounded decisions, but a broad integration would violate pstack's Laziness Protocol and portability boundary.

This change formalizes Jev as an optional advisory decision primitive, not an agent role or workflow runtime. It preserves baseline pstack behavior and requires shadow evidence before any controlling route.

Program: #193.

## What Changes

- Add the `pstack-jev-decisions` formal capability spec.
- Clarify that optional decision providers do not expand the pstack portability support floor.
- Define decision precedence, typed decision output, abstention/fallback, and provider boundary.
- Restrict the pilot to playbook classification and skill suggestion.
- Require shadow mode, a calibration lever, Arena seam selection, Swarm coverage, and Interrogate review before promotion.
- Keep Jev out of code generation, architecture synthesis, exact computation, tool execution, irreversible approval, shipping authority, and human preference decisions.

## Capabilities

### New Capabilities

- `pstack-jev-decisions`: optional bounded semantic decision support with evidence-gated promotion.

### Modified Capabilities

- `pstack-portability`: clarifies that Jev is optional and is not part of the harness conformance floor.

## Impact

Specification and planning only. No runtime behavior changes in this change.