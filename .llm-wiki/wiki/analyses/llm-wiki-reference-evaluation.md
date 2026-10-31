# LLM Wiki Reference Engines and Migration Evaluation

The PStack LLM Wiki has a completed project-local Markdown/Python baseline (historical [#863](https://github.com/tommy-ca/pstack/issues/863)). The follow-on [#871](https://github.com/tommy-ca/pstack/issues/871) evaluates optional reference engines without treating external compiler output as trusted canonical knowledge.

## Reference implementations (source-reviewed, not executed)

- [Atomicstrata llm-wiki-compiler](https://github.com/atomicstrata/llm-wiki-compiler): Node 24+ knowledge compiler (inspected `0f8ff86`, documented v1.5.0) with source change detection, LLM extraction, candidate review, storage seams, provenance and recovery. Suitable as an **optional untrusted candidate producer** only.
- [Geronimo llm-wiki](https://github.com/geronimo-iia/llm-wiki): Rust Git/Markdown engine (inspected `9d974c9`) with typed schemas, BM25 search, graph, MCP/ACP. Its LLM work lives in external skills. Suitable as an **optional derived read/index engine**; it does not replace semantic compilation.
- [QStack wiki governance](https://github.com/tommy-ca/qstack/issues/2624): the nine roles (`WikiSource`, `WikiArticle`, `WikiSynthesis`, `WikiGraphMap`, `WikiSearchIndex`, `WikiLogEntry`, `WikiIndex`, `WikiLever`, `WikiIntent`) are semantic responsibilities; `knowledge/operations.jsonl` is its authoritative operations ledger and its own governed publisher is the canonical write owner.

## PStack boundary and known gaps

Current PStack `scripts/llm_wiki.py` provides `ingest`, `index`, `check` using standard Python, local `raw/sources/`, Markdown `wiki/` and a generated `index.md`. The current `ingest_file` calls `dest.write_bytes(content)` on a basename-derived path, so a repeated filename can overwrite an existing raw source; this contradicts the documented immutability promise and needs a negative test/fix. Structural `check_wiki` does not actually enforce typed frontmatter, immutable content hashes, or schema-bound relations. Treat a structural PASS as structural only.

Preserve zero-dependency offline CLI operation across the six declared host environments. External engines must be optional, source/version pinned, and isolated from canonical writes. A source-to-candidate-to-gate-to-Git-PR flow is the default; QStack's separate admission policy always applies to QStack knowledge.

## Choice and review gates

1. **Keep minimal (default):** fix immutable capture, path confinement, schema truthfulness and deterministic index tests.
2. **Compose optional capabilities:** only after benchmarks prove better retrieval or compilation; no second publisher, ledger, ontology or mandatory daemon.
3. **Full migration:** defer until the new engine proves source, claim, link, schema, lifecycle, permissions, rollback and six-host parity.

Reproduce source defects on isolated fixtures; then compare pinned engines with the same corpus. Use PStack `create-verification-skill` to create a native CLI drive, and `create-formal-verification-skill` for bounded no-overwrite, no-escape, promotion-before-gates and concurrency models with mutation controls. TLC/SDK/binary unavailability means BLOCKED/NOT_RUN, never PASS. Apply Thermos changed-diff correctness/security and code-quality reviews with independent Swarm, Arena and Interrogate receipts.

See also [project-local knowledge system](../concepts/llm-wiki-project-knowledge.md) and [review semantics](../concepts/review-semantics-and-verification.md).

**Current evidence state:** source architecture inspected; upstream engines, formal model checker, and independent multi-model review NOT RUN. The audited design and requirements are in the PStack research document `docs/research/llm-wiki-reference-evaluation-2026-10-31.md` (tracked outside this wiki).
