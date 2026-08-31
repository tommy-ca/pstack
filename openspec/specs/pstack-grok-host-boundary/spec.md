# pstack-grok-host-boundary Specification

## Purpose

Keep PStack orchestration and babysitting on the Grok host's canonical
runtime primitives.

## Requirements

### Requirement: Babysitting uses the host monitor primitive

The babysit playbook MUST use the Grok host `monitor` primitive for watchable
status commands. It MUST describe `command`, `description`, and bounded
`timeout_ms`, and MUST route recurring checks through `/loop` →
`scheduler_create`. It MUST NOT invoke or prescribe a repository-local watcher
path or polling loop.

#### Scenario: Watch one frontier without a local watcher

- **GIVEN** an operator starts the pstack babysit playbook
- **WHEN** the playbook explains how to obtain PR status
- **THEN** it names `monitor` with `command`, `description`, and `timeout_ms`
- **AND** it does not name `scripts/watch-pr/watch-pr`
- **AND** recurring checks use `/loop` → `scheduler_create`

### Requirement: Durable orchestration state remains host-owned on the Grok path

Feature: pstack-grok-host-boundary

The orchestrate playbook MUST NOT create a second scheduler, database, session
manager, or repository-local orchestration store. Durable units, claims,
frontier state, verification records, gates, and decisions MUST be published
through Grok's canonical task and agent state. Gas City adapters MUST use Gas
City formulas and Beads for routing, retries, persistence, and fanout/fanin.
Missing host fields are a reported gap or gate, not a reason to add a parallel
store. Retained Codex compatibility utilities under
`skills/poteto-mode/scripts/` are outside this Grok durable-state requirement
and MUST be identified as such in the Codex host map.

#### Scenario: A long-running Grok program uses canonical state

- **GIVEN** a coordinator starts a multi-day pstack orchestration run in Grok Build
- **WHEN** it records units, completions, verification, or human gates
- **THEN** the playbook directs those records to canonical Grok task and agent state
- **AND** a Gas City adapter names Gas City formulas and Beads as its durable surfaces
- **AND** it does not create `orchestrate/<project-slug>/` or invoke `scripts/orch/orch.ts`

### Requirement: Grok manifests remain lockstep while other adapters stay explicit

Feature: pstack-grok-host-boundary

The root `plugin.json` and retained `.grok-plugin/plugin.json` adapter metadata
MUST expose the same version, skill paths, and agent path. The shared Grok skill
paths MUST include `./skills/` and `./automations/benny-grok/skills/`. Neither
Grok manifest may register plugin-global hooks. The retained Codex and Claude
manifests MUST document their host-specific component sets and MAY omit
Grok-only automation skills.

#### Scenario: Grok parity and non-Grok asymmetry are intentional

- **GIVEN** all retained adapter manifests are loaded
- **WHEN** their component metadata is compared
- **THEN** root and `.grok-plugin` versions, skill-path lists, and agent paths match
- **AND** both Grok manifests include the live Benny skill tree
- **AND** the Codex and Claude manifests retain only their supported shared and host-specific paths
- **AND** no manifest contains a plugin-global `hooks` key
