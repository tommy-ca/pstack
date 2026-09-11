# Release tag contract

Release-tag verify proves `scripts/release.sh` tags with `grok plugin tag` and `gh release` on `v*` without `--force`, and that `plugin.json` version is SemVer `MAJOR.MINOR.PATCH-grokbuild.N`.

## Sub-features

- `release-script-contract` requires `grok plugin validate`, `grok --sandbox off plugin tag --push`, HTTPS `git push` fallback, `gh release create --verify-tag`, and `__GROK_INSIDE_BWRAP` refuse, with no `--force`.
- `release-workflow-vstar` requires `.github/workflows/release.yml` on `v*` without `grok plugin tag`.
- `release-version-grokbuild` requires `plugin.json` version `N.N.N-grokbuild.N`, not CalVer, not `-pstack.N`.
- `release-nested-refuse` does not run `scripts/release.sh` to completion inside nested grok.

## How to get to it (user POV)

- From the plugin checkout, run `python3 tests/test_release.py`.
- Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature release-tag`.
- From a host shell, after tests pass, an operator may run `scripts/release.sh`. Nested grok is not that path.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.
- `python3` is on `PATH`.
- `__GROK_INSIDE_BWRAP` may be set. Drive tests anyway. Do not run `scripts/release.sh`.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Drive the contract tests.** Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature release-tag`. Exit code `0`. Wrapper stdout is `PASS release-tag`. Evidence stdout contains `PASS tests/test_release.py`.
- **Direct CLI.** Run `python3 tests/test_release.py`. Exit code `0`. Stdout contains `PASS tests/test_release.py`.
- **Proof.** Read `features/release-tag/stdout.txt` and `features/release-tag/cmd.txt`. Evidence argv is `sys.executable` plus `tests/test_release.py`, not the literal `python3 tests/test_release.py`. Evidence argv does not contain `scripts/release.sh`. Evidence stdout is not `grok plugin tag` creating a tag.

## Gotchas

- Nested grok cannot write `.git/refs/tags`. `scripts/release.sh` exits 1 when `__GROK_INSIDE_BWRAP` is set. Do not run it to completion from this TUI.
- Host tagging is `grok --sandbox off plugin tag --push`, then the script's `gh` HTTPS fallback. Do not rewrite `origin` to HTTPS.
- Existing tags must not be moved. The tests forbid `--force`.
- Version is adapter SemVer `*-grokbuild.N`. Catalog `*-pstack.N` and CalVer fail the contract.
