## Why

Tag `v0.14.7-grokbuild.0` already points at `420f4ec` and GitHub already has that Release. `origin/main` is six signed commits ahead with adapter contracts that never shipped. Retagging `.0` is forbidden. The next ship must increment the grokbuild counter.

## What Changes

- Audit `420f4ec..HEAD` as the unreleased unit. Keep the six signed commits. Do not rewrite history.
- Bump the six tracked version surfaces from `0.14.7-grokbuild.0` to `0.14.7-grokbuild.1`.
- Update the `This port` line in `UPSTREAM` so the overlay test still matches root.
- Land that bump on `origin/main` with a signed Conventional Commit.
- Run `scripts/release.sh` from a host shell so `grok --sandbox off plugin tag --push` creates `v0.14.7-grokbuild.1` and GitHub converges to a Release.
- Leave `v0.14.7-grokbuild.0` on `420f4ec`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-release-tag`: when HEAD has adapter work past an existing `vMAJOR.MINOR.PATCH-grokbuild.N` tag, the next release increments `N` instead of moving that tag.

## Impact

Root `plugin.json`, `.grok-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `.agents/plugins/marketplace.json`. `scripts/release.sh` and `release.yml` stay as they are. Host plugin install and catalog sibling pins stay out of this change.
