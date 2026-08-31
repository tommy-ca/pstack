# pstack-playbooks-not-rhai Specification

## Purpose

Keep PStack playbooks as the markdown `/poteto-mode` router rather than plugin-shipped Rhai workflows.

## Requirements

### Requirement: Playbooks are not plugin Rhai workflows

Feature: pstack-playbooks-not-rhai

The live pstack router MUST remain `/poteto-mode` and markdown playbooks under `skills/poteto-mode/playbooks/`. This plugin MUST NOT add a `workflows` key to `plugin.json`. This repo MUST NOT contain `.grok/workflows/` playbook clones. `skills/poteto-mode/playbooks/` MUST NOT contain `.rhai` files. Grok discovers workflows from a target repo's `.grok/workflows/` or `~/.grok/workflows/`, not from plugin install. Optional `automations/benny-grok/workflows/*.rhai` MAY exist as copies. They MUST NOT replace `/benny-triage` slash skills or `/poteto-mode`.

#### Scenario: plugin manifest has no workflows key

- **GIVEN** `plugin.json` on this port
- **WHEN** keys are read
- **THEN** `workflows` is absent
- **AND** `skills` still lists `./skills/` and `./automations/benny-grok/skills/`

#### Scenario: playbooks stay markdown

- **GIVEN** `skills/poteto-mode/playbooks/`
- **WHEN** files are listed
- **THEN** there are 22 named playbooks plus `opening-a-pr.md`
- **AND** none of those files is `.rhai`

#### Scenario: no plugin-shipped workflow dir

- **GIVEN** this repository root
- **WHEN** `.grok/workflows/` is checked
- **THEN** that directory does not exist

#### Scenario: Benny rhai is not the router

- **GIVEN** `automations/benny-grok/workflows/benny-triage.rhai`
- **WHEN** an operator enables pstack
- **THEN** `/benny-triage` still loads from the skills path
- **AND** the `.rhai` file is not required for that slash skill
