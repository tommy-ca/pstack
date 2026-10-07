# pstack-jev-decisions Specification

## Purpose

Define the smallest optional integration of TypeSafe Jev decision models into pstack without replacing canonical router semantics, playbooks, agent reasoning, verification, host adapters, or human safety gates.

Jev is a bounded semantic decision primitive. It is not a pstack agent role, coding model, workflow runtime, durable orchestration store, or authority for irreversible actions.

Program tracking: #193.

## Requirements

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
  > Jev bounded semantic decision
  > System-Two LLM judgment
  > human preference/gate when required
```

This ordering describes authority, not mandatory execution. A higher layer MAY settle a decision without invoking lower layers.

Jev MUST NOT override deterministic state, an explicit slash command, hard safety policy, or a required human gate.

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

Later candidates MAY include task-complexity/model-tier hints, review-finding triage, or semantic completion checks only after separate evidence.

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

Portable/shared pstack surfaces MUST depend only on a small host-neutral decision contract.

TypeSafe/Jev SDK, HTTP, authentication, model identifiers, retries, serialization, and provider errors MUST stop at the provider boundary.

The implementation MUST NOT introduce a generic multi-provider gateway unless independent evidence later proves that abstraction is necessary.

#### Scenario: provider replacement or removal

- **GIVEN** shared routing logic consumes a typed decision result
- **WHEN** the Jev adapter is removed or replaced by a test/recorded provider
- **THEN** shared playbooks and skills require no semantic rewrite

### Requirement: The decision result is typed and auditable

A decision result MUST carry enough information to evaluate it without exposing hidden reasoning.

Minimum shape:

```yaml
Decision:
  kind: string
  value: scalar | enum
  confidence: optional number
  probabilities: optional map
  source: rule | jev | llm | human | observation
  model: optional string
  policy_version: string
  mode: shadow | advisory | controlling
```

Evidence MAY additionally record task fixture/revision and provider timing/cost.

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

## Initial decision vocabulary

The pilot MAY define a small vocabulary such as:

```yaml
playbook_class:
  choice:
    - investigation
    - bug_fix
    - performance
    - feature
    - refactor
    - prototype
    - review
    - shipping
    - orchestration
    - other

requires_runtime_evidence:
  boolean: true

requires_design_exploration:
  boolean: true

parallelizable:
  boolean: true

scope_complexity:
  score:
    - local
    - multi_file
    - cross_subsystem
    - project_scale

human_preference_required:
  boolean: true
```

The vocabulary is illustrative rather than a requirement to ask every question for every task.

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

## Program graph

Epic #193 owns delivery.

```text
#182 decision contract
   ↓
#183 Arena seam selection
   ↓
#184 optional provider adapter
   ↓
#185 shadow routing
   ↓
#186 eval/calibration lever
   ↓
┌──────────────┬────────────────┐
↓              ↓
#187 Swarm     #188 Interrogate
└──────────────┬────────────────┘
               ↓
             #189 selective promotion
```

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
