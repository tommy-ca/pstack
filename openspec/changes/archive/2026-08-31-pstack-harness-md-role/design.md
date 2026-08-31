## Context

PluginManifest has no docs field. inspect lists no harness skill. poteto-mode's first todo is to read HARNESS.md. The installed plugin tree includes the file because it is in the git repo.

## Goals / Non-Goals

**Goals:** Record the split. Keep the file in the plugin tree.

**Non-Goals:** Adding a fake plugin.json key. Removing HARNESS.md from install. Splitting a "dev-only" tree.

## Decisions

1. **Ship it, do not load it.** git install copies the repo. grok does not parse the file.
2. **Keep it operational for `/poteto-mode`.** Agents read it for spawn names, skill order, overlay stems.
3. **Development uses the same file.** verify-harness and TEST-PLAN are extra readers, not the only ones.

## Risks / Trade-offs

- [Agents skip the first todo] -> Tests already require the skill text. Behavior is prompt-enforced.
- [File grows] -> Still cheaper than duplicating call sites in every playbook.

## Migration Plan

Docs only. Reinstall picks up setup copy. No plugin.json change.

## Open Questions

None.
