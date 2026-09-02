## Context

`v0.14.7-grokbuild.0` is a published tag at `420f4ec` with a GitHub Release. `origin/main` is six signed commits ahead. ADR-0009 forbids moving tags. The lockstep test already compares six tracked version surfaces to root `plugin.json` without pinning a historical literal.

In-force ADRs that constrain this design: 0003, 0004, 0005, 0007, 0008, 0009, 0010, 0011. ADR-0001 and ADR-0002 are superseded. ADR-0006 is superseded by ADR-0008.

## Goals / Non-Goals

**Goals:**

- Keep the six unreleased commits. Do not rewrite them.
- Bump adapter counter `0` to `1` on the same Cursor `0.14.7` base.
- Tag and Release `v0.14.7-grokbuild.1` through the existing host-shell script.

**Non-Goals:**

- Moving `v0.14.7-grokbuild.0`.
- Changing SemVer grammar or catalog sibling identity.
- Updating the installed host plugin.
- Opening a pull request. This ships from `main`.
- Splitting `481091d` even though that commit bundled three test concerns.

## Decisions

**Keep the pushed history.** The unreleased range is already on `origin/main` and SSH-signed. Rewriting it would need a force-push. The only atomicity nit is `481091d` bundling tests for three landed concerns. That is a review note, not a ship blocker.

**Bump N, then run the existing script.** Do not add a second tagger. `scripts/release.sh` already validates, tags without `--force`, pushes the tag, and converges the GitHub Release. Nested grok still cannot be the tagger.

**One lockstep commit for the six version strings.** The schema test treats them as one identity. Splitting them would fail the test between commits.

**OpenSpec records the increment rule.** The durable spec already said not to move tags. This change adds the missing increment-N scenario so the next ship does not retag under time pressure.

## Risks / Trade-offs

- [HTTPS `git push` asks for a username] -> Use the SSH URL the way the last origin sync did. Do not change `git config`.
- [`grok plugin tag` fails inside bwrap] -> Run `scripts/release.sh` from a host shell. The script already fails closed when `__GROK_INSIDE_BWRAP` is set.
- [Actions and the local script both try to create the Release] -> First writer wins. The other path no-ops when `gh release view` succeeds.

## Migration Plan

1. Land OpenSpec artifacts and the six-file version bump on `main`.
2. Push.
3. Run `./scripts/release.sh`.
4. Prove `v0.14.7-grokbuild.1` on origin and on GitHub. Prove `v0.14.7-grokbuild.0` still at `420f4ec`.
5. Rollback is "do not run the script again with `--force`". A bad bump commit reverts on `main` before tagging. After the tag exists, leave it.

## Open Questions

None. No in-force ADR needs supersession.
