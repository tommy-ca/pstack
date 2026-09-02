## Why

`playbooks/orchestrate.md` still treats Graphite `gt` as the stack frontier source. The in-force `pstack-github-pr-fallback` spec already forbids requiring Graphite, but the forge-neutral pytest never reads that playbook, so CI stays green. The workflows guide still sends `capability_mode` on Rhai `agent()`, which the live Grok user-guide says is not a spawn argument and which would mis-state `pstack:how-explorer`'s YAML `execute` sandbox.

## What Changes

- Rewrite orchestrate stack-safety onto the existing forge-neutral `gh` / Origin map. Never require `gt`.
- Extend the forge-neutral pytest so a future `gt` requirement in orchestrate fails CI.
- Drop `capability_mode` from the `docs/guide/11-grok-workflows.md` `agent()` example. Keep `agent_type: "pstack:how-explorer"`.
- Replace babysit "cloud one plus a local one" with worktree versus shared-cwd wording.
- Do not delete Codex `orch` / `watch-pr`. Do not archive other changes. Do not update the installed host plugin. Do not commit.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pstack-github-pr-fallback`: name `orchestrate.md` as a retained stack playbook that MUST NOT require `gt`, and require the forge-neutral test to read that file.
- `pstack-grok-workflows`: require the Rhai `agent()` example to set `agent_type` `pstack:how-explorer` and to omit `capability_mode`.

## Impact

`skills/poteto-mode/playbooks/orchestrate.md`, `skills/poteto-mode/playbooks/babysit.md`, `docs/guide/11-grok-workflows.md`, `tests/test_verify_harness.py`, durable specs for the two capabilities above. No host plugin update. No new dependency.
