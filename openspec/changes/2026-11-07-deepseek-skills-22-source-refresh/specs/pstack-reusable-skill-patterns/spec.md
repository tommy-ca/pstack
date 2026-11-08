# pstack-reusable-skill-patterns — delta: keep only portable development contracts

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


### Requirement: relevance and host conditionality

Optional UI, i18n, release, archive, and browser evidence workflows MUST activate only for matching target tasks and project capabilities. Forge-native stack mechanics, DSH product rules and OS-specific setup MUST stay outside generic PStack skill requirements. Ordinary new UI development MUST use the existing feature workflow and applicable user-path verification. The `visual-parity` playbook MUST be reserved for an explicitly requested pixel-exact baseline/equivalence task; it MUST NOT be invoked solely because a change is responsive or visually inspectable.

#### Scenario: backend project with no UI or i18n
- **GIVEN** a server-only code change
- **WHEN** pstack selects skill overlays
- **THEN** browser-GIF, UI color, bilingual pairing and DSH build steps remain inactive.

#### Scenario: responsive feature with no existing pixel-match goal
- **GIVEN** a new responsive UI control without a requested reference implementation or pixel baseline
- **WHEN** the agent composes the workflow
- **THEN** the existing `feature` playbook and applicable `create-verification-skill` user-path checks are selected
- **AND** `visual-parity` and mandatory GIF publishing are not required.

#### Scenario: explicit pixel-exact UI migration
- **GIVEN** an explicit request to match a prior visual baseline
- **WHEN** PStack composes the UI verification workflow
- **THEN** `visual-parity` MAY be selected with the target project's real baseline and comparison surface
- **AND** DSH-specific theme tokens, viewport defaults and publication commands MUST NOT be imposed.

## ADDED Requirements

### Requirement: reusable guidance is decomposed into existing leaf, principle and playbook owners

For each retained source behavior, PStack MUST name its atomic leaf skill, principle, and playbook (or state when inapplicable). An upstream SKILL.md MUST NOT register a redundant PStack skill. A proposed new leaf MUST have a recurring trigger and unique output; a new principle MUST own an unowned invariant; a new playbook MUST add distinct sequencing. The source ledger SHALL NOT authorize runtime changes.

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
