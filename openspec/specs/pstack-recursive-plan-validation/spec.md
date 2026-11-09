# pstack-recursive-plan-validation Specification

## Purpose
Define machine-readable plan section identifiers and the recursively validated dependency graph the plan checker enforces before a multi-phase program runs.

## Requirements

### Requirement: Multi-phase plans expose a validated dependency graph
Every PR section between `## Program checklist` and `## Close the program` MUST end its title with a unique identifier in parentheses (`[a-zA-Z0-9_./#-]+`). The identifier `None.` is reserved as the no-dependency sentinel. Its `**Depends on.**` line MUST contain `None.` or comma-separated identifiers. `check-plan.mjs` MUST resolve references, reject duplicate identifiers, reject unknown identifiers, and reject cycles.

#### Scenario: independent and nested tasks validate
- **GIVEN** sections `(sync)`, `(checker)`, and `(smoke)` where `(checker)` depends on `(sync)` and `(smoke)` depends on `(checker)`
- **WHEN** `node skills/poteto-mode/scripts/check-plan.mjs <plan.md>` runs
- **THEN** the checker reports all three sections
- **AND** it exits successfully
- **AND** it reports the resolved dependency depth for each section

#### Scenario: unknown dependency fails closed
- **GIVEN** a section `(watcher)` whose `Depends on.` line names `(missing)`
- **WHEN** the checker runs
- **THEN** it exits nonzero
- **AND** stderr identifies the section and unknown identifier

#### Scenario: duplicate identifiers fail closed
- **GIVEN** two sections with the same parenthesized identifier
- **WHEN** the checker runs
- **THEN** it exits nonzero
- **AND** stderr identifies the duplicate identifier

#### Scenario: dependency cycle fails closed
- **GIVEN** `(a)` depends on `(b)` and `(b)` depends on `(a)`
- **WHEN** the checker runs
- **THEN** it exits nonzero
- **AND** stderr identifies the cycle path

### Requirement: The plan playbook documents the graph syntax

Feature: pstack-recursive-plan-validation

`skills/poteto-mode/playbooks/multi-phase-plan.md` MUST tell plan authors how to choose unique section identifiers and write dependency lists. Its skeleton MUST use the same syntax so a plan can be checked without inventing a second format. The existing Grok verification rule, ten live lanes, and host-native monitoring requirements remain unchanged.

#### Scenario: skeleton teaches machine-readable dependencies

- **GIVEN** an operator reads the multi-phase plan skeleton
- **WHEN** they author a PR section
- **THEN** the section example includes a parenthesized identifier
- **AND** its `Depends on.` block names identifiers or `None.`
- **AND** the playbook points to `check-plan.mjs`
