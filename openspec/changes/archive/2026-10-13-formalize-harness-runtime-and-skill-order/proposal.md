# Change Proposal: Formalize Harness Runtime Conventions and Skill Order

## Why

Grok Build `HARNESS.md` currently holds a monolithic manual specification of Grok Build primitives, 3-tier skill fallback orders, subagent runtime conventions, wire aliases, and forbidden fields. Other harnesses specify their conventions in disconnected Markdown files. Extracting and formalizing these conventions into typed schemas guarantees complete harness parity, prevents runtime dispatch errors, and isolates upstream pstack from host variance.

## What Changes

1. **Skill Order Schema**: Define `schemas/portability/skill-order.schema.json` formalizing the 3-tier skill fallback hierarchy (pstack primary, user secondary, host builtin fallback).
2. **Runtime Conventions Schema**: Define `schemas/portability/runtime-conventions.schema.json` formalizing subagent recursion limits, workspace isolation modes, model-facing spawn fields, forbidden fields, and wire aliases.
3. **Profile Schema Extension**: Update `schemas/portability/profile.schema.json` to link `skill_order` and `runtime_conventions`.
4. **Structured Profile Extraction**: Extract `HARNESS.md` into `profiles/grok.json` and canonical `skills/poteto-mode/references/grok-tools.md`. Populate runtime conventions and skill orders across all five harness profiles.
5. **Portability Levers**: Upgrade `scripts/portability_schema.py` and `scripts/verify-portable.py` to enforce runtime conventions and skill order validation.

## Impact

- Upstream pstack skills remain completely clean.
- All five agent harnesses possess machine-validated skill order tables and execution constraints.
- Host-specific subagent rules (such as max depth 1, worktree isolation, forbidden fields) are validated ahead of dispatch.
