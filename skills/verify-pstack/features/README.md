# pstack verification map

This directory is the maintained source for verifying the operator-facing behavior of the pstack Grok plugin. Read the index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- cwd is a pstack plugin checkout. `plugin.json` name is `pstack`.
- `python3` and `grok` are on `PATH`. Do not run `mise use -g`.
- Run `python3 skills/verify-pstack/scripts/verify.py doctor --root .` and require leftover-scanner `PASS` plus `Plugin manifest is valid.`
- Evidence goes to `/tmp/verify-pstack-evidence-<runid>/`. Scratch goes to `/tmp/verify-pstack-scratch-<runid>/`.
- Never drive until leftover scanner printed `PASS` in this run's doctor log.

## Driving conventions

- Start every recipe from the baseline unless its preconditions say otherwise.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run operator CLIs through `verify.py`. Do not substitute `grok inspect` or `pytest` for leftover scanner.
- Hygiene `--skills` is always the scratch directory. Never the default `~/.grok/skills`.
- Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the command, stdout, stderr, and exit code.
- Mutation proof includes a second read of live dest. Hygiene must leave `~/.grok/skills/reflect` unchanged.
- Record the feature ID with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with verify.py` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Leftover Cursor harness scan](./leftover-scanner.md) covers `scripts/verify-harness.py` as required doctor and as a driveable operator check.
- [Upstream pin](./upstream-pin.md) covers `scripts/sync-from-upstream.py --pin` against the `UPSTREAM` tree line.
- [Refresh hygiene](./refresh-hygiene.md) covers dry-run TSV, `--host-script` with tmp `--skills`, and `verify-refresh-hygiene.py`.
- [Release tag contract](./release-tag.md) covers `tests/test_release.py` and refuses nested `scripts/release.sh`.
