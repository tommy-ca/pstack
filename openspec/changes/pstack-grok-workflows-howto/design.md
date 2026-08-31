## Context

grok-build `PluginManifest` (14 fields) has no workflows. `WorkflowRegistry::scan` in `xai-grok-shell` discovers Rhai from bundled, builtin, project, user. `host_service.rs` maps Rhai `agent_type` to `SubagentRequest.subagent_type`, default `general-purpose`. ADR 0005 forbids playbook clones.

## Goals / Non-Goals

**Goals:** How-to from source. Show `agent_type` `pstack:<role>` in a **target** repo. Keep playbooks markdown.

**Non-Goals:** Adding `.grok/workflows/` to this plugin. Porting 22 playbooks. Changing PluginManifest.

## Decisions

1. **Document, do not ship.** The grok-native join is enable pstack plus a product-repo `.rhai` that sets `agent_type`.
2. **Keep Benny `.rhai` as copies.** Slash skills remain the enable path.
3. **Cite source paths** in the guide so the next grok-build bump can be checked.

## Risks / Trade-offs

- [`agent_type` unknown until enable] -> Guide says enable first.
- [`isolation_worktree` does not merge] -> Guide says so.
- [Built-in names win] -> Do not name a project script `deep-research`.

## Migration Plan

Docs only. No plugin reinstall required for the how-to. Reload after enable to spawn pstack types from a workflow.

## Open Questions

None for this change.
