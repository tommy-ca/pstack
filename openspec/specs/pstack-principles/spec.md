# pstack-principles Specification

## Purpose

Require this port to cover the principle skills present in the pinned canonical pstack tree and preserve decision-oriented use through `/poteto-mode`.

## Requirements

### Requirement: Principle inventory follows the canonical pin

Feature: pstack-principles

The port MUST cover every canonical `skills/principle-*/SKILL.md` artifact at the `UPSTREAM` pin unless an explicit adaptation record classifies it as exclude or gap. The verifier MUST derive the expected inventory from the pin rather than a literal count.

`/poteto-mode` MUST surface the applicable principles and require a real decision citation when a principle is claimed: the response names the principle and the concrete choice it changed.

#### Scenario: canonical adds a principle

- **GIVEN** a new `UPSTREAM` pin adds a `principle-*` skill
- **WHEN** canonical coverage runs
- **THEN** the new artifact is discovered automatically
- **AND** the port fails coverage until it is preserved, adapted, excluded, or gapped
