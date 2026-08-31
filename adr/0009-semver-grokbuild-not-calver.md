# Plugin versions are SemVer plus grokbuild, not CalVer

- Status: accepted
- Date: 2026-08-31

## Context

`grok plugin tag` creates `v` plus `plugin.json` version. Cursor pstack is `0.14.5`. This port is `0.14.5-grokbuild.4`. Calendar versioning would drop the Cursor foreign key and would not unique-key two adapter bumps on one day. SemVer 2.0 treats a hyphen as prerelease. Build metadata after `+` is ignored for precedence.

## Decision

Versions MUST be `MAJOR.MINOR.PATCH-grokbuild.N`. They MUST NOT be calendar-only. Ship day belongs in GitHub Release notes. Existing tags MUST NOT be moved.

## Consequences

Adapter lineage stays in the tag name. Date is still visible on the Release. Next Cursor overlay bump becomes `0.15.0-grokbuild.0`, not `2026.8.31`.
