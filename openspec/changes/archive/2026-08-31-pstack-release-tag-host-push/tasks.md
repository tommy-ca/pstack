## 1. File contracts (TDD)

- [x] 1.1 Fail then pass `tests/test_release.py`: script contains `grok --sandbox off plugin tag --push` and `git push origin`, still no `--force`, still `__GROK_INSIDE_BWRAP`, still `gh release view` and `--verify-tag`. Natives tag row names `grok --sandbox off plugin tag`. Workflow still has no `grok plugin tag`.

## 2. Script and docs

- [x] 2.1 Update `scripts/release.sh` to call `grok --sandbox off plugin tag --push` and `git push origin` a local-only tag.
- [x] 2.2 Update `docs/guide/13-grok-natives.md` and the HARNESS sandbox row so the grok tag argv includes `--sandbox off`.
- [x] 2.3 Sync `openspec/specs/pstack-release-tag/spec.md` from this delta.

## 3. Prove and archive

- [x] 3.1 `python3 tests/test_release.py` and `python3 tests/test_verify_harness.py`. Idempotent `./scripts/release.sh` on the current version exits 0 or documents the remaining host failure.
- [x] 3.2 `openspec validate pstack-release-tag-host-push --type change --strict` then archive after implementation is on `main`.
- [x] 3.3 Review external follow-up. Original action: if the pstack SHA moved, pin the `grok-build-plugins` marketplace pstack SHA to the new `origin/main`. Outcome: deferred. Reason: the marketplace checkout and installed-host mutations were outside this pstack change and were not executed. Follow-up: `/home/tommyk/projects/grok-build-plugins/.grok-plugin/marketplace.json` requires separately authorized review and update.
