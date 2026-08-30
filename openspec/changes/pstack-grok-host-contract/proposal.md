## Why

Research, review, and live grok 1.0.13 inspect showed three host-contract bugs. The bilingual README interleaved Chinese and English and drifted (`task` vs `spawn_subagent`). Plugin agents exist on disk but spawn failed: the plugin was trusted, not in `[plugins].enabled`, and when enabled the CLI registers `pstack:how-explorer` not `how-explorer`. `inspect` `plugins[].enabled` is trust. `provides.agents` is a directory count (1), not 22 files.

## What Changes

- English `README.md` plus `README.zh-CN.md` with a reciprocal switcher.
- Playbooks and HARNESS spawn `pstack:<role-key>`. Setup writes `~/.grok/roles/pstack:<key>.toml`.
- Docs: enable from a host shell (`grok --sandbox off plugin enable pstack` when EROFS). Spawn the qualified name.
- TEST-PLAN Gate 1 reads `.agents[]` names, not `provides.agents`.

## Capabilities

### New Capabilities

- `pstack-grok-host`: Grok Build install, enable, and spawn-type contract for this plugin.

### Modified Capabilities

None.

## Impact

- `/home/tommyk/projects/pstack` skills, HARNESS, READMEs, TEST-PLAN, harness scanners.
- Catalog pin in `tommy-ca/grok-build-plugins` after this lands on pstack `main`.
