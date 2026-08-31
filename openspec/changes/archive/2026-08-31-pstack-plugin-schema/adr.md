# ADR: Ship only fields the Grok host parses

- **Status:** Accepted (retrospective archive repair)
- **Date:** 2026-08-31

## Decision

Keep the pstack plugin manifest and agent YAML limited to fields supported by Grok 1.0.13. Remove ignored `displayName`, unsupported `permissionMode: plan`, and non-spawn `background:`; preserve supported execution and skill-inheritance fields. Model setup overlays with `pstack:<role-key>` stems and do not add unused command, hook, MCP, or LSP surfaces.

## Rationale

Unsupported declarations create false contracts: they look configured while the host ignores or rejects them. The archived audit established the parsed-field boundary, so the port should encode that boundary directly and test it.

## Consequences

- Manifest tests fail when unsupported fields return.
- Documentation matches the actual plugin surface rather than a generic template.
- A future Grok upgrade requires a deliberate schema review.

## Evidence

This retrospective decision is grounded in the archived proposal, specs, implementation, and completed task checklist. It makes no additional claim about an external host version.
