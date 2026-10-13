# pstack-sync-from-upstream Specification

## Purpose
Define the read-only upstream synchronization interface that reports the pinned tree and adaptation recipe without copying files.

## Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`UPSTREAM` MUST record the current official Cursor pstack commit used by the port. `scripts/sync-from-upstream.py --pin` MUST print its 40-hex `tree` SHA. `--recipe` and the default invocation MUST print the same explicit refresh recipe. `--log` MUST fetch and fast-forward the **primary** overlay cache (`primary_checkout_root(ROOT) / .worktrees / upstream-cursor-plugins`) to `origin/main`, then report the pinned SHA and commits after it. `--pin` and `--recipe` MUST NOT exec `skills/swarm/scripts/partition.py`. `--log` MUST bind that primary cache even when the script file lives in a linked worktree. The recipe MUST name `adapt-harness.py`, `verify-harness.py`, `pstack:<role>`, the Codex-only executable surfaces, and the intentional exclusions for `make-bot-ui`, Cursor-only packaging, and the separate `advisor` plugin. The script MUST NOT copy upstream files into the port.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync-from-upstream.py --pin` runs
- **THEN** stdout is that SHA

#### Scenario: default argv prints the recipe

- **GIVEN** the shipped script
- **WHEN** `python3 scripts/sync-from-upstream.py` runs with no flags
- **THEN** stdout is the same as `--recipe`
- **AND** stdout names the host adaptation and verification commands
- **AND** stdout classifies `scripts/orch`, `scripts/watch-pr`, `check-plan.mjs`, and `worktree-audit.sh` as Codex compatibility surfaces

#### Scenario: log names pin and empty-or-commits

- **GIVEN** a fetch of cursor/plugins is possible
- **WHEN** `python3 scripts/sync-from-upstream.py --log` runs
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

#### Scenario: current upstream packaging delta remains classified

- **GIVEN** the upstream compare for the recorded pin tree `1dcc2bacde73ddd284803b7af28164d0436198fc` contains an official pstack packaging/logo delta and a separate `advisor` plugin
- **WHEN** the port refresh is reviewed
- **THEN** the adapter records the new pstack base version (`0.15.21-grokbuild.0` lineage)
- **AND** it excludes the Cursor-only logo and `advisor` plugin
- **AND** it reports unchanged executable files for audit rather than blind copying
