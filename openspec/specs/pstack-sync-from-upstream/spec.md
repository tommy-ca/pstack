# pstack-sync-from-upstream Specification

## Purpose
Define the read-only upstream synchronization interface that reports the pinned tree and adaptation recipe without copying files.

## Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`UPSTREAM` MUST record the current official Cursor pstack commit used by the port. `scripts/sync-from-upstream.py --pin` MUST print its 40-hex `tree` SHA. `--recipe` and the default invocation MUST print the same explicit refresh recipe. `--log` MUST fetch and fast-forward `.worktrees/upstream-cursor-plugins` to `origin/main`, then report the pinned SHA and commits after it. The recipe MUST name `adapt-harness.py`, `verify-harness.py`, `pstack:<role>`, and the intentional exclusions for `make-bot-ui` and Cursor-only packaging. The script MUST NOT copy upstream files into the port.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync-from-upstream.py --pin` runs
- **THEN** stdout is that SHA

#### Scenario: default argv prints the recipe

- **GIVEN** the shipped script
- **WHEN** `python3 scripts/sync-from-upstream.py` runs with no flags
- **THEN** stdout is the same as `--recipe`
- **AND** stdout names the host adaptation and verification commands

#### Scenario: log names pin and empty-or-commits

- **GIVEN** a fetch of cursor/plugins is possible
- **WHEN** `python3 scripts/sync-from-upstream.py --log` runs
- **THEN** stdout contains `pin ` and the 40-hex SHA
- **AND** stdout contains either `up to date` or at least one oneline commit
- **AND** `.worktrees/upstream-cursor-plugins` `HEAD` matches `origin/main`
- **AND** the script does not copy files into `skills/`

#### Scenario: recipe preserves host-owned files

- **GIVEN** the port has Grok, Codex, Claude, Benny, release, and OpenSpec adaptations
- **WHEN** an operator follows the recipe
- **THEN** the recipe excludes `HARNESS.md`, manifests, README files, tests, and scripts from blind copying
- **AND** the recipe excludes Cursor-only `.cursor-plugin`, `assets/logo.png`, and `make-bot-ui`
