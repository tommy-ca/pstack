# Project-Local LLM Wiki Knowledge System

The project-local LLM Wiki (`.llm-wiki/`) provides a structured, git-tracked knowledge base for PStack engineering.

## Purpose and Schema
- **Layer 1 (`raw/sources/`)**: Immutable snapshots of authoritative specifications, audit manifests, and package descriptors.
- **Layer 2 (`wiki/`)**: Curated markdown pages covering entities, concepts, requirements, analyses, sources, and syntheses.
- **Layer 3 (`index.md`, `log.md`, `config.json`)**: Deterministic entrypoint catalog and append-only audit trail.

## Tooling
- CLI manager at `scripts/llm_wiki.py` provides `check`, `index`, and `ingest` commands.
- Automated tests in `tests/test_llm_wiki.py` enforce link integrity, JSON schema validity, and unindexed page detection.
