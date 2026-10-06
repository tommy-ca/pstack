# ADR Review Manifest

- Status: completed
- Review date: 2026-10-06

## Review Summary

The unification change records one durable architecture decision: the Grok host mapping consolidates into the symmetric per-host reference surface and root `HARNESS.md` retires after its current readers migrate. No existing durable ADR is superseded.

Issue #165 originally labeled this decision `ADR-0007 Symmetrical Host Reference Mappings and HARNESS.md Retirement`. `ADR-0007` is occupied by `adr/0007-openspec-archive-chain-gate.md`, so the decision is recorded at the next free identifier, verified against the occupied `adr/` population on 2026-10-06 (ADR-0001 through ADR-0014).

## In-Force ADRs Reviewed

- `adr/0008-host-adapter-boundary-scope.md` - host adapters stay thin; mapping intent stays host-specific rather than universalized.
- `adr/0012-portable-package-descriptor-and-projection.md` - manifests are generated artifacts; the mapping document is a source the manifests must not own or list.
- `adr/0014-portable-verification-skills-architecture.md` - precedent for symmetric per-host surfaces instead of a root-level Grok-specific document.

## New Durable ADRs Created

- `adr/0015-symmetric-host-reference-mappings-and-harness-retirement.md` - Grok's mapping consolidates into `skills/poteto-mode/references/grok-tools.md`, mapping documents stay source-owned and manifest-independent, and root `HARNESS.md` retires after reader migration.
