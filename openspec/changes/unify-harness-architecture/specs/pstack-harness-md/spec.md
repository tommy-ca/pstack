## RENAMED Requirements

- FROM: `### Requirement: HARNESS.md is the host mapping, not a PluginManifest field`
- TO: `### Requirement: grok-tools.md is the unified Grok host mapping, not a PluginManifest field`

## MODIFIED Requirements

### Requirement: grok-tools.md is the unified Grok host mapping, not a PluginManifest field

Feature: pstack-harness-md

`skills/poteto-mode/references/grok-tools.md` MUST be the single Grok host mapping consumed by pstack routing and verification, and root `HARNESS.md` MUST be retired once its current readers have migrated. `/poteto-mode` MUST name `references/grok-tools.md` as the Grok host mapping file. `plugin.json` and generated plugin manifests MUST NOT list the mapping file. grok MUST NOT need the mapping file to discover skills or agents. Development tools (`verify-harness.py`, TEST-PLAN) MAY keep reading the mapping file at its migrated path.

#### Scenario: not a plugin.json field

- **GIVEN** `plugin.json` and the generated `.grok-plugin/plugin.json`
- **WHEN** keys are read
- **THEN** there is no mapping file path
- **AND** `skills` and `agents` still load without it

#### Scenario: poteto-mode requires the file

- **GIVEN** `skills/poteto-mode/SKILL.md`
- **WHEN** the first-todo rule is read
- **THEN** it names `references/grok-tools.md` at the skill reference path for Grok Build

#### Scenario: root HARNESS.md retires after readers migrate

- **GIVEN** the current readers of the former root `HARNESS.md`
- **WHEN** the mapping retires the root file
- **THEN** no current reader requires `HARNESS.md`
- **AND** archived OpenSpec changes and historical planning records keep former file names
