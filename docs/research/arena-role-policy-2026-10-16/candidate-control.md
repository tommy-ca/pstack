# Candidate D0 — no-change control: keep the host-owned role mapping

Status: control (deliberate no-op) · Evaluated at `ae06ef1` (read-only; no repo edits by this brief).
Claim: pstack already resolves canonical role → model/effort per harness, at runtime, through
host-owned artifacts. `openspec/changes/2026-10-15-harness-neutral-role-policy/design.md`,
`schemas/portability/model-role-policy.schema.json`, `model-plan.schema.json`,
`scripts/model_role_policy.py`, `scripts/model_role_resolver.py` are **not added**.
The minimal seam is the incumbent: it is the only candidate with **zero** new surface area.

## (a) Data shape (what ships today, exactly)

```
pstack.package.json#/roles[]        22 × { id, description, default_model_role }
                                    default_model_role ∈ {fast-worker, fast-verifier,
                                    strong-judgment, strongest, panel, adversarial-panel}
                                    -> pstack-owned, single canonical registry

profiles/<host>.json                host-owned observed facts
  runtime_conventions.default_model   grok-4.6 | gpt-6.1-sol | pi | opencode | inherit
  runtime_conventions.allowed_spawn_fields / forbidden_spawn_fields
  bindings[]                          capability -> native primitive, enforcement, receipt ref
  evidence_ledger[]                   claim + scenario + observed_live|static-only

projected host manifest             host-native role->model table, generated and drift-checked:
  scripts/project-package.py:203 generate_antigravity_models(), :235 generate_codex_models()
  written at :406 / :417, verified by --check at :469 / :507

agents/<role>.md frontmatter        effort: medium|high|xhigh  (shipped per-role effort)
~/.<host>/pstack-models.<ext>       user/project override layer, host-native format
setup-pstack prose + live probe     skills/setup-pstack/SKILL.md:8,20,26,93,113 and
  references/resolve-model.md:7,10, references/resolve-effort.md:26,30, scripts/effort_ladder.py:7
```

Resolution order (already the design's order, enforced by host behavior + prose):
explicit session choice → override file → host default from `profiles/<host>.json` →
omit `model` (inherit). Unavailable slug = ask again / omit; unknown effort token = refuse.

## (b) Boundary / ownership table

| Concern | Owner today | Evidence |
| --- | --- | --- |
| Canonical role IDs + tier vocabulary | pstack (`pstack.package.json#/roles`) | 22 roles, 6 tiers; ADR 0012 |
| Concrete model per role, per host | host: `profiles/<host>.json` + projected `models.json` | ADR 0016 (`profiles/codex.json:279`); generator tables |
| Effort default per role | host-shipped agent frontmatter | `agents/arena-runners.md:4` = `xhigh` |
| Live catalog + effort enum discovery | host session, via `/setup-pstack` | `SKILL.md:20,93`; `effort_ladder.py:7` |
| Override precedence | user/project override file (host-native) | `SKILL.md:113` |
| Capability → primitive truth | host profile `bindings[]` + receipts | `profiles/omp.json` rows |
| What is *not* owned | nothing added; no new document, resolver, store or schema | — |

## (c) Why this is the minimal seam

1. **No new authority (C1).** The role registry already has exactly one home. The proposed
   policy document restates `tier_defaults`/`model_catalog` **and** `role_constraints` next to
   facts that ADR 0016 already assigns to `profiles/codex.json` + projected manifests; the
   change's own ADR manifest records that conflict as an **open precedence question (#437)**.
   D0 has no such question by construction.
2. **The added layer cannot be load-bearing (C3).** `scripts/model_role_resolver.py:1-6` states
   "No use of this planner proves a model is available, an agent spawned, or a read-only/
   isolation boundary was enforced"; `status` is "NEVER runtime VERIFIED" (:33) and
   `evidence_level` is fixed to `static-planning-only` (:37). Host-native correctness therefore
   still comes entirely from the host path D0 keeps. In the incumbent, the *only* legal answers
   for an unverified catalog are already `inherit` / omit-model — the safe behavior — with no
   static opinion that can disagree with the host.
3. **Nothing consumes the replacement (C2).** At `ae06ef1` the 1,191 lines
   (235 + 190 schema, 168 + 194 script, 68 example, 336 test) have no caller outside
   `tests/test_model_role_policy.py` and one assertion in `prove-omp-vertical-slice.py:242`;
   `scripts/verify-portable.py` and `scripts/verify-harness.py` do not reference it. The control
   adds 0 files / 0 lines to maintain or to drift.
4. **Existing drift gate is kept, not replaced (C4).** `project-package.py --check` (:469,:507)
   already fails on host-manifest drift, and `profiles/*.json` carry per-claim receipts.

## (d) What D0 rejects, and why

| Rejected | Why |
| --- | --- |
| Typed `model-role-policy` document + `ModelPlan` planner | Second statement of host model/role facts that ADR 0016 assigns to profiles + projected manifests; by its own contract it cannot authorize a dispatch, so it buys claim hygiene at the price of a second authority and an open precedence conflict (#437). |
| Generic agent-runtime gateway / DSL | Second control plane; duplicates host auth/isolation/spawn; YAGNI. |
| Import pstack-claude aliases, `models.json`, orchestration store | Declared policy fork + host-specific durable state; violates ADR 0002/0006 and the change's own non-goals. |
| Scheduler / new durable store / provider proxy | Non-goal; the control state has none and needs none. |
| Replacing the incumbent generator tables wholesale | **Conceded weakness, not defended:** their role labels are host-native compound strings (`"feature, refactoring"`, `project-package.py:214,245`), so they are not canonical role IDs and cross-host parity is not machine-comparable. Fix is host-side and in-place (emit canonical IDs; bind tiers inside the already-authoritative `profiles/<host>.json`), not a new document. |

## Failure modes of the control (honest)

- **FM1 — no fail-closed gate on policy text.** A renamed role, dropped tier or hand-edited
  prose breaks nothing that runs; `--check` catches manifest drift only.
- **FM2 — silent substitution is unenforced.** `explicit > project > user > host default >
  inherit` exists as prose (`resolve-model.md`); outside grok's own reject-or-inherit behavior
  nothing fails closed. A panel can collapse to one seat/one family and still look complete.
- **FM3 — independence claims stay untestable.** `cross-judge` family divergence and
  `interrogate-reviewers` diversity have no negative fixture; "multi-model review" can be
  asserted without a failing test.
- **FM4 — cross-host parity is manual.** omp/opencode/droid have no live catalog-detection skill
  and no per-host tier binding; a new host (#446) has no typed place to declare catalog state
  or tier defaults.
- **FM5 — cost deferred, not removed.** The same design doc and the #437 precedence question
  return at every model-generation churn (this repo already paid it once: `gpt-5.6-terra`
  elimination, ADR 0016).
- **FM6 — the six tiers are inert vocabulary.** Nothing binds a tier to a model per host, so
  `panel` vs `adversarial-panel` carries no enforceable meaning for a reviewer.

## Rubric self-score (honest, not sandbagged)

| Criterion | Score | Basis |
| --- | --- | --- |
| C1 upstream fidelity (30%) | 4 | One pinned workflow source, one role registry, no new authority; −1 for non-canonical compound labels in host manifests. |
| C2 maintenance burden (20%) | 4 | Zero new surface, reuses existing schema/profile/receipt architecture; −1 for the surviving prose drift debt across 4 files. |
| C3 host-native correctness (25%) | 3 | Live detection + omit/inherit on grok, `default_model` in profiles elsewhere; −2 because omp/opencode/droid have no runtime catalog resolution. |
| C4 verifiability (15%) | 2 | `--check` + portability doctor + receipts exist, but no model/effort/diversity negative fixtures; static-vs-runtime boundary is prose. |
| C5 boundary safety (10%) | 5 | Imports no policy fork, no durable store, no qstack router change. |

Weighted total: **3.55 / 5.00**. Surface-area delta: **+0 files, +0 lines** (tie-break winner by construction).

## Switch trigger (when the control stops being right)

Adopt a typed seam only when a *runtime* consumer exists that the host cannot supply — i.e. when
two harnesses must be compared for a model/role claim without a host session (parity matrix,
cross-judge family proof), or when a second host needs a reviewable tier binding. Then extend
`profiles/<host>.json` + the existing projector drift gate, keeping one registry and no new
document. Until such a consumer exists, the typed seam is unimplemented speculation.
