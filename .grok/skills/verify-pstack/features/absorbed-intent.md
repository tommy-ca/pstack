# Absorbed intent

Absorbed intent fails when pstack commits exist after the tree line in `UPSTREAM`, or when a named absorbed sentence is missing or a forbidden sentence is back. It passes when that range is empty and the sentences match.

## Sub-features

- `commits-after-pin` fails when the supplied commit list is non-empty, or when `git log <pin>..HEAD -- pstack` in a cache is non-empty.
- `intent-lines` requires the overnight round sentence, the plan-lane regex, the log append, and the host markers that this port keeps.
- `forbidden-lines` fails when the nit-pad sentence, the deleted outcome bullet, or a bare `"version": "0.15.5"` is present.
- `pin-no-fetch` does not fetch. Currency is the recorded tree line plus the commits the caller already has.

## How to get to it (user POV)

- From the plugin checkout, run `python3 .grok/skills/verify-pstack/scripts/absorbed.py check --root . --commits-file <file>`.
- On a machine that already has the upstream cache, run `python3 .grok/skills/verify-pstack/scripts/absorbed.py check --root . --cache .worktrees/upstream-cursor-plugins`.
- Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature absorbed-intent`.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.
- `UPSTREAM` contains one `tree <40-hex>` line.
- `.worktrees/upstream-cursor-plugins` exists and its `HEAD` is the upstream commit the operator already fetched. This drive does not fetch.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Drive.** Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature absorbed-intent`. Exit code `0`. Wrapper stdout is `PASS absorbed-intent`. Evidence `features/absorbed-intent/stdout.txt` contains `PASS absorbed-intent`. The command argv contains `--cache` and does not contain `--log` or `fetch`.
- **Stale sample.** Run `python3 .grok/skills/verify-pstack/scripts/absorbed.py check --root . --commits-file <file>` with a non-empty file, or with an empty file against a tree that lacks `starts a round at the owner`. Exit code is non-zero. Stdout names `pstack commits after pin` or `missing`.
- **Proof.** A pass is an empty commit range after the recorded tree line together with the named lines. The tip SHA is not hardcoded in the checker.

## Gotchas

- `--log` fetches. This feature does not run it. Do not add the commit walk to `upstream-pin`.
- An empty `--commits-file` means the caller claims there are no commits after the pin. That is the CI path. It does not read the gitignored cache.
- `--cache` runs `git log <pin>..HEAD -- pstack` and does not fetch. A cache left on an old `HEAD` can hide later upstream commits.
- `plugin.json` stays `0.15.5-grokbuild.0`. A bare `"version": "0.15.5"` fails this check.
