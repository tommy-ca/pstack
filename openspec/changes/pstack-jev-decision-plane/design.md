# Design

## Design goal

Add the smallest removable decision seam that can exploit Jev where it is strong without making Jev a dependency of canonical pstack semantics.

## Chosen architecture

```text
deterministic facts / explicit command / safety policy
                     ↓ unresolved bounded fork
              optional DecisionProvider
                     ↓
               existing pstack router
                     ↓
           existing skills/playbooks/agents
                     ↓
             existing verification/gates
```

Jev implements one optional provider behind a typed boundary. Shared pstack consumes only a provider-neutral decision result.

The responsibilities stay separate:

- **Routing policy** decides whether a semantic-provider decision is eligible and how it composes with higher-authority rules.
- **Decision provider** performs one bounded semantic judgment and returns a typed outcome.
- **Evidence sink/lever** records or evaluates receipts outside the provider interface.
- **TypeSafe/Jev adapter** owns provider-specific transport, auth, model, serialization, and bounded retry behavior.

This separation keeps the core dependent on the abstraction rather than on Jev, while avoiding a speculative multi-provider framework.

## Why not a new agent

Jev is not responsible for generation, long-horizon reasoning, tool use, architecture, or execution. Modeling it as a worker role would encourage scope creep and force unnecessary changes into swarm/arena/interrogate and harness profiles.

## Why not a generic provider gateway

The current requirement is one optional decision model. A general provider framework is speculative. Introduce only the boundary required to keep TypeSafe/Jev syntax out of portable/shared pstack.

## Failure semantics

Every failure collapses to baseline pstack:

```text
disabled
unavailable
timeout
invalid result
abstain
below threshold
        ↓
existing pstack decision path
```

No retry policy may block task progress indefinitely.

## Pilot decisions

1. Playbook classification when neither explicit command nor deterministic rule already decides.
2. Skill suggestion/ranking.

Both begin in shadow mode. No later Jev use case is pre-designed here. It must earn a separate change after the pilot.

## Decision receipt

A receipt records decision value, optional probability/confidence, provider/model, policy version, mode, fixture/revision, and optional timing/cost. It records no hidden chain-of-thought.

## Verification

1. #182/#195/#196 settle the typed decision contract, external-context boundary, and canonical playbook vocabulary.
2. #183 Arena compares integration seams, including the no-change control, using a predeclared rubric.
3. #197 reconciles PR #194, runs strict OpenSpec validation and a spec-level Interrogate, then accepts the implementation contract.
4. #184/#185 implement only the optional provider and zero-behavior-change shadow hook.
5. #186 builds deterministic offline calibration, latency, and cost evidence.
6. #199 binds evidence to implementation/canonical/provider-model/policy/fixture revisions and demotes stale evidence.
7. #198 runs the canonical blinded Eval playbook against baseline pstack.
8. #187 Swarm, #188 Interrogate, and #200 rollback proof run independently at the exact candidate head.
9. #189 may promote only the smallest proven low-risk seam. No promotion is a valid outcome.

## Non-goals

- no workflow DSL;
- no second durable tracker;
- no decision database;
- no generic model gateway;
- no playbook rewrite;
- no Jev agent role;
- no weakening of human gates.
