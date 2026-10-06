# ADR 0015: Symmetrical Host Reference Mappings and HARNESS.md Retirement

## Context

The port declares five hosts (grok, codex, omp, opencode, antigravity), and each host's mapping is meant to live at `skills/poteto-mode/references/<host>-tools.md`. Grok's mapping is still split: root `HARNESS.md` carries most of the Grok contract while `references/grok-tools.md` carries the router-facing tokens. Root `HARNESS.md` is a host-specific document at the plugin repo root, its readers are scattered across verification scripts, guides, specs, and the sync recipe, and the mapping requirement is tied to a file name instead of the mapping role. Issue #165 originally labeled this decision ADR-0007; that identifier is occupied by `adr/0007-openspec-archive-chain-gate.md`, so the next free identifier is used (verified 2026-10-06: ADR-0001 through ADR-0014 were occupied).

The candidates evaluated:

- **Keep root `HARNESS.md` as the universal mapping:** rejected. It is Grok-specific, it sits at the plugin root beside generated manifests, and it forces every other host's mapping into a different, asymmetric location.
- **Duplicate mapping content per host:** rejected. Copying the Grok contract into per-host forks multiplies maintenance and drifts.
- **Consolidate Grok's mapping into `skills/poteto-mode/references/grok-tools.md` beside its peers:** selected. It matches the existing symmetric surface, keeps adapters thin, and lets root `HARNESS.md` retire once its readers migrate.

## Decision

1. `skills/poteto-mode/references/grok-tools.md` is the single Grok host mapping. The router names it, and `verify-harness.py` and TEST-PLAN read it at that path.
2. Mapping documents are source-owned skill references, independent of plugin manifests: `plugin.json` and generated plugin manifests MUST NOT list them, and plugin discovery MUST NOT depend on them.
3. Root `HARNESS.md` retires only after its current readers migrate. Archived OpenSpec changes and historical planning records keep former file names as history.
4. Current requirements that name `HARNESS.md` are dispositioned through the `unify-harness-architecture` OpenSpec change: `pstack-harness-md`, `pstack-harness-map`, `pstack-github-pr-fallback`, and `pstack-grok-host` receive modified deltas; `pstack-sync-from-upstream` needs none because its recipe exclusion names upstream-tree artifacts. Those deltas become current when the change is applied to `openspec/specs/` at the retirement slice, not before.
5. Droid, when added as the sixth host, extends the same pattern with `references/droid-tools.md` under its own change.

## Status

Accepted, 2026-10-06. Complements `ADR-0008` (host adapter boundary) and `ADR-0012` (generated manifests); supersedes nothing.
