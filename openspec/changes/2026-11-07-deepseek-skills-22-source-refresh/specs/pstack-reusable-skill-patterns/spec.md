# Delta: pstack-reusable-skill-patterns (DeepSeek 22-skill refresh)

**Source pin:** `deepseek-ai/deepseek-harness@fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159`. **Status:** SOURCE_STATIC / proposed behavior; no host or worker execution.

## MODIFIED Requirements

### Requirement: source provenance and curatorial decisions

Every incorporated external invariant MUST cite an immutable source revision, path, license and target pstack owner. The adoption matrix MUST cover all **twenty-two** DeepSeek source SKILL.md entries at the newly inspected source pin, including explicit deferrals. Prior sixteen-entry artifacts at the old pin remain historically valid and immutable.

#### Scenario: source changes
- **GIVEN** an updated upstream skill after its pinned commit
- **WHEN** the source crosswalk is refreshed
- **THEN** the existing approved decision remains tied to its prior SHA
- **AND** any changed behavior is reassessed before promotion.

#### Scenario: documentation mistaken for proof
- **GIVEN** a source skill describing a successful technique without pstack runtime evidence
- **WHEN** its support claim is reduced
- **THEN** it MUST NOT be treated as observed-live host verification.

#### Scenario: inventory expands
- **GIVEN** a historical audit of 16 upstream skills and a new pinned tree of 22
- **WHEN** the living crosswalk is updated
- **THEN** every one of the 22 has a source path, PStack owner, and adoption/defer decision
- **AND** six additions and eight changed prior source directories are identified as static evidence, not deployed functionality.

## ADDED Requirements

### Requirement: R-DSH22-01 Existing-owner and single-responsibility discipline

Each reusable development invariant SHALL have one canonical owner in the already installed PStack skill/principle/playbook/host-adapter/evidence stack. A source skill name, reference or algorithm MUST NOT create an additional common `dsh-*` skill, command router, runtime type, project scheduler or skill registry by default. Skill composition SHALL preserve explicit host capability and authorized effect boundaries.

#### Scenario: review skill overlap
- **GIVEN** a source code-review guideline maps to `interrogate` or Thermos
- **WHEN** PStack absorbs its useful semantic contract
- **THEN** the existing skill owns the behavior
- **AND** no generic second review mode is required.

#### Scenario: case-specific abstraction is not worthwhile
- **GIVEN** a source behavior has exactly one local consumer and no reusable contract
- **WHEN** an adapter is considered
- **THEN** the implementation remains local or is deferred
- **AND** an interface or class is not added merely to mirror the upstream filename.

### Requirement: R-DSH22-02 Lifetime and effect ownership are verifiable

For any selected lifecycle-sensitive workflow, the reviewer SHALL identify the resource state owner, effect acquisition, cancellation, final dependency use, disposal order and quiescent completion. A catch, abort, close, delete, or logged error MUST NOT alone constitute successful recovery or settlement. Platform-specific Cordis APIs MUST NOT be imposed on other hosts.

#### Scenario: dependent service torn down first
- **GIVEN** a background consumer still requires an event bus during final cleanup
- **WHEN** the owning service begins disposal
- **THEN** cleanup MUST await the consumer's final dependency use before releasing the bus
- **AND** a deterministic failing interleaving MUST be requested where the risk can be exercised.

### Requirement: R-DSH22-03 Event-sourced projection constraints are conditional

When a project already uses restorable event-sourced state, a projection verifier SHALL require replay to be deterministic and side-effect-free, the full replay state to agree with checkpoint-plus-suffix replay, bounded state growth or a documented cost, and consuming services to own read APIs. For projects without projection state, the rule SHALL be inapplicable and MUST NOT introduce a storage subsystem.

#### Scenario: replay re-sends an external side effect
- **GIVEN** a persisted event log replays to recover a projection
- **WHEN** a replay path reissues a network request or repeats a durable write
- **THEN** the projection verification MUST fail
- **AND** the external effect MUST stay with an explicit live-runtime owner.

#### Scenario: ordinary stateless API
- **GIVEN** a stateless CLI workflow without persisted session projections
- **WHEN** PStack selects relevant skills
- **THEN** event-sourced projection guidance MUST remain inactive.

### Requirement: R-DSH22-04 Optional UI and host-dependent workflows have negative triggers

Responsive UI inspection, official icon artwork, macOS computer-use signing, bilingual documentation, live browser recordings and native GitHub PR stacks SHALL activate only under an explicit task/project capability and host-supported execution path. The shared router MUST NOT interpret source instructions as permission to access credentials or alter keys. Exact dimensions, palette constants, language requirements and tool commands are owned by the target project.

#### Scenario: backend-only change
- **GIVEN** a backend repository without a browser surface
- **WHEN** its PR is reviewed
- **THEN** browser GIF, artwork, responsive layout and translation workflows MUST NOT be silently required.

#### Scenario: signing on unsupported host
- **GIVEN** a non-macOS project or advice-only signing question
- **WHEN** the source-derived macOS signing pattern is considered
- **THEN** no certificate, keychain, configuration or credential is modified
- **AND** the unsupported or unapproved path is reported.

### Requirement: R-DSH22-05 PR communication binds claims to actual evidence

A PR description SHALL distinguish motivation, user-observable interface/behavior changes, expected migration, tests actually executed and outstanding unknowns. An exact source/base/head or artifact identity SHALL ground claimed checks. Project-specific headings, languages and AI disclosure formats MAY be applied only when required by target repository policy.

#### Scenario: tests named but never run
- **GIVEN** a candidate PR description lists a planned e2e test
- **WHEN** the PR is opened
- **THEN** the test MUST be marked not run rather than PASS
- **AND** the description MUST NOT treat a previous head's test receipt as current.

### Requirement: R-DSH22-06 Swarm, Arena and Interrogate provide independent proof only when executed

Swarm SHALL partition independent audit/evidence slices with source revision and artifact identity. Arena SHALL compare materially different candidate designs using a declared rubric and isolated workspaces. Interrogate SHALL keep only reproduced defects based on real target-code observations. When a selected host lacks these execution capabilities, the workflow MUST report NOT_RUN/BLOCKED and MUST NOT synthesize fictional workers or votes.

#### Scenario: source-only analysis
- **GIVEN** one agent reads three source skill bodies without starting reviewers
- **WHEN** findings are reported
- **THEN** the result is labeled source inspection
- **AND** it MUST NOT be described as three independent Swarm/Interrogate passes.

### Requirement: R-DSH22-07 Source drift is not behavioral adoption

When an upstream source directory changes, PStack SHALL retain the immutable old decision, inspect changed contracts against the current target owner, and promote only a proven improvement with negative controls, baseline comparisons and honest host receipts. A source-side assertion, downstream documentation, or static link MUST NOT upgrade status to native-runtime PASS.

#### Scenario: eight changed directories but no target run
- **GIVEN** the old source ledger differs from the latest source pin
- **WHEN** the crosswalk is refreshed without executing candidate PStack workflows
- **THEN** provenance SHALL be SOURCE_STATIC with an explicit unverified adoption status
- **AND** existing host/eval receipts remain attached to their original source and target SHAs.

