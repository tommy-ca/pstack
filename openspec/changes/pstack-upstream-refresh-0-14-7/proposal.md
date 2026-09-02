## Why

Official Cursor pstack moved from the pinned `6fecddba` tree to `efa2a531`, adding forge-neutral landing rules, skill invocation metadata, schema-first TypeScript guidance, and a Fable 5.1 upstream default. This port must absorb the upstream behavior without overwriting its Grok, Codex, Claude, Benny, release, and OpenSpec adaptations.

## What Changes

- Refresh the shared pstack skills, playbooks, guides, and tests to the upstream `efa2a531` behavior where that behavior is valid on the retained hosts.
- Replace stale Graphite-first landing text with the upstream forge-neutral `gh`/Origin contract while retaining Grok `monitor`, `scheduler_create`, parent-fanout, and host-specific safety rules.
- Add supported `disable-model-invocation` metadata to the four retained upstream skills and import the TypeScript schema-first boundary guidance.
- Update `UPSTREAM`, `TEST-PLAN.md`, the local manifests, and the Claude marketplace entry to the `0.14.7` upstream base with adapter version `0.14.7-grokbuild.0`.
- Keep Cursor-only `.cursor-plugin`, `assets/logo.png`, and `make-bot-ui` out of the Grok port; record those exclusions in the recipe and verification contract.
- Do not run release tagging, push remote branches, or modify historical OpenSpec archives in this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-sync-from-upstream`: track and verify the current upstream tree while keeping copying and host adaptation explicit.
- `pstack-github-pr-fallback`: make the retained PR and stack instructions forge-neutral instead of Graphite-first.

## Impact

`skills/`, `docs/guide/`, `README.md`, `README.zh-CN.md`, `HARNESS.md`, `UPSTREAM`, `TEST-PLAN.md`, the four retained host manifests, `.claude-plugin/marketplace.json`, `tests/test_verify_harness.py`, and `openspec/specs/` after archive. No new dependency or runtime service is required.
