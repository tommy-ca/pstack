## Why

Refreshing this port from official Cursor pstack is a five-step recipe in UPSTREAM and docs/guide/09-make-it-yours.md. Operators re-type git log/diff against a 40-hex pin. A small stdlib script should print the pin, the recipe, and the log since that tree.

## What Changes

- `scripts/sync-from-upstream.py`: `--pin`, `--recipe` (default), `--log` (network).
- Guide and UPSTREAM point at the script. Copy still stays operator-owned.
- Tests drive `--pin` and `--recipe` against the shipped UPSTREAM file.

## Capabilities

### New Capabilities

- `pstack-sync-from-upstream`: mechanical refresh recipe from Cursor pstack.

### Modified Capabilities

None.

## Impact

scripts/, UPSTREAM, docs/guide/09-make-it-yours.md, tests/test_verify_harness.py.
