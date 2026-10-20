# Source-pinned pstack / pstack-claude / Cursor semantic audit — 2026-10-20

**Scope**: delta since closed program #429; tracked by [#636](https://github.com/tommy-ca/pstack/issues/636), [#637](https://github.com/tommy-ca/pstack/issues/637), [#638](https://github.com/tommy-ca/pstack/issues/638). This is a *source audit*, not a completed host test.

## Pinned heads

- Target: `tommy-ca/pstack@329acf2` (declares six native targets: Grok, Codex, OMP, OpenCode, Antigravity, Droid; canonical 0.15.29 pin `88d47514b82e7c44f00f2b2a72ff6dd12158038c` applied and verified via completed program #622).
- Reference: `michael-denyer/pstack-claude@88f6d39f228c4f9210d93bbf7e5e40a5c671fd5e`, plugin 0.9.95; old reference audit used `94f5ce95abe8a9dec976967d79941f631cf477cd`.
- Canonical HEAD: `cursor/plugins@88d47514b82e7c44f00f2b2a72ff6dd12158038c`, pstack 0.15.29. Applied target pin promoted to `88d47514...` (0.15.29-grokbuild.0) in #629 / #642; program #622 closed via #630 / #643.
- Structural skill census `skills/*/SKILL.md`: target **63**, reference **65**, canonical **56** (names only; not a quality score). Target-only relative to canonical includes integrated team-kit leaves, and canonical-only `make-bot-ui`; reference also has `thermos` and `thermo-nuclear-review`.

## Comparator provenance and changed evidence

- `compare 94f5ce95...88f6d39f`: **16 commits**; changes in `plugins/pstack/pi/{child,agents,config,agent-text,agent-tools,worktree}.ts`, `tests/pi/agents-activity.test.mjs`, `tests/pi/agent-transcript-command.test.mjs`, `tests/pi/worktree-status-config.test.mjs`, `plugins/pstack/skills/poteto-mode/scripts/orch/{orch,store}.ts`, watcher/worktree safety, model mapping, review/policy skill text, and packaging tests.
- Current reference `tools/forks.json` has **48 declared paths**: `pstack` 47 (39 policy, eight port-feature) plus `thermos` one policy; not evidence of 48 changes in this 16-commit window.
- Existing source audit `docs/research/pstack-claude-portability-audit-2026-10-15.md`, adoption ledger `docs/research/pstack-claude-adoption-matrix-2026-10-16.md` and Pi/OMP `docs/research/pi-omp-equivalence-2026-10-18.md` are prior snapshots, not native proof at today's source heads.

## Semantic comparison and decisions

| Semantic boundary | Canonical | Target | Reference delta | Decision |
| --- | --- | --- | --- | --- |
| Intent and principles | `poteto-mode` plus `principle-*` leaves | Host-neutral shared leafs and typed portability contracts | Claude/Codex/Pi syntax rewrites, policy differences declared | **Preserve canonical**, adapt only projection |
| Model and role selection | Cursor setup defaults and agent roles | `pstack.package.json#/roles` + resolver + host observed catalog | Generated `models.json` with roles/tiers/effort/aliases | **Borrow consistency/negative tests**, do not copy role registry |
| Cross-host child invocation | Cursor Task, model/isolated/readonly | Six host native drivers with GAP-capable bindings | Pi RPC child-process extension, new activity/resume observations | **Adapt postconditions** only, native drivers own mechanics |
| Worktree and child cleanup | Worktree safety playbooks / helper scripts | Host scoped existing cleanup/receipt gates | Hidden untracked Git setting tests, child process settlement updates | **Review as negative fixture** #638/#626, no direct copy |
| Orchestration state | Canonical playbook intent | Host-owned durable state, ADR/host-specific mapping | Claude-specific orchestrate directory and Pi sessions | **Exclude competing shared store**; #402 already settled scope |
| Shipping and autonomy | Root verified landing and authorization | Frozen SHA, native independent receipts, approved merge | Explicit `tools/forks.json` shipping and autopilot policy forks | **Manual policy review**, do not silently import |
| Parallel review | Swarm coverage, Arena candidate comparison and cross-judge, Interrogate independent adversarial review | Role topology/resolver and evidence ledger | Reference model-family defaults and role text | **Preserve semantic topology**; no fake multi-model pass |
| Evidence | Canonical `prove-it-works` principle | Static/live receipt levels and SHA-bound promotion | Pi T/A/H/F/S/C/X equivalence rows and live flags | **Borrow mechanism matrix pattern**, no Pi→OMP proof transfer |
| Packaging | Cursor plugin manifest + guide | Native profiles and projected packages | Generated Claude, Codex, Pi and Copilot material | **Compare host-native paths only**; #628 scope |

## High-value new negative controls

Reference `tests/pi/agents-activity.test.mjs` asserts (in source) running tool summaries, parallel tool completion keyed by call ID, no durable activity entries, no activity after agent end, and status restoration. Reference `tests/pi/worktree-status-config.test.mjs` checks hidden untracked files when `status.showUntrackedFiles=no`, per-worktree preference, agent commits and safe cleanup. These are **test propositions to transplant** into the correct target host capability, not tests run in this audit.

## Deliberate exclusions and known gaps

Do not promote the six hosts to seven because `profiles/claude.json` or `.claude-plugin/` exists; descriptor `host_targets` is the declared census. Do not infer OMP steering from Pi native RPC; #443 documented the distinction. Do not claim reviewer diversity from repeated names or a single model's personas. Do not use an upstream HEAD skill diff to change `UPSTREAM` without #629/#630.

## Execution

[#637](https://github.com/tommy-ca/pstack/issues/637) classifies source and policy deltas → [#638](https://github.com/tommy-ca/pstack/issues/638) owns accepted negative fixtures → conditional [#626](https://github.com/tommy-ca/pstack/issues/626), [#627](https://github.com/tommy-ca/pstack/issues/627), [#628](https://github.com/tommy-ca/pstack/issues/628) implement only their existing boundaries → [#630](https://github.com/tommy-ca/pstack/issues/630) owns *actual* exact-head review. [#636](https://github.com/tommy-ca/pstack/issues/636) closes the bounded comparator review without changing closed #429. No runtime tests, independent agent fanout or new source code were run for this document.
