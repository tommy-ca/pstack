## Why

Operators asked whether `HARNESS.md` is required for the plugin or only for development. grok-build `PluginManifest` does not list it. inspect does not name a harness skill. `/poteto-mode` requires reading it as the Grok host map. We need that split in a spec.

## What Changes

- Spec `pstack-harness-md`.
- Setup and `HARNESS.md` say it is the host mapping, not a plugin.json field.
- Tests lock that split.

## Capabilities

### New Capabilities

- `pstack-harness-md`: shipped with the plugin tree; required by `/poteto-mode`; not loaded by grok as a skill.

### Modified Capabilities

None.

## Impact

`HARNESS.md`, `docs/guide/01-setup.md`, `openspec/changes/pstack-harness-md-role/`.
