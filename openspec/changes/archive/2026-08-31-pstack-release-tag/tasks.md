## 1. Tests first

- [x] 1.1 Fail then pass `tests/test_release.py`: workflow on `v*`, `gh release create`, no `grok plugin tag` in Actions, `scripts/release.sh` calls `grok plugin tag --push` without `--force`, natives page names the command.

## 2. Files

- [x] 2.1 Add `scripts/release.sh` and `.github/workflows/release.yml`. Update `docs/guide/13-grok-natives.md`.

## 3. Prove

- [x] 3.1 `python3 tests/test_release.py`. `openspec validate pstack-release-tag --type change --strict`.
