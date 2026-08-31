## Context

How: `grok plugin tag` names the tag `v` plus `plugin.json` version. pstack is one plugin, one repo, one tag namespace. Cursor overlay base is `0.14.5`. The grokbuild token is adapter lineage (ADR 0009). Catalog siblings share one tag namespace, so they put the plugin name in the prerelease (grok-build-plugins ADR 0003). Unifying those grammars is wrong in both directions.

Investigation: no ADR yet says "must not copy the other repo." Specs lock each grammar in isolation. `536fcd6` already treated sibling collision as a catalog non-goal.

## Goals / Non-Goals

**Goals:** Spec and tests name why pstack must not use catalog name-in-version.

**Non-Goals:** Version bump. Retag. Renaming to `-pstack.N`. CalVer. Tagging from the catalog.

## Decisions

Keep `MAJOR.MINOR.PATCH-grokbuild.N`. Forbid `-pstack.N` and other catalog-style plugin-name prereleases. Cursor MAJOR.MINOR.PATCH stays the foreign key.

## Risks / Trade-offs

Two grammars look inconsistent until you know the identity key. That split is the product. Document it in one sentence on the natives Keep row.

## Migration Plan

Land spec and tests. Do not retag `v0.14.5-grokbuild.4`.

## Open Questions

None.
