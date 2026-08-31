# pstack-grok-host-boundary Specification

## Purpose

Keep PStack orchestration and babysitting on the Grok host's canonical runtime primitives.

## Requirements

### Requirement: Babysitting uses the host monitor primitive

The babysit playbook MUST use the Grok host `monitor` primitive for watchable status commands. It MUST describe `command`, `description`, and bounded `timeout_ms`, and MUST route recurring checks through `/loop` → `scheduler_create`. It MUST NOT invoke or prescribe a repository-local watcher path or polling loop.

#### Scenario: Watch one frontier without a local watcher

- **GIVEN** an operator starts the pstack babysit playbook
- **WHEN** the playbook explains how to obtain PR status
- **THEN** it names `monitor` with `command`, `description`, and `timeout_ms`
- **AND** it does not name `scripts/watch-pr/watch-pr`
- **AND** recurring checks use `/loop` → `scheduler_create`

### Requirement: Durable orchestration state remains host-owned

Feature: pstack-grok-host-boundary

The orchestrate playbook MUST NOT create a second scheduler, database, session manager, or repository-local orchestration store. Durable units, claims, frontier state, verification records, gates, and decisions MUST be published through the host's canonical task and agent state. Gas City adapters MUST use Gas City formulas and Beads for routing, retries, persistence, and fanout/fanin. Missing host fields are a reported gap or gate, not a reason to add a parallel store.

#### Scenario: A long-running program uses canonical state

- **GIVEN** a coordinator starts a multi-day pstack orchestration run
- **WHEN** it records units, completions, verification, or human gates
- **THEN** the playbook directs those records to canonical host task and agent state
- **AND** a Gas City adapter names Gas City formulas and Beads as its durable surfaces
- **AND** it does not create `orchestrate/<project-slug>/` or invoke `scripts/orch/orch.ts`

### Requirement: Adapter manifests remain lockstep

Feature: pstack-grok-host-boundary

The root `plugin.json` and retained `.grok-plugin/plugin.json` adapter metadata MUST expose the same version, skill paths, and agent path. The shared skill paths MUST include `./skills/` and `./automations/benny-grok/skills/`. Neither manifest may register plugin-global hooks.

#### Scenario: Benny is visible through every retained manifest

- **GIVEN** the root and adapter plugin manifests are loaded
- **WHEN** their component metadata is compared
- **THEN** their versions match
- **AND** their skill-path lists match and include the live Benny skill tree
- **AND** their agent paths match
- **AND** neither manifest contains `hooks`
