# Harness-neutral authority and verification (2026-10-21)

Status: **source-level reconciliation**, target `tommy-ca/pstack@ef3405282e4afd2636923043ca59aac8a09d4170`. This is not an observed live host run, successful independent fanout, or a newer upstream release. See [Epic #695](https://github.com/tommy-ca/pstack/issues/695).

## Normative ownership (one direction, no Grok intermediary)

| Layer | Owned by | Evidence |
| --- | --- | --- |
| Canonical purpose and ordering | `UPSTREAM`, `skills/`, `skills/poteto-mode/playbooks/`, principles | source-pinned semantic diff; behavioral fixtures |
| Portable vocabulary and role identity | `pstack.package.json`, `schemas/portability/`, `scripts/model_role_policy.py` | schema + negative contract tests |
| Host capability, model and skill precedence | `profiles/<host>.json`, `skills/poteto-mode/references/<host>-tools.md`, host model catalogs | declared mapping; unsupported capability = GAP |
| Host native execution | `scripts/drivers/` and host runtime itself | independently observed spawn/join/cancel/isolation or explicit BLOCKED/UNTESTED |
| Packaging/projection | `scripts/project-package.py`, host manifest directories, lifecycle tests | projected manifest + actual installed behavior |
| Optional JEV advisory decisions | `scripts/decision_adapter.py`, `scripts/route_resolver.py` | bounded policy/transport/evidence receipts; default OFF |

**Dependency rule:** canonical skills describe roles, required capabilities and effects, not native API names or concrete model slugs. A selected host profile maps those requirements to its native tools. Do not translate Codex, OMP, OpenCode, Antigravity or Droid through Grok's syntax. Grok-specific `spawn_subagent`, `~/.grok/`, `scheduler_create`, `grok-4.6`, `/create-skill` and `benny-grok` belong to their own host reference, setup, packaging, or compatibility checks, not a global router default.

## Shipped versus discovered

`pstack.package.json#host_targets` currently lists `grok`, `codex`, `omp`, `opencode`, `antigravity`, `droid`. `profiles/` can also describe **observer/candidate** hosts; a profile alone is not enrollment. `support_state`, every capability binding's `verification_status`, receipt provenance, and exact source revision determine what can be claimed. Droid is a candidate. Package generation, mocked CLI behavior, static/offline tests and planned model seats are not model-backed proof.

Do not add a second scheduler, role registry, top-level orchestration state DB or model gateway. Session/worktree/lifecycle state stays with the host. Optional JEV cannot grant a capability forbidden by native/profile policy.

## Grok compatibility (not shared authority)

This repo originated from a Grok port, and the root `plugin.json`, `.grok-plugin/`, `scripts/setup_pstack.py`, `automations/benny-grok/` and Grok tool reference continue to serve that adapter. Historical Grok decisions remain in dated ADRs/archived OpenSpec records and must not be silently rewritten. The shared package version is host-neutral (`0.15.29-preview.0`) across every adapter, delivered as an explicit breaking release by [#699](https://github.com/tommy-ca/pstack/issues/699): `scripts/package-lifecycle.py#RETIRED_VERSIONS` names the retired Grok-specific label, and `verify` refuses a tree that still carries it with the upgrade command instead of a bare mismatch.

The source-level consistency defects in [#696](https://github.com/tommy-ca/pstack/issues/696) and [#698](https://github.com/tommy-ca/pstack/issues/698) should be closed by small, tested changes, not exemptions masking violations.

## Merge-proof checklist

1. Freeze parent/head SHA, upstream provenance, semantic and risk scope before reviewing each stacked PR. Select checks by changed files and run mandatory offline CI; a green CI proves only that tier.
2. Swarm: independent lanes inspect canonical parity, profile/model boundaries, packaging, and native runtime evidence. A plan for lanes is not an executed multi-model fanout.
3. Arena: compare minimal changes against larger wrapper/gateway redesigns; prefer subtraction and no new control plane. Interrogate: attack unverified capability promotion, false-green fixtures, stale hashes, host-native leak, rollback and manifest/user-file safety.
4. Apply [Thermo Nuclear Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-review) to security/correctness and [Thermo Nuclear Code Quality Review](https://github.com/cursor/plugins/tree/main/thermos/skills/thermo-nuclear-code-quality-review) to structural complexity. A review must cite the actual changed patch, inspect PR discussion after its first pass, and classify each finding with evidence and severity.
5. Require independent per-PR verifier at the current patch, green checks at current head, no unresolved blocker. Land only contiguous bottom-up verified PRs and re-check bases and merged state. Without an observed independent run, report **BLOCKED/UNTESTED**, not PASS.

The [verification tiers](../verification-test-tiers.md) and [implementation map](./harness-adapters-and-jev-2026-10-20.md) remain the authoritative evidence policy.