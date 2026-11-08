# Core Feature: OMP PStack Verification

## Sub-features
- Package manifest projection
- OMP native package enrollment
- Four-plane portable verification doctor checks
- Evidence receipt recording and freshness validation

## How to get to it (user POV)
Run the verification driver doctor check from workspace root.
Execute `bash .omp/skills/verify-omp-pstack/scripts/driver.sh doctor`.

## Driving it with OMP
Drive verification across projection, native package proofs, and portable evidence planes.
Execute `bash .omp/skills/verify-omp-pstack/scripts/driver.sh drive`.

## Gotchas
The active host profile must exist at `profiles/omp.json`.
Dependencies must be installed in the virtual environment.
Stale receipts require running static refresh before validation.
