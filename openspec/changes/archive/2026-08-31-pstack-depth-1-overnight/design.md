## Context

how-critics on 1.0.13: autopilot owner-children plus `/no-comments` is depth 2. `/goal` is a competing driver skipped in `pstack-grok-natives`. Orchestrate already parent-fanouts.

## Goals / Non-Goals

**Goals:** Autopilot playbooks match depth 1. Drop `/goal`. Overnight guide states the rule.

**Non-Goals:** Rewriting orchestrate. Changing `no-comments` SKILL.md this change. bun helpers.

## Decisions

1. **Parent spawns comment-sicko.** Writers apply unslop in-process. They do not call `/no-comments`.
2. **Persist the program in todos and `/loop`.** Do not arm `/goal`.
3. **Keep owner-per-PR writers.** They write code. They do not spawn.

## Risks / Trade-offs

- [Writers forget unslop] -> Playbook still names `/unslop` in the writer. Parent comment-sicko is the second pass.
- [Operators still type /goal] -> Guide skip stands.

## Migration Plan

Playbook text only. No plugin.json change.

## Open Questions

Whether `no-comments` should no-op spawn when already a child. Out of this change.
