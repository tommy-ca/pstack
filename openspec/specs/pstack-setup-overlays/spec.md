# pstack-setup-overlays Specification

## Purpose
Specify optional `/setup-pstack` model and effort overlays, their plugin-qualified role paths, and default behavior.

## Requirements

### Requirement: Host-neutral entry dispatches to the declared setup skill

Feature: pstack-setup-overlays

`/setup-pstack` MUST be host-neutral: it MUST resolve the active host, read that host's `setup` projection from `profiles/<host>.json` (`schemas/portability/setup-projection.schema.json`), and hand off to the skill the projection names. It MUST hold no host file path, model slug, or effort enum itself. A host whose profile declares no `setup` block, or a candidate host that declares a CLI-probing surface, MUST produce a named GAP or BLOCKED report; it MUST NOT fall back to another host's setup.

#### Scenario: no setup block is a reported gap

- **GIVEN** a host profile with no `setup` key
- **WHEN** `/setup-pstack` resolves that host
- **THEN** it reports a GAP naming the host and the missing declaration
- **AND** it runs no host-specific setup steps and writes no other host's files

### Requirement: Optional setup writes grok overlays

Feature: pstack-setup-overlays

Official `/setup-pstack` writes `~/.cursor/rules/pstack-models.mdc`. This port's Grok Build adapter skill `/setup-pstack-grok` (dispatched from the host-neutral entry when `profiles/grok.json#setup.source` is `host-cli`) MUST write `~/.grok/pstack-models.toml` with **top-level** role keys (`feature = "grok-4.6"`) plus `[effort]`, and `~/.grok/roles/pstack:<key>.toml` (`description`, `reasoning_effort`). It MUST NOT use a `[models]` table. It MUST NOT write Cursor mdc. Absent overlay: shipped `grok-4.6` plus agent frontmatter effort. A projected profile or a written config file is a declaration, never evidence that the host accepted the model or the level.

#### Scenario: overlay stem matches spawn type

- **GIVEN** `/setup-pstack-grok` accepted defaults
- **WHEN** it writes a role file for `feature`
- **THEN** the path is `~/.grok/roles/pstack:feature.toml`
- **AND** toml **keys** stay the bare role name (`feature`)
