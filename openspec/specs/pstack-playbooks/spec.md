# pstack-playbooks Specification

## Purpose

Require the port to preserve the canonical playbook set and playbook intent while allowing host-specific mechanism changes at adapter boundaries.

## Requirements

### Requirement: Playbook inventory follows the canonical pin

Feature: pstack-playbooks

The port MUST cover every canonical Markdown playbook under `skills/poteto-mode/playbooks/` at the `UPSTREAM` pin. The expected set MUST be discovered from that pin rather than encoded as a literal count.

Playbooks remain Markdown workflow intent. They MUST NOT be reimplemented as a portable workflow DSL merely to support another harness.

#### Scenario: inventories match the pin

- **GIVEN** official pstack at the recorded `UPSTREAM` pin
- **WHEN** playbook filenames are enumerated
- **THEN** every canonical playbook has a preserve, adapt, exclude, or gap record
- **AND** host-specific tool syntax is handled by the adapter

### Requirement: Composed skills retain their semantics

The `swarm`, `arena`, and `interrogate` skills remain compositions over playbook/agent capabilities rather than new harness primitives. Their independence, evidence, aggregation, synthesis, and verification rules MUST be preserved according to `pstack-portability`.

### Requirement: Domain skills are explicit scope decisions

A canonical skill that is intentionally not shipped by a host port, such as a host- or domain-specific skill, MUST be represented as an explicit exclusion with a reason. Omission alone is not coverage.
