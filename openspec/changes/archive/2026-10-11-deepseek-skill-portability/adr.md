# ADR Review Manifest

- Status: completed
- Review date: 2026-10-13
- Change: `2026-10-11-deepseek-skill-portability` (spec-only)

## Review Summary

ADR review completed for this change. The change adopts **extend existing pstack owners** (option A): refine current pstack skills/playbooks with testable behavioral invariants rather than importing DSH skills under a parallel namespace or rebuilding a skill runtime. That decision is an *application* of ADRs already in force, not a new architectural commitment — ADR-0005 keeps playbooks as the only orchestration layer, ADR-0006 keeps durable state host-owned (no second registry, router or scheduler), ADR-0012 keeps one portable package descriptor, ADR-0014 rejects per-host forking in favour of one profile-driven owner, ADR-0017 requires one route and one owner with explicit proof levels, and ADR-0018 fixes the three verification tiers, evidence tagging and failure-first reduction.

The spec-only artifacts (`evidence-matrix.md`, `atomic-patterns.md`, `qualification-and-eval.md`, `schemas/skill-pattern-qualification.schema.json`, `specs/pstack-reusable-skill-patterns/spec.md`) document existing boundaries and curatorial ledgers. They instantiate no new runtime class, descriptor, router or receipt plane.

No prior ADR file was edited; accepted ADRs remain immutable.

## In-Force ADRs Reviewed

- `adr/0005-playbooks-are-not-rhai-workflows.md` — playbooks stay markdown and remain the orchestration layer; portable patterns land in existing skills/playbooks, not a new DSL.
- `adr/0006-host-owned-durable-orchestration-state.md` — no second scheduler, database, session manager, registry or router; the change's non-goals match this directly.
- `adr/0007-openspec-archive-chain-gate.md` — `design.md` and `adr.md` are required before archive; this manifest is that gate artifact for this change.
- `adr/0009-semver-grokbuild-not-calver.md`, `adr/0010-adapter-not-sibling-version.md`, `adr/0011-single-plugin-repo-not-catalog-folder.md` — no new package, version identity or catalog folder is introduced.
- `adr/0012-portable-package-descriptor-and-projection.md` — one `pstack.package.json` with deterministic projection; the qualification JSON Schema validates curatorial ledger records only and does not compete with the package descriptor or the four-plane receipt schema.
- `adr/0014-portable-verification-skills-architecture.md` — one profile-driven owner instead of per-host forks; directly analogous to rejecting option B (16 parallel DSH skill imports).
- `adr/0015-symmetric-host-reference-mappings-and-harness-retirement.md` — host-specific invocation stays in adapters/profiles, not in portable skill prose.
- `adr/0017-minimal-routing-proof-lifecycle.md` — one shared route resolver, one owner per route, explicit proof levels; the delta spec's single-route/single-owner and deferred-discovery requirements follow it.
- `adr/0018-verification-skill-scaffold-and-audit.md` — three test tiers, evidence-level tagging, bounded drivers and `FAIL > BLOCKED > UNTESTED > PASS`; the change's gate matrix and honest-evidence requirements reuse them unchanged.

Supersession graph checked across the whole inventory: `ADR-0003` supersedes `ADR-0001` and `ADR-0004` supersedes `ADR-0002` (both prior files frozen; not treated as in force). `ADR-0008` is `Status: Proposed` while claiming to supersede `ADR-0006`, so that claimed supersession is not an accepted override and ADR-0006 stays in force. `ADR-0013` (Antigravity) and `ADR-0016` (Codex models/roles) are host-specific and do not normatively define this portable skill-pattern change; they were inspected but are not decision context. Highest sequence number in use: `0018`.

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced. Option A (extend existing owners) meets every qualifying criterion through ADRs already in force, so no `adr/NNNN-*.md` file was created by this change.

If evaluation later proves an existing owner cannot express a required behavior and a leaf skill or new boundary is genuinely needed, that implementation change MUST record its own new repository-level ADR (superseding a prior one only if it intentionally diverges), never amend an accepted file.

## Verification scope

- Completed: source-pinned desk review of the 16 DSH `SKILL.md` entries, the 20-atom decomposition, the qualification corpus, and the ADR review above.
- Not completed: no native OMP execution, no live-host behavioral eval, no baseline E01–E07 / N01–N07 measurement. This manifest is a planning artifact, not a runtime or conformance receipt; unavailable host status stays BLOCKED/UNTESTED.
