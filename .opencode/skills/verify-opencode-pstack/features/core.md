# Core Feature: OpenCode PStack Verification

## Sub-features
- Extension package manifest projection
- OpenCode plugin configuration synchronization
- Four-plane portable verification doctor checks
- Evidence receipt recording and freshness validation

## How to get to it (user POV)
Run the verification driver doctor check from workspace root.
Execute `bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh doctor`.

## Driving it with OpenCode
Drive verification across projection, doctor checks, and portable evidence planes.
Execute `bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh drive`.

## Gotchas
The active host profile must exist at `profiles/opencode.json`.
Dependencies must be installed in the virtual environment.
Stale receipts require running static refresh before validation.
