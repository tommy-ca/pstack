# ADR: Make Grok host qualification explicit

- **Status:** Accepted (retrospective archive repair)
- **Date:** 2026-08-31

## Decision

Use the Grok plugin namespace in every pstack role spawn (`pstack:<role-key>`), write overlays with the same qualified stem, and document enablement as a host-shell operation. Keep README locales separate and validate actual agent metadata rather than the manifest's aggregate directory count.

## Rationale

Grok 1.0.13 distinguishes trusted plugins from enabled plugins and registers plugin agents under a qualified name. The archived proposal reports that relying on trust or an unqualified name caused live spawn failures. Separating README locales also removes scanner and reader ambiguity.

## Consequences

- Operators must enable pstack before spawning its agents.
- Setup output and invocation examples share one stable namespace.
- TEST-PLAN catches drift in actual agent declarations.

## Evidence

This retrospective decision is derived from the archived proposal, specs, implementation, and completed tasks. It does not assert a new live validation run.
