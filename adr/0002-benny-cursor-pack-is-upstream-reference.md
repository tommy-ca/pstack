# Cursor Benny pack is upstream reference

- Status: accepted
- Date: 2026-08-30

## Context

The Cursor pack under `automations/benny/skills/` encodes marker names and two-pipeline intent. Grok has no Cursor automation trigger injection. A live run that "follows SKILL.md" still waits for fields grok never supplies.

## Decision

Treat `automations/benny/skills/` as the upstream reference. The live grok contract is `automations/benny/grok/triage.md` and `repro.md`, driven by workflows with `args.thread_url`, `spawn_subagent` `pstack:<role>`, `/loop` → `scheduler_create`, and opt-in copied hooks.

## Consequences

Marker strings stay shared. Grok-facing files must not use Cursor trigger fields as the live path. Plugin slash skills and plugin-global hooks stay off (ADR 0001).
