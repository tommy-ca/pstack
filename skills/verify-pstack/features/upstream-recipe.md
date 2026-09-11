# Upstream refresh recipe

Upstream recipe prints the operator steps for refreshing this port from official Cursor pstack. It does not copy files and does not fetch the overlay cache.

## Sub-features

- `recipe-print` prints the numbered recipe and exits 0.
- `recipe-names-doctor` names `verify.py doctor` and the leftover scanner.
- `recipe-no-fetch` does not pass `--log` on the recipe drive.

## How to get to it (user POV)

- From the plugin checkout, run `python3 scripts/sync-from-upstream.py --recipe`.
- Run `python3 scripts/sync-from-upstream.py` with no flags. That is the same print.
- Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-recipe`.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Print recipe.** Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature upstream-recipe`. Exit code `0`. Evidence stdout names `--pin`, `--log`, `adapt-harness.py`, `verify.py doctor`, `Full sweep`, `verify-harness.py`, and `verify.py drive`.
- **Direct CLI.** Run `python3 scripts/sync-from-upstream.py --recipe`. Exit code `0`. Stdout matches the evidence file.
- **Proof.** Read `features/upstream-recipe/stdout.txt`. The command argv contains `--recipe` and does not contain `--log`.

## Gotchas

- `--log` fetches `origin/main` into the primary overlay cache. Recipe drive does not fetch.
- `--pin` is a different mapped feature. Recipe stdout includes the pin SHA. That is not pin proof.
- Pytest `tests/test_verify_harness.py` is not leftover doctor. Recipe step 5 is `verify.py doctor` then Full sweep drive.
- `apply.py` copies. This feature does not run it.
