## Why

homelab TUI sessions pin `~/.grok/config.toml` read-only (EROFS). Operators need a daily driver that can edit the pstack repo and reinstall the plugin, without turning sandbox off all day.

## What Changes

- Setup **Daily driver** section: `workspace` for TUI, `off` only for enable.
- `13-grok-natives.md` sandbox rows.
- Spec `pstack-sandbox-daily`.

## Capabilities

### New Capabilities

- `pstack-sandbox-daily`: TUI uses `workspace` (or homelab for extra paths). Plugin source edits in CWD. Enable from host `grok --sandbox off`. Do not deny secrets.

### Modified Capabilities

None.

## Impact

`docs/guide/01-setup.md`, `docs/guide/13-grok-natives.md`.
