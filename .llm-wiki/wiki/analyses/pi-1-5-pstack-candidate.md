# Standalone Pi 1.5.0 → PStack candidate semantic crosswalk

Status: **source-based candidate analysis, NOT live evidence**, 2026-11-05. Parent: [Pi adapter epic #894](https://github.com/tommy-ca/pstack/issues/894).

PStack's canonical workflow intent remains sourced to [Cursor PStack](https://github.com/cursor/plugins/tree/main/pstack), while this port's [17-capability portability specification](https://github.com/tommy-ca/pstack/blob/main/openspec/specs/pstack-portability/spec.md) owns the semantic vocabulary. Pi's separate baseline is [Pi 1.5.0](https://pi.dev/changelog/releases/1.5.0), not the existing OMP adapter.

## Semantic building blocks

- **Native agent loop and context:** Pi owns model interaction, tools, session persistence/resume, context, skill discovery, native MCP, codemode and tool_search.
- **Delegation:** [pi-subagents 0.86.0](https://pi.dev/packages/pi-subagents) offers agent.spawn/join/cancel, monitor, steering, durable missions and scheduled runs. It is an external tool runtime, not Pi core. New `subagent_launch` calls require permissions integration; old background runs from pre-0.85.0 cannot automatically resume. Independent model families still require runtime catalog evidence.
- **Execution trust:** [pi-better-sandbox 0.14.1](https://pi.dev/packages/pi-better-sandbox) offers independently configured main/subagent/background guards; its fresh switches start OFF. **Subagent Stored credentials defaults to Write & delete** and Outside project Write unless explicitly narrowed. Trusted extension tools are not covered by guarded file rules, and remote SSH effects are outside local confinement.
- **Human interaction:** [pi-ask-user 0.17.2](https://pi.dev/packages/pi-ask-user) adds the explicit structured `human.ask` tool in interactive mode. It is not an enforceable `human.gate` unless an independent permission policy also denies unapproved effects.
- **Research:** [pi-web-access 0.47.0](https://pi.dev/packages/pi-web-access) belongs to researcher/evidence-auditor roles only where needed; never grant broad network rights merely to enable a workflow.
- **PStack workflow semantics:** intent, plan, swarm, arena, interrogate, independent review, acceptance and truth-labelled receipts stay in PStack; no new orchestration engine.
- **Verification:** reuse create-verification-skill, create-formal-verification-skill, and their maintenance loops. Mocked or source-only mappings are static-only and not runtime-verified.
- **Knowledge:** the current Markdown + Git .llm-wiki is the knowledge layer; external docs in this candidate page have **not** yet been captured with scripts/llm_wiki.py ingest. No hash or local raw source claim is made.

## Responsibility crosswalk

| Concern | Pi PStack candidate owner | Design acceptance |
| --- | --- | --- |
| Skill and playbook invocation | Native Pi + canonical PStack skills | No duplicate skill namespaces |
| Agents and multi-model fanout | One pi-subagents engine | Real unique child IDs and resolved models |
| Role and model policy | Host profile/catalog, source-owned roles | No invented model slugs |
| Sandbox and permission | Explicitly enabled guard + OS/container | Denied operations observed and recorded |
| Isolation and integration | Per-writer worktree + host-owned merge | No parent mutation before acceptance |
| Human questions | pi-ask-user in interactive mode | Actual explicit decision/cancellation; no autoapproval in headless mode |
| Source-backed research | pi-web-access where authorized | External sources recorded with provenance |
| Verification | Existing portable driver and 3-tier evidence | Exact revision and failing negative controls |
| Formal verification | Existing formal skills and installed checker | Bound code relation and failed mutant |
| LLMWiki synthesis | Existing project-local wiki CLI | Sources and runtime claims kept separate |

## Known gaps and resolution

- **Candidate profile, native project skill/agent discovery, and offline verification skills are now implemented** on [draft PR #901](https://github.com/tommy-ca/pstack/pull/901). A real Pi child-driver, observed receipts and installed-version inventory are still missing. See [#895](https://github.com/tommy-ca/pstack/issues/895), [#896](https://github.com/tommy-ca/pstack/issues/896), and [#897](https://github.com/tommy-ca/pstack/issues/897).
- Sandbox/extension interaction, credentials, malicious worktree links and MCP/web admission remain explicitly unproved; see [#897](https://github.com/tommy-ca/pstack/issues/897).
- Formal state invariants and negative mutants remain planned in [#898](https://github.com/tommy-ca/pstack/issues/898).
- Raw source ingestion and hash-backed local sources remain planned in [#899](https://github.com/tommy-ca/pstack/issues/899).
- Actual independent Swarm/Arena/Interrogate and both Thermo-Nuclear reviews remain a gate in [#900](https://github.com/tommy-ca/pstack/issues/900).

See [the full research audit](https://github.com/tommy-ca/pstack/blob/main/docs/research/pi-1-5-standalone-pstack-audit-2026-11-05.md) for the 17-capability table, supplied 17-extension decisions, trust boundaries and version pins. The six existing shipped harnesses remain the only declared packaged hosts.

## Minimal runtime profiles (source-level only)

- Engineering: native Pi 1.5.0 + `pi-subagents@0.86.0` + `pi-better-sandbox@0.14.1` + `pi-ask-user@0.17.2` (3 runtime extensions), plus canonical PStack skills.
- Research: engineering + `pi-web-access@0.47.0` (4 runtime extensions).
- Temporary migration: `@zenspc/pi-pstack@0.6.0` may remain one *additional policy package* until the canonical `tommy-ca/pstack` projection replaces it; never run duplicate skill/policy copies.
- Headless: `ask_user` can be omitted only with a proven fail-closed policy for unresolved operator decisions.
- Schedule/monitor: reuse versioned `pi-subagents` missions/schedules rather than install another task runner. Require real schedule/recovery receipts.
- Never infer permission safety from package installation: sandbox starts Off, credential and outside-workspace defaults need tightening, and trusted extension tools are outside file guards.

See [the full audit](https://github.com/tommy-ca/pstack/blob/main/docs/research/pi-1-5-standalone-pstack-audit-2026-11-05.md) for pinned sources, the 17-capability crosswalk and the remaining negative tests. This page is a candidate synthesis, not a verified runtime adapter.

## Candidate implementation crosswalk (draft PR #901)

This current branch adds an executable **Tier 1 source-only** adapter slice without registering a seventh shipped host:

| Semantic artifact | Actual path | Scope |
| --- | --- | --- |
| Candidate typed adapter | `profiles/pstack-pi.json` | Existing `HarnessProfile` and `Binding`; 17 classified capabilities; no `verified` bindings |
| Native Pi skills | `.pi/settings.json` → `../skills` | Loads canonical shared PStack skills after Pi project trust, without a copied PStack npm bundle |
| Native pi-subagents role discovery | `.pi/settings.json` → `subagents.agentScanDirs: ["../agents"]` | Reuses PStack's shared role markdown; `projectRootResolution: git-root` stabilizes worktrees |
| Essential extension reference | `references/pi-essential-extensions.json` | 4 engineering, 1 research optional, `@zenspc/pi-pstack` transitional only; **does not auto-install** |
| Source contract verifier | `scripts/verify_pi_candidate.py` | Existing typed models and 43 deliberately rejected source mutations |
| Pi functional verification skill | `.pi/skills/verify-pi-pstack/` | `doctor` source checks; `drive` returns BLOCKED until real child, worktree and sandbox evidence |
| Pi bounded formal verification skill | `.pi/skills/verify-pi-pstack-formal/` | Actual PStack validator code under bounded mutation tests; **not** an OS sandbox/security proof |

Canonical `swarm`, `arena`, and `interrogate` are discoverable skills, while their delegated runtime behavior remains a **Tier 3 unverified requirement** until a real installed Pi runs children with captured IDs and model identity. The two Thermo-Nuclear review skills remain separate acceptance lenses for the implementation patch.

### Capability and trust limits

The original `agent.spawn/join/cancel`, `schedule`, and `monitor` remain **version-gated**, not native. `human.ask` uses `pi-ask-user` only where installed; `human.gate` remains GAP because a user-response UI does not enforce tool permissions. `workspace.readonly` remains advisory until the configured OS policy is shown to deny actual writes, including trusted extension tools and detached children.

Offline CI tests and negative controls can verify the candidate *specification*, not live extension composition. The existing six-host PStack verifier and evidence receipts are intentionally unchanged. Public upstream sources remain external citations here until the separate immutable raw-source ingest task #899 captures and verifies hashes.

## Autonomous approval and selection: pi-verdict 0.16.0 (2026-11-05)

Source evidence: [pi-verdict release](https://github.com/jesset/pi-verdict/releases/tag/v0.16.0), [tool_call code](https://github.com/jesset/pi-verdict/blob/main/extensions/pi-verdict.ts), [security principles](https://github.com/jesset/pi-verdict/blob/main/docs/security-principles.md), [pi-ask-user](https://github.com/edlsh/pi-ask-user/releases/tag/v0.17.2), and [pi-subagents 0.86.0](https://github.com/nicobailon/pi-subagents/releases/tag/v0.86.0).

Atomic responsibilities: **PStack** owns the risk class/human gate specification; **Pi core** owns tools/sessions; **pi-subagents 0.86.0** owns child orchestration and schedules; **pi-verdict 0.16.0** owns a conditional pre-tool-call deterministic floor and model `allow|ask|deny`; **pi-ask-user 0.17.2** owns explicit structured user choices; **pi-better-sandbox 0.14.1** owns configured local OS isolation; **PStack verification** owns independent effect/permission receipts. The research-only `pi-web-access 0.47.0` remains optional. Four engineering / five research extensions are the minimal candidate; `@zenspc/pi-pstack` is transitional packaging, not a new runtime.

A classifier `allow` may admit low-risk *reversible* actions **only inside independently enforced ceilings**. `ask` escalates ambiguity via `ctx.ui.confirm` and becomes deny headless. `ask_user` is a separate sequential selection tool; neither its answer nor a classifier decision proves `human.gate`. The plugin can be disabled, its deterministic floor can be configured off, and its `ignoreTools` shortcut can bypass adjudication of custom tools. Its audit records only gray-zone/protected-path adjudication, not all rule outcomes or OS effects. A fallback classifier may rescue first-layer failure under its `enforce` cascade. Parent tool interception is not proof of child `subagent_launch` enforcement.

The candidate manifest `references/pi-essential-extensions.json` now requires four source-pinned engineering packages and splits the tool authorizer from the sandbox. `references/pi-verdict-pstack.example.json` is a **manual configuration example**, not installed policy: deterministic floor on, empty unreviewed allow/ignore lists, no classifier fallback. The existing typed verifier rejects **53 source-level invalid mutations** (43 prior + 10 new authorization mutants). No live Pi, child or OS denial was observed, no independent Swarm/Arena/Interrogate ran, and PStack `human.gate` remains GAP. Public references have not been ingested into immutable .llm-wiki raw sources with verified digests (#899).
