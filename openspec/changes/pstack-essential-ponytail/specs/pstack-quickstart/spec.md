## ADDED Requirements

None.

## MODIFIED Requirements

### Requirement: Quickstart teaches grok-native spawn and depth

Feature: pstack-quickstart

`docs/guide/01-setup.md` MUST explain grok-native pstack after install: Skill order (pstack then user then bundled), `pstack:<role>` spawn names, `MAX_SUBAGENT_DEPTH` 1, parent fans out, `pstack:independent-verifier`, `/loop` → `scheduler_create`. It MUST NOT tell operators to spawn bare `how-explorer`. Essential entries MUST name `/ponytail` as a user-installed plugin after `/poteto-mode`. It MUST NOT vendor ponytail into `plugin.json`.

#### Scenario: setup names depth and skill order

- **GIVEN** `docs/guide/01-setup.md`
- **WHEN** an operator finishes install
- **THEN** the page names `MAX_SUBAGENT_DEPTH`, Skill order, `pstack:independent-verifier`, and `scheduler_create`

#### Scenario: essential entries table

- **GIVEN** `docs/guide/01-setup.md`
- **WHEN** an operator looks for slash names and spawn types
- **THEN** the page has Essential entries
- **AND** it names `/tdd`, `/how`, `/workflow`, and `/ponytail`
- **AND** `/ponytail` is documented as a user plugin after the router, not a pstack skill

## REMOVED Requirements

None.

## RENAMED Requirements

None.
