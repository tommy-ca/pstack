## Why

Interrogate of PR 12 found leftover fail-open paths in the hygiene lever. `--apply-skills` can write the default `~/.grok/skills` dest without a claude-shape gate. `--apply` exits 0 when a nested delete records `error`. Sync `--log` is not proven from a linked-worktree copy of the script. A live coverage test mutates cwd and duplicates the decoy CLI test.

## What Changes

- Gate `--apply-skills` on claude-shaped dest and `has_symlink_parent`. Fail closed. Do not chmod.
- `--apply` exits 2 when any nested-cache row has `action=error`.
- Prove `remote_cache()` from a tmp linked-worktree copy of `sync-from-upstream.py`.
- Delete `test_print_coverage_relative_cache_uses_primary`. Keep the decoy CLI test.
- Inline `primary_checkout_root` for `--log` so `--pin`/`--recipe` do not exec `partition.py`.
- Add a rerunnable lever verification script that runs the hygiene pytest slice and CLI dry-run.
- Do not write `~/.grok/skills` from this TUI. Do not `git worktree remove`. Do not leftover-scanner phrase work.

## Capabilities

### New Capabilities

- `pstack-refresh-hygiene`: leftover TSV, nested-clone delete Guard, host-script print, apply-skills fail-closed.

### Modified Capabilities

- `pstack-sync-from-upstream`: `--log` binds the primary overlay cache via `primary_checkout_root`, not script-relative `ROOT`.

## Impact

`skills/swarm/scripts/refresh-hygiene.py`, `scripts/sync-from-upstream.py`, `tests/test_refresh_hygiene.py`, `tests/test_swarm_partition.py`, `tests/test_verify_harness.py`, new `skills/swarm/scripts/verify-refresh-hygiene.py`. No host plugin update. No `mise.toml`.
