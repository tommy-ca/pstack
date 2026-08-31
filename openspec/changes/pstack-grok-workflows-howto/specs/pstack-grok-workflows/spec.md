## ADDED Requirements

### Requirement: Document grok workflows without porting playbooks

Feature: pstack-grok-workflows

Operator docs MUST teach Grok workflow discovery from grok-build source: bundled, builtin, project `.grok/workflows/`, user `~/.grok/workflows/`. They MUST name `PluginManifest` and that it has no `workflows` field. They MUST show Rhai `agent_type` `pstack:how-explorer` after enable. They MUST NOT tell operators to clone playbooks into this plugin as Rhai. This plugin repo MUST NOT contain `.grok/workflows/`.

#### Scenario: guide names discovery and agent_type

- **GIVEN** `docs/guide/11-grok-workflows.md`
- **WHEN** an operator wants a bounded fan-out in a product repo
- **THEN** the page names `.grok/workflows`, `/workflow`, `agent_type`, and `pstack:how-explorer`
- **AND** it says workflows are not a plugin.json field

#### Scenario: playbooks stay markdown

- **GIVEN** ADR 0005
- **WHEN** someone asks to port Feature.md to Rhai inside this plugin
- **THEN** the spec and tests still forbid `playbooks/*.rhai` and a plugin `workflows` key
