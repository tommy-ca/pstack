# pstack-jev-decisions Specification

## Purpose

Define the smallest optional integration of TypeSafe Jev decision models into pstack without replacing canonical router semantics, playbooks, agent reasoning, verification, host adapters, or human safety gates.

Jev is a bounded semantic decision primitive. It is not a pstack agent role, coding model, workflow runtime, durable orchestration store, or authority for irreversible actions.

## ADDED Requirements

### Requirement: Existing pstack semantics remain authoritative

Canonical pstack principles, skills, playbook intent/order, explicit commands, deterministic facts, verification rules, autonomy rules, and human gates MUST remain authoritative.

A Jev integration MUST be removable or disabled without changing baseline pstack behavior.

#### Scenario: Jev is disabled or unavailable

- **GIVEN** a valid pstack task
- **WHEN** Jev is disabled, unavailable, times out, abstains, returns low confidence, or returns an invalid response
- **THEN** pstack follows the same non-Jev route it would have followed before this integration
- **AND** no safety or autonomy gate is weakened

### Requirement: Decision precedence is explicit

Decision precedence MUST be:

```text
exact deterministic fact
  > explicit user command
  > hard safety/autonomy policy
  > bounded semantic-provider decision
  > System-Two LLM judgment
  > human preference/gate when required
```

This ordering describes authority, not mandatory execution. A higher layer MAY settle a decision without invoking lower layers.

A bounded semantic provider MUST NOT override deterministic state, an explicit slash command, hard safety policy, or a required human gate.

#### Scenario: explicit playbook command

- **GIVEN** the user explicitly invokes a pstack skill or playbook
- **WHEN** routing begins
- **THEN** that explicit route bypasses Jev classification
- **AND** Jev may at most record non-controlling shadow evidence

### Requirement: Jev questions are atomic bounded judgments

A Jev question MUST express one bounded semantic judgment as one of:

```text
choice
score
boolean
```

Questions SHOULD be independent and SHOULD NOT ask Jev to generate plans, code, prose, workflows, or tool calls.

Complex policy MUST be recomposed in ordinary pstack code from several atomic decisions rather than hidden inside one oversized prompt.

#### Scenario: playbook classification

- **GIVEN** a task with no explicit or deterministic route
- **WHEN** Jev is used for playbook classification
- **THEN** it selects among a closed task-class vocabulary or abstains
- **AND** ordinary pstack policy maps that result to a playbook

### Requirement: Phase-1 scope is routing and skill suggestion only

The first controlling candidates MUST be limited to:

1. playbook classification when explicit/deterministic routing did not already settle the route;
2. skill suggestion/ranking.

Before promotion, both MUST run in shadow mode with zero externally observable routing change.

Any later use case requires its own evidence and specification change.

#### Scenario: shadow mode

- **GIVEN** the Jev integration is in shadow mode
- **WHEN** pstack handles a task
- **THEN** the existing router remains the acting decision maker
- **AND** Jev decisions are recorded only for evaluation
- **AND** user-visible execution remains unchanged

### Requirement: High-risk and generative work stays outside Jev

Jev MUST NOT own:

- code generation;
- architecture synthesis;
- open-ended research;
- root-cause reasoning;
- exact arithmetic or exact runtime-state computation;
- tool execution;
- irreversible-action approval;
- shipping or merge authority;
- human product/preference decisions.

Jev MAY provide advisory narrow predicates around those workflows, but their controlling judgment remains with deterministic policy, System-Two reasoning, or a human gate as appropriate.

#### Scenario: irreversible action

- **GIVEN** a task reaches a pstack always-pause action
- **WHEN** a Jev result says the action appears safe
- **THEN** the existing human gate remains mandatory
- **AND** the Jev result cannot authorize the action

### Requirement: TypeSafe/Jev is isolated behind one optional provider boundary

Portable/shared pstack surfaces MUST depend only on a small host-neutral semantic-decision contract.

The portable contract MUST NOT name Jev-specific transport, SDK, authentication, model, or wire types. Provider identity belongs in metadata, not in the core decision-source type.

TypeSafe/Jev SDK, HTTP, authentication, model identifiers, bounded retries, serialization, and provider errors MUST stop at the provider boundary.

The provider boundary owns provider I/O only. Routing policy, authority precedence, and evidence persistence remain separate responsibilities.

The implementation MUST NOT introduce a generic multi-provider gateway unless independent evidence later proves that abstraction is necessary.

#### Scenario: provider replacement or removal

- **GIVEN** shared routing logic consumes a typed decision result
- **WHEN** the Jev adapter is removed or replaced by a test/recorded provider
- **THEN** shared playbooks and skills require no semantic rewrite

### Requirement: Semantic outcome and integration receipt are separate

The provider outcome MUST describe only the bounded semantic judgment. Routing authority and evidence metadata MUST stay outside the provider result.

Minimum provider outcome:

```yaml
SemanticDecisionOutcome:
  status: decided | abstain | unavailable
  kind: choice | score | boolean
  value: optional scalar | enum
  confidence: optional number
  probabilities: optional map
  provider: optional string
  model: optional string
```

The integration MAY wrap that outcome in an auditable receipt:

```yaml
DecisionReceipt:
  source: deterministic | semantic_provider | system_two | human | observation
  outcome: SemanticDecisionOutcome | scalar | enum
  policy_version: string
  mode: shadow | advisory | controlling
```

A provider MUST NOT decide or mutate `mode`, authority precedence, acting route, or evidence persistence. Those belong to routing policy and the evidence layer.

Evidence MAY additionally record task fixture/revision, canonical mapping revision, and provider timing/cost.

pstack MUST NOT require or store private chain-of-thought.

### Requirement: Confidence is calibrated per decision and consequence

The integration MUST NOT use one universal confidence threshold.

Promotion thresholds MUST be calibrated from a versioned pstack task corpus and SHOULD reflect the cost of a wrong decision.

Low confidence MUST fall through to baseline pstack behavior or a stronger decision layer.

#### Scenario: ambiguous task

- **GIVEN** a task whose Jev classification is below the calibrated controlling threshold
- **WHEN** routing continues
- **THEN** pstack falls back to its existing System-Two route
- **AND** the low-confidence decision is retained only as evaluation evidence when configured

### Requirement: Evaluation precedes control

No Jev result MAY alter pstack behavior until a rerunnable evaluation lever measures it against baseline behavior.

The evaluation MUST include representative playbook/task classes, explicit-command bypasses, ambiguous cases, negative cases, and known jaggedness cases.

Metrics MUST include at least:

- route accuracy;
- unnecessary activation false positives;
- missed-rigor false negatives;
- abstention precision;
- calibration/reliability;
- latency and cost.

A metric MUST be explained before it is used as a promotion gate.

### Requirement: pstack verification playbooks gate promotion

The program MUST use pstack's existing compositions rather than inventing new verification workflows.

- **Arena** compares integration seams before implementation.
- **Build the Lever** supplies deterministic evaluation/calibration.
- **Swarm** covers independent task/harness slices and failure modes.
- **Interrogate** adversarially reviews semantic drift, safety, provider coupling, and false confidence.
- **Prove It Works** gates promotion from shadow/advisory to controlling behavior.

#### Scenario: promotion

- **GIVEN** calibrated shadow evidence exists
- **WHEN** a Jev route is proposed for controlling mode
- **THEN** required Swarm slices have PASS evidence
- **AND** Interrogate has no unresolved Act on finding
- **AND** rollback to baseline behavior remains trivial

### Requirement: Jev does not expand the harness portability floor

A harness MUST NOT need Jev support to satisfy pstack portability or to reach supported status.

Jev integration is an optional product capability layered above the portable semantic contract.

Harness-specific Jev invocation details MUST NOT leak into shared skills/playbooks.

#### Scenario: supported harness without Jev

- **GIVEN** a harness satisfies the pstack portability conformance floor
- **AND** no Jev provider is configured
- **WHEN** support state is derived
- **THEN** absence of Jev does not reduce the harness support state

### Requirement: Minimal-change implementation is an invariant

The pilot SHOULD be implementable with only:

- one typed decision contract/policy surface;
- one optional Jev provider adapter;
- one reversible router/skill-suggestion hook;
- one evaluation fixture/lever surface.

The pilot MUST NOT add a workflow DSL, scheduler, task database, new agent hierarchy, or durable decision service.

Any larger abstraction requires separate evidence and review.

## Minimal control flow

```text
user/event
   ↓
deterministic facts + explicit commands + hard policy
   ↓ unresolved bounded semantic fork
optional Jev decision
   ↓ high-enough calibrated confidence
existing pstack router/policy
   ↓
existing playbook / skill / agent execution
   ↓
existing verification and human gates
```

If Jev is disabled, unavailable, abstains, or is below threshold, the Jev node collapses and the pre-existing pstack path continues.

## Principles

The integration MUST apply:

- Laziness Protocol;
- Subtract Before You Add;
- Foundational Thinking;
- Model the Domain;
- Boundary Discipline;
- Type System Discipline;
- Build the Lever;
- Prove It Works;
- Explain the Number;
- Sequence Work into Verifiable Units;
- Separate Before Serializing Shared State;
- Guard the Context Window;
- Encode Lessons in Structure;
- Attack the Premise;
- Outcome-Oriented Execution;
- DRY/YAGNI.
