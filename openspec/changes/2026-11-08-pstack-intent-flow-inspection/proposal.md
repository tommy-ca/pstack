# Proposal: Complete PStack's intent-driven OpenSpec inspection and verification flow

## Why

PStack has already adopted the intent-driven OpenSpec schema and merged CLI-backed status and mise entrypoints in completed epic #1164. This follow-on adds an OpenSpec-binary-independent inventory across all active proposal → specs → design → adr → tasks chains and a separately named strict aggregate validation gate, while preserving the merged CLI interfaces. Users may confuse file presence with OpenSpec validity, or rerun a single-change legacy validator against a repo containing many concurrent changes.

## What Changes

- Add a typed and testable source-only artifact inspector in the **existing** `scripts/openspec_change.py`, with `--artifacts --json [--change NAME]`, without requiring OpenSpec binary or extending the public harness runtime.
- Add separate `verify-all` mode that requires complete change artifacts and invokes real `openspec schema validate intent-driven` plus `openspec validate ... --type change --strict`; missing CLI is a BLOCKED result, never a static PASS.
- Add **additional** `mise run openspec:artifacts` and `mise run verify:openspec:all`, with tests included in the existing offline CI selection.
- Merge host-neutral context and artifact-stage rules into existing `openspec/config.yaml` without replacing PStack's stronger schema, immutable ADRs or vendor-specific settings.
- Audit active and archived chains, document lifecycle/limitations in the current verification tiers and reconcile GitHub epic #1164 / leaves #1165–#1168.
- Preserve the existing `skip_specs: true` docs-only exception from accepted ADR-0020 without relaxing other artifact gates.

## Capabilities

- **Modified capability:** `pstack-intent-hygiene` (add independently testable visibility and validation requirements; do not alter its existing pre-archive requirement).
- **New capabilities:** None; this is a narrow extension of existing PStack OpenSpec support.

## Impact

`scripts/openspec_change.py`, two existing test modules, `mise.toml`, the offline workflow, `openspec/config.yaml`, `docs/verification-test-tiers.md`, and the new change-local artifacts.

No `opencode.json`, `.opencode/`, `AGENTS.md`, Node build, copied template agents, separate issue tracker, changed native host adapters, or additional external dependencies. Template source pinned for review to [intent-driven-template@b5bda460](https://github.com/intent-driven-dev/intent-driven-template/tree/b5bda460a2180a55fc508fdedc4ef058d95355db).

## Evidence limits

Repository file checks are **filesystem-only**. The OpenSpec CLI and real model-backed Swarm/Arena/Interrogate/Thermos reviews are separate gates. An artifact-complete planning chain is not implemented behavior, archived correctness, or approved ADR provenance.
