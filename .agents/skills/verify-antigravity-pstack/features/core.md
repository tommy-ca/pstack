# Core Feature Verification for Antigravity PStack

## Sub-features

- Plugin manifest, `generate_antigravity_rules()`, and model catalog projection
- Antigravity slash commands synchronization (`.antigravity-plugin/commands`)
- Interactive and headless `wire_aliases` (`read_file`/`view_file`, `edit_file`/`replace_file_content`)
- Four-plane portable verification doctor and receipt freshness checks

## How to get to it (user POV)

Run the verification driver doctor check from the workspace root with `bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh doctor`.

## Driving it with Antigravity

Drive end-to-end projection, native staging validation, unit verification, and 4-plane doctor checks with `bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive`.

## Gotchas

- `profiles/antigravity.json` and `skills/setup-pstack/profiles/antigravity.json` must remain byte-identical.
- Stale receipts require running `verify_portable.py refresh-static --host antigravity` before checking freshness.
- Do not point default CI static receipts at live runtime probes (`planes.runtime` must remain `UNTESTED` in committed receipts).
