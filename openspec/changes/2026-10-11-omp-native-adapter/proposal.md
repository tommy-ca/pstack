# Proposal: OMP native adapter truth and parity

Status: proposed (2026-10-11). This change is a formal specification and audit, **not** a claim that an OMP runtime fix is implemented.

## Intent
Retain `cursor/plugins/pstack` as the semantic authority. Adapt principles, skills and the poteto-mode playbook router to `can1357/oh-my-pi` using documented OMP-native discovery, roles, task/eval agents and plugin lifecycle, without copying a Grok runtime. Correct stale/overstated evidence separately from actual implementation. Preserve existing closed work in #62/#66/#67/#68 as history; link a new follow-up graph for current defects.

## Why
The pstack OMP profile and generated package once claimed stronger native integration and runtime proof than the host driver observed, which risked treating configuration inspection as successful child execution. The spawn and join half of that gap is now closed by an observed live child over RPC v2; the resume, read-only, depth and wire-alias bindings still have no dedicated live scenario; the native installed-package load is now proven by `scripts/prove-omp-native-package.py` against the real binary.

## What Changes
- Document OMP-native capability bindings, discovery precedence, role/model resolution, session behavior, WorkPool independence and safety limits at a pinned OMP revision.
- Specify native plugin installation/projection and ownership-safe lifecycle, keeping the canonical shared skill/playbook content host-neutral.
- Reclassify static/offline/live evidence; require a real OMP child spawn/join and isolated writer proof before declaring runtime support.
- Define Swarm, Arena, Interrogate and flat-versus-nested Orchestrate behavior, negative tests, and a recursive issue graph.

## Capabilities
**New capabilities**
- `pstack-omp-native-adapter`: native discovery, role mapping, safe execution, package lifecycle, and evidence-based conformance.

**Modified capabilities**
- `pstack-portability`: clarify existing semantic building blocks, capability postconditions, role/workspace ownership, compositional playbook parity, and the separation between three conceptual verification concerns and four existing serialized receipt planes. This change adds a dedicated **MODIFIED** requirement for the prior "Verification has three planes" language, without adding a new scheduler, capability enum, schema or orchestration DSL.

## Impact
- Specification and follow-up execution: `profiles/omp.json`, `scripts/drivers/omp.py`, `scripts/project-package.py`, `scripts/package-lifecycle.py`, `.omp-plugin/`, portable schemas and test fixtures, without changing implementations in this draft PR.
- Security/lifecycle: provider/agent settings ownership, plugin code trust, isolated writers, cancellation, and loss-free removal.
- Existing completed issues #62/#66/#67/#68 stay historical; current-head follow-up is epic #288, issues #289-#294 and #296-#298, and this change.

## Baselines (pinned)
- pstack repository: `tommy-ca/pstack@3b1d8efb4d4332de1b084691690e952893fe0c06` (2026-10-08); reconciliation head `a8ecd86` (2026-10-11) after the merged stack #301, #299, #302, #304, #316, #318, #319, #321.
- Current upstream Cursor repository: `cursor/plugins@11713c683fe4add4fd403ea880580abbc9e0875f` (2026-10-11). Existing portable package upstream pin remains `df581122cde17e6e27686b5a448bde23e4ad4318`; freshness and parity are different claims.
- OMP reference: `can1357/oh-my-pi@0affc77e41c357bb33f8bf056c3ea3cf50fd408b` (2026-10-11).
- Existing contracts: `openspec/changes/pstack-portability-contract`, `pstack.package.json`, `profiles/omp.json`.

## Observed gaps
1. `profiles/omp.json` once declared `support_state: verified` from a receipt that never proved model-backed child execution. Resolved in two steps: #301 demoted the profile to `packaged` with `agent.spawn` and `agent.join` at `static-only`, and #319 promoted both to `verified` against a committed `observed_live` scenario carrying a typed settlement. `support_state` remains `verified` and deliberately underclaims the reducer's `supported`, because the package plane is still an offline lifecycle fixture.
2. `scripts/drivers/omp.py` resolves routes locally, greps `omp --help` for isolation and shells `omp plugin list` for discovery, and reports each of those as `static`; none of them observes a child. `child_spawn` now also has a live path behind `PSTACK_RUN_OMP_LIVE=1` that spawns one real `task` child over RPC v2 and returns `observed_live` with a typed settlement, while the offline path keeps the static contract check.
3. `.omp-plugin/plugin.json` was produced from a Grok-style `generate_omp_manifest()` with `skills_root`, `entrypoint` and `lifecycle`, which OMP never reads; it enrolls a package through `package.json` with an `omp` key plus conventional `skills/` and `agents/`. Resolved: the projection emits that native descriptor, `verify_plugin_at_dir` fails without the enrollment key, and `scripts/prove-omp-native-package.py` proves against the real binary that the package is listed, that its skills tree loads (a sentinel skill injected into a temp copy appears only after the link), and that a packaged role agent spawns with `agentSource=user`. A listing alone is not loadability: OMP lists a package whose `package.json` lacks the `omp` key and loads nothing from it.
4. `profiles/omp.json` binds `read_only_mount` with `advisory` enforcement, and advertises an assumed `task`→`spawn_subagent` wire alias, a default `pi` model, `agent.resume` via session resume, and maximum depth 1. The committed receipt anchors the host at `omp/18.8.9`. OMP's `task.maxRecursionDepth` default is 2, so pstack depth-1 is a **policy** to enforce, not a host-native ceiling, and none of these bindings has a dedicated live scenario yet.
5. OMP WorkPool reuses keep-alive agents by default: safe for independent partitioned swarm only if isolation/contamination requirements are explicit; **not** independent Arena/Interrogate reviewers by default.
6. Skills are discovered one directory deep, name collisions are priority/namespace dependent, and user/project plugin/role scopes differ. Both must be acceptance tested.
7. Setup text still makes Grok TOML conventions normative for all hosts. OMP role mappings should use OMP `modelRoles` and agent frontmatter without modifying user auth/provider settings.

## Second-pass findings and source freshness (2026-10-11)
- The existing serialized receipt schema uses `observed_live` rather than the first draft's provisional `live`; `documented` is a source-provenance tag, not a receipt evidence level. See leaf #296.
- OMP native RPC provides structured ready/prompt acknowledgement/prompt_result/session_settled plus child enumeration and cancellation; these are preferable to `--help`/string-proxy runtime checks. See #297.
- `scripts/package-lifecycle.py` now copies `agents/` into the OMP installation branch (#299), so the role-projection omission is closed; the pseudo-manifest question is settled by the packaging observations below. See #298/#290.
- OMP plugin installs/links may be user-scoped even when project/cwd flags exist; native tests MUST verify the effective plugin root is disposable.
- Compared OMP `0affc77e…2070e304`: one later provider/judgment commit, with no changes to the reviewed RPC/task/skills/plugin docs. Keep the frozen behavior pin and re-check freshness before implementation.

## Reconciliation (2026-10-11, head a8ecd86)

The merged stack changed several premises this document was written against. Each row below was observed, not inferred.

| Claim | Observation | Settled by |
|---|---|---|
| A `package.json` is required to link a package | `omp plugin link` refuses a tree that has only a root `plugin.json`: `package.json not found` | arena arm B |
| The `omp` manifest key gates skill discovery | A package with a `package.json` that has no `omp` key links and lists as enabled, but its bundled `skills/` are not discovered; the same tree with an `omp` key is discovered | arena arms C, E and B2 |
| A root `plugin.json` package is installable on its own | Not linkable without `package.json`; a hybrid tree with both links and is discovered | arena arms B and B2 |
| Linked packages contribute roles | A linked package's `agents/` entry resolved in a real spawn with `agentSource: user` | arena arm B2 role run |
| Project-scope linking is isolated | `omp plugin link --scope project` wrote into the config root's `plugins/node_modules` and lockfile, from a disposable git repository as well as from a non-repo cwd | arena cleanup record, re-run control |

Native discovery results, all through `available_commands_update` in RPC mode with isolated config roots: project `.omp/skills` discovered one skill; a bare root `plugin.json` tree failed to link; the hybrid and the `package.json`-with-`omp` trees both discovered their bundled skill after linking.

A bounded RPC session also spawned and joined a real child: `ready` advertised protocol version 1 with `[1, 2]` supported, `negotiate_protocol` 2 succeeded, `subagent_lifecycle` reported `started` then `completed` for the child, `prompt_result` reported `completed` with `sessionSettled: true`, `session_settled` followed, and the process exited 0. That observation became the driver path in PR #319, merged: a committed `observed_live` scenario carries the settlement (`child_id`, `terminal_outcome: success`, the resolved model, `transport: rpc`, the negotiated v2 descriptor). The profile claims `verified` and deliberately underclaims what the reducer derives, because the package plane is still an offline lifecycle fixture and a native installed-package load remains open under #290. A later interrogate pass tightened the predicate, so a PASS now also requires exactly one child, a post-prompt settlement, a negotiated v2 session and the parent's literal reply, and the gate refuses a settlement whose outcome is not success.

Frontier after reconciliation: the source matrix for roles, depth and aliases (#289), the native installed-package proof (#298/#290) and the cancellation half of #297 are executable on this host; #292 to #294 stay gated behind those.

## Outcome
A pinned OMP capability map with evidence grades, minimal native package recipe, host-neutral orchestrations, real driver acceptance and loss-aware lifecycle gates. Candidate → mapped → packaged → verified → supported is **derived from proof**, never manually promoted.

## Non-goals
No new scheduler, no portable WorkPool abstraction, no new orchestration database, no rewrite of canonical skills, no unsandboxed extension unless a host-native command/tool genuinely cannot be represented as a skill, no changes to other harnesses except shared verifier correctness.

## Source docs
- https://github.com/can1357/oh-my-pi/blob/0affc77e41c357bb33f8bf056c3ea3cf50fd408b/docs/tools/eval.md
- https://github.com/can1357/oh-my-pi/blob/0affc77e41c357bb33f8bf056c3ea3cf50fd408b/docs/task-agent-discovery.md
- https://github.com/can1357/oh-my-pi/blob/0affc77e41c357bb33f8bf056c3ea3cf50fd408b/docs/skills.md
- https://github.com/can1357/oh-my-pi/blob/0affc77e41c357bb33f8bf056c3ea3cf50fd408b/docs/plugin-manager-installer-plumbing.md
- https://github.com/can1357/oh-my-pi/blob/0affc77e41c357bb33f8bf056c3ea3cf50fd408b/docs/skills/authoring-extensions.md
- https://github.com/cursor/plugins/tree/main/pstack
