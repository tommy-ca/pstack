## Context

Official README (pin `6fecddba`): pstack is how poteto ships high quality code. Opposite of loc-max. Fearless parallelism after each agent is rigorous. `/poteto-mode` is the shortcut. 21 principles in `08-principles.md`. This Grok port already remaps call sites in `HARNESS.md`.

## Goals / Non-Goals

**Goals:** One porting page. Three layers. Recipe. Tests.

**Non-Goals:** Rewriting playbooks. A new plugin. Porting Benny as core.

## Decisions

1. **Core is philosophy + 21 + 22 intents + router.** Domain packs stay optional.
2. **Host map is the port.** Fill the capability checklist from the new agent's docs or source. Grok's filled table is `HARNESS.md`.
3. **Write `gap` instead of inventing ignored fields.** Nested spawn depth 1 means the parent fans out.
4. **Do not treat automations or host workflows as core.**

## Risks / Trade-offs

- [Ports copy files and keep Cursor ids] -> Scanner requirement in the recipe.
- [21 names feel coding-specific] -> They are still the core. A non-coding domain keeps them and drops visual-parity / Graphite.

## Migration Plan

Docs only.

## Open Questions

None.
