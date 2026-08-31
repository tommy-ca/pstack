# pstack-router Specification

## Purpose
TBD - created by archiving change pstack-atomic-blocks. Update Purpose after archive.

## Requirements

### Requirement: poteto-mode is the default router

Feature: pstack-router

`/poteto-mode` MUST match the user request to one bundled playbook, copy that playbook's steps into the todo list verbatim, and route to other skills as those steps fire. It MUST be slash-invocable (`disable-model-invocation: true` on grok). Casual turns MUST NOT auto-enter.

#### Scenario: bug-shaped request

- **GIVEN** a request with a defect, repro, and checkable outcome
- **WHEN** the operator types `/poteto-mode …`
- **THEN** the parent copies `playbooks/bug-fix.md` steps into todos
- **AND** skipped steps stay listed with `skip: <reason>`
