# pstack-portability delta: model-role and cross-harness contract

## MODIFIED Requirements

### Requirement: Harness runtime conventions are structured and schema-validated

Each host's native model spawn fields, allowed effort tokens, tool capabilities, isolation controls and version-sensitive behaviors MUST be validated against the active host; static documentation MUST NOT be represented as proof of live model availability.

#### Scenario: unsupported model or effort

- **GIVEN** an explicit request for a model slug or effort token absent from the detected live host catalog
- **WHEN** the role resolver validates that request
- **THEN** it fails with the unavailable choice and the host's permitted alternatives
- **AND** it does not silently substitute another model or claim verified dispatch

### Requirement: Adapter bindings are typed and evidence-backed

A reference port's tests, documentation and live receipts MUST be classified independently. Evidence from Pi MUST NOT establish OMP capabilities, and passing a manifest check MUST NOT establish runtime parity.

#### Scenario: claim from reference port

- **GIVEN** a `pstack-claude` test covers a Pi extension capability
- **WHEN** pstack considers reusing the behavior on OMP
- **THEN** the entry is a candidate pattern with source commit and license provenance
- **AND** OMP remains at its existing measured verification level until a host-specific test passes

## ADDED Requirements

### Requirement: Logical model/role policy is typed and harness-neutral

A policy document MUST conform to `schemas/portability/model-role-policy.schema.json`. Roles MUST use stable canonical IDs and declare intent, required semantic capabilities, selection topology and model tier. Host records MUST separate provider/model/family catalogs from role policy. Duplicate role IDs, dangling skill references and undefined tiers MUST fail validation by the implementation lever.

#### Scenario: new harness

- **GIVEN** an additional host with native model identifiers
- **WHEN** a portable canonical role is resolved
- **THEN** it uses that host's validated catalog and declared tier mapping
- **AND** the shared skill/playbook remains unchanged

### Requirement: Model and effort selection is deterministic and conservative

Policy/safety/approval constraints are enforced before choosing a model. Within eligible choices, precedence is explicit invocation, project override, user override, host default, and parent inheritance. `inherit-parent`/`auto` MUST omit model from native spawn arguments. A role MUST NOT dispatch an unavailable real slug or an unsupported effort token. Runtime-discovered model/effort data MUST carry host version and freshness evidence.

#### Scenario: explicit unavailable model

- **GIVEN** an explicit model not offered by the host
- **WHEN** resolution executes
- **THEN** it reports a gap requiring a user decision
- **AND** it does not silently fall back to a different named model

#### Scenario: inherited model

- **GIVEN** a role configured as `inherit-parent`
- **WHEN** its host-native spawn is built
- **THEN** the model field is omitted
- **AND** model inheritance is described as host behavior, not invented model identity

### Requirement: Panels and cross-judges preserve independence

Panel slots MUST be discrete agent invocations. Cross-judges MUST use a distinct family where required and supported; otherwise the verifier MUST report a degraded or blocked independence condition, rather than claiming multi-model review. Required agent.spawn/agent.join and workspace isolation bindings MUST be checked before fan-out.

#### Scenario: only one live model family

- **GIVEN** a cross-judge policy requires family diversity but host discovery identifies only one family
- **WHEN** the panel is planned
- **THEN** the diversity claim cannot pass
- **AND** a degraded/fallback plan or explicit block is recorded

### Requirement: Hook routing has a host-scoped, reversible lifecycle

Host-native routing hooks MAY inject canonical poteto-mode intent only when the package and host permit it. Setup MUST support opt-out and validate startup/resume/compact semantics where available. Hook deployment MUST be idempotent and MUST NOT introduce a parallel orchestration state store.

#### Scenario: routing disabled

- **GIVEN** the user's host-specific setup disables the session hook
- **WHEN** a new session starts or resumes
- **THEN** pstack does not inject an automatic routing instruction
- **AND** explicitly invoked skills still work

### Requirement: Cross-port imports are provenance-filtered

Transfer from `michael-denyer/pstack-claude` MUST identify source commit, license/NOTICE implications, canonical-equivalent behavior, adapter-only behavior, and declared `tools/forks.json` policy modifications. Pstack MUST preserve host-owned durable orchestration state and qstack's post-router domain overlay.

#### Scenario: reference has a policy fork

- **GIVEN** a reference change intentionally differs from canonical upstream
- **WHEN** the porting graph classifies it
- **THEN** the policy change is reviewed separately and not silently imported
- **AND** no pstack or qstack router/state fork is created by default

### Requirement: Claims advance by independently verified gates

Every host addition progresses through candidate, mapped, packaged, verified and supported only with evidence appropriate to that state. Static tests, generated manifests and mock simulations alone MUST NOT promote runtime-supported claims. Swarm/Arena/Interrogate multi-model results MUST cite independently executed runs or remain explicitly pending.

#### Scenario: package projects successfully but live runtime fails

- **GIVEN** projected manifests and JSON schemas pass
- **WHEN** the native host fails to dispatch a configured role
- **THEN** runtime status remains unverified or failed
- **AND** the evidence ledger records the failure without overwriting previous receipts
