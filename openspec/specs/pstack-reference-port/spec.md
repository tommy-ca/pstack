# pstack-reference-port Specification

## Purpose
TBD - created by archiving change pstack-reference-port. Update Purpose after archive.

## Requirements

### Requirement: Portable core is principles, playbooks, and a host map

Feature: pstack-reference-port

Operator docs MUST extract official pstack philosophy: less code over loc, go deep then parallelize, one router, steer with 21 principle names, prove on the real artifact. They MUST split the tree into core (principles, playbook intent, router), host map, and optional domain packs. The host map MUST be the only required new file for a port. This Grok tree MUST be named as a reference implementation of that host-map step.

#### Scenario: porting page names the layers

- **GIVEN** `docs/guide/12-porting.md`
- **WHEN** an operator wants pstack on another host
- **THEN** the page names 21 principles, host map, and Laziness Protocol
- **AND** it tells them not to copy the previous host's spawn fields as the core

#### Scenario: capability checklist is fill-in

- **GIVEN** `docs/guide/12-porting.md`
- **WHEN** the new agent has its own harness
- **THEN** the page has a Capability checklist with Spawn a child, Join / wait, and Overnight loop
- **AND** it tells the porter to write `gap` when the host has no equivalent
