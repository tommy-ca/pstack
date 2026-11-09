# Intent: formalize reference-derived wiki contracts without migrating authority

## Why

The accepted [PStack arena decision](https://github.com/tommy-ca/pstack/issues/873) keeps the stdlib Python / Git Markdown wiki as canonical. Research [#878](https://github.com/tommy-ca/pstack/pull/878) identified useful but **not yet implemented** capabilities in the two reference engines. The previously tested security change [#879](https://github.com/tommy-ca/pstack/pull/879) did not merge: GitHub closed it when its base branch was deleted. [Successor #881](https://github.com/tommy-ca/pstack/pull/881) rebases those functional changes against current main.

The existing binding decision says several safety checks are fixed; that statement describes an intended patch, not behavior present in main at source pin `f7e7fbaee23bd19ae7c03861f121ea65c756650f`. This change makes the difference explicit and introduces formal, independently reviewable requirements and optional candidate schemas.

## What changes

- Pin Atomicstrata compiler 1.5.0 @ `0f8ff86ef0a28f4c15627a2ea5e94a96cadd834e` and Geronimo wiki @ `9d974c9e4d9d6c21638a5f520e6d89f79647724e`.
- Derive unique functional requirements and invariants from **documented upstream behavior** (do not assert the PStack Python code already implements them).
- Recompose semantic atoms into PStack's six wiki directories and QStack's existing nine-role governance model without creating a second canonical publisher.
- Add portable, versioned JSON Schema for **optional, untrusted** `CandidateEnvelope` and valid/invalid test vectors. These are proposal artifacts, not runtime schema enforcement.
- Maintain existing `verify-llm-wiki` and `verify-llm-wiki-formal` skills as the verification surface, add conformance assertions to catch spec drift and ensure negative controls fail.
- Update the wiki with a source-linked synthesis. Preserve historical issue and PR receipts. #871/#874/#876/#877 remain open until actual acceptance evidence; #873 is a **completed decision**, not a benchmark.

## Non-goals

No mandated Node >=24/Rust, migrations, LLM credentials, embedding stores, new runtime wiki service, QStack canonical `knowledge/` writes, or falsely claimed six-host live/factual-support/formal-TLC proof. Preserve SOLID/KISS/DRY/YAGNI; names describe narrow contracts, not deployable microservices.

## Acceptance

Exact-head CI passes for structural specs/schema fixtures, existing CLI verification skill and negative mutation tests. Source pins and design mappings are auditable. Human reviewers separately validate generated content, copyright/rights, and any candidate promotion. Distinguish source-reviewed, offline-tested, formal-modeled (not run) and independently validated statuses.
