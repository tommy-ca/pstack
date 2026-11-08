---
name: verify-omp-pstack
description: "Verify OMP host projection, native package enrollment, and 4-plane doctor verification."
disable-model-invocation: true
---

# Verify OMP PStack

This skill verifies PStack integration with the OMP agent harness.
It validates projection manifests, native package enrollment, and 4-plane doctor health.
Read the core feature map before executing verification routines.

## Launch

Verify the runtime environment and required profiles.
Ensure `profiles/omp.json` is present and valid.
Verify Python virtual environment availability.
Run the launch routine using the verification driver.

```bash
bash .omp/skills/verify-omp-pstack/scripts/driver.sh launch
```

## Doctor

The doctor command performs non-destructive health checks.
It validates projection manifests for the OMP package.
It verifies OMP native package proof passes cleanly.
It executes the portable 4-plane doctor for the OMP host.

```bash
bash .omp/skills/verify-omp-pstack/scripts/driver.sh doctor
```

## Drive

The drive command exercises verification checks.
It confirms projection synchronization for package descriptors.
It checks static evidence receipt freshness.
It verifies receipts against the four verification planes.

```bash
bash .omp/skills/verify-omp-pstack/scripts/driver.sh drive
```

## Proof bar

All checks must pass with exit code zero.
The package manifest at `.omp-plugin/package.json` must match.
Native package enrollment must contribute expected skills.
The 4-plane evidence receipt must be fresh and valid.
Unmet assertions yield exit code non-zero and prevent qualification.

## Evidence

Verification outputs are written to the audit evidence directory.
Static receipts are recorded in `.audit/evidence/omp-*/receipt.json`.
Evidence freshness is confirmed via `verify_portable.py check-staleness`.
Commands are bounded by a 60-second execution timeout.

## Cleanup

The driver runs clean with no persistent background processes.
Temporary test files are removed automatically upon completion.
Run the cleanup routine to verify workspace cleanliness.

```bash
bash .omp/skills/verify-omp-pstack/scripts/driver.sh cleanup
```

## Helpers

Run driver branches directly for focused verification.

```bash
bash .omp/skills/verify-omp-pstack/scripts/driver.sh doctor
bash .omp/skills/verify-omp-pstack/scripts/driver.sh launch
bash .omp/skills/verify-omp-pstack/scripts/driver.sh drive
bash .omp/skills/verify-omp-pstack/scripts/driver.sh cleanup
```
