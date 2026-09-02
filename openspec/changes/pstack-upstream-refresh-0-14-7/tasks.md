## 1. Record the upstream source

- [ ] 1.1 Update `UPSTREAM` to tree `efa2a531985e0a8084d36ff3cf87233be8a9f34b` and record the three commits after the old pin.
- [ ] 1.2 Update `scripts/sync-from-upstream.py` recipe text with the explicit host-owned and Cursor-only exclusions.
- [ ] 1.3 Update `TEST-PLAN.md` to use the refreshed upstream pin and preserve the adapter verification commands.

## 2. Port shared skill guidance

- [ ] 2.1 Port applicable Fable 5.1/default wording from upstream into the retained adapted skills without replacing Grok role mappings.
- [ ] 2.2 Add `disable-model-invocation: true` to `how`, `typescript-best-practices`, `unslop`, and `why` skill frontmatter.
- [ ] 2.3 Add TypeScript `paths` coverage and schemas-before-hand-rolled-guards guidance with the upstream Zod example.

## 3. Port forge-neutral playbooks

- [ ] 3.1 Update `poteto-mode`, `autopilot-full`, and `autopilot-stack` to resolve `gh`/Origin once and use explicit parent-base stacks.
- [ ] 3.2 Update `multi-phase-plan` with regression and dual-sided performance lanes while retaining Grok fanout and scheduler boundaries.
- [ ] 3.3 Update `babysit`, `shipping`, and `opening-a-pr` to use direct forge landing rules and one-PR-at-a-time stack safety.
- [ ] 3.4 Update `references/bugbot-triage.md` and the retained fallback reference to remove Graphite prerequisites without deleting Codex compatibility utilities.

## 4. Reconcile adapter documentation and contracts

- [ ] 4.1 Update `HARNESS.md`, both READMEs, and guides 06, 07, and 12 to remove stale Graphite-first claims.
- [ ] 4.2 Update root, Grok, Codex, Claude, and Claude marketplace manifests to `0.14.7-grokbuild.0` without adding Cursor-only packaging.
- [ ] 4.3 Update `tests/test_verify_harness.py` to assert forge-neutral landing, retained Grok wakes, refreshed sync evidence, and the `make-bot-ui` exclusion.

## 5. Verify the refresh

- [ ] 5.1 Run `python3 scripts/sync-from-upstream.py --pin`, `--recipe`, and `--log` and verify the cache `HEAD` equals `origin/main`.
- [ ] 5.2 Run `python3 scripts/verify-harness.py`, `python3 tests/test_verify_harness.py`, and `python3 tests/test_release.py`.
- [ ] 5.3 Run `openspec validate pstack-upstream-refresh-0-14-7 --type change --strict`.
- [ ] 5.4 Review the final diff for host-boundary regressions, excluded Cursor-only files, and unrequested release or remote mutations.
