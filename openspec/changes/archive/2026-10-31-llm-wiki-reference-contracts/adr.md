# ADR: preserve PStack Markdown authority; extract upstream contract atoms

**Status:** ACCEPTED baseline decision inherited from #873 / PR #880; this change is a **design refinement**, not another migration vote.

## Context

Atomicstrata's `llm-wiki-compiler` is a typed, provider-capable extraction and review compiler with state/recovery. Geronimo's `llm-wiki` is a headless Rust Markdown engine for typed ingest, index, graph and search. These are architecturally distinct systems, and both differ from PStack's minimal project-local CLI and QStack's governed corpus publisher.

## Decision

Keep `.llm-wiki/` + stdlib `scripts/llm_wiki.py` as baseline. Extract the **smallest independent, testable** semantic contracts from reference engines into OpenSpec and `CandidateEnvelope.v1` proposal, reuse existing skill scaffolds, and keep optional upstream engines outside mainline requirements. No second wiki owner, duplicate canonical schema registry, or ad hoc orchestration service. The upstream schema never grants publisher authority.

## Consequences

**Positive:** low-cost offline default, Git diffs, explicit spec gap tracking and bounded negative tests. **Tradeoffs:** semantic extraction, embedded search, typed frontmatter runtime admission, graph relations, reference benchmarks and full TLC/model proof remain GAP/UNTESTED. **Future trigger:** a new opt-in decision with actual identical-corpus tool runs, clear runtime/rights budgets and rollback plan. **Safety:** source writes and activity logs are currently nontransactional; structural source admission cannot be elevated into fully trusted semantic evidence. Existing QStack publisher and `operations.jsonl` are separate and protected.
