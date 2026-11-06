# Proposal: Three-source PStack semantic parity, November 2026

Status: proposed, source review only. Epic: [#906](https://github.com/tommy-ca/pstack/issues/906).

## Why
Keep the portable PStack implementation aligned with normative Cursor skill/playbook intent while selectively adopting newly tested semantics from michael-denyer/pstack-claude, without cross-harness process-management code, unearned proof claims, or duplicated control planes.

The prior cross-port design compared pstack-claude 0.9.95 (commit 88f6d39f) and its predecessor. Its newer main snapshot d88063f includes explicit Pi equivalence tests, scheduler model/mutations, and evolving host package/hook projections. The target already owns six-host portability schemas, verification generators, formal verification skills, and a project-local wiki; reuse them.

## Frozen evidence (2026-11-06)
- Normative upstream pstack-scoped latest commit: cursor/plugins@c742dd61706fbacc1b95f1a20b7b988cf096ce6c (2026-10-27, version 0.15.36). No newer pstack-path commit appeared in the consulted GitHub history.
- Reference comparator: michael-denyer/pstack-claude@d88063f3355a5ecff0e6dbb890a11bab4b08bc2e (2026-11-05); its tools/upstream.json pins upstream c742dd6.
- Target audit base: tommy-ca/pstack@5d58283f40f7fc8f56a536946abe79418538fe6e.
- Target's applied UPSTREAM and pstack.package.json pin remains 88d47514b82e7c44f00f2b2a72ff6dd12158038c; completed semantic upstream program #840 deliberately did not imply a release pin bump.
- Comparator commit range from 88f6d39f to d88063f: GitHub compare reports 86 commits; API returned a truncated 300-file list. Do not claim exhaustiveness from that compare alone.

## Requirements
1. Preserve Cursor intent as normative; distinguish comparator policy forks, host-only mechanisms, reusable postconditions and excluded features.
2. Bind each adoption candidate to source revision, file path, target owner, consequence, negative test, evidence tier and reversible decision.
3. Reuse existing skills/create-verification-skill, skills/create-formal-verification-skill, native adapters, schemas, evidence receipts and OpenSpec.
4. Model Pi/Claude/Codex/Kimi/Muse/Copilot differences in host-local mappings; never infer a seventh declared target host from comparator coverage.
5. Expose explicit blocked/unverified states; static review is not live runtime behavior or independently performed multi-model review.
6. Use the existing .llm-wiki as source-attributed analysis; only write-once ingest can claim local immutable raw provenance.

## Scope
Source-pinned research, semantic decisions, incremental skill creation guidance, executable negative-test follow-ups, code-linked bounded formal requirements and additive wiki analysis. Issues #907–#911 capture separate work; the current PR may implement only the documentation/skill-instruction slice.

## Out of scope
Copying the comparator Pi RPC supervisor, scheduler, hooks, generated model aliases or declared policy forks into the shared runtime; changing existing released host_targets; claiming TLC or real Pi execution without checker/CLI receipts; merging this change automatically.

## Acceptance and rollback
OpenSpec proposal/spec/design match existing contracts; no legacy authority rewritten; wiki analysis is labeled source-only and indexed; generator guidance remains scaffold-compatible. Revert the change/skill edits without modifying shipped host packages. Runtime/independent proof gates tracked under #908/#909/#911.
