# pstack-sync-from-upstream Specification

## Purpose
Define the read-only upstream synchronization interface that reports the pinned tree and adaptation recipe without copying files.

## Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`scripts/sync-from-upstream.py --pin` MUST print the 40-hex `tree` SHA from `UPSTREAM`. `--recipe` MUST name `adapt-harness.py`, `verify-harness.py`, skip `make-bot-ui`, and `pstack:<role>`. Default invocation MUST print the recipe. The script MUST NOT overwrite this tree unless a later flag is added.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync-from-upstream.py --pin` runs
- **THEN** stdout is that SHA

#### Scenario: default argv prints the recipe

- **GIVEN** the shipped script
- **WHEN** `python3 scripts/sync-from-upstream.py` runs with no flags
- **THEN** stdout is the same as `--recipe`

#### Scenario: log names pin and empty-or-commits

- **GIVEN** a fetch of cursor/plugins is possible
- **WHEN** `python3 scripts/sync-from-upstream.py --log` runs
- **THEN** stdout contains `pin ` and the 40-hex SHA
- **AND** stdout contains either `up to date` or at least one oneline commit
- **AND** the script does not copy files into `skills/`
- **AND** `.worktrees/upstream-cursor-plugins` `HEAD` matches `origin/main` after `--log`
