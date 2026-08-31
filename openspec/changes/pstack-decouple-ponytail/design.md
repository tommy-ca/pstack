## Context

Archived change `pstack-essential-ponytail` taught `/ponytail` on the pstack quickstart because operators had it installed. That recoupled two plugins. Inspect still shows two plugin ids: `pstack` and `ponytail`. `plugin.json` never listed ponytail. Catalog v1 is pstack only.

In-force ADRs 0001-0005 (and later host-boundary ADRs if present) do not make ponytail a pstack pack. Benny is in-plugin. Ponytail is not.

## Goals / Non-Goals

**Goals:** Delete ponytail from live pstack operator docs, HARNESS Skill order, the main `pstack-quickstart` spec, and the test that required the coupling.

**Non-Goals:** Uninstalling ponytail. Catalog listing. Editing the archive. Adding a YAGNI row that names Laziness Protocol as a slash. Documenting other user plugins by name.

## Decisions

1. **Subtract the named row, do not retarget it.** Kind Lazy and the HARNESS YAGNI row go away. Skill order already says user column exists. Naming one foreign plugin is the bug.
2. **Invert the test.** Replace `test_essential_entries_include_user_ponytail` with a recouple lock: live setup, HARNESS, and `openspec/specs/pstack-quickstart/spec.md` contain no `/ponytail`. Keep `plugin.json` free of ponytail. Do not scan `openspec/changes/archive/`.
3. **Leave the archive frozen.** `openspec/changes/archive/2026-08-31-pstack-essential-ponytail/` stays as history.

Alternatives considered: keep a "foreign plugin" Kind with no names (rejected, empty Kind teaches nothing). Move ponytail into the catalog (rejected, v1 is pstack only and the operator said pstack has nothing to do with it).

## Risks / Trade-offs

- [Operators who learned `/ponytail` from 01-setup lose that map] -> Ponytail's own `/ponytail-help` owns that map.
- [Archive still names ponytail] -> Tests do not scan archive.

## Migration Plan

Docs and tests only. Reinstall is not required. Ponytail stays enabled as its own plugin.

## Open Questions

None.
