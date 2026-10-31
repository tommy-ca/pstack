# LLM Wiki v2 — Reference-Derived Formal Contracts

**Status:** specification and design only for upstream semantic features; optional adapter engines NOT installed or exercised. PStack's `scripts/llm_wiki.py check` is **structural only**. The Python safety code and Codex verification skills are proposed for main through [successor PR #881](https://github.com/tommy-ca/pstack/pull/881).

## Reference foundations

- [Atomicstrata LLMWiki compiler](https://github.com/atomicstrata/llm-wiki-compiler/tree/0f8ff86ef0a28f4c15627a2ea5e94a96cadd834e): content-hash incremental compilation, candidate holds and approvals, citation resolution, state recovery, generic lifecycle profile contracts. It is an LLM-capable **compiler**; not the PStack project-local publisher.
- [Geronimo LLM Wiki engine](https://github.com/geronimo-iia/llm-wiki/tree/9d974c9e4d9d6c21638a5f520e6d89f79647724e): JSON-Schema-typed Markdown frontmatter, typed graph edges, Tantivy BM25 index with rebuildability, explicit source/concept/query separation. It is a local **engine**; it does not embed the same semantic compiler.
- [QStack wiki governance](https://github.com/tommy-ca/qstack/blob/149b6082fe7bcd00e86a13ed48fbf8ee51268882/openspec/specs/wiki-governance/spec.md) and [nine-role primitives](https://github.com/tommy-ca/qstack/blob/149b6082fe7bcd00e86a13ed48fbf8ee51268882/docs/spec/catalog/llm-wiki-v1-atomic-primitives.md): independently authorized `knowledge/` publication, `knowledge/operations.jsonl` canonical ledger, quarantine and explicit rights and high-impact approval gates.

## Resulting semantic primitives

`SourceRevision → EvidenceSpan → AffectedClosure → CandidateEnvelope → TypeRegistry + PolicyGate → PromotionCAS → ProjectionManifest → TypedRelation + QueryPlan → Attestation`.

These are small **contracts**, not services or deployed code. They map to the existing `WikiSource, WikiSynthesis, WikiArticle, WikiGraphMap, WikiSearchIndex, WikiLogEntry, WikiIndex, WikiLever, WikiIntent` semantic ownership roles. The model respects the separate epistemic roles **source** (observed), **concept** (synthesized) and **query result** (derived answer).

## Proposed cross-cutting invariants

1. Source revision bytes never change after an accepted capture; retries with identical bytes are idempotent.
2. External compiler output is untrusted and never grants canonical write authority.
3. Promotion requires fresh source and target digests, schema/rights checks and authorized review.
4. Citation path resolution is not factual evidence of claim truth.
5. Search/graph/index results are rebuildable read projections, never sole evidence or authority.
6. Offline tests retain `FAIL > BLOCKED > UNTESTED > PASS` and never claim a missing TLC/LLM run passed.

## Where formal specs live

The [OpenSpec requirements](../../../openspec/changes/2026-10-31-llm-wiki-reference-contracts/specs/llm-wiki/spec.md), [design and state machine](../../../openspec/changes/2026-10-31-llm-wiki-reference-contracts/design.md) and [data models](../../../openspec/changes/2026-10-31-llm-wiki-reference-contracts/data-models.md) are project-level design artifacts. The proposed versioned `CandidateEnvelope.v1` JSON Schema is **not a runtime PStack schema validator**.

The `verify-llm-wiki` driver has 9 baseline, 11 source/path, and 3 bounded model tests in the previous PR #879 run. New schema-negative fixtures are introduced separately; report their execution result by exact PR-head GitHub Actions. The 39-history code trace test has a deliberately broken overwrite variant; this is not unbounded concurrency or TLC proof.

[Migration decision #873](https://github.com/tommy-ca/pstack/issues/873) keeps the lightweight Python baseline. Optional reference engines remain deferred, not silently migrated.
