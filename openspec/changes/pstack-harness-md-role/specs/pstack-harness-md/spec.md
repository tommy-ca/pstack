## ADDED Requirements

### Requirement: HARNESS.md is the host mapping, not a PluginManifest field

Feature: pstack-harness-md

`HARNESS.md` MUST remain at the plugin repo root so git install copies it. `/poteto-mode` MUST name it as the Grok host mapping file. `plugin.json` MUST NOT list `HARNESS.md`. grok MUST NOT need it to discover skills or agents. Development tools (`verify-harness.py`, TEST-PLAN) MAY keep reading it.

#### Scenario: not a plugin.json field

- **GIVEN** `plugin.json`
- **WHEN** keys are read
- **THEN** there is no HARNESS path
- **AND** `skills` and `agents` still load without it

#### Scenario: poteto-mode requires the file

- **GIVEN** `skills/poteto-mode/SKILL.md`
- **WHEN** the first-todo rule is read
- **THEN** it names `HARNESS.md` at the plugin root for Grok Build
