# pstack-sync-from-upstream Specification

## Purpose
Define the read-only upstream synchronization interface that reports the pinned tree and adaptation recipe without copying files.

## Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`UPSTREAM` MUST record the current official Cursor pstack commit used by the port. `scripts/sync_from_upstream.py --pin` MUST print its 40-hex `tree` SHA. `--recipe` and the default invocation MUST print the same explicit refresh recipe. `--log` MUST fetch and fast-forward the **primary** overlay cache (`primary_checkout_root(ROOT) / .worktrees / upstream-cursor-plugins`) to `origin/main`, then report the pinned SHA and commits after it. `--pin` and `--recipe` MUST NOT exec `skills/swarm/scripts/partition.py`. `--log` MUST bind that primary cache even when the script file lives in a linked worktree. The recipe MUST name `adapt_harness.py`, `verify_harness.py`, `pstack:<role>`, the Codex-only executable surfaces, and the intentional exclusions for `make-bot-ui`, Cursor-only packaging, and the separate `advisor` plugin. The script MUST NOT copy upstream files into the port.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync_from_upstream.py --pin` runs
- **THEN** stdout is that SHA

#### Scenario: default argv prints the recipe

- **GIVEN** the shipped script
- **WHEN** `python3 scripts/sync_from_upstream.py` runs with no flags
- **THEN** stdout is the same as `--recipe`
- **AND** stdout names the host adaptation and verification commands
- **AND** stdout classifies `scripts/orch`, `scripts/watch-pr`, `check-plan.mjs`, and `worktree-audit.sh` as Codex compatibility surfaces

#### Scenario: log names pin and empty-or-commits

- **GIVEN** a fetch of cursor/plugins is possible
- **WHEN** `python3 scripts/sync_from_upstream.py --log` runs
- **THEN** stdout contains `pin ` and the 40-hex SHA
- **AND** stdout contains either `up to date` or at least one oneline commit
- **AND** `.worktrees/upstream-cursor-plugins` `HEAD` matches `origin/main`
- **AND** the script does not copy files into `skills/`

#### Scenario: recipe preserves host-owned files

- **GIVEN** the port has Grok, Codex, Claude, Benny, release, and OpenSpec adaptations
- **WHEN** an operator follows the recipe for the current upstream tree
- **THEN** the recipe excludes `HARNESS.md`, manifests, README files, tests, and scripts from blind copying
- **AND** the recipe excludes Cursor-only `.cursor-plugin`, `assets/logo.png`, `make-bot-ui`, and the separate `advisor` plugin
- **AND** the recipe states that unchanged executable files are audited rather than blindly adapted

#### Scenario: log binds primary cache from a worktree copy of the script

- **GIVEN** a tmp linked worktree that contains copies of `sync-from-upstream.py` and `partition.py`
- **WHEN** that worktree copy's `remote_cache()` is loaded
- **THEN** the path is the primary overlay cache
- **AND** the path is not `<worktree>/.worktrees/upstream-cursor-plugins`

#### Scenario: candidate upstream version does not become an applied version

- **GIVEN** the recorded applied pin is `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (0.15.29)
- **AND** the independently observed target in CHANGELOG.md is `c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (0.15.36)
- **WHEN** an operator reads the recipe or runs `--pin` or `--log`
- **THEN** the script MUST NOT modify `UPSTREAM`, `plugin.json`, `pstack.package.json`, the canonical inventory or host package projections
- **AND** the recipe MUST preserve explicit host evidence and independent conformance gates before promotion
- **AND** the CHANGELOG MUST distinguish candidate, adapted, optional, excluded, blocked and actually applied semantics
- **AND** source-only and offline verification MUST NOT be represented as native observed-live execution

#### Scenario: removed orchestration script is not blindly synced

- **GIVEN** upstream 0.15.36 removed its Orchestrate CLI/store
- **WHEN** the repository compares upstream changes to its host-owned adapters
- **THEN** the recipe MUST direct an audit of callers before any removal of local compatibility entrypoints
- **AND** it MUST NOT introduce a second durable scheduler or store
- **AND** unsupported native project state, PR events and nested supervisors remain explicit capability gaps

#### Scenario: statechart is optional without an executable host binding

- **GIVEN** the upstream TypeScript/TLC Statechart compiler is not shipped locally
- **WHEN** a formal-verification creator references the compiler
- **THEN** it MUST resolve the active host's installed capability before invoking it
- **AND** a missing compiler or Java/TLC MUST NOT be counted as a passing model check
- **AND** direct TLC verification may proceed independently of optional visualization
