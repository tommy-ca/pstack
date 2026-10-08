# pstack-jev-decisions Specification

## Purpose

Define an optional provider-neutral contract for bounded semantic decisions. Preserve canonical pstack routing, verification, and human gates while evidence for any future provider is gathered.

## Requirements

### Requirement: Existing pstack authority remains unchanged

Canonical principles, skills, playbooks, explicit commands, deterministic facts, safety and autonomy policy, verification rules, and required human gates MUST remain authoritative. The caller MUST compute the baseline route before any provider call. A semantic provider MUST NOT change authority, mode, or the acting route.

#### Scenario: A higher-authority rule settles the route

- **GIVEN** an explicit command, deterministic fact, hard policy, or required human gate settles a decision
- **WHEN** routing proceeds
- **THEN** the decision bypasses the semantic provider
- **AND** pstack follows the canonical route

### Requirement: Authority precedence is explicit

Authority precedence MUST be exact deterministic fact, explicit user command, hard safety or autonomy policy, calibrated eligible semantic decision, System-Two judgment, then required human preference escalation. This ordering describes authority. It MUST NOT permit bypassing a mandatory safety or human gate, and it does not require sequential execution of every layer.

#### Scenario: A lower layer appears to permit a gated action

- **GIVEN** a semantic or System-Two result appears to permit an action with a mandatory gate
- **WHEN** authority is resolved
- **THEN** the safety or human gate remains mandatory
- **AND** the lower-layer result cannot authorize the action

### Requirement: The provider contract contains one bounded operation

`SemanticDecisionProvider` MUST expose only `decide`. Its request MUST be a provider-neutral union discriminated by `choice`, `score`, or `boolean`. Choices MUST be nonempty ID and label pairs. Scores MUST declare a bounded range. Each decided kind MUST admit only its matching value type. The linked shapes are defined in the change design.

#### Scenario: A provider returns a non-decided outcome

- **GIVEN** a well-formed bounded request
- **WHEN** the provider abstains, is unavailable, or returns an invalid result
- **THEN** the outcome carries no decided value
- **AND** the caller resumes the precomputed baseline route

### Requirement: Provider observations keep optional calibration metadata

A provider observation MUST contain a typed outcome plus provider and model identity. It MAY contain confidence and probabilities. It MUST NOT contain authority, mode, routing policy, the acting route, or evidence-persistence instructions. Its outcome MUST distinguish `decided`, `abstain`, `unavailable`, and `invalid`.

#### Scenario: A provider returns a decided observation

- **GIVEN** a provider makes a bounded choice judgment
- **WHEN** it returns an observation
- **THEN** the decided value matches the choice kind
- **AND** any confidence or probabilities remain non-authoritative metadata
- **AND** provider and model identity are available to the receipt layer

### Requirement: Egress is classified before request construction

The egress policy MUST classify candidate input as `local_only`, `safe_to_send`, `derived_sanitized`, or `prohibited`. Only a public sanitized fixture or an explicitly selected public current-task summary with closed labels MAY create sendable context. The current prompt MUST NOT be presumed public. Secret detection MUST NOT promote input to a sendable class.

#### Scenario: Candidate context is unsafe

- **GIVEN** candidate context contains or derives from raw transcripts, diffs, repository dumps, logs, tool output, files, authentication material, configuration, or secrets
- **WHEN** the egress boundary classifies the context
- **THEN** it rejects provider request construction
- **AND** it does not use lossy redaction or truncation to make the context sendable
- **AND** the caller resumes the precomputed baseline route

### Requirement: Provider requests obey conservative policy ceilings

Sendable context MUST NOT exceed 2,048 UTF-8 bytes. A choice request MUST NOT contain more than 32 choices. Identifiers MUST NOT exceed 64 UTF-8 bytes. Labels MUST NOT exceed 128 UTF-8 bytes. A complete request MUST NOT exceed 8,192 UTF-8 bytes. These values are policy ceilings and MUST NOT be represented as measured provider, performance, cost, or quality facts.

#### Scenario: A request exceeds a ceiling

- **GIVEN** an otherwise sendable request exceeds any policy ceiling
- **WHEN** the boundary validates the request
- **THEN** it rejects the request without calling the provider
- **AND** the caller resumes the precomputed baseline route

### Requirement: One canonical mapping owns semantic eligibility

A single provider-neutral mapping at `references/decision-routing.json` MUST own phase-one classes and canonical playbook candidates. Every canonical playbook MUST appear once. The mapping MUST fail closed on inventory drift, contain no provider or model names, confidence thresholds, or execution authority, and return baseline for unknown or `other` classes.

#### Scenario: The canonical inventory drifts

- **GIVEN** a canonical playbook is missing, duplicated, renamed, or unclassified in the mapping
- **WHEN** mapping validation runs
- **THEN** validation fails
- **AND** no semantic result from that mapping receives routing authority

### Requirement: Eligibility never grants execution authority

Semantic eligibility MUST be a classification hint only. Explicit and directly inspectable routes MUST bypass the provider. High-risk, generative, arithmetic, tool-execution, shipping, and preference decisions MUST receive no semantic authority. Skill suggestion MUST remain unavailable until its taxonomy and caller are grounded in a separate accepted change.

#### Scenario: A provider classifies an excluded decision

- **GIVEN** a semantic result concerns an excluded decision class
- **WHEN** routing policy evaluates the result
- **THEN** it grants the result no execution authority
- **AND** the canonical System-Two, deterministic, or human-gated path continues

### Requirement: Receipts bind every controlling input

A receipt MUST contain source, outcome, mode, implementation revision, canonical mapping revision, provider identity, model identity, policy and question-set revision, and fixture revision. Provider and model identity MUST be available at runtime before evidence can authorize control. `unknown` MUST NOT authorize control.

#### Scenario: Receipt identity is incomplete

- **GIVEN** a receipt lacks a required revision or has an unavailable provider or model identity
- **WHEN** routing policy considers the receipt for control
- **THEN** the receipt cannot authorize a controlling decision
- **AND** the caller resumes the precomputed baseline route

### Requirement: Evidence excludes private input and hidden reasoning

Evidence MUST store only the fixture identifier, fixture digest, closed labels, revisions, mode, source, and typed outcome required by the receipt. It MUST NOT store raw context, hidden reasoning, or private chain-of-thought. A digest MUST be treated as correlatable fixture evidence rather than anonymous data.

#### Scenario: Shadow evidence is recorded

- **GIVEN** a sanitized public fixture produces a shadow outcome
- **WHEN** the evidence layer persists its receipt
- **THEN** it stores the fixture identifier and digest with labels and revisions
- **AND** it stores neither the raw context nor hidden reasoning

### Requirement: Every failure preserves baseline behavior

Provider failure, invalid output, rejected or unconstructible context, receipt failure, and stale evidence MUST preserve the precomputed baseline route. Disabling or removing the optional provider MUST preserve baseline behavior. A provider retry policy MUST NOT block task progress indefinitely.

#### Scenario: Receipt persistence fails

- **GIVEN** the provider returned a decided outcome
- **WHEN** the required receipt cannot be persisted
- **THEN** the outcome receives no routing authority
- **AND** the caller resumes the precomputed baseline route

### Requirement: Shadow mode has zero behavior change

Shadow mode MUST keep the precomputed baseline route as the acting route. Provider observations MAY be recorded only as non-controlling evidence. Provider latency, failure, evidence failure, or an observation value MUST NOT change user-visible execution.

#### Scenario: A shadow observation disagrees with baseline

- **GIVEN** the provider returns a route class different from the baseline route
- **WHEN** mode is `shadow`
- **THEN** pstack follows the baseline route
- **AND** the disagreement may be recorded only as evaluation evidence

### Requirement: Calibration is specific to class and consequence

The integration MUST NOT use one universal confidence threshold. Each eligible class MUST use evidence and a predeclared policy that reflects the consequence of error. A low-confidence result MUST return the precomputed baseline route or a stronger decision layer.

#### Scenario: Confidence is below the class policy

- **GIVEN** a semantic result is below its class-specific controlling threshold
- **WHEN** routing policy evaluates the observation
- **THEN** the result receives no controlling authority
- **AND** routing resumes at the baseline or a stronger decision layer

### Requirement: Accepted and refreshed baselines gate implementation

#197 MUST accept and merge the reconciled specification before runtime implementation. #209 MUST complete the refreshed baseline before runtime implementation. Proposed specification text MUST NOT mark those issue tasks complete.

#### Scenario: An implementation gate remains open

- **GIVEN** #197 or #209 is incomplete
- **WHEN** runtime implementation is proposed
- **THEN** implementation remains blocked
- **AND** the no-change route remains the acting baseline

### Requirement: Offline evidence defines promotion budgets

#186 MUST produce rerunnable offline evidence and predeclare class-specific quality, abstention, false-activation, missed-rigor, latency, and cost metrics and budgets. A budget MUST be explained before it gates promotion. Provider quality, latency, and cost MUST remain unproven until this evidence exists.

#### Scenario: A promotion budget was not predeclared

- **GIVEN** a candidate result is measured against a budget chosen after the run
- **WHEN** promotion evidence is reviewed
- **THEN** that result does not satisfy the promotion gate
- **AND** the no-change route remains the acting baseline

### Requirement: Fresh blinded exact-head evidence gates promotion

Promotion MUST require fresh #186 offline evidence, blinded Eval evidence from #198, and revision freshness from #199. Every required #187 exact-head Swarm slice MUST pass. #188 exact-head Interrogate MUST have no unresolved Act on finding. The candidate MUST meet predeclared latency and cost budgets and pass rollback proof from #200. No-change MUST remain a valid outcome.

#### Scenario: Promotion evidence is stale or incomplete

- **GIVEN** any required evidence, budget result, Swarm slice, Interrogate resolution, or rollback proof is missing, failing, or stale
- **WHEN** controlling mode is considered
- **THEN** promotion is refused
- **AND** the no-change route remains the acting baseline

### Requirement: Jev remains outside the portability support floor

A harness MUST NOT need Jev or another semantic provider to satisfy pstack portability or reach supported status. Provider-specific SDK, transport, authentication, model, and wire types MUST remain outside shared pstack contracts.

#### Scenario: A supported harness has no provider

- **GIVEN** a harness satisfies the pstack portability conformance floor
- **AND** no semantic provider is configured
- **WHEN** support state is derived
- **THEN** the harness may still reach `supported`
- **AND** pstack follows its existing route

### Requirement: The optional integration stays minimal

The contract MUST NOT require a provider runtime, shared decision service, generic provider gateway, runtime schema, workflow runtime, durable decision store, second tracker, or new agent role. Any future runtime seam MUST be added only after the named gates and its own accepted implementation change.

#### Scenario: A speculative shared runtime is proposed

- **GIVEN** no second grounded runtime caller exists
- **WHEN** a shared semantic decision service or generic gateway is proposed
- **THEN** the proposal is outside this contract
- **AND** the provider-neutral specification remains sufficient
