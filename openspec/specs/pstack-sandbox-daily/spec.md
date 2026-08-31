# pstack-sandbox-daily Specification

## Purpose
Daily TUI is grok workspace. Plugin enable rewrites config.toml from a host shell with sandbox off.

## Requirements

### Requirement: Daily TUI is workspace, enable is host-shell off

Feature: pstack-sandbox-daily

Operator docs MUST name grok **workspace** as the pstack daily TUI driver. They MUST say Linux bwrap pins `config.toml` read-only, so `grok plugin enable` runs from a host shell with `--sandbox off`. Plugin source MUST be edited in the git CWD (writable under workspace/homelab), then reinstalled. Docs MUST NOT tell operators to run the all-day TUI with `--sandbox off` just to enable a plugin. Docs MUST NOT remove `workspace-secrets` denials.

#### Scenario: setup names workspace daily driver

- **GIVEN** `docs/guide/01-setup.md`
- **WHEN** an operator starts a pstack day
- **THEN** the page has Daily driver
- **AND** it names `workspace`
- **AND** it keeps enable on `grok --sandbox off`
