## Context

01-setup already covers install, EROFS enable, inspect trust vs `[plugins].enabled`, HARNESS.md as host map. Production critique and HARNESS still live in other pages. First-session operators never reach them.

## Goals / Non-Goals

**Goals:** One mental-model section on the quickstart page.

**Non-Goals:** Duplicating all of HARNESS. Changing plugin.json.

## Decisions

1. **Put the grok-native model on 01-setup.** Router, spawn, depth, overnight, Benny, prove-it commands.
2. **Keep HARNESS as the full map.** Quickstart links it.
3. **Point overnight and natives pages** instead of repeating adopt/skip tables.

## Risks / Trade-offs

- [01-setup grows] -> One section, then models, then first task.
- [Drift vs HARNESS] -> Tests lock four tokens, not the whole table.

## Migration Plan

Docs only.

## Open Questions

None.
