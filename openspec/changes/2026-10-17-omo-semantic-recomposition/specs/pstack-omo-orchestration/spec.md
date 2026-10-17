# pstack-omo-orchestration: source-grounded reference semantics

## ADDED Requirements

### Requirement: OmO source extraction is version-pinned and semantically typed
OmO reference mechanisms MUST be recorded with an immutable source commit, source path, behavior summary, owning design contract, canonical pstack principle/leaf/playbook mapping, and proof status. Principle, leaf skill, playbook and runtime mechanism MUST be classified separately. Extraction MAY adopt an algorithmic idea; code reuse requires licensing review.

#### Scenario: an extracted primitive appears similar to a pstack skill
- **GIVEN** OmO's DAG readiness algorithm is extracted
- **WHEN** it is mapped into portable pstack
- **THEN** it is classified as host-owned scheduling behavior rather than a new canonical skill
- **AND** the corresponding decision rules are linked to pinned upstream principles without duplicating them.

### Requirement: OmO child execution has one parent-work ownership boundary
The orchestrating host MUST own program work, graph revisions and acceptance. An OmO child DAG, TaskManager, team or Workpool MAY coordinate a bounded attempt but MUST publish results through its owning parent attempt. No child execution mechanism may claim or transition unrelated host work.

#### Scenario: child DAG completes its internal run
- **GIVEN** an OmO DAG operates inside one host-owned work attempt
- **WHEN** that DAG reaches its own terminal status
- **THEN** the adapter returns a typed attempt outcome and artifact references
- **AND** the parent host independently evaluates verification and program completion.

### Requirement: Data dependencies are distinct from DAG scheduling dependencies
A `dependsOn` control edge orders dispatch; an artifact edge identifies source work, artifact type and accepted digest/revision. Where the host requires typed dataflow, the input references MUST be resolved before launch. A successful predecessor with a missing artifact MUST NOT silently unblock an artifact-dependent successor.

#### Scenario: dependencies are complete but input digest is missing
- **GIVEN** all control predecessors are terminal and accepted
- **WHEN** the host checks a successor with a required artifact input
- **THEN** it blocks or returns an explicit missing-artifact readiness error
- **AND** no invented artifact content is inserted into the worker brief.

### Requirement: Native recovery declares uncertainty, not inferred continuity
OmO task run epochs, journal data, and Workpool delivery phases MAY inform recovery, but a parent session resume MUST NOT establish child resume by assumption. Unacknowledged delivery, provisional exit, lost child, and unobserved external writes MUST retain uncertainty until authoritative reconciliation.

#### Scenario: Workpool message delivery timed out
- **GIVEN** the worker may have observed a keyed message before timeout
- **WHEN** the host or adapter reconciles a restart
- **THEN** it inspects task/output/effect evidence and maintains unknown if inconclusive
- **AND** it never blindly resends a non-idempotent effect.

### Requirement: Reference verification uses canonical pstack evidence planes
OmO source-review results MUST remain distinct from runtime verification of the selected host adapter. The existing pstack canonical, adapter, package and runtime serialized receipt planes remain authoritative. A passed source classification or offline test MUST NOT be presented as an independent Swarm/Arena/Interrogate execution.

#### Scenario: design review only
- **GIVEN** Swarm coverage, Arena design alternatives and Interrogate hypotheses were evaluated by a single analytical review
- **WHEN** the change reports conformance
- **THEN** it labels independent native agent execution UNTESTED
- **AND** records the future executable scenarios needed for promotion.
