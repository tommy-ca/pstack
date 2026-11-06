# Arena Architectural Decision: Cross-Port Implementation Strategy (2026-11-06)

**Context**: Epic [#906](https://github.com/tommy-ca/pstack/issues/906) and Unit E [#911](https://github.com/tommy-ca/pstack/issues/911). Resolves the architectural topology for integrating comparator `pstack-claude` semantics into `tommy-ca/pstack`.

---

## Candidates Evaluated

### Candidate A: No-Code / Documentation-Only
- **Summary**: Document the comparator deltas and forks purely in research notes without writing any executable contract tests or formal invariant verification.
- **Pros**: Zero maintenance footprint.
- **Cons**: Lacks verifiable proof; future refactoring or host updates could silently violate negative safety contracts.

### Candidate B: Clean-Room Contract Tests & Bounded Formal Models (Selected)
- **Summary**: Implement negative scenario contracts in `tests/test_cross_port_contracts.py` and bounded exhaustive state-machine checks in `scripts/verify_cross_port_invariants.py`. Curate source-backed LLMWiki concepts.
- **Pros**: Strict SOLID, KISS, DRY, and YAGNI compliance. Zero new external daemon or runtime dependencies. Offline checks run hermetically in milliseconds. Verifies reachable mutants fail closed.
- **Cons**: Requires ongoing maintenance of contract test suites.

### Candidate C: Foreign Middleware Engine & Session Store Import
- **Summary**: Import comparator's Node.js child-process supervisor, `PiChild`, and `~/.claude/orchestrate` state store into target core.
- **Pros**: Matches comparator implementation byte-for-byte.
- **Cons**: Violates ADR 0006 (Host-Owned Orchestration State) and ADR 0021. Creates dual control planes, memory leaks, and single-harness lock-in across the 6-host matrix. Extreme complexity bloat.

---

## Verdict & Decision: Candidate B

**Rationale**: Candidate B satisfies all requirements of Epic #906 with the minimal sufficient footprint:
1. Reuses existing test infrastructure (`pytest`, `verify_portable.py`, `llm_wiki.py`).
2. Introduces no third-party npm packages, persistent orchestration stores, or duplicate runners.
3. Provides concrete, runnable falsification proofs for all 5 safety invariants via mutants.
