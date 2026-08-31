## ADDED Requirements

### Requirement: Adapter-specific surfaces are explicit

Feature: pstack-host-adapter-boundaries

The repository MUST distinguish the Grok plugin surface from retained Codex and
Claude adapter surfaces. Grok-only skills and host primitives MUST NOT be
presented as shared requirements for every adapter. Retained Codex utilities
MAY include `skills/poteto-mode/scripts/orch` and `scripts/watch-pr`, but those
utilities MUST NOT be used as the Grok durable orchestration surface.

#### Scenario: Host manifests expose only their supported surfaces

- **GIVEN** the root, `.grok-plugin`, `.codex-plugin`, and `.claude-plugin` manifests are inspected
- **WHEN** their component paths are compared
- **THEN** root and `.grok-plugin` expose the same Grok skills and agents
- **AND** `.codex-plugin` and `.claude-plugin` expose the shared `./skills/` path and their supported host metadata
- **AND** the Codex and Claude manifests are not required to expose the Grok-only Benny skill tree

#### Scenario: Retained Codex utilities do not become Grok state

- **GIVEN** a reader follows the host mapping for `scripts/orch` or `scripts/watch-pr`
- **WHEN** the mapping is used to choose a live orchestration surface
- **THEN** it identifies those utilities as Codex-only or non-Grok compatibility surfaces
- **AND** Grok durable units, claims, retries, and fanout/fanin remain on canonical host task/agent state and Gas City/Beads

#### Scenario: Verification guidance names the host monitor

- **GIVEN** an operator reads `docs/guide/06-verify-and-ship.md`
- **WHEN** the Babysit boundary is described
- **THEN** the guide names the host `monitor` primitive
- **AND** it does not describe a bundled local watcher

## MODIFIED Requirements

### Requirement: Durable orchestration state remains host-owned

The Grok orchestrate playbook MUST NOT create a second scheduler, database,
session manager, or repository-local orchestration store. Durable units, claims,
frontier state, verification records, gates, and decisions MUST be published
through Grok's canonical task and agent state. Gas City adapters MUST use Gas
City formulas and Beads for routing, retries, persistence, and fanout/fanin.
Missing host fields are a reported gap or gate, not a reason to add a parallel
store. Retained Codex compatibility utilities under `skills/poteto-mode/scripts/`
are outside this Grok durable-state requirement and MUST be identified as such
in the Codex host map.

#### Scenario: A long-running Grok program uses canonical state

- **GIVEN** a coordinator starts a multi-day pstack orchestration run in Grok Build
- **WHEN** it records units, completions, verification, or human gates
- **THEN** the playbook directs those records to canonical Grok task and agent state
- **AND** a Gas City adapter names Gas City formulas and Beads as its durable surfaces
- **AND** it does not create `orchestrate/<project-slug>/` or invoke `scripts/orch/orch.ts`

### Requirement: Grok manifests remain in lockstep while other adapters stay explicit

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
