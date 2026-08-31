# pstack-grok-host Specification

## Purpose
TBD - created by archiving change pstack-grok-host-contract. Update Purpose after archive.

## Requirements

### Requirement: English README is the GitHub default

Feature: pstack-grok-host
Rule: Locale files are README.<BCP-47>.md

Root `README.md` MUST be English. Simplified Chinese MUST live in `README.zh-CN.md`. Both MUST carry the switcher `[English](README.md) · [简体中文](README.zh-CN.md)` as the first non-blank line after `# pstack`. English MUST have no CJK Unified Ideographs outside that switcher.

#### Scenario: GitHub landing is English

- **GIVEN** the plugin repository root
- **WHEN** GitHub renders `README.md`
- **THEN** the page is English
- **AND** it links to `README.zh-CN.md`

### Requirement: Spawn types are plugin-qualified

Feature: pstack-grok-host
Rule: grok 1.0.13 registers plugin:name

Shipped skills and HARNESS MUST set `subagent_type` to `pstack:<role-key>` (`pstack:how-explorer`, `pstack:feature`, `pstack:poteto-agent`, `pstack:comment-sicko`, `pstack:independent-verifier`). They MUST NOT treat the bare stem as the TUI type. Toml model keys stay the bare role key. Effort overlays MUST use `~/.grok/roles/pstack:<key>.toml`.

#### Scenario: Bare how-explorer is unknown

- **GIVEN** pstack is in `[plugins].enabled`
- **WHEN** a parent spawns a how explorer
- **THEN** `subagent_type` is `pstack:how-explorer`
- **AND** inspect `.agents[].name` includes `pstack:how-explorer`
- **AND** it does not include bare `how-explorer`

### Requirement: Enable is the skills-and-agents gate

Feature: pstack-grok-host
Rule: inspect enabled is trust

Shipped docs MUST say skills and plugin agents load only when `pstack` is in `[plugins].enabled`. They MUST say `inspect` `plugins[].enabled` is trust. They MUST say enable rewrites `config.toml` and fails with EROFS inside the agent sandbox, and that the fix is a host shell (`grok --sandbox off plugin enable pstack`).

#### Scenario: Trusted but not enabled

- **GIVEN** pstack is installed with `--trust` and missing from `[plugins].enabled`
- **WHEN** inspect is read
- **THEN** docs still tell the operator to enable
- **AND** they name EROFS and the host-shell / `--sandbox off` path

### Requirement: Inspect agent count is the catalog list

Feature: pstack-grok-host
Rule: provides.agents is a directory count

TEST-PLAN MUST NOT require `plugins[].provides.agents == 22`. It MUST require 22 entries in inspect `.agents[]` whose `source.plugin_name` is `pstack`.

#### Scenario: Gate 1 uses agents[]

- **GIVEN** grok 1.0.13 inspect JSON
- **WHEN** Gate 1 checks agent inventory
- **THEN** it counts `.agents[]` with plugin_name pstack
- **AND** it does not treat `provides.agents` as the file count
