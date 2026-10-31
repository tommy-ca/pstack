# LLM Wiki Reference Engine Arena Decision

The PStack LLM Wiki Arena evaluation resolves the architecture choice between standard library Python core and external reference engines (Atomicstrata Node.js compiler, Geronimo Rust engine).

## Decision Summary

- **Selected Option:** Option A (Keep and harden Python stdlib baseline).
- **Deferred Option:** Option B (Optional upstream engine adapters). Formally resolved as `not_planned` for Issue #875.
- **Rejected Option:** Option C (Full migration to Node or Rust reference engine).

## Rationale Highlights

1. **Portability:** Python stdlib requires zero external dependencies and runs reliably across all six supported hosts (Cursor, Windsurf, Claude Code, Grok, Codex, OpenCode).
2. **Simplicity (KISS & YAGNI):** Current ~280-line Python implementation compiles, indexes, and validates the entire wiki in under 200ms. Speculative features such as external daemons or heavy indexers add unneeded maintenance overhead.
3. **Canonical Authority:** PStack knowledge remains governed exclusively by Git, operator review, and transparent Markdown commits. External autonomous compilation daemons are disallowed.
4. **Targeted Hardening:** Known audit findings (raw source overwrite, non-atomic index writes, link path traversal) are remediated directly within `scripts/llm_wiki.py` under Issue #874.

## Related Resources

- Full Decision Record: `docs/research/llm-wiki-arena-decision-2026-10-31.md` (tracked in repository root).
- Reference Engine Evaluation: [Reference Evaluation](../analyses/llm-wiki-reference-evaluation.md)
- Architecture Specification: [LLM Wiki Project Knowledge](../concepts/llm-wiki-project-knowledge.md)
