# Three-way semantic porting design (proposal)

## Source and authority

| Role | Source | Frozen revision | Authority |
| --- | --- | --- | --- |
| Canonical behavior | `cursor/plugins/pstack` | `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (0.15.29) | Canonical normative source of truth |
| Applied canonical pin | `tommy-ca/pstack/UPSTREAM` | `88d47514b82e7c44f00f2b2a72ff6dd12158038c` (0.15.29-grokbuild.0) | Promoted and verified in #629 / #642; program #622 closed via #630 / #643 |
| Target | `tommy-ca/pstack` | `329acf2` | Existing six-host port implementation on main |
| Reference port | `michael-denyer/pstack-claude` | `88f6d39f228c4f9210d93bbf7e5e40a5c671fd5e` (0.9.95) | Candidate design/test pattern, not normative |
| Previous reference audit | reference port | `94f5ce95abe8a9dec976967d79941f631cf477cd` | Comparator diff base |

Existing design authority: ADR-0021 and `openspec/specs/pstack-portability/spec.md`. Reuse implemented `pstack.package.json#/roles`, `profiles/`, `scripts/model_role_resolver.py`, `scripts/drivers/`, `schemas/portability/`, `scripts/project-package.py`, and `scripts/verify-portable.py`. Do not create parallel registries or evidence formats.

## Atomic semantic building blocks

| Atom | Contract/invariant | Owner | Deliberate exclusion |
| --- | --- | --- | --- |
| `CanonicalArtifact` | source SHA, relative path, hash, normative revision | Provenance/classifier | Reference-port authority |
| `SemanticDecision` | preserve/adapt/exclude/policy-fork/gap with postcondition and source | Audit ledger | Filename-only parity |
| `IntentClassifier` | user intent → canonical playbook, no host call | Router skill | Provider/client SDK |
| `PrinciplePolicy` | cross-cutting decision rules applied as constraints | `principle-*/SKILL.md` | Runtime control flow |
| `LeafSkill` | one prompt/work contract + required capabilities | `skills/` | Host tool name/slugs |
| `PlaybookStep` | preconditions, action intent, verification predicate | `poteto-mode/playbooks` | Spawn protocol |
| `RolePlan` | stable role ID → requested seats, effort, topology, limits | Existing role policy/resolver | Host catalog invention |
| `HostCatalog` | observed models, tools, version, freshness | Native adapter | Cross-host proof reuse |
| `CapabilityBinding` | semantic operation → native primitive or explicit GAP | `profiles/`, `scripts/drivers/` | Second generic engine |
| `ChildLifecycle` | spawn/observe/join/steer/cancel/settle transitions | Host native runtime | Universal PID or session-store layout |
| `WorktreeLease` | ownership, dirty/ignored/untracked/commit/lock guard | Host worktree tools | Unsafe delete-on-clean-status |
| `EvidenceReceipt` | frozen target SHA, host version, scenario, proof level, settlement | Existing receipt verifier | Synthetic live success |
| `ReviewTopology` | worker slices, candidate arms, reviewer model-family identity | Swarm/Arena/Interrogate composition | Fixed universal panel |
| `DeliveryGate` | independent exact-head verdict before authorized land | Shipping and #630 | Green-CI-is-safe assumption |

These names are **conceptual decomposition**, not a request to add fourteen runtime classes. Prefer reuse of existing domain types and data schemas.

## Code and data flow

```text
pinned canonical artifacts -----\
                                  +--> path + semantic classification
pinned reference diff ----------/    -> provenance ledger + candidate decisions
target port current behavior --------/

user intent -> pstack-mode router -> canonical playbook + principle constraints
 -> typed role/model plan -> current host profile + catalog + capability bindings
 -> native spawn/observe/settle -> host-owned persistent state
 -> scenario evidence receipt -> reviewer adjudication -> delivery gate

Pi reference negative tests -> observable postcondition/negative fixture
 -> target host-specific scenario (NOT copied process manager)
 -> static/mocked/live status distinguished -> evidence reduction
```

## Typed review and receipt shape (illustrative; align with extant schemas)

```json
{
  "source": {"repository": "michael-denyer/pstack-claude", "commit": "88f6d39f228c4f9210d93bbf7e5e40a5c671fd5e", "path": "tests/pi/agents-activity.test.mjs"},
  "semantic_atom": "ChildLifecycle",
  "decision": "adapt",
  "owner_plane": "host-adapter",
  "postcondition": "A concurrent tool completion cannot mark another call as finished",
  "target_harness": "omp",
  "proof": {"level": "static-only", "host_version": null, "target_sha": null, "scenario": "parallel-tool-call-ids", "status": "GAP"},
  "policy_fork": false
}
```

`static-only` and `GAP` here deliberately mean **no runtime support claim**. Schema implementation must map these conceptual fields to existing validated `Evidence`/`VerificationReceipt` shapes, not paste the example as a new wire format.

## Four main semantic fork decisions

1. **Host process/agent lifetime**: pstack-claude's Pi RPC child/session model is not OMP's native `task` or the target's six-host abstraction. Borrow *postconditions*, not `PiChild` and `~/.claude/orchestrate` runtime code.
2. **Config/model roles**: reference `plugins/pstack/models.json` is a generator input with aliases and a separate `roles` array. The target retains `pstack.package.json#/roles` and observed host catalogs. Alias presence is not model availability.
3. **Autonomy and shipping**: reference `tools/forks.json` declares intentional policy changes. Safety and authorization variants must be interrogated against canonical Shipping and existing port policy, never auto-overwritten.
4. **Review fanout**: `swarm` means independent coverage partitions; `arena` means independent competing candidates, cross-judge and graft; `interrogate` means independent model-family adversarial review with lead judgment. A single reader simulating multiple personas is not a verified multi-agent run.

## Design Arena (actual external runs NOT yet performed)

Candidate 0 — **no new code**; document delta and retain existing host tests. Candidate 1 — add narrow host-specific negative fixtures through existing verifier (default if measurable uncovered cases). Candidate 2 — introduce a generic lifecycle intermediary. Reject Candidate 2 unless two hosts independently demonstrate unaddressable contract duplication, because it adds state and a new failure surface. Assess with test reach, state ownership, rollback, new file count, and observed native proof. Run an actual Arena only if meaningful design alternatives remain after source classification.

## Interrogate failure hypotheses (not a completed multi-model review)

- Hidden `git status.showUntrackedFiles=no` causes a false-clean worktree deletion.
- Child process killed after PID reuse or after successful process-group settlement.
- Stale agent activity recorded as durable session evidence, or one parallel tool call prematurely settled another.
- Provider alias treated as proof of native model support; all reviewers share one family while reporting independent multi-model consensus.
- Closed #429 tasks are accidentally reopened or a reference fork silently overrides canonical Shipping permission.

## Proof gates

Source review -> deterministic diff fixture -> static schema and projection tests -> host-native negative tests (where runtime exists) -> immutable receipt scoped to exact candidate SHA and host version -> independent Swarm/Interrogate #630, optional Arena -> update accepted spec and provenance -> **only then** consider applied pin promotion via #629. An unavailable host remains BLOCKED/GAP. No auto-merge.
