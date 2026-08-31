## 1. File contracts (TDD)

- [ ] 1.1 Fail then pass `tests/test_release.py`: script contains `grok --sandbox off plugin tag --push` and `git push origin`, still no `--force`, still `__GROK_INSIDE_BWRAP`, still `gh release view` and `--verify-tag`. Natives tag row names `grok --sandbox off plugin tag`. Workflow still has no `grok plugin tag`.

## 2. Script and docs

- [ ] 2.1 Update `scripts/release.sh` to call `grok --sandbox off plugin tag --push` and `git push origin` a local-only tag.
- [ ] 2.2 Update `docs/guide/13-grok-natives.md` and the HARNESS sandbox row so the grok tag argv includes `--sandbox off`.
- [ ] 2.3 Sync `openspec/specs/pstack-release-tag/spec.md` from this delta.

## 3. Prove and archive

- [ ] 3.1 `python3 tests/test_release.py` and `python3 tests/test_verify_harness.py`. Idempotent `./scripts/release.sh` on the current version exits 0 or documents the remaining host failure.
- [ ] 3.2 `openspec validate pstack-release-tag-host-push --type change --strict` then archive after implementation is on `main`.
- [ ] 3.3 Pin `grok-build-plugins` marketplace pstack sha to the new `origin/main` if that SHA moved.
