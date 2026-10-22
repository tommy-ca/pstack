# Release tag contract

The `release-tag` drive checks `plugin.json` version metadata. It also compares that version with the packaging version printed by the read-only `sync-from-upstream.py --recipe` command.
The drive does not exercise tagging, pushing, GitHub release creation, or runtime nested-grok refusal. A passing run cannot establish any of those behaviors.

## Sub-features

- `release-version-prerelease` checks that `plugin.json` uses `N.N.N-<neutral-label>.N`, not CalVer and not `-pstack.N`.
- `release-port-base` runs the read-only `sync-from-upstream.py --recipe` command and checks that the `plugin.json` version uses its packaging base and a neutral prerelease suffix.

## How to get to it (user POV)

- From the plugin checkout, run `python3 tests/test_release.py`.
- Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature release-tag`.
- From a host shell, an operator may run `scripts/release.sh` after tests pass. Do not run it from nested grok.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.
- `python3` is on `PATH`.
- `__GROK_INSIDE_BWRAP` may be set. Drive tests anyway. Do not run `scripts/release.sh`.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 .grok/skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Drive the contract tests.** Run `python3 .grok/skills/verify-pstack/scripts/verify.py drive --root . --feature release-tag`. Exit code `0`. Wrapper stdout is `PASS release-tag`. Evidence stdout contains `PASS tests/test_release.py`.
- **Direct CLI.** Run `python3 tests/test_release.py`. Exit code `0`. Stdout contains `PASS tests/test_release.py`.
- **Proof.** Read `features/release-tag/stdout.txt` and `features/release-tag/cmd.txt`. Evidence argv is `sys.executable` plus `tests/test_release.py`, not the literal `python3 tests/test_release.py`. Evidence argv does not contain `scripts/release.sh`. The output records metadata and recipe checks only. It records no release actions or nested refusal.

## Gotchas

- `scripts/release.sh` exits with code 1 before release work when `__GROK_INSIDE_BWRAP` is set. This source guard is not checked by the drive. Do not run the script from nested grok.
- On a host, `scripts/release.sh` runs `grok --sandbox off plugin tag --push`. If that command fails, the script uses the HTTPS `git push` fallback. The script does not use `--force`, but the drive does not check these rules. Do not rewrite `origin` to HTTPS.
- The release policy forbids moving existing tags. The drive does not check that policy.
