# Refresh hygiene

Refresh hygiene reports leftover overlay caches and stale skills as TSV, prints a host `cp --` command that writes nothing, and never copies into live `~/.grok/skills`.

## Sub-features

- `hygiene-dry-run` prints `kind\taction\tpath\tnote` TSV and does not delete the primary overlay cache.
- `hygiene-host-script` prints `cp -- <git-tracked SKILL.md> <tmp dest>` and writes no dest file.
- `hygiene-packaged-lever` runs `python3 skills/swarm/scripts/verify-refresh-hygiene.py` and exits 0.
- `hygiene-live-untouched` leaves `~/.grok/skills/reflect` unchanged.

## How to get to it (user POV)

- From the plugin checkout, run `python3 skills/swarm/scripts/refresh-hygiene.py --root . --skills <tmp>/skills`.
- Run the same command with `--host-script` and the same tmp `--skills`.
- Run `python3 skills/swarm/scripts/verify-refresh-hygiene.py`.
- Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature refresh-hygiene`.

## Driving it with verify.py

Preconditions:

- Leftover scanner printed `PASS` for this run.
- `uv` is on `PATH` for the packaged hygiene lever.
- `--skills` is `/tmp/verify-pstack-scratch-<runid>/skills`, not `~/.grok/skills`.

- **Doctor first.** If this run has no leftover `PASS` yet, run `python3 skills/verify-pstack/scripts/verify.py doctor --root .`.
- **Drive hygiene.** Run `python3 skills/verify-pstack/scripts/verify.py drive --root . --feature refresh-hygiene`. Exit code `0`.
- **Dry-run TSV.** Evidence dry-run stdout starts with `kind\taction\tpath\tnote`. Exit code is `0` or `2`. Exit `2` is fail-closed nested would-delete. It is not a missing TSV.
- **Host script.** Evidence host-script stdout starts with `cp -- `. Exit code `0`. Dest path is under `/tmp/verify-pstack-scratch-<runid>/`. Dest file does not exist after the command. Dest path does not contain `/.grok/skills/`.
- **Packaged lever.** Evidence for `verify-refresh-hygiene.py` has exit `0`.
- **Proof.** `~/.grok/skills/reflect` fingerprint matches the pre-drive snapshot. Scratch dest `skills/reflect/SKILL.md` was not created by `--host-script`.

## Gotchas

- Default `--skills` is `~/.grok/skills`. Live `reflect` may be a symlink. Always pass tmp `--skills`.
- Do not pass `--apply-skills`. Do not chmod overlay dests when a copy hits EPERM.
- `--host-script` dest is the overlay path under `--skills`, not `~/.agents`.
- Do not `git worktree remove` leftover-worktree rows. OPEN PR worktrees stay. TSV `report` is not delete permission.
- Do not delete the primary overlay cache. Dry-run `nested-cache keep` is the keep.
- `--apply` deletes nested overlay clones. Verify drives dry-run and `--host-script` only.
- Do not write `~/.grok/skills`. Cleanup must not remove evidence while removing the scratch `--skills` dir.
