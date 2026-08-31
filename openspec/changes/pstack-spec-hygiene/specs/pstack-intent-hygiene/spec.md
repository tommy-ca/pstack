## ADDED Requirements

### Requirement: Task-complete changes have a complete intent chain before archive

Feature: pstack-intent-hygiene

The repository verification gate MUST inspect active OpenSpec changes before archive. For an active change whose `tasks.md` has at least one task and every task checkbox is checked, the gate MUST require both `design.md` and `adr.md`. Incomplete changes MAY remain in planning without this gate. Archived historical directories are outside this pre-archive check and MUST NOT be rewritten by it.

#### Scenario: Complete change missing design or ADR fails the gate

- **GIVEN** an active change has a task list with every task checked
- **WHEN** the repository verification gate scans active changes
- **THEN** it reports each missing `design.md` or `adr.md`
- **AND** it does not report an archived directory for the same missing files

#### Scenario: Incomplete planning change remains editable

- **GIVEN** an active change has at least one unchecked task
- **WHEN** the repository verification gate scans active changes
- **THEN** it does not apply the pre-archive design/ADR completeness failure
- **AND** the change remains available for the normal OpenSpec planning flow
