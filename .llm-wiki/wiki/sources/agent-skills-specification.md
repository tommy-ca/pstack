# Agent Skills Specification and Audit Source Reference

## Provenance and Ingestion Record

- Raw Source: `raw/sources/agent-skills-conformance-audit-2026-11-15.md`.
- Ingestion Tool: `scripts/llm_wiki.py ingest`.
- Digest: `e5612e1422591acd90dd2e0a6fa97ef025ced6aa5585768572b6284708edc6df`.
- Scope: 84 SKILL.md files across canonical, host-local, and automation roots.
- Canonical Upstream: `cursor/plugins@main/pstack`.
- Official Standard: https://agentskills.io/specification.

## Classification

- Raw sources are immutable and write-once under `raw/sources/`.
- Curated semantic articles live under `wiki/concepts/` and `wiki/sources/`.
- Navigation indexes are generated projections produced by `scripts/llm_wiki.py index --write`.

## Atomic Building Blocks

The atomic blocks are curated in [Agent Skills Conformance](../concepts/agent-skills-conformance.md).
Ten core atoms define the specification:
1. `metadata`: standard frontmatter schema and constraints.
2. `activation`: description-based discovery and triggering conditions.
3. `instruction`: procedural steps and invariants in SKILL.md body.
4. `resource`: references, assets, and relative file targets.
5. `adapter`: thin host-specific bindings without workflow forks.
6. `checker`: offline validation of frontmatter, links, and layout.
7. `evidence`: exit code receipts, digests, and multi-harness status.
8. `property`: formal invariant, safety, and liveness declarations.
9. `mutation`: deliberate negative controls and failing mutants.
10. `projection`: harness packaging and profile manifests.

## Verification Boundary

Structural wiki integrity is validated by `scripts/llm_wiki.py check`.
Raw source digests are verified by `scripts/llm_wiki.py verify-sources`.
No live LLM compilation or unexecuted formal proof is claimed.
