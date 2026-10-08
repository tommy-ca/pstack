# Decision routing registry

`decision-routing.json` is the canonical, provider-neutral inventory for the playbooks in the official pstack source tree. Each route records the playbook name, its source blob hash, and one selection mode. Semantic candidates also carry one closed class label. The JSON owns the rows; this document records how to read them and where the source came from.

## Interpretation

`direct` marks an explicit command or deterministic trigger. Those routes bypass semantic classification. `system_two` keeps route choice with the existing pstack judgment path. `semantic_candidate` allows a bounded semantic result to suggest only the listed route class after explicit commands, deterministic facts, and hard safety or autonomy policy have been applied. These labels are advisory. They grant no authority to diagnose, generate, execute tools, approve irreversible actions, merge, or bypass a human gate.

Explicit playbook invocation bypasses classification. Every other unknown, unsupported, `other`, unavailable, or abstaining result uses `baseline`. Hard safety, autonomy, and human-gate policy remains in the formal contract and cannot be changed by this registry. The registry does not enable a provider or alter current behavior.

The production route seam is the unresolved point in `/poteto-mode` immediately before it copies the selected playbook steps into the todo list. The `route_playbook` checks in conformance drivers validate a harness profile and target file. They do not classify a user task, so this registry does not treat them as the production router.

## Source capture

The inventory follows the official `cursor/plugins` source at commit `d0ef80d86795816da932a153458c5dbe192d294e`. Its resolved Git tree is `ef1c6ab4b7f1016cfbd4fbdb2e25cfa5ceecaa55`. `source.revision` identifies the commit; `source.tree` identifies its tree. The recorded router blob supports drift checks, and each playbook row records its own canonical blob hash.

Capture the commit object and its resolved tree with:

```sh
gh api 'repos/cursor/plugins/commits/d0ef80d86795816da932a153458c5dbe192d294e' > upstream-commit.json
gh api 'repos/cursor/plugins/git/trees/ef1c6ab4b7f1016cfbd4fbdb2e25cfa5ceecaa55?recursive=1' > upstream-tree.json
jq -e '.sha == "d0ef80d86795816da932a153458c5dbe192d294e" and .commit.tree.sha == "ef1c6ab4b7f1016cfbd4fbdb2e25cfa5ceecaa55"' upstream-commit.json
```

The commit response binds the source revision to the separate tree identity recorded in the registry. The complete API export used for this registry reported `truncated: false`. The local `UPSTREAM` pin still reflects an older source revision. Refreshing it belongs to #209. This registry does not claim to represent a newer source state or to prove provider behavior, runtime integration, evaluation quality, calibration, or promotion readiness. Skill suggestions are not exposed because they lack grounded taxonomy and callers.
