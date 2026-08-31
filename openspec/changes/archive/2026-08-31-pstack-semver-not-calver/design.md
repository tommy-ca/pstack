## Context

Investigation plus how-critique: CalVer or SemVer-with-date as uniqueness is a data-model lie. pstack’s key is adapter-of-Cursor. SemVer 2.0 prerelease (`0.14.5-grokbuild.N`) is lower precedence than upstream `0.14.5`. That is honest. Creative Commons left CalVer because YYYY looks like a huge major. Date is already on the GitHub Release.

## Goals / Non-Goals

**Goals:** Spec and tests name the grammar. Reject CalVer as identity.

**Non-Goals:** Version bump. Retag. CalVer. Putting YYYYMMDD in build metadata as uniqueness (SemVer ignores `+` for precedence).

## Decisions

Keep `MAJOR.MINOR.PATCH-grokbuild.N`. N is not a date. `--generate-notes` already records when.

## Risks / Trade-offs

Hyphen means SemVer prerelease. Consumers that skip prereleases will skip this port versus a hypothetical `0.14.5`. That is the intended “not upstream” signal.

## Migration Plan

Land spec and tests. Do not retag `v0.14.5-grokbuild.4`.

## Open Questions

None.
