# Cursor PStack 0.15.43 → Portable PStack: Audited Upstream Delta

**Status:** Research and intent audit. Linked to Epic #1425 and Issue #1426.

## Source Revision Contract

| Property | Verified Input |
|---|---|
| Port base | `tommy-ca/pstack@bc51eb9` |
| Port applied upstream pin | `cursor/plugins@bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7` (0.15.42) |
| Upstream target tip | `cursor/plugins@2f87c854fe3e2fcda44ca86b46ede35aad3c46b7` (0.15.43) |
| Upstream tree SHA | `71d8e1d1d718e2149dc43b2535618064f29cba6b` |
| Declared package versions | Upstream `0.15.43`, Port `0.15.36-preview.0` |

Source-scoped Git comparison across `cursor/plugins/pstack` identified 70 changed files (253 insertions, 1381 deletions).
The primary focus of upstream 0.15.43 is token density, streamlining prose across principle skills, playbooks, and utility skills, introducing a unified `worker.md` contract for subagents, and capping Opus model routing at `xhigh`.

## High-Impact Semantic Changes

### 1. 14 Principle Leaves Streamlined to Dense Rules
Upstream condensed 14 principle skill bodies (`principle-attack-the-premise`, `principle-boundary-discipline`, `principle-build-the-lever`, `principle-explain-the-number`, `principle-fix-root-causes`, `principle-foundational-thinking`, `principle-make-operations-idempotent`, `principle-minimize-reader-load`, `principle-model-the-domain`, `principle-prove-it-works`, `principle-separate-before-serializing-shared-state`, `principle-sequence-verifiable-units`, `principle-test-behavior-not-implementation`, `principle-type-system-discipline`).
Each trimmed skill retains its core rule, actionable test, and stop conditions, eliminating redundant bolding and verbose narrative explanations. Frontmatter names and descriptions are preserved without drift.

### 2. Streamlined Unslop and Technical Writing
- `skills/unslop/SKILL.md`: Streamlines pattern explanations into single-line imperative rules while strictly preserving stable rule IDs (for example, rule 13 for no dashes, rule 14 for no mid-sentence colons, rule 26 for abstract metaphor nouns).
- `skills/technical-writing/SKILL.md`: Condenses the four-layer writing guidance into compact, clear paragraphs.

### 3. Playbook Streamlining and Retained Compatibility Surfaces
- `skills/poteto-mode/playbooks/opening-a-pr.md`: Condensed to three focused paragraphs covering worktree isolation, small reviewable commits, `/unslop` and `/no-comments`, title formatting, and the six `##` headings. Forge resolution continues to prefer `origin pr` when available, falling back to `gh pr create` without `--draft`.
- `skills/poteto-mode/playbooks/babysit.md`: Trimmed to six clear rules covering mode declaration, the conflict-thread-CI order, the no-rebase rule, and forge resolution.
- `skills/poteto-mode/playbooks/multi-phase-plan.md`: Condensed to five steps.
- **Architectural Retention for Portable PStack:** Upstream deleted `skills/poteto-mode/scripts/check-plan.mjs` and `skills/poteto-mode/scripts/check-plan.test.ts`. In Portable PStack, `check-plan.mjs` is an audited Codex compatibility surface governed by `openspec/specs/pstack-recursive-plan-validation/spec.md` and verified in offline CI and harness driver scenarios (`drive-check-plan`). We retain `check-plan.mjs` and its test `check-plan.test.mjs` in our repository.

### 4. Introduction of `worker.md` Subagent Contract
Upstream introduced `skills/poteto-mode/worker.md`, an explicit 11-line contract for delegated subagent workers. It establishes that:
- Every worker acts for the operator, not the calling subagent.
- The kickoff bar is the entire bar; no unrequested extra gates or reviews may be added.
- Workers must never present blocking questions for reversible actions.
- PRs must open ready for review with strict Conventional Commit titles and the six standardized body headings.

### 5. Architectural Invariant: 22 Canonical Roles Preserved
In upstream Cursor, subagent roles for `reflect` and `architect` prompt templates were removed in favor of single-file inline execution or Arena delegation.
In Portable PStack, our six-host architecture (Grok, Codex, OMP, OpenCode, Antigravity, Droid) relies on the 22 canonical roles defined in `pstack.package.json`. These roles are verified by `tests/test_model_role_constraints.py` and `tests/test_verify_harness.py`.
Therefore, we retain all 22 roles and their host projections while adopting the streamlined skill bodies for `reflect` and `architect`.

### 6. Classification TSV Reconciliation
All 70 delta files between pin `bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7` and tip `2f87c854fe3e2fcda44ca86b46ede35aad3c46b7` are fully classified in `skills/swarm/references/classification.tsv`.
