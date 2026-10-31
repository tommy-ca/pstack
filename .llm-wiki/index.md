# Knowledge Base Index: PStack multi-harness portability and canonical upstream 0.15.36 reconciliation

## Sources
- [Upstream Cursor PStack 0.15.36 Source Reference](wiki/sources/upstream-0.15.36.md): - **Source:** `cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (release 0.15.36)

## Entities
- [PStack Six-Harness Architecture and Profiles](wiki/entities/pstack-harnesses.md): PStack formally declares six supported host environments with native adapters and truthful evidence reporting:

## Concepts
- [Agentic Orchestrate Architecture](wiki/concepts/agentic-orchestrate.md): In upstream release 0.15.36 (commit #1043), canonical PStack retired the `orch` CLI and SQLite store (`skills/poteto-mode/scripts/orch/orch.ts`, `store.ts`), replacing it with agentic coordination where the parent chat acts as the coordinator owning briefs, queue draining, and stack frontier tracking.
- [Project-Local LLM Wiki Knowledge System](wiki/concepts/llm-wiki-project-knowledge.md): PStack's `.llm-wiki/` is a Markdown-first, Git-reviewed knowledge store used by engineering agents and human maintainers. It is not a mandatory semantic compiler or QStack's governed knowledge publisher.
- [Review Semantics and Verification Discipline](wiki/concepts/review-semantics-and-verification.md): Upstream 0.15.36 introduces rigorous adversarial review and verification contracts across Arena, Interrogate, Autopilot, and principles.
- [Semantic Blocks and QStack Governance Crosswalk](wiki/concepts/semantic-blocks-and-crosswalk.md): The PStack LLM Wiki implements formal semantic blocks mapped to QStack knowledge governance roles, ensuring clean cross-repository boundaries and precise data contracts.

## Requirements
- [Epic #840 Acceptance Gates and Dependency Graph](wiki/requirements/epic-840-acceptance-gates.md): flowchart TD
- [Epic #871 LLM Wiki v2 Requirements and Contracts](wiki/requirements/epic-871-llm-wiki-v2-contracts.md): Epic #871 evaluates reference engines, hardens knowledge contracts, and governs migration for the PStack LLM Wiki.

## Analyses
- [LLM Wiki Reference Engines and Migration Evaluation](wiki/analyses/llm-wiki-reference-evaluation.md): The PStack LLM Wiki has a completed project-local Markdown/Python baseline (historical [#863](https://github.com/tommy-ca/pstack/issues/863)). The follow-on [#871](https://github.com/tommy-ca/pstack/issues/871) evaluates optional reference engines without treating external compiler output as trusted canonical knowledge.
- [Statechart Compiler Qualification Analysis](wiki/analyses/statechart-qualification.md): Upstream commit #977 added `skills/statechart`, featuring a TypeScript CLI that compiles statecharts, checks TLA+ invariants with TLC, and renders Mermaid diagrams.

## Syntheses
- [LLM Wiki Reference Engine Arena Decision](wiki/syntheses/llm-wiki-arena-decision.md): The PStack LLM Wiki Arena evaluation resolves the architecture choice between standard library Python core and external reference engines (Atomicstrata Node.js compiler, Geronimo Rust engine).
- [Synthesis: Canonical Intent vs Multi-Harness Portability](wiki/syntheses/multi-harness-portability-synthesis.md): The PStack multi-harness port resolves the tension between rapidly evolving canonical Cursor features and broad, truthful host portability:
