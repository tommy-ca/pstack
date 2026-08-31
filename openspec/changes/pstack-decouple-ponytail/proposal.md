## Why

Live pstack docs name `/ponytail` on the first-session table and in HARNESS Skill order. Ponytail is a separate Grok plugin. pstack does not own it, load it, or ship it. Teaching it inside pstack recouples two products.

## What Changes

- Remove `/ponytail` from `docs/guide/01-setup.md` Essential entries, Router prose, and the after-the-router sentence.
- Remove the HARNESS Skill order YAGNI row that names `/ponytail`.
- Restore `pstack-quickstart` so Essential entries names `/tdd`, `/how`, `/workflow` and MUST NOT name `/ponytail`.
- Replace the test that required ponytail in pstack docs with a recouple lock.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-quickstart`: live setup and HARNESS MUST NOT name `/ponytail`. Essential entries stays a pstack table.

## Impact

`docs/guide/01-setup.md`, `HARNESS.md`, `openspec/specs/pstack-quickstart/spec.md`, `tests/test_verify_harness.py`. Not `plugin.json`. Not the catalog. Not the archived `pstack-essential-ponytail` change.
