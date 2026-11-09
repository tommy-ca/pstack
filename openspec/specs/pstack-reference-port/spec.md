# pstack-reference-port Specification

## Purpose

Define this repository as a reference port of canonical Cursor pstack and prevent any host adapter from becoming the source of truth for another host.

## Requirements

### Requirement: Cursor pstack is canonical and this repository is reference evidence

Feature: pstack-reference-port

Official `cursor/plugins/pstack` at the immutable `UPSTREAM` pin MUST remain the canonical authority for principles, skills, router behavior, playbook intent, roles, ordering, and verification rules. Operator docs MUST extract official pstack philosophy: less code over loc, go deep then parallelize, one router, steer with 23 principle names, prove on the real artifact.

This repository MUST be described as a reference port. Grok Build is the strongest implemented reference adapter in this tree. Codex and Claude Code mappings or manifests MAY be present, but their support status MUST follow `pstack-portability` conformance rather than inherit authority from the Grok adapter.

#### Scenario: porting page names the layers

- **GIVEN** `docs/guide/12-porting.md`
- **WHEN** an operator wants pstack on another host
- **THEN** the page names 23 principles, host map, and Laziness Protocol
- **AND** it tells them not to copy the previous host's spawn fields as the core

#### Scenario: port another harness

- **GIVEN** an operator ports pstack to another harness
- **WHEN** they need canonical behavior
- **THEN** they read the pinned official pstack source and the portability contract
- **AND** they may use this Grok implementation as evidence or prior art
- **AND** they do not derive semantics transitively from Grok-specific call sites

### Requirement: Pin conformance and upstream freshness are separate

The port MUST report whether it conforms to its recorded pin separately from whether official pstack has newer unclassified changes.

#### Scenario: upstream advances

- **GIVEN** the recorded pin still passes its coverage checks
- **AND** official pstack has commits after that pin
- **THEN** pin conformance may remain PASS
- **AND** upstream freshness reports drift until the new changes are classified

### Requirement: External executor precedents cannot become PStack-owned contracts
PStack MUST derive shared engineering semantics from the recorded official Cursor PStack pin. External Mu/Dogsled execution details MAY be cited as reference-only but MUST NOT create a PStack task dispatcher, provider registry, worker lifecycle, placement engine, or public execution-request/receipt API through a documentation change.

#### Scenario: External DAG example proposes a second development task store
- **GIVEN** a Mu or Dogsled source observation about its own tasks or jobs
- **WHEN** the reference port classifies that observation
- **THEN** it MUST be marked reference-only unless independently supported by canonical PStack intent
- **AND** no runtime API or store is inferred from the observation

### Requirement: PStack specifications extend existing canonical capabilities
Semantic changes MUST update the existing reference-port, playbook or portability contracts as appropriate and preserve source provenance. A new specification capability MUST NOT be created solely because a third-party runtime uses a different type name.

#### Scenario: Candidate execution schema has no canonical owner
- **GIVEN** a proposed ExecutionRequest, HostExecutionPort or HostPlacement abstraction
- **WHEN** its only justification is Mu/Dogsled implementation detail
- **THEN** it MUST be excluded from PStack's active semantic contract
- **AND** the explicit non-adoption rationale MUST remain traceable

### Requirement: Port and downstream dependencies stay directed
PStack MUST NOT import QStack or an external executor as a semantic authority. Host-specific bindings MAY implement existing PStack playbook intent, but their capability and evidence status MUST be explicit. QStack MAY consume PStack skills through qstack-mode -> pstack-mode.

#### Scenario: Downstream domain attempts to define a core PStack skill
- **GIVEN** a quant orchestration behavior exists only in QStack
- **WHEN** a PStack source inventory is updated
- **THEN** the behavior MUST remain downstream
- **AND** the canonical PStack definition MUST NOT acquire a qorch dependency

### Requirement: Evidence labels must match real observations
A source review, successful offline test and actual host-native run MUST be recorded separately. A proposal or static review alone MUST NOT be presented as a running implementation, formal model proof, or independent panel result.

#### Scenario: Source-only review is called a live verification pass
- **GIVEN** no target execution was observed
- **WHEN** the review summary is prepared
- **THEN** observed-native status MUST remain NOT_RUN or BLOCKED
- **AND** the source-only analysis MAY be reported separately
