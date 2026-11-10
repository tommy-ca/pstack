# pstack-playbooks-not-rhai — Specification hygiene and validation tightening

## MODIFIED Requirements

### Requirement: Playbooks are not plugin Rhai workflows

Feature: pstack-playbooks-not-rhai

The live pstack router MUST remain `/poteto-mode` with markdown playbooks under `skills/poteto-mode/playbooks/`. The manifest `plugin.json` MUST NOT add a `workflows` key, and the repository MUST NOT contain `.grok/workflows/` playbook clones or `.rhai` files under playbooks. Workflow discovery occurs from target repository paths rather than plugin installation. Any optional `.rhai` automations MUST NOT replace `/benny-triage` or `/poteto-mode`.

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
