# pstack-portability delta: OmO semantic mapping and evidence

## ADDED Requirements

### Requirement: Reference semantic blocks do not expand portable capability identifiers
An OmO-derived domain block MUST map to the existing 17 portable capability postconditions or to host-owned/internal methodology behavior. A new portable capability identifier MUST NOT be introduced merely because OmO exposes a DAG, team, Workpool, memory or model router.

#### Scenario: Workpool used for Swarm dispatch
- **GIVEN** a host offers a native reusable worker pool
- **WHEN** pstack maps a Swarm plan to that mechanism
- **THEN** it continues to report ordinary `agent.spawn` and `agent.join` postconditions, plus isolation and evidence requirements
- **AND** it does not add a portable `workpool` capability or a new scheduler.

### Requirement: Model selection has one authority and a separate native settlement
The canonical role registry remains `pstack.package.json#/roles`. Where the proposed ModelPlan contract is adopted, a selected native model MUST satisfy its policy/constraints. OmO model resolution MAY supply native routing implementation details but MUST NOT silently override a blocked or explicitly selected model. Planning-only evidence MUST NOT certify runtime availability.

#### Scenario: OmO native fallback conflicts with a pstack model plan
- **GIVEN** the pstack plan rejects a native fallback because it violates a hard constraint
- **WHEN** an OmO-backed adapter resolves the actual spawn
- **THEN** the adapter reports BLOCKED and does not launch that alternate model
- **AND** model availability requires its own observed native evidence.

### Requirement: Work, attempt and session identity are distinct
A host MUST retain durable work state independently of any child session. An OmO DAG acting as a bounded child MUST NOT claim authority over unrelated host work. The adapter MUST NOT infer successful work, failed work or model-backed child resume merely from parent-session state.

#### Scenario: parent resumes after worker process was lost
- **GIVEN** a host work item has an authoritative attempt record and no conclusive native observation
- **WHEN** the controller reconciles after restart
- **THEN** it produces an explicit unknown, adopt, resume, checkpoint-restart or blocked outcome
- **AND** it does not silently declare completion or launch a duplicate external effect.

### Requirement: Dependency readiness includes required output artifacts
Control dependencies MAY be enforced through the host graph; typed data dependencies MUST resolve valid, revision-bound artifact references before dispatch. OmO's scheduling-only `dependsOn` behavior MUST NOT be represented as automatic upstream output propagation.

#### Scenario: accepted predecessor has no required artifact
- **GIVEN** a successor's required input artifact is missing or stale
- **WHEN** the scheduler evaluates readiness
- **THEN** the successor cannot dispatch with an unspecified replacement
- **AND** the missing artifact is surfaced as a validation or readiness gap.

### Requirement: Recovery does not replay unobserved external side effects
Attempt generation, stable dispatch/effect IDs and native status observations MUST be retained with sufficient provenance to reconcile uncertain side effects. A local run epoch MUST NOT be claimed to fence arbitrary remote APIs. Unknown liveness and uncertain delivery MUST remain explicit.

#### Scenario: timed-out remote mutation
- **GIVEN** a remote mutation may have completed after timeout
- **WHEN** retry policy evaluates the attempt
- **THEN** remote state is inspected or an operator gate is recorded before further mutation
- **AND** no automatic blind retry is authorized.

### Requirement: Source and runtime proof have separate freshness
Source-level OmO extraction MUST name an immutable commit/path and classify the adopted concept as preserve, adapt, exclude or gap. Conformance MUST continue to serialize canonical, adapter, package and runtime verdicts using the existing receipt schema. Static and offline passes MUST NOT satisfy required observed-live scenarios.

#### Scenario: source review is complete but native child spawn is untested
- **GIVEN** all reference mappings and schema checks passed
- **WHEN** the support report is computed
- **THEN** runtime remains UNTESTED or BLOCKED
- **AND** an independent live receipt from another harness cannot promote this harness.
