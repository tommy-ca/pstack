## MODIFIED Requirements

### Requirement: Sync script prints pin and recipe without copying

Feature: pstack-sync-from-upstream

`UPSTREAM` MUST record the current official Cursor pstack commit used by the port. `scripts/sync-from-upstream.py --pin` MUST print its 40-hex `tree` SHA. `--recipe` and the default invocation MUST print the same explicit refresh recipe. `--log` MUST fetch and fast-forward the **primary** overlay cache (`primary_checkout_root(ROOT) / .worktrees / upstream-cursor-plugins`) to `origin/main`, then report the pinned SHA and commits after it. `--pin` and `--recipe` MUST NOT exec `skills/swarm/scripts/partition.py`. `--log` MUST bind that primary cache even when the script file lives in a linked worktree. The recipe MUST name `adapt-harness.py`, `verify-harness.py`, `pstack:<role>`, and the intentional exclusions for `make-bot-ui` and Cursor-only packaging. The script MUST NOT copy upstream files into the port.

#### Scenario: pin matches UPSTREAM

- **GIVEN** `UPSTREAM` contains `tree <40-hex>`
- **WHEN** `python3 scripts/sync-from-upstream.py --pin` runs
- **THEN** stdout is that SHA

#### Scenario: log binds primary cache from a worktree copy of the script

- **GIVEN** a tmp linked worktree that contains copies of `sync-from-upstream.py` and `partition.py`
- **WHEN** that worktree copy's `remote_cache()` is loaded
- **THEN** the path is the primary overlay cache
- **AND** the path is not `<worktree>/.worktrees/upstream-cursor-plugins`
