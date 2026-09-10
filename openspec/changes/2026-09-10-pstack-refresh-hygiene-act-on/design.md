## Context

In-force ADRs: 0005, 0007, 0008. PR 12 already ships `refresh-hygiene.py`. Interrogate at head `2e1e3b6` found fail-open apply-skills, fail-open `--apply` error exit, unproven `--log` bind, and a redundant cwd-mutating coverage test.

## Goals / Non-Goals

**Goals:**

- Fail-close `--apply-skills` and `--apply` error rows.
- Prove `--log` from a linked-worktree copy of the script.
- Keep decoy coverage as the only relative-cache CLI proof.
- Ship a lever verification script.

**Non-Goals:**

- Do not write `~/.grok/skills` from this TUI.
- Do not `git worktree remove`.
- Do not leftover-scanner phrase work.
- Do not add `mise.toml`.
- Do not archive `pstack-upstream-executable-surfaces`.

## Decisions

### Claude-shape plus symlink parent, not refuse default dest

`--host-script` must still print the default overlay dest. `--apply-skills` copies only when dest is claude-shaped and has no symlink parent. Alternative rejected: refuse all default `~/.grok/skills` dests. That would break the printed `cp` pairing.

### Inline git-common-dir for sync `--log`

`--pin`/`--recipe` stay partition-free. `--log` uses a local `primary_checkout_root` (same 20-line helper), not `exec_module` of `partition.py`. Alternative rejected: keep importlib of the full classifier.

### Delete the live coverage cwd test

`test_print_coverage_decoy_nested.py` is the proof. The live `chdir(ROOT)` test cannot plant a decoy and couples to this machine's overlay.

## Risks / Tradeoffs

`--apply` exit 2 on error changes a test that currently asserts exit 0. Callers using `&&` start seeing failures they previously missed. That is the point.
