# Semantic Blocks and QStack Governance Crosswalk

The PStack LLM Wiki implements formal semantic blocks mapped to QStack knowledge governance roles, ensuring clean cross-repository boundaries and precise data contracts.

## Crosswalk Overview

The nine QStack knowledge roles map directly to PStack's local markdown and git-tracked semantic blocks:

1. **`WikiSource` -> `SourceRevision`**: Immutable raw external sources stored under `.llm-wiki/raw/sources/` with SHA-256 digests. Write-once exclusive creation prevents accidental data overwrites.
2. **`WikiArticle` -> `FieldContract`**: Structured markdown articles residing in `.llm-wiki/wiki/{entities,concepts,requirements,analyses,syntheses}/` conforming to structural schema requirements.
3. **`WikiSynthesis` -> `PromotionDecision`**: Consolidated architectural decisions (such as Arena resolutions) providing binding decisions backed by evidence.
4. **`WikiGraphMap` -> `RelationType`**: Directed links between knowledge pages, structurally verified by `scripts/llm_wiki.py check`.
5. **`WikiSearchIndex` -> `QueryPlan`**: Headless catalog lookup and fast ripgrep queries driven by `index.md`.
6. **`WikiLogEntry` -> `Attestation`**: Append-only activity records in `log.md` detailing timestamped maintenance events.
7. **`WikiIndex` -> `ProjectionManifest`**: The generated catalog `index.md`, rebuilt atomically via `scripts/llm_wiki.py index --write`.
8. **`WikiLever` -> `EvidenceSpan`**: Executable verification skills and tests producing reproducible proof receipts.
9. **`WikiIntent` -> `Candidate`**: Unmerged proposals or pull requests awaiting human and agent verification.

## Governance Boundaries

- PStack maintains exclusive mutation authority over its project-local `.llm-wiki/`.
- QStack retains exclusive governance over cross-repository ontologies and `knowledge/operations.jsonl`.
- External engines (Atomicstrata, Geronimo) act as optional candidate producers with no direct write permissions.

## Related Resources

- Architecture Specification: [LLM Wiki Project Knowledge](llm-wiki-project-knowledge.md)
- Review Policies: [Review Semantics and Verification](review-semantics-and-verification.md)
- Formal Decision: [Arena Decision](../syntheses/llm-wiki-arena-decision.md)
