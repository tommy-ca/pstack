# Core Feature: Droid PStack Verification

## Sub-features
- Plugin manifest and marketplace catalog projection
- Droid role definitions synchronization
- Four-plane portable verification doctor checks
- Evidence receipt recording and freshness validation

## How to get to it (user POV)
Run the verification driver doctor check from workspace root.
Execute `bash .factory/skills/verify-droid-pstack/scripts/driver.sh doctor`.

## Driving it with Droid
Drive verification across projection, role catalogs, and portable evidence planes.
Execute `bash .factory/skills/verify-droid-pstack/scripts/driver.sh drive`.

## Gotchas
The active host profile must exist at `profiles/droid.json`.
Dependencies must be installed in the virtual environment.
Stale receipts require running static refresh before validation.
