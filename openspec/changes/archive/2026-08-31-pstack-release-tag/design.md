## Context

`grok plugin tag --dry-run .` would create `v0.14.5-grokbuild.3`. No tags exist. GHA has no grok binary. Catalog tagging is a later phase (sibling version collision).

## Goals / Non-Goals

**Goals:** Local lever to tag. Remote job to publish a GitHub Release. Docs match.

**Non-Goals:** Auto-tag on every main push. Catalog pin job. Sibling tags. `--force`. Installing grok in Actions.

## Decisions

1. **Tag locally with grok.** The CLI owns the tag name from `plugin.json`.
2. **Release remotely with gh.** Actions on `v*` only needs `contents: write`.
3. **File-only CI test.** Full `test_verify_harness.py` calls `grok plugin validate` and may fetch. Actions runs `tests/test_release.py` instead.

## Risks / Trade-offs

- [Operator tags without running tests] -> `release.sh` runs `python3 tests/test_verify_harness.py` first. Nested `--log` fetch can fail off-network; script still requires validate.

## Migration Plan

Land this change. Then from a clean main: `./scripts/release.sh`. First tag is `v0.14.5-grokbuild.3`.

## Open Questions

None.
