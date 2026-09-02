## 1. Lockstep regression contract

- [ ] 1.1 Extend `tests/test_verify_harness.py` to compare the six tracked pstack manifest/index version fields against root `plugin.json` without hardcoding a release version.
- [ ] 1.2 Run the focused manifest test before metadata repair and capture the failure for the stale `.agents/plugins/marketplace.json` value.

## 2. Metadata repair

- [ ] 2.1 Update only `.agents/plugins/marketplace.json` so its `pstack` entry uses the root adapter version `0.14.7-grokbuild.0`.
- [ ] 2.2 Preserve host-specific manifest shapes and confirm no sibling-repository, installed-host, release, tag, or remote state changes occur.

## 3. Verification and specification sync

- [ ] 3.1 Run `python3 scripts/verify-harness.py`, `uv run --with pytest pytest -q tests/test_verify_harness.py`, `python3 tests/test_release.py`, and `grok plugin validate .`.
- [ ] 3.2 Run `openspec validate pstack-manifest-lockstep --type change --strict` and review the final diff for version-scope drift.
- [ ] 3.3 Sync the `pstack-plugin-schema` delta into the durable main specification after implementation verification.
- [ ] 3.4 Commit the metadata, test, and specification changes as semantic atomic work without performing release, tag, push, or archive actions.
