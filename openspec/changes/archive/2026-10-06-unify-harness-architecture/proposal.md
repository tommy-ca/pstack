# Unify harness mapping architecture and retire root HARNESS.md

## Why

The port now declares five hosts (grok, codex, omp, opencode, antigravity), and the symmetric per-host mapping surface already exists at `skills/poteto-mode/references/<host>-tools.md`. The Grok mapping, however, is still split: root `HARNESS.md` carries most of it while `references/grok-tools.md` carries the router-facing contract. Root `HARNESS.md` is a host-specific document at the plugin root, current readers are scattered across verification scripts, guides, specs, and the sync recipe, and the mapping requirement is entangled with a file name instead of the mapping role. This change records the intent-driven unification for issue #165, part of epic #162.

## What Changes

- Make `skills/poteto-mode/references/grok-tools.md` the single Grok host mapping and retire root `HARNESS.md` once its current readers have migrated.
- Keep mapping documents source-owned: they are skill references read by routing and verification, never plugin-manifest fields, and generated plugin manifests MUST NOT list them.
- Move the forge-path documentation requirement (`gh` as default forge path) from the retired root file to the Grok mapping.
- Refresh the plugin-qualified spawn-type wording so the discipline is carried by shipped skills and the migrated mapping.
- Leave the upstream sync-recipe exclusion list unchanged: it names upstream-tree artifacts, which still exist upstream.
- Explicitly disposition the reviewed current requirements and active deltas (see `design.md`); archived OpenSpec changes and historical planning records keep former file names untouched.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `pstack-harness-md`: `references/grok-tools.md` is the unified Grok host mapping; root `HARNESS.md` retires after reader migration.
- `pstack-harness-map`: Grok call sites follow the migrated mapping path.
- `pstack-github-pr-fallback`: the Grok mapping documents the forge path instead of the retired root file.
- `pstack-grok-host`: the spawn-type discipline wording follows the migrated mapping path.

## Impact

Affects the `grok-tools.md` content migration, the root `HARNESS.md` retirement, and current readers of the mapping (router skill, verification scripts, absorbed checks, tests, generated manifest description, README and translated instructions, and the four specs above). The pstack-sync-from-upstream recipe requirement is dispositioned with no delta. Unrelated active changes (`formalize-harness-tool-schemas`, `formalize-harness-runtime-and-skill-order`, `2026-09-10-pstack-refresh-hygiene-act-on`) are outside this mission's scope and are preserved as found, including their current strict-validation failures. The next free ADR identifier at recording time is ADR-0015; issue #165's original ADR-0007 label is occupied by `adr/0007-openspec-archive-chain-gate.md` and is not overwritten.
