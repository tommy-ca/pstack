---
name: verify-antigravity-pstack
description: "Verify Antigravity host projection, slash commands, model definitions, and 4-plane doctor verification."
disable-model-invocation: true
---

# Verify Antigravity PStack

This skill verifies PStack integration with the Antigravity agent harness.
It validates projection manifests, model mappings, and 4-plane doctor health.
Read the core feature map before executing verification routines.

## Launch

Verify the runtime environment and required profiles.
Ensure `profiles/antigravity.json` is present and valid.
Verify Python virtual environment availability.
Run the launch routine using the verification driver.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh launch
```

## Doctor

The doctor command performs non-destructive health checks.
It validates projection manifests for Antigravity plugin and commands.
It verifies Antigravity test suites pass cleanly.
It executes the portable 4-plane doctor for the Antigravity host.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh doctor
```

## Drive

The drive command exercises verification checks.
It confirms projection synchronization across manifests and models.
It checks static evidence receipt freshness.
It verifies receipts against the four verification planes.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive
```

## Proof bar

All checks must pass with exit code zero.
The plugin manifest at `.antigravity-plugin/plugin.json` must match.
The model catalog at `.antigravity-plugin/models.json` must match.
All 21 commands at `.antigravity-plugin/commands` must match.
The 4-plane evidence receipt must be fresh and valid.
Unmet assertions yield exit code non-zero and prevent qualification.

## Evidence

Verification outputs are written to the audit evidence directory.
Static receipts are recorded in `.audit/evidence/antigravity-*/receipt.json`.
Evidence freshness is confirmed via `verify_portable.py check-staleness`.
Commands are bounded by a 60-second execution timeout.

## Cleanup

The driver runs clean with no persistent background processes.
Temporary test files are removed automatically upon completion.
Run the cleanup routine to verify workspace cleanliness.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh cleanup
```

## Helpers

Run driver branches directly for focused verification.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh doctor
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh launch
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh cleanup
```
