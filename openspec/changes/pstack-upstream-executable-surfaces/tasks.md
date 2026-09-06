## 1. Refresh upstream metadata

Depends: none. Lane A.

- [x] 1.1 Update `UPSTREAM` to tree `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, record the three post-pin commits, and classify pstack versus advisor changes.
- [x] 1.2 Update root, Grok, Codex, Claude, and both marketplace manifests to `0.14.8-grokbuild.0`; keep Cursor packaging, logo, and advisor excluded. Depends on 1.1.
- [x] 1.3 Update the sync recipe to name the executable audit surfaces and the advisor exclusion. Depends on 1.1.

## 2. Write failing behavioral tests

Depends: 1.1. Lanes B, C, and D are independent after the metadata contract is understood.

- [x] 2.1 Add checker fixtures for a valid nested graph, unknown dependency, duplicate identifier, and dependency cycle. Depends on 1.1.
- [x] 2.2 Add a real `GhGitHubReader` missing-`gh` test that expects a retryable typed query failure. Depends on 1.1.
- [x] 2.3 Add a worktree-audit smoke fixture with a spaced worktree path, no `origin/main`, GNU `stat`, and `PSTACK_TRANSCRIPTS_DIR`. Depends on 1.1.
- [x] 2.4 Run the three new tests and record the expected red failures before production edits. Depends on 2.1, 2.2, and 2.3.

## 3. Implement executable behavior

Depends: 2.4. Lanes E, F, and G are independent.

- [x] 3.1 Extend `check-plan.mjs` with section identifiers, dependency parsing, duplicate and unknown-reference failures, DFS cycle detection, recursive depth output, and strict errors. Depends on 2.4.
- [x] 3.2 Add the `command-error` `QueryFailure` variant and normalize child-process spawn errors in `watch-pr/github.ts`. Depends on 2.4.
- [x] 3.3 Make `worktree-audit.sh` path-safe and conservative for missing base refs, explicit transcript roots, and GNU/BSD `stat` and date commands. Depends on 2.4.
- [x] 3.4 Add the checker and worktree tests to the existing Bun package test command. Depends on 3.1 and 3.3.

## 4. Update host contracts

Depends: 1.3, 3.1, 3.2, and 3.3.

- [x] 4.1 Document the identifier and `Depends on.` syntax in `multi-phase-plan.md` and update its skeleton to use it.
- [x] 4.2 Document the Codex executable inventory, `PSTACK_TRANSCRIPTS_DIR`, and non-Grok ownership in `codex-tools.md`.
- [x] 4.3 Extend the harness contract test for the current upstream pin, version lineage, executable inventory, and intentional exclusions.

## 5. Verify the change

Depends: 3.4 and 4.3.

- [x] 5.1 Run the focused Bun tests and strict watcher typecheck; confirm the new tests are green.
- [x] 5.2 Run `python3 scripts/verify-harness.py` and the focused Python harness/release tests.
- [x] 5.3 Run the sync pin/recipe commands and inspect that `--log` remains read-only.
- [x] 5.4 Run `openspec validate pstack-upstream-executable-surfaces --type change --strict` and review the complete diff for Cursor packaging, Grok local state, generated index files, and unrelated edits.
