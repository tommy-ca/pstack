# Upstream executable surfaces and recursive plans

## Why

The live Cursor `pstack` tree moved from the pinned `efa2a531985e0a8084d36ff3cf87233be8a9f34b` tree to `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`. The pstack-specific upstream delta is a `0.14.8` packaging/logo change; the other commits add a separate Cursor-only `advisor` plugin. The port has correctly excluded those host surfaces, but its pin and release lineage are stale.

The retained executable tools are useful Codex compatibility surfaces, yet their ownership is only prose. The plan checker accepts a nonempty dependency sentence without validating a graph, the watcher leaks a missing-`gh` error, and the worktree audit loses evidence on Linux or paths containing spaces.

## What Changes

- Refresh `UPSTREAM` to the live upstream pstack tree and record the exact three-commit delta.
- Bump every tracked adapter manifest to the new upstream base lineage, resetting the grokbuild counter for the upstream base bump.
- Record explicit exclusions for Cursor `.cursor-plugin/`, the logo asset, and the separate `advisor` plugin. Do not copy them into the Grok port.
- Add a durable Codex executable-surface contract covering `orch`/`store`, `watch-pr`, `check-plan.mjs`, and `worktree-audit.sh`; keep these outside Grok durable orchestration.
- Extend the local plan checker with explicit task identifiers, dependency resolution, unknown-reference detection, duplicate detection, cycle detection, and recursive dependency traversal.
- Make `worktree-audit.sh` preserve worktree paths, report an unavailable base ref as unknown, support an explicit transcript root, and work with GNU or BSD `stat`.
- Convert a missing `gh` executable into the watcher’s typed retryable query error instead of an uncaught process error.
- Add focused behavioral and contract tests plus documentation for the host boundary and recursive plan format.

## Capabilities

### New Capabilities

- `pstack-codex-executable-surfaces`: Defines the retained executable tools, their Codex-only ownership, and their smoke/error contracts.
- `pstack-recursive-plan-validation`: Defines machine-readable plan node IDs and recursively validated dependency graphs.

### Modified Capabilities

- `pstack-sync-from-upstream`: Updates the upstream pin and requires explicit classification of upstream packaging, advisor, and executable surfaces during refresh.

## Impact

Affected paths are `UPSTREAM`, the six tracked plugin/catalog manifests, the sync recipe, `skills/poteto-mode/scripts/check-plan.mjs`, `skills/poteto-mode/scripts/worktree-audit.sh`, `skills/poteto-mode/scripts/watch-pr/{github.ts,types.ts}`, the Codex host map and multi-phase-plan playbook, focused tests, and OpenSpec durable specs. No Grok runtime state store, scheduler, Cursor packaging, advisor plugin, or new dependency is introduced.
