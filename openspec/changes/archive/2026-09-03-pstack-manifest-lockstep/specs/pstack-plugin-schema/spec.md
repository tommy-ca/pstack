## ADDED Requirements

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
