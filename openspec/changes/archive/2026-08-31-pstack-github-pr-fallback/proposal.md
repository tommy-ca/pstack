## Why

Official pstack playbooks assume Graphite (`gt`). This host has `gh` and no `gt`. HARNESS already says gt is optional, but it does not name the GitHub-native call sites. Agents still copy `gt submit --merge-when-ready` from playbooks.

## What Changes

- Add grok-native `skills/poteto-mode/references/github-pr-fallback.md`. It is not an upstream playbook file.
- HARNESS Graphite row points at that map: `command -v gt` then `gt`, else `gh` plus git.
- Tests lock the file and the HARNESS pointer.
- Do not edit `playbooks/*.md` or the cursor/plugins cache.

## Capabilities

### New Capabilities

- `pstack-github-pr-fallback`: when `gt` is missing, land with GitHub-native `gh pr` commands. Playbook intent stays. The CLI is `gh`.

### Modified Capabilities

None.

## Impact

`HARNESS.md`, `skills/poteto-mode/references/github-pr-fallback.md`, `tests/test_verify_harness.py`. Not `playbooks/`. Not `.worktrees/upstream-cursor-plugins`.
