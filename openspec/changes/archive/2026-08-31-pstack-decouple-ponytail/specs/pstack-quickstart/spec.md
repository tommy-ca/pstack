## ADDED Requirements

None.

## MODIFIED Requirements

### Requirement: Quickstart teaches grok-native spawn and depth

Feature: pstack-quickstart

`docs/guide/01-setup.md` MUST explain grok-native pstack after install: Skill order (pstack then user then bundled), `pstack:<role>` spawn names, `MAX_SUBAGENT_DEPTH` 1, parent fans out, `pstack:independent-verifier`, `/loop` → `scheduler_create`. It MUST NOT tell operators to spawn bare `how-explorer`. Live pstack operator docs MUST NOT name `/ponytail`. That means `docs/guide/01-setup.md` and `HARNESS.md`. Ponytail is a foreign plugin. pstack does not ship it.

#### Scenario: setup names depth and skill order

- **GIVEN** `docs/guide/01-setup.md`
- **WHEN** an operator finishes install
- **THEN** the page names `MAX_SUBAGENT_DEPTH`, Skill order, `pstack:independent-verifier`, and `scheduler_create`

#### Scenario: essential entries table

- **GIVEN** `docs/guide/01-setup.md`
- **WHEN** an operator looks for slash names and spawn types
- **THEN** the page has Essential entries
- **AND** it names `/tdd`, `/how`, and `/workflow`
- **AND** it does not name `/ponytail`

#### Scenario: harness skill order does not name ponytail

- **GIVEN** `HARNESS.md`
- **WHEN** an operator or playbook reads Skill order
- **THEN** the page does not name `/ponytail`

## REMOVED Requirements

None.

## RENAMED Requirements

None.
