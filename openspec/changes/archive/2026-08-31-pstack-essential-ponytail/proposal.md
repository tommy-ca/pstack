## Why

The setup Essential entries table and HARNESS Skill order do not name `/ponytail`. Operators who already installed that user plugin have no first-session map for it. They either skip it or treat it as a pstack router, which it is not.

## What Changes

- `docs/guide/01-setup.md` Essential entries: a Lazy row for `/ponytail` after `/poteto-mode`.
- `HARNESS.md` Skill order: a YAGNI row with user-column `/ponytail` if inspect lists it.
- Spec `pstack-quickstart` essential entries scenario also names `/ponytail`.
- Tests lock `/ponytail` on setup and HARNESS, and lock that `plugin.json` does not name ponytail.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-quickstart`: Essential entries names `/ponytail` as a user plugin after the router. It does not vendor ponytail into pstack.

## Impact

`docs/guide/01-setup.md`, `HARNESS.md`, `openspec/specs/pstack-quickstart/spec.md`, `tests/test_verify_harness.py`. Not `plugin.json`. Not the catalog.
