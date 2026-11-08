---
name: verify-opencode-pstack
description: "Verify OpenCode host projection, package manifests, and 4-plane doctor verification."
disable-model-invocation: true
---

# Verify OpenCode PStack

This skill verifies PStack integration with the OpenCode agent harness.
It validates projection manifests, extension package descriptors, and 4-plane doctor health.
Read the core feature map before executing verification routines.

## Launch

Verify the runtime environment and required profiles.
Ensure `profiles/opencode.json` is present and valid.
Verify Python virtual environment availability.
Run the launch routine using the verification driver.

```bash
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh launch
```

## Doctor

The doctor command performs non-destructive health checks.
It validates projection manifests for the OpenCode extension package.
It verifies OpenCode plugin definitions remain synchronized.
It executes the portable 4-plane doctor for the OpenCode host.

```bash
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh doctor
```

## Drive

The drive command exercises verification checks.
It confirms projection synchronization for package manifests.
It checks static evidence receipt freshness.
It verifies receipts against the four verification planes.

```bash
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh drive
```

## Proof bar

All checks must pass with exit code zero.
The package manifest at `.opencode-plugin/package.json` must match.
The 4-plane evidence receipt must be fresh and valid.
Unmet assertions yield exit code non-zero and prevent qualification.

## Evidence

Verification outputs are written to the audit evidence directory.
Static receipts are recorded in `.audit/evidence/opencode-*/receipt.json`.
Evidence freshness is confirmed via `verify_portable.py check-staleness`.
Commands are bounded by a 60-second execution timeout.

## Cleanup

The driver runs clean with no persistent background processes.
Temporary test files are removed automatically upon completion.
Run the cleanup routine to verify workspace cleanliness.

```bash
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh cleanup
```

## Helpers

Run driver branches directly for focused verification.

```bash
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh doctor
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh launch
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh drive
bash .opencode/skills/verify-opencode-pstack/scripts/driver.sh cleanup
```
