# pstack-principles Specification

## Purpose
TBD - created by archiving change pstack-atomic-blocks. Update Purpose after archive.

## Requirements

### Requirement: Twenty-one principle skills

Feature: pstack-principles

The plugin MUST ship 21 `skills/principle-*/SKILL.md` files. `/poteto-mode` MUST index them inline (core, architecture, verification, delegation, meta) and require a real decision citation when a principle is applied.

#### Scenario: principle count

- **GIVEN** the plugin tree
- **WHEN** `verify-harness.py` runs
- **THEN** it reports principles: 21
