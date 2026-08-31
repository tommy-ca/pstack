## 1. File contracts (TDD)

- [x] 1.1 Fail then pass `tests/test_release.py` for dual-writer: both `scripts/release.sh` and `.github/workflows/release.yml` contain `gh release view` and `gh release create` with `--verify-tag`, neither contains `--force` or `workflow_dispatch`, the workflow does not contain `grok plugin tag`, the script contains `__GROK_INSIDE_BWRAP`, natives name `grok plugin tag` and `grok --sandbox off` and do not contain `wait-for-release`.

## 2. Writers

- [x] 2.1 Update `scripts/release.sh`: refuse nested bwrap, validate, `grok plugin tag --push`, then `gh release view` or `gh release create --verify-tag --generate-notes`.
- [x] 2.2 Update `.github/workflows/release.yml` to `gh release view || gh release create --verify-tag --generate-notes`. Keep `on.push.tags: v*` and `contents: write`. Do not add grok or `workflow_dispatch`.
- [x] 2.3 Update `docs/guide/13-grok-natives.md` and the HARNESS sandbox row so tagging names host-shell `grok --sandbox off`.

## 3. Prove on origin

- [x] 3.1 After the writers are on `origin/main`, bump `plugin.json` to `0.14.5-grokbuild.4` and land that commit.
- [x] 3.2 From a host shell run `./scripts/release.sh`. Confirm `gh run list --workflow=release.yml` is non-empty and the GitHub Release for `v0.14.5-grokbuild.4` exists.
- [ ] 3.3 Pin `grok-build-plugins` marketplace pstack sha to that pstack HEAD. `python3 tests/test_marketplace.py`. `grok --sandbox off plugin update pstack` and `plugin marketplace update grok-build-plugins`.

## 4. Archive

- [x] 4.1 `openspec validate pstack-release-actions-proof --type change --strict` then archive after implementation is on `main`.
