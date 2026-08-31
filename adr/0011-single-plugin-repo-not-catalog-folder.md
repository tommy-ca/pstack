# pstack stays a single-plugin repo, not a catalog folder

- Status: accepted
- Date: 2026-08-31

## Context

This repository is the Grok, Claude, and Codex adapter tree. `plugin.json` lives at the repo root. Claude marketplace `source` is `"./"`. `grok plugin install tommy-ca/pstack --trust` clones this root. Catalog ADR 0001 pins this url. Moving the tree into `grok-build-plugins/pstack` would copy Cursor's sibling farm and would break repo-root install, put tags on catalog HEAD, and mix Claude/Codex indexes into a grok marketplace.

## Decision

pstack MUST remain `tommy-ca/pstack`. It MUST NOT relocate into grok-build-plugins. Tags stay on this repo. Version grammar stays `MAJOR.MINOR.PATCH-grokbuild.N` (ADR 0009, ADR 0010). Existing tags MUST NOT be moved.

## Consequences

Grok-native catalog work stays a second remote. That is cheaper than merging remotes.
