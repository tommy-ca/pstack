# pstack-principles Specification

## Purpose
Define the 23 principle skill inventory and require cited decisions when applying principles through `/poteto-mode`.

## Requirements

### Requirement: Twenty-three principle skills

Feature: pstack-principles

The plugin MUST ship 23 `skills/principle-*/SKILL.md` files. `/poteto-mode` MUST index them inline (core, architecture, verification, delegation, meta) and require a real decision citation when a principle is applied.

#### Scenario: principle count

- **GIVEN** the plugin tree
- **WHEN** `verify-harness.py` runs
- **THEN** it reports principles: 23
