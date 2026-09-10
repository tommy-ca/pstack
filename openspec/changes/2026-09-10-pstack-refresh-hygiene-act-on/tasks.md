## 1. Apply-skills fail-closed

Depends: none. Lane A.

- [x] 1.1 Gate `--apply-skills` on claude-shaped dest and `has_symlink_parent`.
- [x] 1.2 Pytest: symlink parent is `eperm`, grok-shaped dest is not-stale, dest bytes unchanged.

## 2. Apply error exit

Depends: none. Lane B.

- [x] 2.1 `--apply` exit 2 when any nested-cache row is `action=error`.
- [x] 2.2 Update `test_apply_collects_then_records_error_and_still_present` to expect 2.

## 3. Sync log bind proof

Depends: none. Lane C.

- [x] 3.1 Inline `primary_checkout_root` in `sync-from-upstream.py`. `--pin`/`--recipe` do not load partition.
- [x] 3.2 Load a tmp linked-worktree copy of the script and assert `remote_cache()` is primary.

## 4. Coverage tests

Depends: none. Lane D.

- [x] 4.1 Delete `test_print_coverage_relative_cache_uses_primary`.
- [x] 4.2 Keep `test_print_coverage_decoy_nested.py`.

## 5. Lever verification

Depends: 1.2, 2.2, 3.2, 4.1.

- [ ] 5.1 Add `skills/swarm/scripts/verify-refresh-hygiene.py` that runs the hygiene pytest slice and CLI dry-run.
- [ ] 5.2 Run `python3 scripts/verify-harness.py` and `uv run --with pytest pytest -q tests/test_refresh_hygiene.py tests/test_print_coverage_decoy_nested.py`.
