## Why

Strict archived validation currently reports two unchecked marketplace tasks in the release archives even though those tasks require a separate `grok-build-plugins` checkout, a marketplace-specific test, and host-side plugin update commands. The archive records need a truthful outcome trail that distinguishes local evidence from external follow-up instead of leaving stale checkboxes or pretending those external actions ran.

## What Changes

- Audit the two unchecked release-task entries and preserve their exact external scope as deferred follow-up work.
- Amend the archived task records with explicit, truthful outcome annotations so checked boxes mean the task outcome was reviewed, not that an unavailable external command was fabricated as run.
- Keep the actual sibling marketplace checkout and installed-plugin update out of this pstack change; no sibling-repository edit, commit, push, or host plugin mutation is authorized here.
- Update the archive-chain specification to require an explicit reason and follow-up for deferred external task outcomes.
- Verify `openspec validate --archived --strict` passes while retaining the external evidence gap in the archive text.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `archive-chain-integrity`: allow transparent, reasoned outcome annotations for external tasks while preserving fail-closed artifact-chain checks.

## Impact

Two files under `openspec/changes/archive/`, the archive-chain delta spec, and this change's planning artifacts. The sibling `/home/tommyk/projects/grok-build-plugins` checkout, installed Grok state, and remote services remain unchanged.
