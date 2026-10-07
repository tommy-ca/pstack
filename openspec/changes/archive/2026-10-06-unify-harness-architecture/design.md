## Context

Root `HARNESS.md` is the current Grok host mapping: the router points Grok Build at it, `verify-harness.py` reads tokens from it, the forge spec requires it to document the forge path, and the sync recipe excludes it from blind copying. Meanwhile the other declared hosts own their mappings at `skills/poteto-mode/references/<host>-tools.md`, `profiles/<host>.json` owns capabilities, and `project-package.py` generates plugin manifests from `pstack.package.json`. The Grok mapping is the only one whose intent is split across a root document and a skill reference.

## Goals / Non-Goals

**Goals:**
- One mapping document per host at `skills/poteto-mode/references/<host>-tools.md`, with Grok consolidated into `grok-tools.md`.
- Source-map independence: mapping documents are canonical skill sources, independent of plugin manifests.
- Explicit dispositions for the reviewed current requirements and active deltas.
- Preserve all applicable scenarios, source citations, archived changes, and historical planning records.

**Non-Goals:**
- No universal runtime framework, workflow DSL, registry, or provenance subsystem.
- No blanket-merged scanner exclusion sets; exemptions are reassessed against migrated content in the migration slice.
- No repair of unrelated OpenSpec changes or archive history.

## Decisions

- **Symmetric reference mapping.** Each host's mapping lives at `skills/poteto-mode/references/<host>-tools.md` (grok, codex, omp, opencode, antigravity). The Grok mapping consolidates into `references/grok-tools.md` next to its peers. Droid, when added as the sixth host, extends the same pattern with `references/droid-tools.md`; that is a separate change.
- **Source-map independence from manifests.** Mapping documents are owned by canonical `skills/` and consumed by routing and verification. `plugin.json`, generated plugin manifests, and plugin discovery MUST NOT depend on them, and manifests MUST NOT list them.
- **Delta currency.** OpenSpec deltas in an active change are proposals; they become current when the change is applied to `openspec/specs/` at this change's archive during the retirement slice. S1 records intent; the migration slice makes `grok-tools.md` operative; the retirement slice removes root `HARNESS.md` and completes the current-state transition. Until then, the root file and old paths remain the recorded current state.

## Dispositions

Reviewed per the approved architecture: live mapping, harness-map, upstream-recipe, and forge requirements, plus the active `pstack-upstream-executable-surfaces` deltas.

- `pstack-harness-md` (current spec) — **delta, modified.** The mapping requirement is retitled to the unified mapping role and carries the retirement scenarios. Full conflict with retirement.
- `pstack-harness-map` (current spec) — **delta, modified.** Only the first requirement names `HARNESS.md` as the call-site authority; it now names `skills/poteto-mode/references/grok-tools.md`. Its scenario is preserved verbatim; the depth and static-check requirements are untouched.
- `pstack-github-pr-fallback` (current spec) — **delta, modified.** The requirement that `HARNESS.md` document the forge path moves to the Grok mapping; all seven scenarios are preserved, with only the reader path adapted.
- `pstack-grok-host` (current spec) — **delta, modified.** The spawn-types requirement names `HARNESS` as a document that MUST set plugin-qualified `subagent_type`; the phrase now names the migrated mapping. Its scenario is preserved verbatim.
- `pstack-sync-from-upstream` (current spec and the active `pstack-upstream-executable-surfaces` delta) — **no delta.** The recipe's `HARNESS.md` exclusion names upstream-tree artifacts, which still exist upstream, so the requirement stays correct after the port retires its own root file. The recipe-line hunk adding `grok-tools.md` to the sync script's docstring is an implementation detail adopted in the migration slice and needs no spec change. The active delta is valid as found and is not modified.
- Unrelated active changes (`formalize-harness-tool-schemas`, `formalize-harness-runtime-and-skill-order`, `2026-09-10-pstack-refresh-hygiene-act-on`) — **not repaired, not exempted.** Their strict-validation failures at recording time are preserved as found; only a genuinely conflicting overlap with this change's deltas would be resolved, and none touches those changes' capabilities.

## Risks / Trade-offs

- Between this change and the retirement slice, the spec current state still names `HARNESS.md` while the intent already records retirement. Accepted and recorded; the deltas state their currency condition instead of silently diverging.
- The migration slice must move content without blanket-merging scanner exclusions and must keep source citations in `docs/guide/13-grok-natives.md`; drift there is caught by the existing gates.

## Migration Plan

1. Record intent (this change): proposal, design, deltas, ADR manifest, durable ADR-0015.
2. Migration slice: absorb remaining Grok guidance into `grok-tools.md`, migrate readers and generated manifest output, adopt the reviewed source-dirty hunks.
3. Retirement slice: remove root `HARNESS.md`, apply this change's deltas to the current specs, and validate the host matrix.

## Open Questions

- None.
