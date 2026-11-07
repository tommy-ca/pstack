# pstack-reusable-skill-patterns — delta: keep only portable development contracts

**Source:** `deepseek-ai/deepseek-harness@fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` (22/22 SOURCE_STATIC); see `../../source-crosswalk.md`. **Disposition:** 12 GENERAL, 5 CONDITIONAL, 5 EXCLUDE. Runtime skill changes and multi-agent evaluation are NOT_RUN.

## MODIFIED Requirements

### Requirement: source provenance and curatorial decisions

Every incorporated external invariant MUST cite an immutable source revision, path, license and target pstack owner. The source ledger MUST classify all twenty-two pinned DeepSeek source SKILL.md entries, including explicit exclusions. Only generally reusable engineering contracts and explicitly task-conditional reusable guidance MAY enter active PStack behavior; DSH/Cordis/product/OS/forge-specific skill implementations MUST remain source-only evidence. The historical sixteen-skill ledger remains pinned and unmodified.

#### Scenario: source changes
- **GIVEN** an updated upstream skill after its pinned commit
- **WHEN** the source crosswalk is refreshed
- **THEN** the existing approved decision remains tied to its prior SHA
- **AND** any changed behavior is reassessed before promotion.

#### Scenario: 22-source census and active filter
- **GIVEN** the 2026-10-11 ledger covered sixteen skills and the pinned 2026-11-07 source tree covers twenty-two
- **WHEN** the source ledger is reconciled
- **THEN** every source skill SHALL receive exactly one GENERAL, CONDITIONAL or EXCLUDE disposition
- **AND** excluded behaviors SHALL be absent from active generic PStack requirements
- **AND** sources and pre-existing decisions remain traceable by immutable source pin.

#### Scenario: documentation mistaken for proof
- **GIVEN** a source skill describing a successful technique without pstack runtime evidence
- **WHEN** its support claim is reduced
- **THEN** it MUST NOT be treated as observed-live host verification.


## ADDED Requirements

### Requirement: reusable guidance is decomposed into existing leaf, principle and playbook owners

For each retained source-derived behavior, PStack MUST name its existing atomic leaf skill, cross-task principle and sequencing playbook (or explicitly state when a category is inapplicable). An upstream source SKILL.md MUST NOT be treated as a requirement to register a new PStack skill. A proposed new leaf MUST have a recurring standalone trigger, unique testable output and absence of a current owner; a new principle MUST own a previously unowned invariant; a new playbook MUST add genuinely distinct sequencing. The source ledger itself SHALL NOT authorize runtime changes.

#### Scenario: generic code-review pattern is already owned

- **GIVEN** a source review instruction is already satisfied by `interrogate` and `thermo-nuclear-review`
- **WHEN** the source skill is classified as GENERAL
- **THEN** PStack SHALL map the behavior to those existing leaves, a relevant principle and the investigation/review playbook
- **AND** SHALL NOT create a `dsh-code-review` clone.

#### Scenario: source skill is DSH-only

- **GIVEN** a source skill prescribes Cordis plugin wiring, a product icon palette or macOS CUA certificates
- **WHEN** the general PStack skill inventory is reconciled
- **THEN** the source skill SHALL be recorded as EXCLUDE
- **AND** no PStack runtime skill, mandatory host dependency or generic new principle is created.

### Requirement: asynchronous resource lifecycles retain owners through completion

When reviewing actual resource-owning runtime code, a reusable lifecycle check SHALL identify the owner of effects, their registration, cancellation, settlement and last required dependency use. The owner MUST NOT release required dependencies or declare recovered/successful state before owned tasks settle. The analysis SHALL use target-project primitives, never require Cordis APIs, and SHALL request a deterministic interleaving when the suspected defect can be reproduced.

#### Scenario: release happens before callback completion

- **GIVEN** a component schedules asynchronous cleanup that uses a service until its last await
- **WHEN** the service is released before the cleanup task settles
- **THEN** an applicable lifecycle verification MUST flag or reproduce the resulting invalid dependency access
- **AND** abort/close/log statements alone MUST NOT be treated as quiescence.

### Requirement: PR descriptions preserve executable evidence and migration truth

For a changed interface or externally visible behavior, the existing PStack PR/technical-writing workflow SHALL describe the actual change, affected consumer and necessary migration. Test entries SHALL distinguish executed checks from plans, stale-head receipts, incomplete evidence and blocked capabilities. PStack MUST NOT impose a DeepSeek-specific PR template, language, AI scoring rubric or GUI-recording prerequisite on other repositories.

#### Scenario: pre-push test was not executed

- **GIVEN** a proposed pull request contains a test command in its plan, but no execution receipt at its head
- **WHEN** the PR description is authored
- **THEN** the test MUST be reported as NOT_RUN rather than PASS
- **AND** the relevant target-project verification gate remains unproven.
