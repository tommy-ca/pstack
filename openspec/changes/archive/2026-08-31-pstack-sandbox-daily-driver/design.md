## Context

`18-sandbox.md`: `workspace` writes CWD + `~/.grok/` + tmp. homelab is custom, extends workspace. Linux TUI bind-mounts `config.toml`, `sandbox.toml`, `hooks/` RO. This agent session was not inside `__GROK_INSIDE_BWRAP`, so probes wrote `~/.grok`. The EROFS shows when the TUI is in bwrap.

## Goals / Non-Goals

**Goals:** Daily driver = workspace TUI + host enable. Plugin edits in CWD.

**Non-Goals:** Forking grok-build to un-pin config.toml. Setting the operator's `[sandbox] profile` from this plugin.

## Decisions

1. **Do not recommend all-day `--sandbox off`.** Enable is the one off command.
2. **Do not replace homelab.** It is extra write grants. Same EROFS.
3. **Plugin tweaks live in the git repo.** Reinstall copies to `installed-plugins/` (writable under workspace).

## Risks / Trade-offs

- [Operators still hit EROFS on enable] -> Host-shell remains the fix. grok-build owns the pin.
- [homelab extra paths lost on workspace] -> Keep homelab if you need npm/cache writes.

## Migration Plan

Docs only. Operator may set `[sandbox] profile = "workspace"` once from a host shell.

## Open Questions

Whether grok-build will stop pinning `config.toml`. Out of this plugin.
