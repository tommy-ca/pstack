# Candidate D1 — typed seam: policy schema + pure static ModelPlan + thin host adapters

Branch `pr428-stack` @ `ae06ef1`. Change context: `openspec/changes/2026-10-15-harness-neutral-role-policy/{design,proposal}.md`.
This candidate is the shape the repo already shipped: it *is* the seam, not a proposal to build one. Evidence is read-only inspection of this checkout; no runtime claim is made.

## (a) Data shape

One canonical registry, one host-owned policy document, one wire type, one pure function. Nothing else.

| # | Artifact | Shape | Evidence |
|---|---|---|---|
| 1 | `pstack.package.json#/roles` — **canonical, read-only** | 22 entries `{id, description, default_model_role}`; 6 tiers: `fast-worker, fast-verifier, strong-judgment, strongest, panel, adversarial-panel`; `upstream_pin=1dcc2bac…6198fc` | descriptor head; `scripts/model_role_policy.py` |
| 2 | `schemas/portability/model-role-policy.schema.json` (Draft 2020-12, v1) driving `examples/portability/model-role-policy.example.json` | `version:1`, `canonical_source{repository:"cursor/plugins", pin:^[0-9a-f]{40}$}`, `role_source` **const** `"pstack.package.json#/roles"`, `role_constraints{<role>:{selection∈{single,panel,cross-judge}, required_capabilities[], minimum_independent_workers 1..16, require_distinct_model_families}}`, `hosts{<host>:{discovery∈{live,catalog,unverified}, model_catalog[{id,provider,family,supported_efforts[],evidence_ref}], tier_defaults{<tier>: [slug\|inherit-parent]}, role_overrides{<role>:{models[],effort,seats 1..16}}, fallback∈{inherit-parent,fail-closed}, verification_status∈{unverified,static-only,verified,stale}, catalog_observation{host_version,observed_at,receipt,implementation_revision:40hex}}}`, `constraints{allow_unverified_models:const false, require_review_for_configured_cross_judge_diversity}`. `additionalProperties:false` at every level. | shipped schema, 235 lines |
| 3 | `schemas/portability/model-plan.schema.json` — `ModelPlan` wire | `{host, role, selection∈{single,panel,cross-judge,unknown}, source∈{explicit,project,user,host-role,host-tier,inherit-parent,none}, status∈{PLANNED,DEGRADED,BLOCKED}, seats[≤16]{ordinal≥1, model\|null, family\|null, provider\|null}, reasons[], effort\|null, evidence_level **const** "static-planning-only"}`. Conditional invariants: `model:null ⇒ family:null ∧ provider:null`; `model:string ⇒ family ∧ provider required`; `status:BLOCKED ⇒ seats maxItems 0 ∧ reasons minItems 1`. | shipped schema, 190 lines |
| 4 | `scripts/model_role_resolver.py::plan_role(policy, descriptor, *, host, role, explicit, project, user, parent_family, capabilities) -> ModelPlan` | Frozen dataclasses (`ModelPlan`, `ModelSeat`); pure, no I/O, no spawn; precedence `explicit → project → user → host-role → host-tier → inherit-parent \| fail-closed`; `INHERIT={inherit-parent,auto}` normalises to `model=None`; unknown slug/effort/role/host/gap ⇒ `BLOCKED` with zero seats and a reason, **never** substitution | 194 lines + `scripts/model_role_policy.py` (168 lines) cross-document validator (`role_source`, unique role IDs, upstream-pin parity, tier/selection legality, `agent.spawn`+`agent.join` required for panels) |

Host-owned inputs are untouched: `profiles/<host>.json` keeps `bindings` (e.g. `profiles/omp.json` `agent.spawn` = `native`/`hard`/`verified` + `evidence_ref.receipt`), and `catalog_observation` binds any catalog claim to `host_version + observed_at + receipt + implementation_revision`. A plan is an *input* to `receipt.schema.json` record kinds—not a record kind. Slugs exist only as catalog rows; a checked-in catalog is not dispatch authorization (`design.md` "catalog means static inventory only").

## (b) Boundary / ownership

| Owner | Owns | MUST NOT own |
|---|---|---|
| `pstack.package.json#/roles` (canonical) | role IDs, descriptions, tier strings | host defaults, model slugs |
| `model-role-policy` doc (host-owned per-host block) | catalogs, tier defaults, role overrides, effort, seat counts, fallback, observation binding | role IDs / tier names (re-declaration is schema-illegal: `role_source` const; validator rejects unknown role keys) |
| `plan_role` | deterministic planning state `PLANNED\|DEGRADED\|BLOCKED` + reasons + source label | spawn args, availability claims, isolation, join, `VERIFIED` promotion (`evidence_level` const) |
| `profiles/<host>.json` | capability bindings, tool mappings, enforcement level, evidence refs | model catalogs, policy precedence |
| Host adapter (per harness) | seat → native spawn fields; omission of `model` for inherit | routing decisions, registry edits, durable state |
| `scripts/project-package.py` | the single projector, descriptor → manifests/hooks/stubs | a second manifest authority |
| Receipts (`schemas/portability/{receipt,evidence}.schema.json`) | runtime proof, host version, surface revisions | being synthesised from a plan |
| `qstack` (external) | post-router quant invariants | pstack router or model namespace |

## (c) Why minimal

- **No new plane, runtime, scheduler, gateway, or store.** Surface = 2 JSON Schemas + 1 example doc + 1 pure module (194 LOC) + 1 validator (168 LOC); no dependency added; nothing durable is created. Host session state stays host-owned.
- **One authority for role IDs.** `role_source` is a schema `const`, so a duplicate registry is not merely discouraged—it fails schema, then validator.
- **Failure is the default path.** Missing role/host, absent catalog slug, non-`single` topology with one model, `cross-judge` family not provably distinct from parent, advisory (`soft`/`advisory`) capability where a role needs enforcement, panel >16 seats, or model-specific effort without `discovery:"live"` + `supported_efforts` all terminate as `BLOCKED`/`DEGRADED`. `allow_unverified_models` is `const false`.
- **Static proof and runtime proof cannot be confused.** Planning status is a disjoint enum from runtime verdicts, and `evidence_level` is pinned to `static-planning-only`, so no adapter can launder a plan into a receipt.
- **Adapters stay thin because the planner emits seats, not addresses.** `inherit-parent` ⇒ omit `model`; `auto` is not a slug. Adding a host = one host block in the policy doc + one profile, zero core edits.
- **Verifiable with existing CI, no live host.** `tests/test_model_role_policy.py` already carries the negative fixtures the rubric asks for: `test_unconfigured_host_and_role_fail_closed`, `test_overrides_are_precedent_but_do_not_silently_replace_unknown_slug`, `test_inherit_parent_omits_model_and_does_not_forge_family`, `test_panel_diversity_is_not_assumed_from_repeated_family`, `test_cross_judge_prefers_different_family_from_parent`, `test_missing_required_family_diversity_blocks_without_switching_silently`, `test_unknown_or_advisory_capability_cannot_hard_pass`, `test_live_claim_without_observation_fails`, `test_wrong_effort_fails_for_named_model`, `test_plan_wire_schema_accepts_pure_planner_and_forbids_fake_runtime_claims`, plus `test_separate_seat_count_from_family_count` (seats ≠ slugs ≠ families ≠ settled agents).
- **Rubric fit:** C1 30% — one pinned workflow source, one role registry, no second authority. C2 20% — incremental on the schema/profile/receipt trio. C3 25% — per-host catalogs resolved at runtime; nothing is invented; host state untouched. C4 15% — deterministic negative fixtures + fail-closed + static/runtime separation. C5 10% — no fork import, qstack stays post-router, no hidden store.

## (d) What it rejects, and why

1. **Copy `pstack-claude` wholesale** (alternatives A in `design.md` and in its portability record). 48 declared fork paths awaiting classification (#434), a second durable store (`~/.claude/orchestrate`, closed #402), Pi-specific engine behaviour that proves nothing about OMP.
2. **Generic agent-runtime gateway / policy DSL + workflow DB** (candidate C). Second control plane; must re-implement native auth, isolation and memory semantics; maximum untested surface — YAGNI.
3. **Prose-only mapping as the final design** (candidate D). Untestable drift; retained *only* for non-executable host guidance.
4. **A second role registry or hand-maintained per-host manifests.** Two authorities guarantee divergence across 22 roles; `project-package.py` stays the only projector.
5. **In-resolver host probing (dynamic discovery in `plan_role`).** Makes planning impure, non-deterministic and tempts a static result to stand in for availability proof. Discovery output is typed metadata; `catalog_observation` + a separate runtime receipt gate it.
6. **A second catalog copy inside `profiles/<host>.json`.** The per-host block is already host-owned and keyed by the same host ID; duplicating rows creates a merge/drift hazard with no added authority. `profiles/` currently holds bindings, not catalogs (`grep model_catalog profiles/` → no hits).
7. **A single artifact that also carries runtime proof (post-dispatch `VERIFIED`).** Conflates static and native evidence; the wire schema forbids it structurally.
8. **Invented seats or mandatory fan-out.** `seats` counts planned invocations on possibly one slug; the canonical default stays one runner; `DEGRADED`/`BLOCKED` is mandatory when family independence is unproven.
9. **Dynamic/untrusted host-identity code loading (from #446's registry option).** Executing adapter code during schema validation is not acceptable; fixed six-host enum + `custom` remains until #446 clears a descriptor-validated registry.
10. **`qstack` as router, or any policy-fork import.** Domain overlay stays post-routing.

**Alternatives considered and rejected for *this* seam specifically:** single policy document that also holds role IDs (rejected — C1, drift); per-host manifests generated by hand (rejected — C2, two authorities); planner returning a fully resolved native spawn call (rejected — C3/C4, plans would assert availability); catalog-only authorization with no `discovery` gate (rejected — C4, static inventory promoted to availability); and letting callers pass capability attestations the planner trusts as receipts (`design.md` remnant #1 — rejected; caller metadata is advisory, `unknown != supported`).
