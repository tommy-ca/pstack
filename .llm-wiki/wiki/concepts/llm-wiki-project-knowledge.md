# Project-Local LLM Wiki Knowledge System

PStack's `.llm-wiki/` is a Markdown-first, Git-reviewed knowledge store used by engineering agents and human maintainers. It is not a mandatory semantic compiler or QStack's governed knowledge publisher.

## Purpose and storage

- **Layer 1 (`raw/sources/`)**: explicit captured source bytes. The PStack Python ingestion CLI creates files exclusively and refuses same-basename changes; direct filesystem changes are not prevented by this tool.
- **Layer 2 (`wiki/`)**: curated sources, entities, concepts, requirements, analyses and syntheses.
- **Layer 3 (`index.md`, `log.md`, `config.json`)**: generated navigation, human activity notes and structural configuration. `log.md` is **not** an atomic event ledger.

## Tooling and verification

- `scripts/llm_wiki.py` supports `check`, `index`, `ingest` with Python standard-library dependencies.
- `tests/test_llm_wiki.py` checks the structural baseline; `tests/test_llm_wiki_safety.py` tests write-once replay, collisions and path/link negatives.
- `scripts/verify_llm_wiki_model.py` explores 39 bounded serial actual-code ingest traces and verifies that a deliberately broken overwrite variant is detected. It does not prove unbounded concurrency, crash atomicity, or TLA+ conformance.
- Project-local verification skill: `.codex/skills/verify-llm-wiki/SKILL.md`; bounded formal-analysis skill: `.codex/skills/verify-llm-wiki-formal/SKILL.md`. External TLC remains untested unless a pinned run receipt is produced.

## Reference-engine evaluation

The [reference engine evaluation](../analyses/llm-wiki-reference-evaluation.md) compares Atomicstrata LLMWiki (semantic candidate compilation) with Geronimo LLMWiki (headless graph/search). The [engine parity analysis](../analyses/llm-wiki-v3-engine-parity.md) details the native Python stdlib implementation of source verification, knowledge graph analysis, and in-memory search. QStack retains sole authority over its own canonical publisher, operation ledger and knowledge records.

See `.llm-wiki/WIKI_SCHEMA.md` for the exact implementation limits and ownership rules.
