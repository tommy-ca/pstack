# pstack-recursive-plan-validation — Spec hygiene and validation tightening

## MODIFIED Requirements

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
