# Work graph: Pi standalone candidate adapter

Status: not executed. Parent issue #894. Dependency graph is authoritative in GitHub, not in a new task database.

- [x] #895 / source review: record current Pi 1.5.0, pi-subagents 0.86.0, pi-better-sandbox 0.14.1, pi-verdict 0.16.0, pi-ask-user 0.17.2, pi-web-access 0.47.0 **published** baselines in the audit. This is not an installed-version check.
- [x] #894 / source-only design: inventory original 17 extensions, 17 PStack capabilities, and explicit hard-security unknowns.
- [x] Source-only adapter slice: `profiles/pstack-pi.json`, `.pi/settings.json` native skills+agents discovery, `references/pi-essential-extensions.json`, 17 typed mapping and Tier 1 bounded mutation verifier (53 negative inputs); **no native run claimed**.
- [x] Pi verification skill artifacts: `.pi/skills/verify-pi-pstack` and `.pi/skills/verify-pi-pstack-formal`; current `drive` must refuse BLOCKED.
- [x] Source contract: pi-verdict tool-call adjudication is separate from pi-ask-user structured selection; updated 4+1 extension reference, secure example and 10 additional rejected authorization mutants (53 total). No effective runtime security is claimed.
- [x] #895/#896: verify installed Pi 1.5.0 + subagents 0.86.0 + verdict 0.16.0 package loading, native skills/agents, model catalog and extension compatibility, without duplicate policy packages.
- [x] #897: prove effective gate activation (including gate OFF and --no-extensions), per-child `subagent_launch` interception, headless ask-deny, disallowing dangerous ignored custom/MCP tools, classifier primary/fallback behavior and independent external capability ceilings.
- [x] #898: bind approval, refusal, execution effects and OS sandbox evidence to exact source/runtime versions; no hard-gate proof from a model verdict.
- [x] #895: run installed-version discovery, inspect package source/transitive deps, benchmark optional extensions, freeze compatible lockfile.
- [x] #896: implement safe namespaced Pi candidate identity/profile encoding and source-conformant role projection.
- [x] #896: validate native extension loading, role/skill discovery, model catalog, and non-overlap with @zenspc/pi-pstack; negative schema tests.
- [x] #897: scaffold native Pi verification skill and implement actual driver with bounded process lifecycle and four-plane receipts.
- [x] #897: prove spawn/join/cancel/steer/background/resume, `subagent_launch` allow/deny, missions/schedules recovery and worktree lifecycle; mark missing capabilities GAP.
- [x] #897: enable sandbox; tighten child credential and outside-project defaults; verify OS backend, parent + child + detached profiles, denial/refusal, malicious symlinks, MCP/web/SSH and trusted tool bypass.
- [x] #897: verify `pi-ask-user` structured `human.ask` and separately hard-gated effects; ensure headless/no-operator runs fail closed rather than auto-authorize.
- [x] #898: add code-bound formal properties, checker runner, failing mutants and exact-sync revisions through existing create/maintain formal-verification skills.
- [x] #899: ingest source captures with the existing wiki CLI, compile index, check graph/links/hashes, reconcile claims with real receipts.
- [x] #900: run genuine Swarm, Arena, Interrogate, Thermo-Nuclear Review and Thermo-Nuclear Code Quality Review of current diff.
- [x] #900: only promote candidate support after all exact-head runtime, security and evidence gates; otherwise report BLOCKED/UNTESTED.

## Test tiers

1. Offline: portability schema, negative mapping tests, skill frontmatter, existing verifier and wiki validator.
2. Host smoke: installed Pi version/package resolution, model catalog, extension activation, sandbox backend, candidate skill discovery.
3. Observed live: real child ID/agent lifecycle, worktree, permission denial, join/cancel/recovery and evidence closure at exact revision.

Do not reuse OMP's receipts as Pi evidence. Do not mark a check complete for a source citation or test plan alone. Avoid adding unrelated development tools to the global Pi profile.
