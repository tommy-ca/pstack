## ADDED Requirements

### Requirement: pstack is a single-plugin git repo

Feature: pstack-release-tag
Rule: one plugin, one git tag namespace
Rule: not a catalog sibling folder

pstack MUST remain the `tommy-ca/pstack` repository with `plugin.json` at the repo root. It MUST NOT relocate into `grok-build-plugins/pstack` or `plugins/pstack`. `scripts/release.sh` MUST keep tagging this repo. Catalog tagging MUST NOT become the pstack tagger. Documented install MUST stay `grok plugin install tommy-ca/pstack --trust`. Existing tags MUST NOT be moved.

#### Scenario: plugin.json stays at repo root

- **GIVEN** `plugin.json` at the repository root
- **WHEN** `grok plugin tag` runs from this checkout
- **THEN** the tag is created in `tommy-ca/pstack`
- **AND** the version grammar stays `MAJOR.MINOR.PATCH-grokbuild.N`

#### Scenario: catalog nest is rejected

- **GIVEN** a later change that would copy this tree into grok-build-plugins
- **WHEN** pstack location is considered
- **THEN** the plugin remains this repository
- **AND** existing tags are not moved
