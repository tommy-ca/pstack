# LLM Wiki v2 data contracts and upstream mappings

## Canonical, candidate and read-only models

`CandidateEnvelope.v1` lives at [schemas/candidate-envelope.v1.schema.json](schemas/candidate-envelope.v1.schema.json). This is a **proposal/test fixture only**, not part of PStack's `scripts/llm_wiki.py check` and not an automatically installed runtime type registry. Draft 2020-12 syntax is used because Geronimo uses JSON Schema for per-type frontmatter and Atomicstrata has typed lifecycle profiles.

### CandidateEnvelope.v1

| Field | Type / semantic role | Validity rule |
| --- | --- | --- |
| `schema_version` | literal `1` | unknown future versions fail closed |
| `candidate_id` | stable human-readable slug | unique per proposal and immutable during review |
| `kind` | `concept/entity/comparison/overview/source/analysis/synthesis/query_result` | preserve source, synthesis and query role |
| `state` | `proposed/held/validated/rejected` | never equate `validated` with publication |
| `target_path` | repository-relative Markdown path | starts at `wiki/`; path resolver must enforce root confinement |
| `content_sha256` | hex SHA-256 of proposed Markdown bytes | explicit same-body approval precondition |
| `source_revisions[]` | `SourceRevision` pointers | each has stable id, reference, revision sha256, and rights label |
| `target_precondition` | one-of `not_exists` or published sha256 | compare-and-swap gate; no blind clobber |
| `review` | hold reasons + approval claim / reviewer | actual reviewer authorization must be established OUTSIDE JSON |
| `citations[]` | `EvidenceSpan` pointers | optional 1-indexed start/end bounded by real source; not factual support |
| `derived_from` | optional upstream engine name/version | telemetry; confers no trust or authority |

**Hard distinction:** syntactically valid `sha256` string is not a computed digest; a schema validator does not read files, prove matching bytes or verify licenses. A runtime validator must rehash and check source revision rights and target CAS before promotion. A model can invent a `reviewer` string; policy must verify principal authorization independently.

### SourceRevision

```json
{"source_id":"pstack-docs:design-1","uri":"repo:docs/research/llm-wiki-architecture.md","sha256":"<64 computed hex digits>","rights":"repository","captured_at":"2026-10-31T15:41:49Z"}
```

This is illustrative. Placeholder digests must never be promoted or asserted as computed evidence.

### ProjectionManifest (proposed)

```text
manifest = {
  canonical_repo, canonical_commit, schema_digest, indexer_version,
  source_revision_ids, page_content_digests, projection_digest,
  built_at, stale_since?, verification_receipt?
}
```

Publication must not depend on projection freshness or its ability to return results. Graph and search indices may be wiped and rebuilt. Geronimo's snapshot/rebuild invariant motivates the deterministic derivation identity; PStack currently does **not** have a Tantivy search index or this manifest.

### ReviewDecision (proposed)

```text
decision = {
  candidate_id, candidate_digest, expected_published_revision,
  hold_reasons, policy_version, rights_evidence_ref,
  reviewer_principal, reviewer_attestation, verdict,
  recorded_at
}
```

Review decisions are not trusted merely because a file includes a reviewer string. An authorized publisher must compare the digest, policy version and page target precondition when applying them. Atomicstrata's review pipeline documents last-minute mutation-locked checks; we extract the contract without asserting PStack implements that code.

## Layout ownership crosswalk

| Meaning | PStack (canonical project-local) | Atomicstrata reference | Geronimo reference | QStack canonical |
| --- | --- | --- | --- | --- |
| Captured evidence | `.llm-wiki/raw/sources/` | `sources/` | `raw/` | `.wiki/` quarantine and source registry |
| Curated Markdown | `.llm-wiki/wiki/{sources,entities,concepts,requirements,analyses,syntheses}` | `wiki/concepts/`, `wiki/queries/` + optional profile types | configurable `wiki_root`, typed frontmatter | `knowledge/` |
| Review candidates | not implemented as native Python CLI type | `.llmwiki/candidates/` | author/editor controls, typed validation on ingest | governed candidate/quarantine workflow |
| Schema | short `.llm-wiki/WIKI_SCHEMA.md` structural guide | `.llmwiki/schema.json`, profile config | `schemas/*.json` with `x-wiki-types` and `x-graph-edges` | `openspec/specs/wiki-governance/spec.md`, domain schemas |
| Journal | `.llm-wiki/log.md` human notes | `log.md` + internal recovery files | Git history | `knowledge/operations.jsonl` authoritative |
| Projection | generated `.llm-wiki/index.md` | generated `wiki/index.md`, embeddings optional | local Tantivy index, graph | derived indexes, search/graph projections |

QStack nine roles: `WikiSource` owns SourceRevision/EvidenceSpan; `WikiSynthesis` owns candidate construction; `WikiArticle` owns article decisions; `WikiGraphMap` typed edges; `WikiSearchIndex` query/projection; `WikiLogEntry` operation receipts; `WikiIndex` index views; `WikiLever` policy/validation; `WikiIntent` governs stage/admit intent. These are **roles**, not 1:1 files or services.

## Reference implementation differences that must not be flattened

- Atomicstrata is a semantic **compiler**, with provider-backed extraction, review hold modes, save/revalidation and state recovery. Its default profile permits concept pages; opt-in CLP enriches lifecycle contracts.
- Geronimo is a Rust **knowledge engine** with typed Markdown ingestion, read/search/graph/MCP surfaces. It intentionally separates LLM content authoring into external skills and does not promise the same extraction pipeline.
- Neither authoritative upstream design is a drop-in replacement for the PStack project-local layout or QStack's governed publication/operation ledger.
- A schema validates structure. A verified citation path validates reference resolution. Neither proves claim truth, rights, approved reviewer identity or a completed model-checker run.
