# pstack-principles Specification

## Purpose

Require this port to cover the principle skills present in the pinned canonical pstack tree and preserve decision-oriented use through `/poteto-mode`.

## Requirements

### Requirement: Twenty-four principle skills

Feature: pstack-principles

The plugin MUST ship 24 `skills/principle-*/SKILL.md` files for the canonical reference pin, covering every canonical artifact unless classified as exclude or gap. The verifier MUST derive the expected inventory from the pin. `/poteto-mode` MUST surface applicable principles and require a concrete decision citation when a principle is claimed.

#### Scenario: principle count

- **GIVEN** the plugin tree
- **WHEN** `verify-harness.py` runs
- **THEN** it reports principles: 24

#### Scenario: canonical adds a principle

- **GIVEN** a new `UPSTREAM` pin adds a `principle-*` skill
- **WHEN** canonical coverage runs
- **THEN** the new artifact is discovered automatically
- **AND** the port fails coverage until it is preserved, adapted, excluded, or gapped
