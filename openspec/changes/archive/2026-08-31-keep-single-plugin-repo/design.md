## Context

pstack is one plugin, one repo. Claude marketplace `source` is `"./"`. Codex is the same. Catalog ADR 0001 already kept this repo as the Grok pin.

Nesting under grok-build-plugins would match Cursor sibling topology and would break repo-root install, catalog tests, and host adapters.

## Goals / Non-Goals

**Goals:** Spec names the repo as the plugin unit.

**Non-Goals:** File move. Version bump. Retag. Changing grokbuild grammar.

## Decisions

Add ADR 0011. Keep tagging here. Catalog remains a pin.

## Risks / Trade-offs

Two remotes to clone for grok-native work. Operator workspace can hold both. Do not merge remotes to save a `cd`.

## Migration Plan

Land spec and ADR. Do not relocate.

## Open Questions

None.
