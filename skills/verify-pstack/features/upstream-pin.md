# Upstream pin

Upstream pin prints the official Cursor pstack tree SHA recorded in `UPSTREAM` so an operator can see which upstream commit this grok port is pinned to.

## Sub-features

- `pin-print` prints one 40-hex SHA and exits 0.
- `pin-matches-upstream` matches the `tree <40-hex>` line in `UPSTREAM`.
- `pin-no-fetch` does not clone or fetch the upstream cache.

## How to get to it (user POV)

- From the plugin checkout, run `python3 scripts/sync-from-upstream.py --pin`.
- Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-pin`.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.
- `UPSTREAM` exists at the plugin root and contains a `tree` line.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Print pin.** Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-pin`. Exit code `0`. Stdout is one 40-hex SHA.
- **Direct CLI.** Run `python3 scripts/sync-from-upstream.py --pin`. Exit code `0`. Stdout equals the SHA in `UPSTREAM`.
- **Proof.** Read `features/upstream-pin/stdout.txt`. The trimmed text matches `[0-9a-f]{40}` and appears on the `tree` line of `UPSTREAM`. The command argv contains `--pin` and does not contain `--log`.

## Gotchas

- `--log` fetches `origin/main` into the overlay cache. Pin verify does not fetch.
- `--recipe` prints operator steps. It is not pin proof.
- A short SHA from `git rev-parse --short` is not the pin. Require 40 hex.
- Relative cache paths resolve on the primary checkout. Pin print does not need `--cache`.
