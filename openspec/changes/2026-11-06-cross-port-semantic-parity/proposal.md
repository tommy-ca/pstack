## Why

Following the completion of canonical upstream 0.15.36 reconciliation (#840) and standalone Pi candidate verification (#894-#902), comparator `michael-denyer/pstack-claude` advanced to commit `d88063f3` (v0.9.130). Epic [#906](https://github.com/tommy-ca/pstack/issues/906) authorizes a three-source semantic audit across canonical Cursor PStack (`c742dd61`), comparator `pstack-claude` (`d88063f3`), and target `tommy-ca/pstack` (`5d58283f`). This change classifies all 65 declared comparator fork paths, specifies negative-control contracts, links formal invariants, and curates source-backed LLMWiki concepts without importing foreign runtime state engines or violating the six-host adapter core.

## What Changes

- **Source Pin Ledger**: Record exact SHAs and licensing reviews for Canonical (`cursor/plugins@c742dd61`), Comparator (`pstack-claude@d88063f3`), and Target (`tommy-ca/pstack@5d58283f`).
- **Declared Forks Classification**: Classify all 65 comparator fork paths in `docs/research/pstack-claude-forks-2026-11-06.json` into adapt, preserve, policy-fork, and exclude.
- **Negative Invariant Contracts**: Port failure-oriented postconditions (canceled child non-passage, worktree untracked rejection, headless ask fail-closed, scheduler late-wakeup cancellation) into functional tests.
- **Formal Verification Alignment**: Corroborate safety and liveness invariants with falsifier mutants without requiring external TLC/Lean toolchains.
- **LLMWiki Cross-Port Curation**: Ingest and compile source-attributed cross-port atoms in `.llm-wiki/wiki/analyses/` using `scripts/llm_wiki.py`.

## Modified Capabilities

- `pstack-portability`: Three-source cross-port semantic delta, negative invariant contracts, and source-attributed verification.

## Non-goals

- No automatic promotion of policy forks to canonical.
- No second runtime supervisor, external state store (`~/.claude/orchestrate`), or Node child-process machinery.
- No promotion of candidate Pi to a seventh built-in shipped host.
- No unobserved live pass claims; missing runtime tools remain `BLOCKED` or `UNTESTED`.
