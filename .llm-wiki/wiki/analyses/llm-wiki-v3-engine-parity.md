# LLM Wiki v3 Engine Parity Analysis

This page documents the reference engine parity architecture implemented for Epic #887.

## Overview

The PStack LLM Wiki achieved functional parity with the Geronimo Rust engine and the Atomicstrata compiler while preserving zero-dependency Python 3 standard library architecture.

## Key Capabilities

1. **Source Hash Verification:** Re-computes SHA-256 for all raw sources against digests recorded in the append-only log. Validates raw source integrity and rejects unlogged files.
2. **Directed Knowledge Graph:** Extracts cross-references between wiki articles, computes inbound/outbound links, calculates graph density, and detects orphan articles.
3. **Headless Keyword Search:** Fast multi-term search scoring across article titles, markdown headings, and text bodies with extracted snippets.

## Related Pages

- [Reference Evaluation](llm-wiki-reference-evaluation.md)
- [Project Knowledge System](../concepts/llm-wiki-project-knowledge.md)
- [Epic #871 Contracts](../requirements/epic-871-llm-wiki-v2-contracts.md)
