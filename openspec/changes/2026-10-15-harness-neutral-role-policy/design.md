# Harness-neutral model/role mapping and pstack-claude pattern audit

Status: Proposed · 2026-10-15. Implementation requires issue graph and runtime receipts.

## Authority and provenance

1. `cursor/plugins/pstack` at `UPSTREAM` is the normative source for canonical principles, role intent, skills, router and playbooks. In this port, `pstack.package.json#/roles` is the unique local role ID/description/default-model-tier registry; host policy augments it without copying the role array.
2. `tommy-ca/pstack` is the portability implementation, not the canonical source.
3. `michael-denyer/pstack-claude` at a recorded commit is a reference port; `tools/forks.json` explicitly declares policy forks. Adopt a pattern only after a behavior and license/provenance review.
4. `tommy-ca/qstack` supplies quant-domain invariants after the host router; it MUST NOT own a pstack router or model namespace.

At audit time: target main `7700faa158558e47260565a71e7d0b6cdc95679a`; reference main `94f5ce95abe8a9dec976967d79941f631cf477cd`; canonical target pin `1dcc2bacde73ddd284803b7af28164d0436198fc`. Refresh and record those pins in evidence before implementing. Reconciled 2026-10-16 at trunk `54082a6`: the 14 commits `7700faa..54082a6` delivered the static planner, schemas, 40-test policy suite, OpenSpec change plus ADR-0021, 48-row fork index, resolver invocation contract, OpenSpec reconcile, durable receipts, fork matrix, skill-token regression, license disposition, verify retarget, and schema-first refactor (#447, #450/#451/#452/#453/#454/#455/#456/#457/#458/#459/#460/#461 plus unnumbered bb97e50). The runtime and multi-family gates stay open per tasks G2/G7.

## Reusable atomic blocks (ownership / interfaces)

| Block | Owns | Must not own |
| --- | --- | --- |
| Canonical inventory | role/skill/playbook IDs and pinned source provenance | host defaults |
| Intent resolver | task -> canonical playbook and role intent | model/provider calls |
| Role policy | canonical role ID -> existing descriptor tier, spawn topology, minimal capabilities | redefining role IDs/tiers or model catalog discovery |
| Host catalog | observed models, provider/family, effort enum and evidence | global policy |
| Role resolver | input + constraints + catalog -> typed choice or explicit gap | spawning |
| Capability adapter | semantic spawn/join/cancel/resume/isolated/read-only to native primitives | playbook decisions |
| Package projector | core descriptor -> manifest/hooks/stubs/reference paths | runtime workflow store |
| Hook adapter | startup/resume/compact injection (idempotent, opt-out, trusted) | permanent session ownership |
| Receipt verifier | versioned static/live proof and model-resolution trace | suppressing gaps |
| Domain overlay | post-routing qstack quant invariants | replacement router |

### Role resolver data flow

```text
canonical role registry + playbook task
  -> required capabilities + topology + tier
  -> host profile + observed runtime model catalog
  -> constraints (security/approval/allowlists/host abilities)
  -> explicit invocation > project override > user override > host defaults > parent inheritance
  -> validate requested model IDs / family diversity / effort against observed host support
  -> {selected models, effort, reason, evidence refs} OR {gap, fallback reason}
  -> adapter translates to host-native spawn fields
  -> host-native settlement + immutable evidence receipt
```

Explicit user choices never bypass policy/approval constraints. An unavailable explicit model yields an actionable error, NOT a silent substitution. `auto` / `inherit-parent` means omit model on the spawn call; it is not a model slug. Host-detected effort sets control acceptance: unsupported tokens do not become valid by appearing in documentation. Never infer live availability from a checked-in `models.json`.

For single roles require one resolved model or documented inherit behavior. For a panel, each entry is an independently spawned seat. For the `arena-cross-judge-pool` cross-judge selector, choose a judge family different from the candidate/parent even if only one judge is dispatched. For `interrogate-reviewers`, which is an adversarial panel, each reviewer is a separate agent; count only actual independent model families. If the requested independence or diversity is impossible, mark `DEGRADED` or `BLOCKED`, never claim multi-model proof.

### Tool/control flow

```text
parent poteto-mode router
  -> call semantic capability / role request
  -> resolve against profiles/<host>.json + role policy
  -> host-native dispatch (depth-1 parent fan-out policy unless separately proven)
  -> join/settlement and verify app/test behavior
  -> evidence receipt (host binary/version, model catalog source, family, SHA, scenario)
```

No child may silently become the coordinator. Hard read-only isolation and advisory no-write prompts are different enforcement levels. Persistent task state remains host-owned. Do not import `pstack-claude`'s `~/.claude/orchestrate` store (cf. closed #402). Pi and OMP are separate adapters; an observed Pi extension feature proves nothing about OMP. Host gaps are explicit.

### Projection contract

`pstack.package.json` remains package authority; `scripts/project-package.py` remains the single projector. The new schema declares `role_source: pstack.package.json#/roles`, optional per-role constraints and per-host tiers; it must reuse exactly the existing tier values (`fast-worker`, `fast-verifier`, `strong-judgment`, `strongest`, `panel`, `adversarial-panel`). It does not redeclare canonical roles. This can initially be checked as an example. The implementation phase may incorporate it as an optional field in `pstack.package.json` or a single adjacent `model-role-policy.json`, but MUST NOT create competing role registries or separately hand-maintained host manifests. Add only a minimal resolver/validator; keep host-specific hooks/extensions in host packages.

Before accepting a Copilot or Claude host entry: implement profile, manifest, hook policy, runtime scope, identity/permission checks and a package install/uninstall smoke test. `candidate` and `mapped` do not equal `supported`. Discovered skills do not prove independent agents, hooks, or model assignment.

### Arena (architecture choice, design review only)

| Candidate | Tradeoff | Decision |
| --- | --- | --- |
| A. Copy pstack-claude wholesale | Pi/runtime features arrive quickly; forks, divergent state model and duplicated sources | Reject |
| B. Extend existing schema/profile/receipt architecture using proven patterns | Maintains canonical authority and incremental proof, minimal behavioral delta | **Select** |
| C. Build a generic agent-runtime gateway/DSL | Apparent consistency but adds a second control plane | Reject (YAGNI) |
| D. Keep prose-only mappings | No immediate cost, but model drift is untestable | Reject for model policy; retain for non-executable host guidance |

### Interrogate: pre-implementation failure hypotheses

- Role ID strings in reference `models.json` combine roles (e.g. `feature, refactoring`); do not make those compound labels canonical stable IDs.
- Host/source model IDs are volatile; a model catalog entry without live probe is static, not dispatch authorization.
- Single-family `arena` should not be documented as independent cross-model validation.
- Nested subagent and isolation semantics differ between Claude Code, Codex, Pi and OMP; verify per host/per version.
- Routing hooks may duplicate injected instructions at resume/compact, fail when trust/permissions are absent, or conflict with other plugins.
- A green generator is not a live capability receipt.
- Installing Copilot/Claude manifests could accidentally copy upstream policy forks, paths, or external state.
- Avoid replacing `qstack`'s generic-vs-quant overlay with a second decision router.

## Verification / acceptance

- Static: JSON Schema draft 2020-12, unique role IDs, resolvable skill refs, projections `--check`, portable doctor, no forbidden primitives in shared content.
- Model fixtures: unknown model, unavailable provider, stale catalog, effort mismatch, panel diversity, cross-judge independence, missing privilege, `inherit-parent`, override precedence, malformed sheet.
- Hook fixtures: on/off, no duplicate install, startup/resume/compact, absent trust, opt-out and upgrade.
- Live gates: each host install + skill discovery + role dispatch + join + cancel/resume where claimed + read-only & isolation checks + receipt-bound version evidence.
- Swarm: independent host/source slices; Arena: same design brief with no-change baseline; Interrogate: independent model-family reviewers on an exact diff. This document is a **static synthesis only**, not evidence that those parallel agent runs occurred.

No claims of PASS for tests not executed. Candidate patterns are not promoted until verifiers settle with objective evidence.

## Pure role-model planning boundary (v1)

The source-owned `pstack.package.json#/roles` registry defines role IDs and six tier strings. An optional `model-role-policy` document binds host catalogs, effort and per-role topology; it MUST NOT become a second registry. `scripts/model_role_resolver.py` is a pure **planning-only** reference which has no model runtime dependencies and never claims a live verification receipt.

Input: `ModelPlanRequest` = `(host, role, explicit?, project?, user?, parent_family?, reported_capability_bindings?)`. Resolve the model choice in this order: explicit request → project override → user override → host role override → host tier default → configured inheritance or FAIL CLOSED. No unknown slug may silently fall back. Per-model effort needs observed host support. Native spawn API arguments are NOT constructed by the planner.

Output: `ModelPlan` with `source`, `selection`, `seats[]`, `status=PLANNED|DEGRADED|BLOCKED`, `reasons[]`, `effort` and **`evidence_level=static-planning-only`**. A runtime adapter must independently prove availability, actual spawn, isolation, family identity, and join before upgrading a separate runtime receipt. Capability input is typed host *metadata*, not an attestation.

**Arena:** `selection=panel`; `seats` may be greater than the unique model slug list. Round-robin assignment generates independent *planned slots* on one named model, not multi-family validation. Native runtime must give slots distinct contexts/worktrees. The canonical default remains one runner, not an invented mandatory two.

**Arena cross-judge:** `selection=cross-judge` selects *one* model from a pool preferring a family different from the parent/candidate, not one judge per pool entry. When family divergence cannot be proven, mark DEGRADED or BLOCKED if explicitly required.

**Interrogate:** `selection=panel` maps each configured model to a planned reviewer seat, records missing family diversity as DEGRADED, and treats advisory read-only enforcement as DEGRADED, never a hard access boundary. The canonical default may be one reviewer; do not invent an additional mandatory seat absent a configured choice.

**Swarm:** `selection=single` describes the default model for each worker, NOT the worker fan-out count; actual task partitioning remains a playbook concern.

Configured model list uniqueness does not impose unique models across `seats`. A separate `role_overrides.<role>.seats` controls bounded fan-out. Agent count, model slug count, model-family count and verified independently settled agent count are separate metrics. Runtime reporting MUST include all four.

### Remnant issues to interrogate

1. The runtime planner accepts host capability metadata passed by the caller; the caller MUST authenticate its profile/receipt rather than treating untrusted request data as proof.
2. Model discovery `catalog` means static inventory only. Even `live` declared in JSON is insufficient to authorize a model call until receipt integrity and freshness have been checked by the host driver.
3. `project` override as an input parameter is a contract, not a file path or policy engine. The setup skill owns safe configuration parsing/migration.
4. The reference `pstack-claude` aliases (`opus/fable/sonnet/haiku`) are not the canonical role registry, and its Codex/Pi tables may not reflect the currently installed host. Models must be discovered from the target harness session.

## Portability Arena decision record (static candidate evaluation, not an agent run)

Rubric: upstream fidelity 30%, maintenance burden 20%, host-native correctness 25%, verifiability 15%, flexibility 10%. Alternatives:

| Candidate | Canonical fidelity | Maintenance | Host correctness | Verification | Decision |
| --- | --- | --- | --- | --- | --- |
| A Copy comparator plugin, models and Pi engine | Lower: declared policy forks and alternate state | High drift cost | Pi-specific, not OMP | Existing Pi tests only | Reject |
| B Keep typed descriptor + pure model planner + thin native adapters | Strong: one pinned workflow source | Incremental | Host version isolated | Existing CI + per-host native gate | **Recommend** |
| C Introduce a provider-independent agent runtime and persistent workflow DB | Weak: duplicates router and state | Highest | Must imitate native auth/isolation | Extra untested surface | Reject |
| D Preserve only documentation mapping | No implementation change | Low short term | Unverified runtime behavior | Prose only | Reject as final design |

**Interrogate checklist, not an executed independent review:** Is the model alias a role ID? Are model/provider/family identities verified, not inferred from a list? Does an explicit invalid model fail rather than silently inherit? Is an Arena runner the same as a reviewer family? Is hard read-only really enforced? Can hooks run twice after compaction? Does a reference policy fork alter merge authority? Does this design introduce another durable store? Do review receipts bind precise model, host version, parent/candidate context, and SHA? Each requires independently recorded evidence at #436/#445 before a multi-agent PASS.

## Pinned comparator fork inventory

`docs/research/pstack-claude-forks-2026-10-15.json` records all 48 paths from the comparator's `tools/forks.json` at immutable revision `94f5ce95abe8a9dec976967d79941f631cf477cd` (47 pstack paths and one thermos-group path). The initial inventory was unclassified. Its current rows are `review_state=lane-triaged`, with proposed dispositions and review lanes; per-file diff review and attribution remain open under #434. This index is separate from `skills/swarm/references/classification.tsv`, which tracks canonical upstream-pin refresh only, and must not be repurposed for a third-party fork.

## ModelPlan typed wire contract

`schemas/portability/model-plan.schema.json` is the JSON Schema Draft 2020-12 wire model for `scripts/model_role_resolver.ModelPlan`. It enumerates the only legal static planning states, source-precedence labels, bounded seat ordinals, optional model/provider/family fields, human-readable reasons and effort. `evidence_level` is fixed to `static-planning-only`. An inherited model has `model=null`, `provider=null` and `family=null`; a BLOCKED plan has zero seats and at least one reason. Hosts MUST construct their own signed/receipt-bound execution records separately and MUST NOT mutate a plan into `VERIFIED` by altering its status.

## Harness identity extensibility (#446)

The #446 host-identity registry has landed in `scripts/host_identity.py` and `schemas/portability/host-id.schema.json` (#533). The source centralizes six built-in hosts, legacy aliases and the namespaced external-identity rule; host-bearing schemas reference the shared schema. Declaring an external identity does not add a native driver or promote runtime status. External identities remain candidate/GAP until host-specific evidence satisfies the existing gates.

The registry adapts the declarative-row idea from `pstack-claude/tools/runtimes.mjs`; it does not import runtime-specific model aliases, hooks or process trees. Identity registration does not load executable plugins. The implementation preserves built-in host behavior and rejects reserved namespaces and malformed identities. See `tests/test_host_identity.py` for the source-level regression contract; this design statement does not claim host runtime support or acceptance of #446, whose formal dependencies remain open.

Architecture alternatives remain: fixed enums plus `custom` are safe but inflexible; a typed identity registry is the selected seam; a generic dynamic code loader is rejected as unsafe and unnecessary. Do not repeat the registry implementation; resolve the remaining #446 acceptance and dependencies with exact-head evidence.
