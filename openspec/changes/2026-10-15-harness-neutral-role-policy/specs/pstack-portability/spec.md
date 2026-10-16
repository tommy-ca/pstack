# pstack-portability delta: model-role and cross-harness contract

## ADDED Requirements

### Requirement: Model catalog discovery and proof are host-specific

Native model availability, allowed effort tokens and spawn fields MUST be resolved from the actual host version. Checked-in models and reference-port tests MUST NOT authorize a live dispatch claim. Capability-specific evidence from one host MUST NOT upgrade another host's `verified` status.

#### Scenario: unsupported model or effort

- **GIVEN** a model slug or effort token absent from the live host catalog
- **WHEN** role resolution validates an explicit request
- **THEN** it stops with an actionable unsupported-choice error
- **AND** it does not silently substitute a different named model

#### Scenario: a Pi reference proves a feature but OMP does not

- **GIVEN** a tested mechanism in the Pi extension of pstack-claude
- **WHEN** the target OMP profile is audited
- **THEN** that mechanism is only a candidate pattern
- **AND** OMP requires its own native evidence receipt to advance status


### Requirement: Logical model/role policy is typed and harness-neutral

A policy document MUST conform to `schemas/portability/model-role-policy.schema.json`. `pstack.package.json#/roles` MUST remain the only canonical role registry; the policy MAY add per-role constraints but MUST NOT duplicate role definitions or tier names. It MUST reuse the six `default_model_role` tier values. Host records MUST separate catalogs from role policy. Unknown roles, tiers, or dangling references MUST fail validation.

#### Scenario: new harness

- **GIVEN** an additional host with native model identifiers
- **WHEN** a portable canonical role is resolved
- **THEN** it uses that host's validated catalog and declared tier mapping
- **AND** the shared skill/playbook remains unchanged

Policy/safety/approval constraints are enforced before choosing a model. Within eligible choices, precedence is explicit invocation, project override, user override, host role override, host tier default, and parent inheritance. `inherit-parent`/`auto` MUST omit model from native spawn arguments. A role MUST NOT dispatch an unavailable real slug or an unsupported effort token. Runtime-discovered model/effort data MUST carry host version and freshness evidence.

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

Panel slots MUST be discrete agent invocations. An Arena cross-judge seat MUST differ from the candidate family when required and available; an Interrogate reviewer panel MUST preserve its declared independent-model family diversity; otherwise the verifier MUST report a degraded or blocked independence condition, rather than claiming multi-model review. Required agent.spawn/agent.join and workspace isolation bindings MUST be checked before fan-out.

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

### Requirement: Role/model resolution is a pure, auditable plan before native dispatch

A role resolver MUST produce a deterministic `ModelPlan` without spawning children or asserting model availability. The planner MUST report `PLANNED`, `DEGRADED` or `BLOCKED` as planning states, never runtime verdicts. Source precedence MUST be explicit → project → user → host role → host tier → inherited parent or fail-closed. Host metadata MUST NOT count as verified runtime receipts.

#### Scenario: explicit configuration overrides project and user choices

- **GIVEN** a canonical role, eligible host catalog, and different explicit, project and user model selections
- **WHEN** the pure resolver runs
- **THEN** explicit wins and the selected origin is recorded in the plan
- **AND** the plan is labeled `static-planning-only`
- **AND** the host must separately prove real invocation

#### Scenario: unsupported explicit model fails rather than downgrading

- **GIVEN** a requested explicit model missing from the declared host catalog
- **WHEN** role planning runs
- **THEN** the plan is `BLOCKED` with a named-missing-model reason
- **AND** no parent-inheritance or guessed substitute is dispatched

### Requirement: Independent seats and model diversity are distinct measures

Role settings MAY declare a bounded `seats` count independent of configured model slugs. A panel MAY use one model for multiple fresh-context seats but MUST record reduced family diversity. The canonical one-runner default MUST remain possible. The Arena cross-judge pool MUST select one eligible seat preferring a different family. Interrogate reviewers MUST count independent sessions and families separately.

#### Scenario: three Arena candidates using one configured model

- **GIVEN** one configured model and `seats=3`
- **WHEN** Arena plans its candidate fan-out
- **THEN** three independent planned seats are produced with unique ordinal identifiers
- **AND** the report states only one configured model and model family
- **AND** true session independence remains pending host-native evidence

#### Scenario: single canonical-default Arena runner

- **GIVEN** no user-requested multi-candidate configuration
- **WHEN** the canonical default resolves to one runner
- **THEN** role planning permits one candidate
- **AND** no implicit two-runner requirement is inserted by this port

### Requirement: Planner output is typed and cannot masquerade as runtime proof

`ModelPlan` MUST conform to `schemas/portability/model-plan.schema.json`. The output schema MUST reject runtime verdict statuses and evidence-level upgrades, carry immutable seat ordinals, and distinguish an inherited model's unknown provider/family from detected real model identity.

#### Scenario: static plan cannot become a fake verified receipt

- **GIVEN** a structurally valid static `ModelPlan`
- **WHEN** its status is changed to `VERIFIED` or evidence level to `runtime-verified`
- **THEN** JSON Schema validation fails
- **AND** host-native runtime proof remains a separate capability receipt

#### Scenario: blocked planning result

- **GIVEN** a model not present in the host's declared catalog
- **WHEN** the pure role planner returns `BLOCKED`
- **THEN** the output has no planned seats and at least one explicit reason
- **AND** the plan validates as an honest error artifact

### Requirement: Harness identity can extend without replicating the workflow router

The design MUST support future harness identities through a versioned declarative adapter descriptor, not one undifferentiated `custom` entry. Until a migration is tested, known-host enums stay operational and new IDs are NOT runtime-supported. A new identity MUST NOT inherit verified capabilities, tool mappings, or model availability. Shared skill and playbook content MUST remain unchanged.

#### Scenario: two new candidate harnesses

- **GIVEN** two distinct future harness descriptors that are not in the current six-host inventory
- **WHEN** they are validated as candidate adapters by a future extensible registry
- **THEN** their identities and model catalogs cannot collide or alias to `custom` as the same host
- **AND** no native capability becomes `verified` or `supported` merely by registry insertion
- **AND** the current six hosts continue to validate and project without drift

#### Scenario: attempted untrusted host alias

- **GIVEN** a proposed adapter identity colliding with a built-in host or containing path traversal
- **WHEN** the registry resolves its manifest
- **THEN** the descriptor is rejected without executing any provider code
- **AND** no host tool mapping or user config file is rewritten
