# PStack Project-Local LLM Wiki Schema and Ownership

This is a **structural Markdown/Git schema**, not a JSON-Schema-validated ontology or semantic proof. The baseline does not require Node, Rust, embeddings, an LLM provider or a wiki daemon. Normative cross-repository QStack policies live in QStack, not in this file.

## Ownership and data-flow rules

| Path | Owner | Contract |
|---|---|---|
| `raw/sources/**` | explicit capture/maintainer | Write-once **through `scripts/llm_wiki.py ingest`**; basename collision with different bytes fails, identical replay is a no-op |
| `wiki/{sources,entities,concepts,requirements,analyses,syntheses}/**` | model + authorized engineer | Curated Markdown; all pages should be linked from the derived navigation index |
| `index.md` | CLI projection | Generated navigation; `index --write` uses an atomic replacement |
| `log.md` | CLI and maintainer | Human-readable operation history; **not a transactionally authoritative event store** |
| `config.json` | maintainer | `name`, `mode`, `topic`, `version` must be nonempty strings |
| `WIKI_SCHEMA.md` | maintainer | Declares structural storage and ownership policy |

## Structural contract vs unproved properties

`scripts/llm_wiki.py check` checks required paths, config key shape, indexed Markdown pages and reachable local links. It rejects wiki page or link destinations resolving outside the local wiki root, and rejects symlinked mandatory directories. Its Markdown link detector is deliberately limited: it does **not** fully parse all Markdown variants, anchors, remote citations, frontmatter types, typed relations, semantic accuracy, or reproducible compiler outputs.

The ingestion CLI uses atomic **exclusive file creation** to prevent sequential overwrite and straightforward same-name races. It rejects symlinked raw and log directories in the tested case, but a preflight is not an OS sandbox against adversarial concurrent directory replacement. Source copy and activity-log append remain **separate writes**, so a crash can leave incomplete history. Repository write permissions, Git review, and negative controls remain necessary.

## Reference and migration boundaries

`docs/research/llm-wiki-reference-evaluation-2026-10-31.md` defines a source-pinned comparison of Atomicstrata and Geronimo, optional adapter candidates, rollback, and the nine QStack semantic roles. PStack's wiki is **not** QStack's canonical `knowledge/` publisher or `knowledge/operations.jsonl` ledger. No external engine may bypass QStack's independent governance.

## Verification

Use `.codex/skills/verify-llm-wiki/` for actual Python CLI/scratch-path checks and `.codex/skills/verify-llm-wiki-formal/` for the bounded 39-trace real-code model and optional (unexecuted unless evidence is recorded) TLC specification. None of these offline checks establish native six-host execution or live LLM compilation. See [issue #874](https://github.com/tommy-ca/pstack/issues/874).
