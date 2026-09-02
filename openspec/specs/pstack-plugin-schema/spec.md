# pstack-plugin-schema Specification

## Purpose
Constrain pstack plugin manifests and agent frontmatter to fields Grok actually deserializes, excluding unsupported components and overlay shapes.

## Requirements

### Requirement: Manifest uses only deserialized plugin.json keys

Feature: pstack-plugin-schema

`plugin.json` MUST NOT contain `displayName`. `repository` MUST be a string. `author` MUST be an object. The plugin MUST NOT ship `commands/`, `hooks/`, `.mcp.json`, or `.lsp.json`.

#### Scenario: validate extra keys stay out

- **GIVEN** repo-root `plugin.json`
- **WHEN** tests read it
- **THEN** `displayName` is absent
- **AND** `commands/` does not exist

### Requirement: Plugin agents omit invalid permissionMode and YAML background

Feature: pstack-plugin-schema

Agent frontmatter MUST NOT set `permissionMode: plan` or `permissionMode: bypassPermissions`. It MUST NOT set `background:`. Overlay paths MUST use `~/.grok/roles/pstack:<key>.toml`. Spawn background remains `spawn_subagent` `background`.

#### Scenario: how-explorer YAML

- **GIVEN** `agents/how-explorer.md`
- **WHEN** frontmatter is read
- **THEN** it has `effort` and `capabilityMode: execute`
- **AND** it has no `permissionMode: plan`
- **AND** it has no `background: true`

### Requirement: No-write plugin agents use capabilityMode execute

Feature: pstack-plugin-schema
Rule: closed no-write set vs everyone else

Grok 1.0.13 applies `AgentDefinition.capabilityMode`. Mode `execute` allows read and shell and forbids file edits. Spawn `capability_mode` is ignored.

The no-write set is exactly `how-explorer`, `how-explainer`, `how-critics`, `interrogate-reviewers`, `arena-cross-judge-pool`, `independent-verifier`, and `comment-sicko`. Each of those agent files MUST set `capabilityMode: execute`. Every other `agents/*.md` file MUST omit `capabilityMode`. `why-investigators`, `why-synthesizer`, `reflect-judgment`, and `reflect-tooling` stay prompt posture. `inheritSkills` is not part of this write-bit contract.

#### Scenario: no-write agents keep execute

- **GIVEN** the seven no-write agent files exist
- **WHEN** the verification test reads their YAML frontmatter
- **THEN** each file contains `capabilityMode: execute`
- **AND** a missing or different mode on any of those files fails the test with the agent path

#### Scenario: writers and prompt-posture agents omit capabilityMode

- **GIVEN** every other file under `agents/`
- **WHEN** the verification test reads their YAML frontmatter
- **THEN** `capabilityMode` is absent
- **AND** an accidental `capabilityMode: execute` on a writer or prompt-posture agent fails the test with the agent path

### Requirement: Tracked manifests share adapter version

Feature: pstack-plugin-schema
Rule: one adapter version across every tracked manifest surface

The repository MUST keep the version in root `plugin.json`, `.grok-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json` equal. The first `pstack` entry in `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` MUST declare that same version. The root `plugin.json` version is authoritative; the contract MUST remain `MAJOR.MINOR.PATCH-grokbuild.N` and MUST NOT hardcode a historical version in the verification rule.

#### Scenario: all tracked manifests match the root version

- **GIVEN** the repository contains the five host/catalog manifests and root `plugin.json`
- **WHEN** the manifest verification test reads their version fields
- **THEN** every manifest version equals the root `plugin.json` version
- **AND** both marketplace files select the `pstack` entry rather than an unrelated plugin

#### Scenario: stale overlay metadata fails verification

- **GIVEN** any tracked manifest declares a version different from root `plugin.json`
- **WHEN** the manifest verification test runs
- **THEN** the test fails
- **AND** the failure identifies the stale manifest path and expected root version

#### Scenario: version bumps update all surfaces without a historical constant

- **GIVEN** root `plugin.json` changes to a new valid `MAJOR.MINOR.PATCH-grokbuild.N` version
- **WHEN** the manifest verification test runs
- **THEN** every tracked manifest must use the new root version
- **AND** the test does not require a literal version string tied to one release
