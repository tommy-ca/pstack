# pstack-reference-port Specification

## Purpose

Define this repository as a reference port of canonical Cursor pstack and prevent any host adapter from becoming the source of truth for another host.

## Requirements

### Requirement: Cursor pstack is canonical and this repository is reference evidence

Feature: pstack-reference-port

Official `cursor/plugins/pstack` at the immutable `UPSTREAM` pin MUST remain the canonical authority for principles, skills, router behavior, playbook intent, roles, ordering, and verification rules.

This repository MUST be described as a reference port. Grok Build is the strongest implemented reference adapter in this tree. Codex and Claude Code mappings or manifests MAY be present, but their support status MUST follow `pstack-portability` conformance rather than inherit authority from the Grok adapter.

#### Scenario: port another harness

- **GIVEN** an operator ports pstack to another harness
- **WHEN** they need canonical behavior
- **THEN** they read the pinned official pstack source and the portability contract
- **AND** they may use this Grok implementation as evidence or prior art
- **AND** they do not derive semantics transitively from Grok-specific call sites

### Requirement: Pin conformance and upstream freshness are separate

The port MUST report whether it conforms to its recorded pin separately from whether official pstack has newer unclassified changes.

#### Scenario: upstream advances

- **GIVEN** the recorded pin still passes its coverage checks
- **AND** official pstack has commits after that pin
- **THEN** pin conformance may remain PASS
- **AND** upstream freshness reports drift until the new changes are classified
