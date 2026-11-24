---
name: verify-antigravity-pstack
description: "Verify Antigravity CLI 1.5.16 projection, native plugin validation, gated swarm and workflow routing, model definitions, and 4-plane doctor checks."
disable-model-invocation: true
---

# Verify Antigravity PStack

This skill verifies PStack integration with Google Antigravity CLI (`agy` 1.5.16).
It validates manifest projection, native `agy plugin validate --strict --json` packaging, gated `/swarm` and `run_workflow` bindings, model catalogs, and 4-plane doctor health.

## Launch

Verify the runtime environment, active host profile, projected model catalog, and optional `agy` CLI availability.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh launch
```

## Doctor

The doctor command runs non-destructive static and packaging health checks across `.antigravity-plugin/`, command projections, unit test suites, native package staging, and the 4-plane doctor.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh doctor
```

## Drive

The drive command executes projection checks, the native `agy plugin validate --strict --json` package proof, receipt staleness checks, and 4-plane evidence checks.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive
```

## Proof bar

All checks must exit zero.
The plugin manifest at `.antigravity-plugin/plugin.json` and commands at `.antigravity-plugin/commands` must stay synced.
The model catalog at `.antigravity-plugin/models.json` must keep `singleRoleDefault` at `pro`, expose 22 canonical roles, exclude `gpt-oss-*`, and record `2026-11-30` deprecations.
`prove_antigravity_native_package.py --json` must report `verdict` as `PASS`, `findings` empty, at least 65 skills, 22 agents, and 1 rule file.

## Evidence

Verification outputs write to `.audit/evidence/` via temporary staged directories.
Static receipts live in `.audit/evidence/antigravity-receipt.json` with `planes.runtime` kept `UNTESTED` unless an isolated live runtime proof runs explicitly.
Freshness is verified through `verify_portable.py check-staleness --host antigravity`.
Every command runs bounded by a 60-second execution timeout.

## Cleanup

Staged native plugin proof directories clean up automatically on exit.
No persistent background processes or stray worktrees remain after running the driver.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh cleanup
```

## Helpers

Run individual phases directly for targeted diagnostics.

```bash
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh launch
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh doctor
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh drive
bash .agents/skills/verify-antigravity-pstack/scripts/driver.sh cleanup
```
