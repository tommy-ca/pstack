## Context

Retrospective artifact for the archived `pstack-grok-host-contract` change. The original proposal captured Grok 1.0.13 host-contract failures around locale, plugin enablement, qualified agent names, and TEST-PLAN inspection. The implementation and task checklist are archived, but the design handoff was omitted.

## Goals / Non-Goals

**Goals:**

- Keep user-facing English and Chinese README content separate with a reciprocal switcher.
- Use plugin-qualified role names (`pstack:<role-key>`) consistently in skills, HARNESS, and setup overlays.
- Document host-shell enablement, including the EROFS case.
- Count actual `.agents[]` entries in TEST-PLAN rather than the manifest's directory summary.

**Non-Goals:**

- No new provider abstraction or runtime orchestration.
- No change to the archived catalog follow-up beyond recording its existing task.

## Decisions

1. Treat the Grok plugin namespace as part of the spawn contract; unqualified local names are not valid replacements.
2. Keep enablement as an operator action in the host shell, because trust and `[plugins].enabled` are distinct host states.
3. Treat manifest `provides.agents` as a coarse directory count; inspect agent metadata when validating names.
4. Keep locale files independent so scanners and users receive one language per README surface.

## Verification

The archived tasks record locale splitting, qualified spawn checks, setup overlay checks, explicit enablement/EROFS documentation, and `.agents[]` inspection. This design records those decisions retrospectively.
