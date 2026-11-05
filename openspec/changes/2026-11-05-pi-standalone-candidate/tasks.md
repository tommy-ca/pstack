# Work graph: Pi standalone candidate adapter

Status: not executed. Parent issue #894. Dependency graph is authoritative in GitHub, not in a new task database.

- [x] #895 / source review: record current Pi 1.5.0, pi-subagents 0.85.0 and pi-better-sandbox 0.14.1 **published** baselines in the audit. This is not an installed-version check.
- [x] #894 / source-only design: inventory original 17 extensions, 17 PStack capabilities, and explicit hard-security unknowns.
- [ ] #895: run installed-version discovery, inspect package source/transitive deps, benchmark optional extensions, freeze compatible lockfile.
- [ ] #896: implement safe namespaced Pi candidate identity/profile encoding and source-conformant role projection.
- [ ] #896: validate native extension loading, role/skill discovery, model catalog, and non-overlap with @zenspc/pi-pstack; negative schema tests.
- [ ] #897: scaffold native Pi verification skill and implement actual driver with bounded process lifecycle and four-plane receipts.
- [ ] #897: prove spawn/join/cancel/steer/background/resume and worktree lifecycle; mark missing capabilities GAP.
- [ ] #897: enable sandbox; verify OS backend, parent + child + detached profiles, denial/refusal, malicious symlinks, MCP/web/SSH and trusted tool bypass.
- [ ] #898: add code-bound formal properties, checker runner, failing mutants and exact-sync revisions through existing create/maintain formal-verification skills.
- [ ] #899: ingest source captures with the existing wiki CLI, compile index, check graph/links/hashes, reconcile claims with real receipts.
- [ ] #900: run genuine Swarm, Arena, Interrogate, Thermo-Nuclear Review and Thermo-Nuclear Code Quality Review of current diff.
- [ ] #900: only promote candidate support after all exact-head runtime, security and evidence gates; otherwise report BLOCKED/UNTESTED.

## Test tiers

1. Offline: portability schema, negative mapping tests, skill frontmatter, existing verifier and wiki validator.
2. Host smoke: installed Pi version/package resolution, model catalog, extension activation, sandbox backend, candidate skill discovery.
3. Observed live: real child ID/agent lifecycle, worktree, permission denial, join/cancel/recovery and evidence closure at exact revision.

Do not reuse OMP's receipts as Pi evidence. Do not mark a check complete for a source citation or test plan alone. Avoid adding unrelated development tools to the global Pi profile.
