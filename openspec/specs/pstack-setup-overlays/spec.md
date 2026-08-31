# pstack-setup-overlays Specification

## Purpose
TBD - created by archiving change pstack-atomic-blocks. Update Purpose after archive.

## Requirements

### Requirement: Optional setup writes grok overlays

Feature: pstack-setup-overlays

Official `/setup-pstack` writes `~/.cursor/rules/pstack-models.mdc`. This port's `/setup-pstack` MUST write `~/.grok/pstack-models.toml` with **top-level** role keys (`feature = "grok-4.6"`) plus `[effort]`, and `~/.grok/roles/pstack:<key>.toml` (`description`, `reasoning_effort`). It MUST NOT use a `[models]` table. It MUST NOT write Cursor mdc. Absent overlay: shipped `grok-4.6` plus agent frontmatter effort.

#### Scenario: overlay stem matches spawn type

- **GIVEN** `/setup-pstack` accepted defaults
- **WHEN** it writes a role file for `feature`
- **THEN** the path is `~/.grok/roles/pstack:feature.toml`
- **AND** toml **keys** stay the bare role name (`feature`)
